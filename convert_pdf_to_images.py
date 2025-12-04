from pdf2image import convert_from_path
import os

pdf_path = "IFM E-Brochure (1).pdf"
output_dir = "assets/img/projects"

if not os.path.exists(output_dir):
    try:
        os.makedirs(output_dir)
    except FileExistsError:
        pass

try:
    print("Converting PDF to images...")
    images = convert_from_path(pdf_path)
    for i, image in enumerate(images):
        image_path = os.path.join(output_dir, f"page_{i+1}.png")
        image.save(image_path, "PNG")
        print(f"Saved {image_path}")
    print(f"Successfully converted {len(images)} pages.")
except Exception as e:
    print(f"Error converting PDF: {e}")
