import PyPDF2

# Define the word to search for
word_to_search = 'Your Word'

# Open the PDF file
with open('path/to/pdf/file.pdf', 'rb') as f:
    # Create a PDF reader object
    reader = PyPDF2.PdfReader(f)

    # Iterate over each page in the PDF file
    for page in reader.pages:
        # Get the page text
        page_text = page.extract_text()

        # Check if the word is in the page text
        if word_to_search in page_text:
            # Print the page number and location of the word
            print(f'Word found on page {page.page_number} at location {page_text.index(word_to_search)}')

