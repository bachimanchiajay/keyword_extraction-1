import fitz
import spacy

# Load the spacy model
nlp = spacy.load('en_core_web_sm')

# Load the PDF document
doc = fitz.open('path/to/pdf/file.pdf')

# Define the keyword to search for
keyword = 'Your Keyword'

# Define the field to extract data for
field = 'Your Field Name'

# Iterate over each page in the document
for page_number in range(doc.page_count):
    # Get the page text
    page_text = doc[page_number].get_text()

    # Create a Spacy document from the page text
    doc_spacy = nlp(page_text)

    # Iterate over each sentence in the Spacy document
    for sent in doc_spacy.sents:
        # Check if the keyword is in the sentence
        if keyword in sent.text.lower():
            # Get the field value
            field_value = doc[page_number].getField(field)

            # Print the field value
            print(f'{field}: {field_value}')
