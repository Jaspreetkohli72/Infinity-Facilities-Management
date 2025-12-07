import fitz  # PyMuPDF
import os
import io
from PIL import Image

def extract_images_from_pdf(pdf_path, pages_to_extract, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return
    
    image_count = 0
    
    for page_num in pages_to_extract:
        # Adjust for 0-based index
        page_index = page_num - 1
        if page_index < 0 or page_index >= len(doc):
            print(f"Page {page_num} is out of range.")
            continue
            
        page = doc[page_index]
        try:
            image_list = page.get_images(full=True)
        except Exception as e:
            print(f"Error getting images from page {page_num}: {e}")
            continue
        
        print(f"Found {len(image_list)} images on page {page_num}")
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                print(f"Processing image {img_index} on page {page_num}: size={len(image_bytes)}, ext={image_ext}")

                # Filter out very small images
                if len(image_bytes) < 1000: 
                    print(f"Skipping small image {img_index} (size: {len(image_bytes)})")
                    continue
                
                # Try to process with PIL
                try:
                    image = Image.open(io.BytesIO(image_bytes))
                    width, height = image.size
                    
                    if width < 50 or height < 50:
                        print(f"Skipping small dimension image {img_index} ({width}x{height})")
                        continue
                    
                    # Convert to RGB if necessary
                    if image.mode in ("RGBA", "P", "CMYK"):
                        image = image.convert("RGB")
                    
                    # Save as JPG
                    image_filename = f"gallery_p{page_num}_{img_index}.jpg"
                    image_path = os.path.join(output_dir, image_filename)
                    
                    image.save(image_path, "JPEG", quality=95)
                    print(f"Saved {image_path} (converted via PIL)")
                    image_count += 1
                    
                except Exception as e:
                    print(f"PIL failed for image {img_index}: {e}. Falling back to raw save.")
                    # Fallback: save raw bytes if PIL fails, but try to enforce jpg extension if possible
                    # If original was png, we can't just name it jpg. 
                    # But if it was jpeg, we can.
                    
                    if image_ext == "jpeg" or image_ext == "jpg":
                         final_ext = "jpg"
                    else:
                         final_ext = image_ext # Keep original if not jpeg
                    
                    image_filename = f"gallery_p{page_num}_{img_index}.{final_ext}"
                    image_path = os.path.join(output_dir, image_filename)
                    
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    print(f"Saved {image_path} (raw bytes)")
                    image_count += 1

            except Exception as e:
                print(f"Error extracting image {img_index} on page {page_num}: {e}")

    print(f"Total images extracted: {image_count}")

if __name__ == "__main__":
    pdf_path = "IFM E-Brochure (1).pdf"
    # Pages 14 and 15
    pages = [14, 15]
    output_directory = "assets/img/gallery"
    
    extract_images_from_pdf(pdf_path, pages, output_directory)
