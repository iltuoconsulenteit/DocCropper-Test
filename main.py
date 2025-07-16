import base64
import io
import logging
import json
import math
import os
import subprocess

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile, Body
from PIL import Image
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

SETTINGS_FILE = "settings.json"
# Developer license key for demonstration
DEV_LICENSE_KEY = os.environ.get("DOCROPPER_DEV_LICENSE", "ILTUOCONSULENTEIT-DEV")

def get_last_commit_date() -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--date=short", "--pretty=%ad"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().replace("-", "")
    except Exception:
        return ""

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        data = {"language": "en", "layout": 1, "orientation": "portrait", "arrangement": "auto", "scale_mode": "fit", "scale_percent": 100, "port": 8000, "license_key": "", "license_name": "", "payment_mode": "none", "paypal_link": "", "stripe_link": "", "bank_info": "", "google_client_id": ""}
        with open(SETTINGS_FILE, "w") as fh:
            json.dump(data, fh)
        return data
    try:
        with open(SETTINGS_FILE) as fh:
            return json.load(fh)
    except Exception:
        return {"language": "en", "layout": 1, "orientation": "portrait", "arrangement": "auto", "scale_mode": "fit", "scale_percent": 100, "port": 8000, "license_key": "", "license_name": "", "payment_mode": "none", "paypal_link": "", "stripe_link": "", "bank_info": "", "google_client_id": ""}

def save_settings(update: dict):
    data = load_settings()
    data.update(update)
    with open(SETTINGS_FILE, "w") as fh:
        json.dump(data, fh)
    return data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("static/index.html") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        logger.error("static/index.html not found")
        return HTMLResponse(content="Frontend not found.", status_code=500)


@app.get("/settings/")
async def get_settings():
    return load_settings()


@app.post("/settings/")
async def update_settings(settings: dict = Body(...)):
    return save_settings(settings)


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
        return {"email": info.get("email"), "name": info.get("name")}
    except Exception as e:
        logger.exception("Google token verification failed")
        return JSONResponse(status_code=400, content={"message": "Invalid token"})


@app.post("/verify-dev-password/")
async def verify_dev_password(password: str = Body(...)):
    settings = load_settings()
    if settings.get("license_key") != DEV_LICENSE_KEY:
        return JSONResponse(status_code=400, content={"message": "Developer key not set"})
    if password == get_last_commit_date():
        return {"ok": True}
    return JSONResponse(status_code=403, content={"message": "Invalid"})


@app.post("/process-image/")
async def process_image(
    image_file: UploadFile = File(...),
    points: str = Form(...), # JSON string of points: "[x1,y1,x2,y2,x3,y3,x4,y4]"
    original_width: int = Form(...),
    original_height: int = Form(...)
):
    logger.info(f"Received image: {image_file.filename}, original_width: {original_width}, original_height: {original_height}")
    logger.info(f"Received points string (raw form data): {points}")

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
    images: list[str] = Body(...),
    layout: int = Body(1),
    orientation: str = Body("portrait"),
    arrangement: str = Body("auto"),
    scale_mode: str = Body("fit"),
    scale_percent: int = Body(100),
    dev_password: str | None = Body(None)
):
    try:
        settings = load_settings()
        key = settings.get("license_key", "")
        if key == DEV_LICENSE_KEY:
            licensed = dev_password == get_last_commit_date()
        else:
            licensed = bool(key)
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
                try:
                    bbox = draw.textbbox((0, 0), text, font=font)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                except AttributeError:
                    tw, th = draw.textsize(text, font=font)
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
        return JSONResponse(content={"pdf": "data:application/pdf;base64," + pdf_base64})
    except Exception as e:
        logger.exception("Failed to create PDF")
        return JSONResponse(status_code=500, content={"message": f"Could not create PDF: {str(e)}"})

if __name__ == "__main__":
    settings = load_settings()
    try:
        port = int(settings.get("port", 8000))
    except Exception:
        port = 8000
    uvicorn.run(app, host="0.0.0.0", port=port)
