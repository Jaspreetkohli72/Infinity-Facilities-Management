import os
import hashlib
from PIL import Image
import glob

ASSETS_DIR = r"c:/Users/Jaskaran/Documents/Infinity Facilities Management/Infinity_Facilities_Management/assets"
HTML_DIR = r"c:/Users/Jaskaran/Documents/Infinity Facilities Management/Infinity_Facilities_Management"

def get_file_hash(filepath):
    """Calculate MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def optimize_repo():
    print("Starting optimization...")
    
    # 1. Find all images
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(ASSETS_DIR, '**', ext), recursive=True))
    
    # Deduplicate file list (handle case-insensitivity on Windows)
    image_files = sorted(list(set([os.path.normpath(p) for p in image_files])))
    
    print(f"Found {len(image_files)} unique images.")

    # 2. Deduplicate
    hashes = {}
    duplicates = {} # {deleted_path: kept_path}
    kept_files = []

    for img_path in image_files:
        file_hash = get_file_hash(img_path)
        if file_hash in hashes:
            # Duplicate found
            kept_path = hashes[file_hash]
            duplicates[img_path] = kept_path
            print(f"Duplicate found: {os.path.basename(img_path)} -> keeping {os.path.basename(kept_path)}")
            try:
                os.remove(img_path)
            except OSError as e:
                print(f"Error deleting {img_path}: {e}")
        else:
            hashes[file_hash] = img_path
            kept_files.append(img_path)

    print(f"Removed {len(duplicates)} duplicate files.")

    # 3. Convert to WebP
    conversion_map = {} # {original_filename: new_webp_filename}
    
    for img_path in kept_files:
        try:
            with Image.open(img_path) as im:
                # Create new path with .webp extension
                root, ext = os.path.splitext(img_path)
                webp_path = root + ".webp"
                
                # Convert and save
                im.save(webp_path, "WEBP", quality=85)
                print(f"Converted: {os.path.basename(img_path)} -> {os.path.basename(webp_path)}")
                
                # Record mapping (basename only for simplicity in HTML replacement, 
                # assuming unique basenames or relative paths match)
                # Better: map full relative path or just basename if unique.
                # Given the structure, let's map basename -> basename.webp
                conversion_map[os.path.basename(img_path)] = os.path.basename(webp_path)
                
                # Remove original
                os.remove(img_path)
        except Exception as e:
            print(f"Failed to convert {img_path}: {e}")

    # Add duplicate mappings to conversion map
    # If A.png was a duplicate of B.png, and B.png became B.webp
    # Then A.png should map to B.webp
    for deleted_path, kept_path in duplicates.items():
        deleted_name = os.path.basename(deleted_path)
        kept_name = os.path.basename(kept_path)
        # Find what kept_name converted to
        if kept_name in conversion_map:
            conversion_map[deleted_name] = conversion_map[kept_name]

    # 4. Update HTML files
    html_files = glob.glob(os.path.join(HTML_DIR, '*.html'))
    
    for html_file in html_files:
        print(f"Updating {os.path.basename(html_file)}...")
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for old_name, new_name in conversion_map.items():
            # Simple string replacement - be careful with partial matches
            # but filenames usually have extensions which helps uniqueness
            if old_name in content:
                content = content.replace(old_name, new_name)
        
        if content != original_content:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated references in {os.path.basename(html_file)}")

    print("Optimization complete!")

if __name__ == "__main__":
    optimize_repo()
