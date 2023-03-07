import fitz
import re

# Define the keyword to search for
keyword = 'Your Keyword'

# Compile the regular expression pattern
regex = re.compile(keyword)

# Open the PDF file
doc = fitz.open('path/to/pdf/file.pdf')

# Iterate over each page in the document
for page_number in range(doc.page_count):
    # Get the page object
    page = doc[page_number]

    # Search for the keyword using the regular expression
    matches = regex.finditer(page.get_text())

    # Iterate over each match
    for match in matches:
        # Get the rectangle of the match
        rect = match.group(0).strip('\n').replace('\n', ' ').replace('\r', ' ')
        rect = page.search_for(rect)[0]

        # Get the text region of the keyword
        text_region = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1 + 10)
        text = page.get_text("text", clip=text_region)

        # Print the page number, location, and text region of the match
        print(f'Page {page_number+1}: {match.start()} - {match.end()}\n{rect}\n{text}')


