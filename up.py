import fitz

# Load the PDF document
doc = fitz.open('path/to/pdf/file.pdf')

# Define the text to search for
text_to_search = 'Your Text'

# Define the right-side region
right_region = [0.5, 0, 1, 1]

# Iterate over each page in the document
for page_number in range(doc.page_count):
    # Get the page object
    page = doc[page_number]

    # Search for the text
    search_results = page.search_for(text_to_search)

    # Iterate over each search result
    for search_result in search_results:
        # Check if the search result is in the right-side region
        if search_result[0] > page.MediaBox[2]*right_region[0] and \
           search_result[1] > page.MediaBox[3]*right_region[1] and \
           search_result[2] > page.MediaBox[2]*right_region[2] and \
           search_result[3] > page.MediaBox[3]*right_region[3]:
            # Get the text in the right-side region
            right_text = page.get_textbox([page.MediaBox[2]*right_region[0],
                                           page.MediaBox[3]*right_region[1],
                                           page.MediaBox[2]*right_region[2],
                                           page.MediaBox[3]*right_region[3]])

            # Print the text in the right-side region
            print(right_text)
