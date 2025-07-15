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
- Select portrait or landscape orientation for the PDF
- Choose whether images are arranged horizontally, vertically or in a grid and preview the layout before exporting
- Control how images are scaled on each page: fill the cell, keep original size or apply a custom percentage.
  When using **Original** or **100%** the generator now adjusts for the image's
  DPI so photos scanned at 150–200 DPI render closer to real size on a 300 DPI
  PDF page.
- A small margin is applied around each image so nothing touches the page edges
- Change the interface language (Italian translation included)

All JavaScript is contained in `static/app.js`.

### Data sent to backend:
- `original_height`, `original_width`: dimensions of the image
- `points`: coordinates of the 4 corners (TL, TR, BR, BL)
- `image_file`: the uploaded file

After all images are processed, choose how many images appear on each page, how they are scaled, the page orientation and the image arrangement. A small preview updates to reflect your choices before you use **Export PDF** to download.
The interface includes small placeholder logos encoded directly in the HTML. Replace these `data:` URIs with your own branding. Place your own images inside `static/logos/` and reference them from `static/index.html`.
The expected filenames are `header_logo.png` for the top banner and `footer_logo.png` for the footer. If these files are missing, the placeholders will be used automatically.
Default preferences for language, PDF layout, page orientation and scaling are stored in `settings.json`. Any change you make through the interface is saved back to this file via the `/settings` API.
Without una licenza valida i PDF esportati mostrano un grande watermark "DEMO" da pagina due in poi. Per prove e dimostrazioni puoi inserire la chiave `ILTUOCONSULENTEIT-DEV` in `settings.json` o indicarla tramite la variabile `DOCROPPER_DEV_LICENSE`.
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

Run `install_DocCropper.sh` on Linux/macOS or `install_DocCropper.bat` on Windows from the folder where you want the project. If the script is inside an existing clone it simply updates that copy. Otherwise it creates a new `DocCropper` subfolder next to the script. Both versions verify that `git`, `python3`/`python` and `pip3`/`pip` are available before pulling the latest changes with `--rebase`.

The application reads configuration from `settings.json` in the project root. You can pre-populate this file with your preferred defaults or edit it later.

## 🔓 Licenza e versione commerciale

**DocCropper** è distribuito con licenza [MIT](LICENSE.txt). Senza una chiave valida il programma rimane in modalità **DEMO**. È comunque possibile caricare più immagini ed esportare in PDF: dalla seconda pagina in poi comparirà un vistoso watermark "DEMO".

### 💼 Funzionalità PRO

- rimozione del watermark dai PDF multipagina
- moduli OCR e salvataggio su cartelle di rete (in sviluppo)
- accesso LAN con autenticazione

### 💰 Costi e attivazione

L'acquisto della licenza PRO fornisce un file `license.key` e l'indicazione del nominativo a cui è intestata. Inserendo questo file nella cartella del progetto l'interfaccia mostrerà "Licenziato a &lt;nome&gt;" e tutte le funzioni saranno abilitate.

### 🔑 Chiave di sviluppo

Per dimostrazioni e test puoi usare la chiave `ILTUOCONSULENTEIT-DEV` inserendola nel campo `license_key` di `settings.json`. L'applicazione si comporterà come registrata e le funzionalità PRO saranno disponibili. Puoi personalizzare questa chiave tramite la variabile d'ambiente `DOCROPPER_DEV_LICENSE`.

Per informazioni commerciali: **doccropper@iltuoconsulenteit.it**.

