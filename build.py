"""
build.py — Restaurant POS EXE Builder
======================================
Run this script to package the app into a standalone Windows EXE:

    python build.py

The output EXE will be at:  dist/RestaurantPOS.exe

To change the EXE icon later, update the ICON_PATH variable in
RestaurantPOS.spec (look for the line: icon='static/logo.ico')
and run this script again.
"""

import subprocess
import sys
import os

def check_and_install_pyinstaller():
    """Ensure PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} is already installed.")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed successfully.")

def convert_icon():
    """
    Convert logo.jpg → logo.ico for use as the EXE icon.
    Requires Pillow. Installs it automatically if missing.
    """
    ico_path = os.path.join("static", "logo.ico")
    jpg_path = os.path.join("static", "logo.jpg")

    if os.path.exists(ico_path):
        print(f"✓ Icon already exists: {ico_path}")
        return ico_path

    try:
        from PIL import Image
    except ImportError:
        print("Pillow not found. Installing for icon conversion...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        from PIL import Image

    print(f"Converting {jpg_path} → {ico_path} ...")
    img = Image.open(jpg_path)
    # Resize to standard icon sizes and save as .ico
    img = img.resize((256, 256), Image.LANCZOS)
    img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"✓ Icon saved: {ico_path}")
    return ico_path

def build():
    print("\n" + "="*50)
    print("  Restaurant POS — EXE Builder")
    print("="*50 + "\n")

    # Step 1: Ensure PyInstaller is available
    check_and_install_pyinstaller()

    # Step 2: Convert logo.jpg to .ico
    convert_icon()

    # Step 3: Run PyInstaller with the spec file
    print("\nBuilding EXE with PyInstaller...")
    result = subprocess.run(
        ["pyinstaller", "RestaurantPOS.spec", "--clean"],
        capture_output=False
    )

    if result.returncode == 0:
        exe_path = os.path.join("dist", "RestaurantPOS.exe")
        print("\n" + "="*50)
        print("✓ Build successful!")
        print(f"  EXE location: {os.path.abspath(exe_path)}")
        print("\nIMPORTANT: Copy the entire 'dist/RestaurantPOS' folder to the")
        print("client machine (not just the .exe). The first time the client")
        print("runs it, the machine will be registered automatically.")
        print("="*50 + "\n")
    else:
        print("\n✗ Build failed. Check the output above for errors.")
        sys.exit(1)

if __name__ == "__main__":
    build()
