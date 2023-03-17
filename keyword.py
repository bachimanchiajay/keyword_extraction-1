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


import boto3
from PyPDF2 import PdfFileReader
from pdf2image import convert_from_path
import io

# Replace these with the S3 bucket details
bucket_name = 'YOUR_BUCKET_NAME'
pdf_file_key = 'path/to/your/pdf/file.pdf'

# Set the starting and ending page numbers
start_page = 3
end_page = 5

# Set up the S3 client
s3 = boto3.client('s3')

# Download the PDF file from the S3 bucket
pdf_file = io.BytesIO()
s3.download_fileobj(bucket_name, pdf_file_key, pdf_file)
pdf_file.seek(0)

# Get the number of pages in the PDF
pdf_reader = PdfFileReader(pdf_file)
num_pages = pdf_reader.getNumPages()

# Check if the specified range is within the total number of pages
if start_page <= 0 or end_page > num_pages:
    raise ValueError("Invalid page range. Check the start_page and end_page values.")

# Convert the specified pages of the PDF file to images
images = convert_from_path(pdf_file, first_page=start_page, last_page=end_page)

# Save the images
for i, image in enumerate(images, start=start_page):
    image_file_name = f'image_page_{i}.png'
    image.save(image_file_name, 'PNG')
    
    # Upload the image to S3
    with open(image_file_name, 'rb') as image_file:
        s3.upload_fileobj(image_file, bucket_name, f'path/to/save/{image_file_name}')
