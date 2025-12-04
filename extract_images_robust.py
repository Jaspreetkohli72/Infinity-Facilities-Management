import pypdf
import os

pdf_path = "IFM E-Brochure (1).pdf"
output_dir = "assets/img/projects"

if not os.path.exists(output_dir):
    try:
        os.makedirs(output_dir)
    except FileExistsError:
        pass

try:
    reader = pypdf.PdfReader(pdf_path)
    count = 0
    for page_num, page in enumerate(reader.pages):
        try:
            for image_file_object in page.images:
                try:
                    image_name = f"page_{page_num+1}_img_{count}.webp"
                    with open(os.path.join(output_dir, image_name), "wb") as fp:
                        fp.write(image_file_object.data)
                    print(f"Extracted {image_name}")
                    count += 1
                except Exception as img_e:
                    print(f"Error extracting image on page {page_num+1}: {img_e}")
        except Exception as page_e:
            print(f"Error processing page {page_num+1}: {page_e}")

    print(f"Extracted {count} images to {output_dir}")

except Exception as e:
    print(f"Critical error: {e}")
