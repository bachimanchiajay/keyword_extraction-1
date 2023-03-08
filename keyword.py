import fitz
import os
import fitz
from PyPDF2 import PdfFileReader

# Input directory containing the PDF files
pdf_dir = '/path/to/pdf/directory/'

# Output directory to save the converted images
output_dir = '/path/to/output/directory/'

# Create the output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Loop through each PDF file in the input directory
for pdf_file in os.listdir(pdf_dir):
    if pdf_file.endswith('.pdf'):
        # Load the PDF file using PyPDF2
        pdf_path = os.path.join(pdf_dir, pdf_file)
        with open(pdf_path, 'rb') as f:
            pdf_reader = PdfFileReader(f)
            # Get the number of pages in the PDF
            num_pages = pdf_reader.getNumPages()

            # Loop through each page in the PDF
            for page_num in range(num_pages):
                # Load the PDF page using PyMuPDF
                pdf_page = fitz.open(pdf_path)[page_num]
                # Convert the PDF page to a PNG image
                pix = pdf_page.getPixmap(alpha=False)
                image_path = os.path.join(output_dir, f"{pdf_file[:-4]}_page{page_num+1}.png")
                pix.writePNG(image_path)

