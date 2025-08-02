import base64
import io
import logging
import json
import math
import os
import shutil
import time
import uuid

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile, Body, Request
from PIL import Image
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import subprocess
from dotenv import load_dotenv

SETTINGS_FILE = "settings.json"
# Load environment variables from any .env files in env/
ENV_DIR = "env"
if os.path.isdir(ENV_DIR):
    for name in os.listdir(ENV_DIR):
        if name.endswith(".env"):
            load_dotenv(os.path.join(ENV_DIR, name), override=False)
# Directory containing per-user settings
USERS_DIR = "users"

# Developer license key for demonstration (case-insensitive)
DEV_LICENSE_KEY = os.environ.get("DOCROPPER_DEV_LICENSE", "ILTUOCONSULENTEIT-DEV")
DEV_LICENSE_KEY_UPPER = DEV_LICENSE_KEY.upper()

try:
    VERSION = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=os.path.dirname(__file__),
    ).decode().strip()
except Exception:
    VERSION = "unknown"

SESSIONS_ROOT = "sessions"
PID_FILE = "doccropper.pid"

DEFAULT_SETTINGS = {
    "language": "en",
    "layout": 1,
    "orientation": "portrait",
    "arrangement": "auto",
    "scale_mode": "fit",
    "scale_percent": 100,
    "port": 8000,
    "license_key": "",
    "license_name": "",
    "payment_mode": "donation",
    "paypal_link": "",
    "stripe_link": "",
    "bank_info": "",
    "google_client_id": "",
    "brand_html": "",
}

def get_session_dir(session_id: str) -> str:
    if not session_id:
        return None
    path = os.path.join(SESSIONS_ROOT, session_id)
    os.makedirs(path, exist_ok=True)
    return path

def cleanup_old_sessions(max_age: int = 3600):
    if not os.path.exists(SESSIONS_ROOT):
        return
    now = time.time()
    for name in os.listdir(SESSIONS_ROOT):
        p = os.path.join(SESSIONS_ROOT, name)
        try:
            if os.path.isdir(p) and now - os.path.getmtime(p) > max_age:
                shutil.rmtree(p, ignore_errors=True)
        except Exception:
            pass

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w") as fh:
            json.dump(DEFAULT_SETTINGS, fh)
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE) as fh:
            base = json.load(fh)
        merged = DEFAULT_SETTINGS.copy()
        merged.update(base)
        env_key = os.getenv("DOCROPPER_LICENSE_KEY")
        env_name = os.getenv("DOCROPPER_LICENSE_NAME")
        if env_key:
            merged["license_key"] = env_key
        if env_name:
            merged["license_name"] = env_name
        return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(update: dict):
    data = load_settings()
    data.update(update)
    with open(SETTINGS_FILE, "w") as fh:
        json.dump(data, fh)
    return data

def sanitize_email(email: str) -> str:
    return email.replace("@", "_at_").replace(".", "_")

def load_user_settings(email: str):
    base = load_settings()
    os.makedirs(USERS_DIR, exist_ok=True)
    path = os.path.join(USERS_DIR, sanitize_email(email) + ".json")
    if os.path.exists(path):
        try:
            with open(path) as fh:
                user = json.load(fh)
            base.update(user)
        except Exception:
            pass
    return base

def save_user_settings(email: str, update: dict):
    os.makedirs(USERS_DIR, exist_ok=True)
    path = os.path.join(USERS_DIR, sanitize_email(email) + ".json")
    data = {}
    if os.path.exists(path):
        try:
            with open(path) as fh:
                data = json.load(fh)
        except Exception:
            data = {}
    data.update(update)
    with open(path, "w") as fh:
        json.dump(data, fh)
    merged = load_settings()
    merged.update(data)
    return merged

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    cleanup_old_sessions()
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = uuid.uuid4().hex
    get_session_dir(session_id)
    try:
        with open("static/index.html") as f:
            content = f.read()
    except FileNotFoundError:
        logger.error("static/index.html not found")
        return HTMLResponse(content="Frontend not found.", status_code=500)
    response = HTMLResponse(content=content, status_code=200)
    response.set_cookie("session_id", session_id, httponly=True)
    return response


@app.get("/settings/")
async def get_settings():
    data = load_settings()
    data["version"] = VERSION
    return data


@app.post("/settings/")
async def update_settings(settings: dict = Body(...)):
    return save_settings(settings)


@app.get("/user-settings/")
async def get_user_settings_endpoint(request: Request):
    email = request.cookies.get("user_email")
    if not email:
        return JSONResponse(status_code=401, content={"message": "Not logged in"})
    data = load_user_settings(email)
    data["version"] = VERSION
    return data


@app.post("/user-settings/")
async def update_user_settings_endpoint(request: Request, settings: dict = Body(...)):
    email = request.cookies.get("user_email")
    if not email:
        return JSONResponse(status_code=401, content={"message": "Not logged in"})
    data = save_user_settings(email, settings)
    data["version"] = VERSION
    return data


@app.post("/google-login/")
async def google_login(token: str = Body(...)):
    settings = load_settings()
    client_id = settings.get("google_client_id", "")
    if not client_id:
        return JSONResponse(status_code=400, content={"message": "Google login not configured"})
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests
        info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
        resp = JSONResponse({"email": info.get("email"), "name": info.get("name")})
        if info.get("email"):
            resp.set_cookie("user_email", info.get("email"), httponly=True)
        return resp
    except Exception as e:
        logger.exception("Google token verification failed")
        return JSONResponse(status_code=400, content={"message": "Invalid token"})


@app.post("/process-image/")
async def process_image(
    request: Request,
    image_file: UploadFile = File(...),
    points: str = Form(...), # JSON string of points: "[x1,y1,x2,y2,x3,y3,x4,y4]"
    original_width: int = Form(...),
    original_height: int = Form(...)
):
    logger.info(f"Received image: {image_file.filename}, original_width: {original_width}, original_height: {original_height}")
    logger.info(f"Received points string (raw form data): {points}")
    session_id = request.cookies.get("session_id")
    session_dir = get_session_dir(session_id)
    try:
        # Read image
        contents = await image_file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_cv is None:
            logger.error("Failed to decode image.")
            return JSONResponse(status_code=400, content={"message": "Invalid image file"})

        logger.info(f"Image decoded successfully. Shape: {img_cv.shape} (HxWxC)")

        # Parse points from JSON string
        # Points are expected as a flat list: [p1x, p1y, p2x, p2y, p3x, p3y, p4x, p4y]
        # Frontend order: Top-Left, Top-Right, Bottom-Right, Bottom-Left
        try:
            scaled_points_flat = json.loads(points)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse points JSON: {points}")
            return JSONResponse(status_code=400, content={"message": "Invalid points JSON format."})

        if not isinstance(scaled_points_flat, list) or len(scaled_points_flat) != 8:
            logger.error(f"Invalid number of points or format: {len(scaled_points_flat)} points, type: {type(scaled_points_flat)}")
            return JSONResponse(status_code=400, content={"message": "Requires an array of 8 coordinates for 4 points."})

        # Reshape points to (4, 2) for OpenCV
        # Ensure points are float32
        src_pts = np.array(scaled_points_flat, dtype=np.float32).reshape((4, 2))
        logger.info(f"Source points for perspective transform (scaled to original image, TL, TR, BR, BL order expected): \n{src_pts}")


        # Define destination points for perspective transform (output rectangle)
        # The order of these points must correspond to the order of src_pts
        # src_pts order: Top-Left, Top-Right, Bottom-Right, Bottom-Left

        tl, tr, br, bl = src_pts # Unpack for clarity in dimension calculation

        # Calculate width of the new image based on the longer of the top/bottom edges of the selection
        width_a = np.sqrt(((br[0] - bl[0])**2) + ((br[1] - bl[1])**2)) # Length of bottom edge
        width_b = np.sqrt(((tr[0] - tl[0])**2) + ((tr[1] - tl[1])**2)) # Length of top edge
        max_width = max(int(width_a), int(width_b))


        # Let's calculate height based on the selected left/right edges first,
        # then decide if we override it with a fixed aspect ratio.
        height_from_selection_a = np.sqrt(((tr[0] - br[0])**2) + ((tr[1] - br[1])**2)) # Length of right edge
        height_from_selection_b = np.sqrt(((tl[0] - bl[0])**2) + ((tl[1] - bl[1])**2)) # Length of left edge
        max_height_from_selection = max(int(height_from_selection_a), int(height_from_selection_b))


        # For this example, let's enforce a portrait A4-like aspect ratio.
        # If the calculated max_width is likely the shorter dimension of the paper:
        A4_PORTRAIT_RATIO_H_W = math.sqrt(2)
        max_height = int(max_width * A4_PORTRAIT_RATIO_H_W)

        logger.info(f"Max width from selection: {max_width}")
        logger.info(f"Max height from selection (before aspect ratio adjustment): {max_height_from_selection}")
        logger.info(f"Target max height (after A4 portrait aspect ratio adjustment): {max_height}")


        if max_width <= 0 or max_height <=0: # Check adjusted max_height
            logger.error(f"Calculated max_width or max_height is zero or negative. Width: {max_width}, Adjusted Height: {max_height}. Points: {src_pts.tolist()}")
            # Fallback to selection height if adjusted height is problematic
            max_height = max_height_from_selection
            if max_height <=0:
                 return JSONResponse(status_code=400, content={"message": "Invalid points leading to zero/negative output dimensions even after fallback."})
            logger.warning(f"Falling back to max_height_from_selection: {max_height}")


        # Define the 4 corners of the output rectangle using the potentially adjusted max_height
        dst_pts = np.array([
            [0, 0],                          # Top-left corner of output
            [max_width - 1, 0],              # Top-right corner of output
            [max_width - 1, max_height - 1], # Bottom-right corner of output
            [0, max_height - 1]              # Bottom-left corner of output
        ], dtype=np.float32)

        logger.info(f"Destination points for perspective transform (output rectangle corners): \n{dst_pts}")
        logger.info(f"Calculated output dimensions for warped image: Width={max_width}, Height={max_height}")

        # Perform the perspective transform
        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

        if matrix is None:
            logger.error("Failed to compute perspective transform matrix. Points might be collinear or invalid.")
            return JSONResponse(status_code=400, content={"message": "Could not compute perspective transform. Check point alignment."})

        logger.info(f"Perspective transform matrix: \n{matrix}")

        warped_image = cv2.warpPerspective(img_cv, matrix, (max_width, max_height))
        logger.info(f"Image warped successfully. Warped shape: {warped_image.shape}")

        # ---- Image Sharpening Step ----
        kernel = np.array([[-1,-1,-1],
                           [-1, 9,-1],
                           [-1,-1,-1]])

        # Apply the kernel to the warped image
        sharpened_image = cv2.filter2D(warped_image, -1, kernel)
        logger.info(f"Image sharpened successfully. Sharpened shape: {sharpened_image.shape}")


        # Encode processed image (now the sharpened one) to base64 to send to frontend
        success, img_encoded_buffer = cv2.imencode(".png", sharpened_image) # Use sharpened_image
        if not success:
            logger.error("Failed to encode sharpened image to PNG.")
            return JSONResponse(status_code=500, content={"message": "Failed to encode processed image."})

        img_base64 = base64.b64encode(img_encoded_buffer).decode("utf-8")

        if session_dir:
            try:
                fname = os.path.join(session_dir, f"{uuid.uuid4().hex}.png")
                with open(fname, "wb") as fh:
                    fh.write(img_encoded_buffer)
            except Exception:
                logger.exception("Failed to save processed image to session dir")

        return JSONResponse(content={
            "message": "Image processed successfully",
            "processed_image": "data:image/png;base64," + img_base64
        })

    except json.JSONDecodeError as e:
        logger.exception(f"JSON parsing error: {e}")
        return JSONResponse(status_code=400, content={"message": f"Invalid points format: {e}"})
    except Exception as e:
        logger.exception("An error occurred during image processing.")
        return JSONResponse(status_code=500, content={"message": f"An internal error occurred: {str(e)}"})


@app.post("/create-pdf/")
async def create_pdf(
    request: Request,
    images: list[str] = Body(...),
    layout: int = Body(1),
    orientation: str = Body("portrait"),
    arrangement: str = Body("auto"),
    scale_mode: str = Body("fit"),
    scale_percent: int = Body(100)
):
    try:
        settings = load_settings()
        key = settings.get("license_key", "").strip().upper()
        licensed = bool(key)
        if key == DEV_LICENSE_KEY_UPPER:
            licensed = True
        session_id = request.cookies.get("session_id")
        session_dir = get_session_dir(session_id)
        pil_images = []
        for img_b64 in images:
            if img_b64.startswith('data:'):
                img_b64 = img_b64.split(',', 1)[1]
            img_bytes = base64.b64decode(img_b64)
            pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            pil_images.append(pil_img)

        if not pil_images:
            return JSONResponse(status_code=400, content={"message": "No images provided"})

        layout = max(1, layout)
        if layout not in (1, 2, 4):
            layout = 1

        arrangement = arrangement.lower()
        if arrangement not in ("auto", "vertical", "horizontal", "grid"):
            arrangement = "auto"

        orientation = orientation.lower()
        if orientation not in ("portrait", "landscape"):
            orientation = "portrait"

        cols = 1
        rows = 1
        if layout == 2:
            if arrangement == "horizontal":
                cols, rows = 2, 1
            elif arrangement == "vertical":
                cols, rows = 1, 2
            else:  # auto
                if orientation == "landscape":
                    cols, rows = 2, 1
                else:
                    cols, rows = 1, 2
        elif layout == 4:
            if arrangement == "horizontal":
                cols, rows = 4, 1
            elif arrangement == "vertical":
                cols, rows = 1, 4
            else:  # grid or auto
                cols, rows = 2, 2

        if orientation == "portrait":
            page_w, page_h = 2480, 3508
        else:
            page_w, page_h = 3508, 2480

        scale_mode = scale_mode.lower()
        if scale_mode not in ("fit", "original", "percent"):
            scale_mode = "fit"
        cell_w = page_w // cols
        cell_h = page_h // rows
        margin = 40  # pixels of padding around each image
        inner_w = max(1, cell_w - margin * 2)
        inner_h = max(1, cell_h - margin * 2)

        pages = []
        TARGET_DPI = 300
        for i in range(0, len(pil_images), layout):
            page_index = i // layout
            page = Image.new("RGB", (page_w, page_h), "white")
            for j, img in enumerate(pil_images[i:i+layout]):
                col = j % cols
                row = j // cols
                temp = img.copy()

                img_dpi = temp.info.get("dpi", (72, 72))[0] or 72
                dpi_ratio = TARGET_DPI / img_dpi

                if scale_mode == "percent":
                    ratio = max(0.01, scale_percent / 100.0) * dpi_ratio
                elif scale_mode == "fit":
                    ratio = min(inner_w / temp.width, inner_h / temp.height)
                else:  # original
                    ratio = dpi_ratio

                max_ratio = min(inner_w / temp.width, inner_h / temp.height)
                if ratio > max_ratio:
                    ratio = max_ratio

                new_w = max(1, int(temp.width * ratio))
                new_h = max(1, int(temp.height * ratio))
                temp = temp.resize((new_w, new_h), Image.LANCZOS)
                offset_x = col * cell_w + margin + (inner_w - new_w) // 2
                offset_y = row * cell_h + margin + (inner_h - new_h) // 2
                page.paste(temp, (offset_x, offset_y))
            if not licensed and page_index > 0:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(page)
                text = "DEMO"
                try:
                    font_size = min(page_w, page_h) // 8
                    font = ImageFont.truetype("DejaVuSans.ttf", font_size)
                except Exception:
                    font = ImageFont.load_default()
                bbox_method = getattr(draw, "textbbox", None)
                if callable(bbox_method):
                    bbox = bbox_method((0, 0), text, font=font)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                else:
                    size_method = getattr(draw, "textsize", None)
                    if callable(size_method):
                        tw, th = size_method(text, font=font)
                    else:
                        tw, th = font.getsize(text)
                draw.text(
                    ((page_w - tw) / 2, (page_h - th) / 2),
                    text,
                    fill=(255, 0, 0),
                    font=font,
                )
            pages.append(page)

        pdf_bytes_io = io.BytesIO()
        pages[0].save(pdf_bytes_io, format="PDF", save_all=True, append_images=pages[1:])
        pdf_bytes = pdf_bytes_io.getvalue()
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
        # Do not delete the session immediately so the user can re-export if needed
        return JSONResponse(content={"pdf": "data:application/pdf;base64," + pdf_base64})
    except Exception as e:
        logger.exception("Failed to create PDF")
        return JSONResponse(status_code=500, content={"message": f"Could not create PDF: {str(e)}"})


@app.post("/shutdown/")
async def shutdown():
    server = getattr(app.state, "server", None)
    if server:
        server.should_exit = True
        return {"message": "Shutting down"}
    return {"message": "Server not running"}

if __name__ == "__main__":
    import argparse
    import signal

    parser = argparse.ArgumentParser(description="Run or control DocCropper")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--stop", action="store_true", help="Stop a running instance")
    args = parser.parse_args()

    if args.stop:
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE) as fh:
                    pid = int(fh.read().strip())
                os.kill(pid, signal.SIGTERM)
                print(f"Stopped DocCropper (PID {pid})")
                os.remove(PID_FILE)
            except Exception as e:
                print(f"Failed to stop server: {e}")
        else:
            print("PID file not found. Server may not be running.")
        raise SystemExit

    settings = load_settings()
    port = args.port if args.port is not None else int(settings.get("port", 8000))

    config = uvicorn.Config(app, host=args.host, port=port)
    server = uvicorn.Server(config)
    app.state.server = server
    with open(PID_FILE, "w") as fh:
        fh.write(str(os.getpid()))
    try:
        server.run()
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
