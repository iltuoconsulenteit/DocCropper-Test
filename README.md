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
- Upload one or more images (on mobile devices the file picker can use the camera directly)
- Manually adjust the four corners of each image
- Submit data (image, coordinates, size) to the backend
- Export all processed images to PDF
- Choose how many processed images appear on each PDF page
- Select portrait or landscape orientation for the PDF
- Choose whether images are arranged horizontally, vertically or in a grid and preview the layout before exporting
- Control how images are scaled on each page: fill the cell, keep original size or apply a custom percentage.
  When using **Original** or **100%** the generator now adjusts for the image's
  DPI so photos scanned at 150–200 DPI render closer to real size on a 300 DPI
-  PDF page.
- A small margin is applied around each image so nothing touches the page edges
- Change the interface language (Italian translation included)
- The layout is responsive so DocCropper works well on smartphones and tablets

All JavaScript is contained in `static/app.js`.

### Data sent to backend:
- `original_height`, `original_width`: dimensions of the image
- `points`: coordinates of the 4 corners (TL, TR, BR, BL)
- `image_file`: the uploaded file

After all images are processed, choose how many images appear on each page, how they are scaled, the page orientation and the image arrangement. A small preview updates to reflect your choices before you use **Export PDF** to download.
The interface includes small placeholder logos encoded directly in the HTML. Replace these `data:` URIs with your own branding. Place your own images inside `static/logos/` and reference them from `static/index.html`.
The expected filenames are `header_logo.png` for the top banner and `footer_logo.png` for the footer. If these files are missing, the placeholders will be used automatically.
You can also show a custom brand name or logo in the top‑right corner by placing any HTML snippet in the `brand_html` value inside `settings.json`. Whatever you put there will be injected into the `brandBox` element of the header when the page loads.
The footer displays the current Git commit hash so you can confirm which version of DocCropper is running.
Default preferences for language, PDF layout, page orientation, scaling and the HTTP server port are stored in `settings.json`. When users sign in, their personal preferences are saved in the `users/` folder using their email address, accessed through the `/user-settings` API. Without logging in the global `settings.json` values are used. Edit the `port` value if you want DocCropper to listen on a different port.
You can also configure a small payment box through `settings.json` by setting `payment_mode` to `donation` or `subscription` (the value is read case‑insensitively). By default `payment_mode` is `donation`. Provide your PayPal or Stripe link (and optional bank transfer details) using the `paypal_link`, `stripe_link` and `bank_info` fields. When enabled, the interface shows a box with those payment options so users can donate or subscribe. If no links are configured the box still appears with a notice. These boxes are visible even in demo or developer mode.
If you supply a `google_client_id` in `settings.json`, DocCropper displays a Google sign‑in button so users can authenticate with their Google account. Without this ID the login area simply shows a "Login not configured" message. After signing in, the app can associate the logged in user with a donation or subscription plan. The login box is visible regardless of licensing.
When a user signs in the server stores a cookie with the email address and loads or saves settings specific to that user inside the `users/` directory.
Without a valid license the exported PDF shows a large "DEMO" watermark from the second page onward. For testing or demonstrations you may use a developer key placed manually in `settings.json`. License keys are compared case‑insensitively. When DocCropper detects the developer key all features are unlocked automatically. Request the developer key from **doccropper@iltuoconsulenteit.it**.
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
- A margin is always kept around each image so they don't run into the edges when printed
 - Uploaded files are stored in a temporary folder unique to each browser session. The folder
   stays available after exporting a PDF so you can regenerate it if needed. Old session
   directories are automatically cleaned up after about an hour

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

Run `install/install_DocCropper.sh` on Linux or macOS (or double‑click `install/install_DocCropper.command` on macOS) and `install/install_DocCropper.bat` on Windows from the folder where you want the project. If the script lives inside an existing clone under `install/` it updates that copy; otherwise it creates a new `DocCropper` subfolder next to the script. Both versions verify that `git`, `python3`/`python` and `pip3`/`pip` are available before pulling the latest changes with `--rebase --autostash`. At the end the script can start the application automatically using the configured port.

After cloning or updating, the installer optionally asks for a license key. Leaving it blank keeps the application in demo mode. If the key does not match a valid commercial or developer key the installer warns that it is invalid and continues in demo mode. Valid keys together with the licensee name are stored in `settings.json` so the interface shows "Licensed to &lt;name&gt;". After the setup completes it can launch the application through the companion `start_DocCropper` script for your platform.

The application reads configuration from `settings.json` in the project root. You can pre-populate this file with your preferred defaults or edit it later.
A small status box in the interface shows "DEMO" or "Licensed to &lt;name&gt;" based on these settings.

If `settings.json` contains the developer license key, the installer pulls updates
from the branch specified by `DOCROPPER_BRANCH` (default
`dgwo4q-codex/add-features-from-doccropper-project`) instead of the `main` branch.

### ▶️ Running DocCropper

Use `install/start_DocCropper.sh` on Linux, `install/start_DocCropper.command` on macOS or `install/start_DocCropper.bat` on Windows to run the server later. The script creates a virtual environment when needed, installs requirements and launches the app on the port defined in `settings.json`.
If the application keeps running after closing the window, run the matching `stop_DocCropper` script to shut it down (or send a `POST` request to `/shutdown/`).

### 🖥 Tray icon

For convenience you can run `doccropper_tray.py` which adds a small system tray
icon and writes activity to `doccropper_tray.log` in the project folder. On
Windows run it with `pythonw` (or rename it to `doccropper_tray.pyw`) so no
console window appears. The menu lets you start or stop the server and update it
using the installer scripts. Set `DOCROPPER_DEVELOPER=1` to also show an
*Update from branch* option that respects `DOCROPPER_BRANCH`.
Developer mode is automatically enabled when the developer license key is present in `settings.json`.
The start scripts automatically create a virtual environment and install
`requirements.txt`, so dependencies like OpenCV are available when the server
launches.

## 🔓 Licensing and commercial version

**DocCropper** is released under the [MIT](LICENSE.txt) license. Without a valid key the software runs in **DEMO** mode. PDFs exported in demo mode keep a large "DEMO" watermark from the second page onward, though you can still upload multiple images.

### 💼 PRO features

- removal of the watermark on multipage PDFs
- OCR modules and saving to network folders (in development)
- LAN access with authentication

### 💰 Pricing and activation

Purchasing a PRO license provides a `license.key` file and the registered licensee name. Placing this file in the project folder shows "Licensed to <name>" in the interface and unlocks all features.

### 🔑 Developer key

For demonstrations and testing you may use a developer key. Place this key in the `license_key` field of `settings.json`. When DocCropper detects the developer key the interface shows `Licensed to Developer` and behaves like the full version.

For commercial inquiries: **doccropper@iltuoconsulenteit.it**.

