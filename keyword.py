import fitz
import spacy

# Load the spacy model
nlp = spacy.load('en_core_web_sm')

# Load the PDF document
doc = fitz.open('document.pdf')

# Define the keyword to search for
keyword = 'machine learning'

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
            # Print the page number, sentence text, and keyword position
            print(f'Page {page_number+1}: {sent.text}')
            for token in sent:
                if token.text.lower() == keyword:
                    print(f'Keyword found at position {token.idx} on page {page_number+1}')
