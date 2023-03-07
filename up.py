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


