"""
Helper script to download free fonts for Galton's Goalie.
Downloads Montserrat and Open Sans from Google Fonts.
"""

import os
import urllib.request
import zipfile
import shutil

FONTS_DIR = os.path.join(os.path.dirname(__file__), 'fonts')

# Google Fonts download URLs
FONTS = {
    'Open Sans': 'https://fonts.google.com/download?family=Open%20Sans',
    'Montserrat': 'https://fonts.google.com/download?family=Montserrat'
}

def download_and_extract(name, url):
    """Download and extract a font from Google Fonts."""
    print(f"Downloading {name}...")

    # Create fonts directory if it doesn't exist
    os.makedirs(FONTS_DIR, exist_ok=True)

    # Download zip file
    zip_path = os.path.join(FONTS_DIR, f'{name}.zip')
    try:
        urllib.request.urlretrieve(url, zip_path)
        print(f"  Downloaded {name}")

        # Extract zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract only .ttf files
            for file in zip_ref.namelist():
                if file.endswith('.ttf'):
                    # Extract to fonts directory
                    source = zip_ref.open(file)
                    target_path = os.path.join(FONTS_DIR, os.path.basename(file))

                    with open(target_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    print(f"  Extracted: {os.path.basename(file)}")

        # Clean up zip file
        os.remove(zip_path)
        print(f"  ✓ {name} installed successfully!\n")

    except Exception as e:
        print(f"  ✗ Error downloading {name}: {e}\n")

def main():
    print("=" * 60)
    print("Galton's Goalie - Font Downloader")
    print("=" * 60)
    print("\nThis will download free fonts from Google Fonts:")
    print("  • Open Sans (body text)")
    print("  • Montserrat (alternative to Campton for headings)")
    print()

    response = input("Continue? (y/n): ").lower()
    if response != 'y':
        print("Cancelled.")
        return

    print("\nDownloading fonts...\n")

    for name, url in FONTS.items():
        download_and_extract(name, url)

    print("=" * 60)
    print("✓ Font installation complete!")
    print("=" * 60)
    print("\nFonts have been installed to:", FONTS_DIR)
    print("\nYou can now run galton_goalie_qt.py and the fonts will load automatically.")
    print("\nNote: If you want Campton (the actual Mark Rober font), you'll need")
    print("to purchase it separately and add the .otf/.ttf files to the fonts/ folder.")

if __name__ == "__main__":
    main()
