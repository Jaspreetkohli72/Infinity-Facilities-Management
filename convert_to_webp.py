import os
import glob
from PIL import Image

BASE_DIR = r"c:/Users/Jaskaran/Documents/Infinity Facilities Management/Infinity_Facilities_Management"
IMG_DIR = os.path.join(BASE_DIR, "assets", "img")

def convert_to_webp():
    print("Starting WebP conversion...")
    
    # Find all images in assets/img
    # We only care about non-webp images
    extensions = ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']
    image_files = []
    for ext in extensions:
        image_files.extend(glob.glob(os.path.join(IMG_DIR, ext)))
    
    print(f"Found {len(image_files)} images to convert.")
    
    conversion_map = {} # {old_filename: new_filename}

    for img_path in image_files:
        try:
            filename = os.path.basename(img_path)
            root, ext = os.path.splitext(filename)
            new_filename = root + ".webp"
            new_path = os.path.join(IMG_DIR, new_filename)
            
            # Convert
            with Image.open(img_path) as im:
                im.save(new_path, "WEBP", quality=85)
                print(f"Converted: {filename} -> {new_filename}")
            
            conversion_map[filename] = new_filename
            
            # Delete original
            os.remove(img_path)
            
        except Exception as e:
            print(f"Error converting {img_path}: {e}")

    # Update HTML
    html_files = glob.glob(os.path.join(BASE_DIR, '*.html'))
    for html_file in html_files:
        print(f"Updating {os.path.basename(html_file)}...")
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = content
        for old_name, new_name in conversion_map.items():
            # We know they are in assets/img/ now
            # Replace 'assets/img/old_name' with 'assets/img/new_name'
            # Also handle if they were referenced differently? 
            # No, smart_organize moved them to assets/img/ and updated HTML to assets/img/
            # So we just need to replace the filename in that path.
            
            # Be careful with partial matches.
            # "foo.png" -> "foo.webp"
            # "foo-bar.png" -> "foo-bar.webp"
            # If we replace "foo.png", we might break "foo-bar.png" if we are not careful?
            # No, "foo.png" is not a substring of "foo-bar.png" (well, it is if we don't check boundaries).
            # But we are replacing "assets/img/foo.png".
            
            old_ref = f"assets/img/{old_name}"
            new_ref = f"assets/img/{new_name}"
            
            new_content = new_content.replace(old_ref, new_ref)
        
        if new_content != content:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated references in {os.path.basename(html_file)}")

    print("WebP conversion complete!")

if __name__ == "__main__":
    convert_to_webp()
