import os
import re
import shutil
import glob
# from slugify import slugify # Need to install python-slugify or use simple regex

# Simple slugify if library not available
def simple_slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text if text else "image"

BASE_DIR = r"c:/Users/Jaskaran/Documents/Infinity Facilities Management/Infinity_Facilities_Management"
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMG_DIR = os.path.join(ASSETS_DIR, "img")

def smart_organize():
    print("Starting smart asset organization...")
    
    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)

    html_files = glob.glob(os.path.join(BASE_DIR, '*.html'))
    
    # Track used files to delete unused ones later
    used_files = set()
    
    # Map old_path -> new_relative_path
    moves = {}

    for html_file in html_files:
        print(f"Processing {os.path.basename(html_file)}...")
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = content
        
        # Find img tags: <img ... src="assets/..." ... alt="..." ...>
        # We need to capture src and alt. Regex is tricky for HTML, but sufficient for this cleanup.
        # Pattern: src=["']assets/([^"']+)["'].*?alt=["']([^"']*)["']
        # Note: alt might come before src.
        
        # Strategy: Find all 'assets/...' references first.
        # Then try to find the alt text for that tag.
        
        # 1. Find all asset references
        references = re.findall(r'assets/([^"\'\)\s>]+)', content)
        
        for ref in references:
            old_filename = ref
            old_path = os.path.join(ASSETS_DIR, old_filename)
            
            # Handle subdirectories in old path (e.g. renamed/logo.png)
            if os.path.sep in old_filename:
                 old_path = os.path.join(ASSETS_DIR, old_filename.replace('/', os.path.sep))

            if not os.path.exists(old_path):
                # Try checking if it's just a filename in assets root (flattened by previous script)
                basename = os.path.basename(old_filename)
                potential_path = os.path.join(ASSETS_DIR, basename)
                if os.path.exists(potential_path):
                    old_path = potential_path
                    old_filename = basename # Update ref to point to root
                else:
                    # Try checking for .webp version (if previous script converted but didn't update HTML)
                    root, ext = os.path.splitext(old_path)
                    webp_path = root + ".webp"
                    if os.path.exists(webp_path):
                        old_path = webp_path
                        # Don't update old_filename yet, we will replace the whole ref later
                    else:
                        # Try flattened webp
                        root, ext = os.path.splitext(basename)
                        webp_path = os.path.join(ASSETS_DIR, root + ".webp")
                        if os.path.exists(webp_path):
                            old_path = webp_path
                        else:
                            print(f"Warning: Asset not found: {old_filename} (checked {old_path} and webp variants)")
                            continue

            used_files.add(os.path.normpath(old_path))
            
            # Determine new name
            new_name = ""
            
            # Try to find alt text for this image in the content
            # Look for the specific string 'assets/old_filename' and surrounding alt
            # This is a bit heuristic.
            
            # Regex to find the tag containing this source
            # <img [^>]*src="assets/old_filename"[^>]*>
            tag_match = re.search(r'<img[^>]*src=["\']assets/' + re.escape(old_filename) + r'["\'][^>]*>', content)
            
            if tag_match:
                tag_content = tag_match.group(0)
                alt_match = re.search(r'alt=["\']([^"\']+)["\']', tag_content)
                if alt_match:
                    alt_text = alt_match.group(1)
                    new_name = simple_slugify(alt_text)
            
            # Fallback if no alt or not an img tag (e.g. background)
            if not new_name:
                # Use current basename without extension
                base, _ = os.path.splitext(os.path.basename(old_filename))
                new_name = simple_slugify(base)
                
            # Ensure unique filename
            ext = os.path.splitext(old_filename)[1]
            if not ext: ext = ".webp" # Default
            
            candidate_name = new_name + ext
            counter = 1
            while os.path.exists(os.path.join(IMG_DIR, candidate_name)) and os.path.join(IMG_DIR, candidate_name) != old_path:
                # Check if it's the SAME file (already moved/mapped)
                # If we already decided to move this file to this name, good.
                if old_path in moves and moves[old_path] == f"assets/img/{candidate_name}":
                    break
                
                # If it's a different file wanting the same name
                candidate_name = f"{new_name}-{counter}{ext}"
                counter += 1
            
            new_relative_path = f"assets/img/{candidate_name}"
            moves[old_path] = new_relative_path
            
            # Update content
            # Replace 'assets/old_filename' with 'assets/img/new_name'
            # Be careful not to replace 'assets/old_filename_extra'
            new_content = new_content.replace(f"assets/{old_filename}", new_relative_path)
            
        if new_content != content:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {os.path.basename(html_file)}")

    # Execute Moves
    print("Moving files...")
    for old_path, new_rel_path in moves.items():
        new_full_path = os.path.join(BASE_DIR, new_rel_path.replace('/', os.path.sep))
        
        if os.path.abspath(old_path) == os.path.abspath(new_full_path):
            continue
            
        try:
            shutil.move(old_path, new_full_path)
            print(f"Moved: {os.path.basename(old_path)} -> {os.path.basename(new_full_path)}")
        except Exception as e:
            print(f"Error moving {old_path}: {e}")

    # Cleanup Unused
    print("Cleaning up unused files...")
    all_assets = glob.glob(os.path.join(ASSETS_DIR, '*'))
    for asset in all_assets:
        if os.path.isdir(asset):
            if os.path.basename(asset) == "img": continue
            # Check subfiles
            # For simplicity, if it's 'renamed' or others, and not in used_files, delete?
            # Recursive check is safer.
            # Let's just delete files in root of assets that weren't used.
            pass
        else:
            if os.path.normpath(asset) not in used_files and os.path.normpath(asset) != os.path.normpath(os.path.join(ASSETS_DIR, 'favicon.ico')): # Keep favicon if there
                # Check if it was moved (it won't be in assets root anymore if moved)
                # But we iterate glob result which is snapshot? No.
                # If we moved it, it's gone from source.
                # So if it's still there, it wasn't moved.
                try:
                    os.remove(asset)
                    print(f"Deleted unused: {os.path.basename(asset)}")
                except Exception as e:
                    print(f"Error deleting {asset}: {e}")

    # Remove empty directories
    for root, dirs, files in os.walk(ASSETS_DIR, topdown=False):
        for name in dirs:
            if name == "img": continue
            try:
                os.rmdir(os.path.join(root, name))
                print(f"Removed empty dir: {name}")
            except:
                pass

    print("Smart organization complete!")

if __name__ == "__main__":
    smart_organize()
