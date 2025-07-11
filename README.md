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
- Control how images are scaled on each page: fill the cell, keep original size or apply a custom percentage.
  When using **Original** or **100%** the generator now adjusts for the image's
  DPI so photos scanned at 150–200 DPI render closer to real size on a 300 DPI
  PDF page.
- Change the interface language (Italian translation included)

All JavaScript is contained in `static/app.js`.

### Data sent to backend:
- `original_height`, `original_width`: dimensions of the image
- `points`: coordinates of the 4 corners (TL, TR, BR, BL)
- `image_file`: the uploaded file

After all images are processed, choose how many images appear on each page, how they are scaled and whether the PDF is in portrait or landscape orientation, then use the **Export PDF** button to download it.
The interface includes small placeholder logos encoded directly in the HTML. Replace these `data:` URIs with your own branding. Place your own images inside `static/logos/` and reference them from `static/index.html`.
The expected filenames are `header_logo.png` for the top banner and `footer_logo.png` for the footer. If these files are missing, the placeholders will be used automatically.
Default preferences for language, PDF layout, page orientation and scaling are stored in `settings.json`. Any change you make through the interface is saved back to this file via the `/settings` API.
Without a valid license key in `settings.json` the exported PDF includes a large "DEMO" watermark centered on each page.
Language JSON files live in `static/lang/`. Add additional translations by creating new `<code>lang.json</code>` files and updating the language selector.
Processed images appear as thumbnails. Each thumbnail offers **Rotate**, **Edit**, and **Delete** buttons so you can refine the results. Click a thumbnail itself to view it in a modal overlay.

---

## 🐍 Backend

Implemented with **FastAPI** + **Uvicorn**, the backend:

- Applies a perspective transformation
- Crops the image to corrected bounds
- Applies optional sharpening filter
- Saves or returns the corrected image
- Compiles all processed images into a single **PDF**, arranging up to four per page
- Supports portrait or landscape page orientation; when using two images per page, landscape arranges them horizontally
- Images can be scaled per page: fill the cell, keep original size or apply a custom percentage

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

The application reads configuration from `settings.json` in the project root. You can pre-populate this file with your preferred defaults or edit it later.

