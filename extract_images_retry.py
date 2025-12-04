import pypdf
import os

pdf_path = "IFM E-Brochure (1).pdf"
output_dir = "assets/img/projects"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

reader = pypdf.PdfReader(pdf_path)

count = 0
for page_num, page in enumerate(reader.pages):
    for image_file_object in page.images:
        with open(os.path.join(output_dir, f"page_{page_num+1}_img_{count}.webp"), "wb") as fp:
            fp.write(image_file_object.data)
            count += 1

print(f"Extracted {count} images to {output_dir}")
