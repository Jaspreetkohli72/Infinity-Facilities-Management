import fitz  # PyMuPDF
import os

pdf_path = "IFM E-Brochure (1).pdf"
output_dir = "assets/img/projects" # Changed output directory to projects as it is the most relevant 

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

try:
    document = fitz.open(pdf_path)
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        pix = page.get_pixmap()
        output_filepath = os.path.join(output_dir, f"page_{page_num+1}.png")
        pix.save(output_filepath)
        print(f"Extracted page {page_num+1} to {output_filepath}")
    document.close()
    print(f"Extracted all pages from {pdf_path} to {output_dir}")
except Exception as e:
    print(f"Error: {e}")
    print("Please ensure PyMuPDF is installed (`pip install PyMuPDF`) and the PDF path is correct.")

