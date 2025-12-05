import os
import requests
from PIL import Image
from io import BytesIO

# Define the images to download
# Format: (url, filename_without_extension)
images_to_download = [
    ("https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhN_EEm2BoCioFeFs7VBnZFDY-CuxcC1DmtZWBJNbpAgfVed34WGxVWkAJGZBQKg_BMYNa65dwDOLPYNDVn399EohFWzJKnEZ1PPMwybDz4Vqp3OtdyUXICWE3W4yqQgSM0GY-P6hYS9CoM/s1600/CAM-01.jpg", "golden-trade-centre-building"),
    ("https://asgeyehospital.com/public/storage/settings/April2025/g4pHACqqa41yPfedtGC7.png", "asg-eye-hospital-logo"),
    ("https://asgeyehospital.com/public/storage/hospitals/January2025/622czVtUB6d4ZD79mEWF.jpeg", "asg-eye-hospital-building"),
    ("https://images.jdmagicbox.com/v2/comp/raipur-chhattisgarh/t4/9999px771.x771.241127190641.g4t4/catalogue/carcinoma-care-center-tatibandh-raipur-chhattisgarh-cancer-centres-el2guy04sk-250.jpg", "carcinoma-clinic-building"),
    ("https://teja12.kuikr.com/is/a/c/800x600/gallery_images/original/4f6021e5c3640.jpg", "maruti-lifestyle-building"),
    ("https://fplogoimages.withfloats.com/actual/597993f8f5a047050c3f7c47.jpg", "avinash-group-logo"),
    ("https://img.staticmb.com/mbimages/project/Photo_h470_w1080/Photo_h310_w462/2021/10/12/Project-Photo-21-Avinash-One-Raipur-5309385_1200_1600_310_462_470_1080.jpg.webp", "avinash-one-building"),
]

# Target directory
output_dir = r"c:\Users\Jaskaran\Documents\Infinity Facilities Management\Infinity_Facilities_Management\assets\img"

def download_and_convert(url, filename):
    try:
        print(f"Downloading {filename} from {url}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        
        # Convert to RGB if necessary (e.g. for PNGs with transparency if saving as JPEG, but WebP handles RGBA)
        # WebP supports transparency, so we don't strictly need to convert RGBA to RGB, 
        # but it's good practice to ensure compatibility if we wanted JPG. 
        # For WebP, we can keep RGBA.
        
        output_path = os.path.join(output_dir, f"{filename}.webp")
        img.save(output_path, "WEBP", quality=85)
        print(f"Saved {output_path}")
        
    except Exception as e:
        print(f"Failed to process {filename}: {e}")

if __name__ == "__main__":
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for url, filename in images_to_download:
        download_and_convert(url, filename)
