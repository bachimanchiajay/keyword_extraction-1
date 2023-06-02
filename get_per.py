import json

def get_text_in_range(file_path, left_range, above_range):
    with open(file_path, 'r') as f:
        textract_output = json.load(f)

    all_texts = []

    for block in textract_output['Blocks']:
        if block['BlockType'] in ['WORD', 'LINE']:
            all_texts.append(block)

    # Filter out only the texts that are within the specified range from the left and top
    left_texts = [text_block['Text'] for text_block in all_texts
                  if text_block['Geometry']['BoundingBox']['Left'] < left_range]

    above_texts = [text_block['Text'] for text_block in all_texts
                   if text_block['Geometry']['BoundingBox']['Top'] < above_range]

    return ' '.join(left_texts), ' '.join(above_texts)

file_path = 'your_json_file.json'  # Replace this with your file path

left_text, above_text = get_text_in_range(file_path, 0.3, 0.2)
print(f'Text in the left 30% of the document: {left_text}')
print(f'Text in the top 20% of the document: {above_text}')




import json

def get_text_in_range(file_path, search_string, left_range, above_range, page_number):
    with open(file_path, 'r') as f:
        textract_output = json.load(f)

    search_string_data = None
    all_texts = []

    for block in textract_output['Blocks']:
        # Check if block is in the specified page
        if block['BlockType'] in ['WORD', 'LINE'] and block['Page'] == page_number:
            text = block['Text']
            all_texts.append(block)

            # Save the block data if it matches the search string
            if text == search_string:
                search_string_data = block

    if search_string_data is None:
        print(f'Search string "{search_string}" not found in the document.')
        return None, None

    left_texts = [text_block['Text'] for text_block in all_texts
                  if abs(text_block['Geometry']['BoundingBox']['Top'] - search_string_data['Geometry']['BoundingBox']['Top']) < 0.01
                  and text_block['Geometry']['BoundingBox']['Left'] < search_string_data['Geometry']['BoundingBox']['Left']
                  and text_block['Geometry']['BoundingBox']['Left'] > search_string_data['Geometry']['BoundingBox']['Left'] - left_range]

    above_texts = [text_block['Text'] for text_block in all_texts
                   if text_block['Geometry']['BoundingBox']['Top'] < search_string_data['Geometry']['BoundingBox']['Top']
                   and text_block['Geometry']['BoundingBox']['Top'] > search_string_data['Geometry']['BoundingBox']['Top'] - above_range]

    return ' '.join(left_texts), ' '.join(above_texts)

file_path = 'your_json_file.json'  # Replace this with your file path
search_string = 'YourSearchString'  # Replace this with your search string
page_number = 2  # Replace this with your desired page number

left_text, above_text = get_text_in_range(file_path, search_string, 0.2, 0.2, page_number)

if left_text is not None and above_text is not None:
    print(f'Text to the left of "{search_string}": {left_text}')
    print(f'Text above "{search_string}": {above_text}')
