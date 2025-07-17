import os
import platform
import subprocess
from pathlib import Path
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent
INSTALL_DIR = BASE_DIR / 'install'

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

def run_script(name, env=None):
    script = INSTALL_DIR / name
    if SYSTEM == 'Windows':
        subprocess.Popen(['cmd', '/c', str(script)], env=env)
    else:
        subprocess.Popen(['bash', str(script)], env=env)


def start_app():
    run_script(START_SCRIPTS)

def stop_app():
    run_script(STOP_SCRIPTS)

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
    developer = os.environ.get('DOCROPPER_DEVELOPER') == '1'
    menu_items = [
        MenuItem('Start DocCropper', lambda icon, item: start_app()),
        MenuItem('Stop DocCropper', lambda icon, item: stop_app()),
        MenuItem('Update from main', lambda icon, item: update_main())
    ]
    if developer:
        menu_items.append(MenuItem('Update from branch', lambda icon, item: update_branch()))
    menu_items.append(MenuItem('Quit', quit_app))

    icon = Icon('DocCropper', create_image(), 'DocCropper', menu=Menu(*menu_items))
    icon.run()


if __name__ == '__main__':
    main()
