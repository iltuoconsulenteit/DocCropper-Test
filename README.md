# DocCropper

🗂️ *DocCropper* is a fork of [`varna9000/image-perspective-crop`](https://github.com/varna9000/image-perspective-crop), enhanced to support:

- ✅ Multi-image upload
- 📐 Batch perspective correction
- 📄 Export to PDF
- 🧰 LAN-ready setup for document stations

---

## 🔧 Frontend

This project uses [Interact.JS](https://github.com/taye/interact.js) for managing draggable corner points.

The frontend allows the user to:
- Upload one or more images
- Manually adjust the four corners of each image
- Submit data (image, coordinates, size) to the backend
- Export all processed images to PDF
- Choose how many processed images appear on each PDF page
- Select portrait or landscape orientation for the PDF. With two images per page, landscape places them side by side while portrait stacks them vertically

All JavaScript is contained in `static/app.js`.

### Data sent to backend:
- `original_height`, `original_width`: dimensions of the image
- `points`: coordinates of the 4 corners (TL, TR, BR, BL)
- `image_file`: the uploaded file

After all images are processed, choose how many images appear on each page and whether the PDF is in portrait or landscape orientation, then use the **Export PDF** button to download it.
The interface includes small placeholder logos encoded directly in the HTML. Replace these `data:` URIs with your own branding. A convenient place for custom logos is `static/logos/` (create it if missing) and reference the files from `static/index.html`.

---

## 🐍 Backend

Implemented with **FastAPI** + **Uvicorn**, the backend:

- Applies a perspective transformation
- Crops the image to corrected bounds
- Applies optional sharpening filter
- Saves or returns the corrected image
- Compiles all processed images into a single **PDF**, arranging up to four per page
- Supports portrait or landscape page orientation; when using two images per page, landscape arranges them horizontally

---

## 🚀 Setup Instructions

### 🧱 Create virtual environment

```bash
cd doccropper
python -m venv venv
venv\Scripts\activate        # On Windows
# OR
source venv/bin/activate     # On Linux/macOS

pip install --upgrade pip
pip install -r requirements.txt
```

You could use other server-side languages or tools for this processing (e.g. Imagemagick).

### 🛠 Install script

Run `./install_DocCropper.sh` to clone or update the project in `~/Scrivania/DocCropper`. The script checks for `git`, `python3`, and `pip3` before pulling the latest changes with `--rebase`.

