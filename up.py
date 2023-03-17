import fitz
from PIL import Image
from layoutparser import OCR, Document

# Load the PDF file using PyMuPDF
pdf_path = 'path/to/pdf/file.pdf'
doc = fitz.open(pdf_path)

# Convert each page in the PDF file to a JPEG image
for page_number in range(doc.page_count):
    page = doc[page_number]
    zoom = 2.0
    rotation = 0
    trans = fitz.Matrix(zoom, zoom).preRotate(rotation)
    pix = page.getPixmap(matrix=trans, alpha=False)
    image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    image_path = f'page_{page_number+1}.jpg'
    image.save(image_path)

    # Extract text and layout information using OCR
    ocr_agent = OCR()
    layout = ocr_agent.detect(image_path, return_response=True)

    # Convert the layout information to a LayoutParser document
    document = Document(layout=layout, page_size=(image.width, image.height))

    # Add the text to the LayoutParser document
    text = ocr_agent.detect(image_path)
    page_layout = layout[0]
    block = page_layout['layout']
    text_block = block.filter_blocks(lambda b, _: b['type'] == 'text')
    text_block.set(text=text, type='text')

    # Print the text and layout information for the page
    print(f'Page {page_number + 1}:')
    print(f'Text: {text}')
    print(f'Layout: {page_layout}')



import fitz
import re

# Open the PDF file
doc = fitz.open('path/to/pdf/file.pdf')

# Define the regular expression pattern for key-value pairs
pattern = r'(\w+)\s*:\s*(.+)'

# Iterate over each page in the document
for page_number in range(doc.page_count):
    # Get the page object
    page = doc[page_number]

    # Get the text on the page
    text = page.get_text()

    # Search for key-value pairs in the text
    matches = re.findall(pattern, text)

    # Print the key-value pairs
    for match in matches:
        key = match[0]
        value = match[1]
        print(f'{key}: {value}')

        
        import textract

# Define the path to the PDF file
pdf_path = "path/to/pdf/file.pdf"

# Extract the text from the PDF file using Textract
text = textract.process(pdf_path)

# Split the text into lines
lines = text.decode("utf-8").splitlines()

# Initialize an empty dictionary to store the form data
form_data = {}

# Iterate over each line in the text
for line in lines:
    # Check if the line contains a key-value pair
    if ":" in line:
        # Split the line into key and value
        key, value = line.split(":", 1)

        # Strip leading and trailing whitespace from the key and value
        key = key.strip()
        value = value.strip()

        # Add the key-value pair to the form data dictionary
        form_data[key] = value

# Print the extracted form data
print(form_data)


import fitz
from layoutparser import OCR, Document

# Load the PDF file using PyMuPDF
pdf_path = 'path/to/pdf/file.pdf'
doc = fitz.open(pdf_path)

# Extract text and layout information using OCR
ocr_agent = OCR()
layout = ocr_agent.detect(doc, return_response=True)

# Convert the layout information to a LayoutParser document
document = Document(layout=layout, page_size=(doc[0].rect.width, doc[0].rect.height))

# Print the text and layout information for each page in the document
for page_number in range(doc.page_count):
    # Get the page object
    page = doc[page_number]

    # Get the text on the page using OCR
    text = ocr_agent.detect(page)

    # Add the text to the LayoutParser document
    page_layout = layout[page_number]
    block = page_layout['layout']
    text_block = block.filter_blocks(lambda b, _: b['type'] == 'text')
    text_block.set(text=text, type='text')

    # Print the text and layout information for the page
    print(f'Page {page_number + 1}:')
    print(f'Text: {text}')
    print(f'Layout: {page_layout}')

    
    from pdf2image import convert_from_path

pdf_path = '/path/to/pdf/file.pdf'
first_page = 1
last_page = 3
image_path_prefix = '/path/to/image/file'

images = convert_from_path(pdf_path, first_page=first_page, last_page=last_page)

for i, image in enumerate(images):
    image_path = f"{image_path_prefix}_{i+1}.jpg"
    image.save(image_path, 'JPEG')
