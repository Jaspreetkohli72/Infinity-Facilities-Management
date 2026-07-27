import sys
from pathlib import Path

# Import main function from Site Uploader/app.py
uploader_dir = Path(__file__).resolve().parent / "Site Uploader"
if uploader_dir.exists() and str(uploader_dir) not in sys.path:
    sys.path.insert(0, str(uploader_dir))

from app import main

if __name__ == "__main__":
    main()
