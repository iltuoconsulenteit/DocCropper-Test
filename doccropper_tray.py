import os
import platform
import subprocess
import logging
from pathlib import Path
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import json
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
INSTALL_DIR = BASE_DIR / 'install'
SCRIPTS_DIR = BASE_DIR / 'scripts'

LOG_FILE = BASE_DIR / 'doccropper_tray.log'
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Load environment variables from env/*.env files
ENV_DIR = BASE_DIR / 'env'
if ENV_DIR.is_dir():
    for env_file in ENV_DIR.glob('*.env'):
        load_dotenv(env_file, override=False)

SYSTEM = platform.system()
START_SCRIPTS = {
    'Windows': 'start_DocCropper.bat',
    'Darwin': 'start_DocCropper.command',
}.get(SYSTEM, 'start_DocCropper.sh')
STOP_SCRIPTS = {
    'Windows': 'stop_DocCropper.bat',
    'Darwin': 'stop_DocCropper.command',
}.get(SYSTEM, 'stop_DocCropper.sh')
INSTALL_SCRIPTS = {
    'Windows': 'install_DocCropper.bat',
    'Darwin': 'install_DocCropper.command',
}.get(SYSTEM, 'install_DocCropper.sh')

def is_developer():
    settings_file = BASE_DIR / 'settings.json'
    try:
        with open(settings_file) as fh:
            data = json.load(fh)
        key = data.get('license_key', '').strip().upper()
        dev = os.environ.get('DOCROPPER_DEV_LICENSE', 'ILTUOCONSULENTEIT-DEV').upper()
        return key == dev
    except Exception:
        return False

def run_script(name, env=None, folder=INSTALL_DIR):
    script = folder / name
    logging.info("Running %s", script)
    stdout = open(LOG_FILE, 'a')
    if SYSTEM == 'Windows':
        flags = 0
        if hasattr(subprocess, 'CREATE_NO_WINDOW'):
            flags = subprocess.CREATE_NO_WINDOW
        subprocess.Popen(['cmd', '/c', str(script)], env=env,
                         stdout=stdout, stderr=subprocess.STDOUT,
                         creationflags=flags)
    else:
        subprocess.Popen(['bash', str(script)], env=env,
                         stdout=stdout, stderr=subprocess.STDOUT)


def start_app():
    run_script(START_SCRIPTS, folder=SCRIPTS_DIR)

def stop_app():
    run_script(STOP_SCRIPTS, folder=SCRIPTS_DIR)

def update_main():
    env = os.environ.copy()
    env['BRANCH'] = 'main'
    run_script(INSTALL_SCRIPTS, env)

def update_branch():
    env = os.environ.copy()
    branch = env.get('DOCROPPER_BRANCH', 'main')
    env['BRANCH'] = branch
    run_script(INSTALL_SCRIPTS, env)

def quit_app(icon, item):
    icon.stop()


def create_image():
    image = Image.new('RGB', (64, 64), 'white')
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, 56, 56), fill='black')
    draw.text((16, 20), 'DC', fill='white')
    return image


def main():
    developer = os.environ.get('DOCROPPER_DEVELOPER') == '1' or is_developer()
    logging.info("Tray icon started (developer=%s)", developer)
    menu_items = [
        MenuItem('Start DocCropper', lambda icon, item: start_app()),
        MenuItem('Stop DocCropper', lambda icon, item: stop_app()),
        MenuItem('Update from main', lambda icon, item: update_main())
    ]
    if developer:
        menu_items.append(MenuItem('Update from branch', lambda icon, item: update_branch()))
    menu_items.append(MenuItem('Quit', quit_app))

    icon = Icon('DocCropper', create_image(), 'DocCropper', menu=Menu(*menu_items))
    try:
        icon.run()
    except Exception as e:
        logging.exception("Tray icon error: %s", e)


if __name__ == '__main__':
    main()
