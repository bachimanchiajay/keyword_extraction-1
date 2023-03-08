import os
import fitz

# Input PDF file path
pdf_path = '/path/to/input.pdf'

# Output directory to save the extracted images
output_dir = '/path/to/output/directory/'

# Create the output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Load the PDF file using PyMuPDF
pdf_doc = fitz.open(pdf_path)

# Loop through each page in the PDF
for page_num, pdf_page in enumerate(pdf_doc):
    # Render the PDF page as a PNG image
    pix = pdf_page.getPixmap(alpha=False)

    # Save the image to the output directory
    image_path = os.path.join(output_dir, f"page_{page_num+1}.png")
    pix.writePNG(image_path)

# Close the PDF file
pdf_doc.close()


