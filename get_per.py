import json

def get_text_near_search_string(file_path, search_string, page_num, left_percent, above_percent, below_percent):
    with open(file_path, 'r') as f:
        textract_output = json.load(f)

    search_string_data = None
    all_texts = []

    for block in textract_output['Blocks']:
        if block['BlockType'] in ['WORD', 'LINE'] and block['Page'] == page_num:
            text = block['Text']
            all_texts.append(block)

            # Save the block data if it matches the search string
            if text == search_string:
                search_string_data = block

    if search_string_data is None:
        print(f'Search string "{search_string}" not found on page {page_num}.')
        return None, None, None

    left_range = search_string_data['Geometry']['BoundingBox']['Left'] * left_percent
    above_range = search_string_data['Geometry']['BoundingBox']['Top'] * above_percent
    below_range = (1 - search_string_data['Geometry']['BoundingBox']['Top']) * below_percent

    left_texts = [text_block['Text'] for text_block in all_texts
                  if text_block['Geometry']['BoundingBox']['Left'] < search_string_data['Geometry']['BoundingBox']['Left']
                  and text_block['Geometry']['BoundingBox']['Left'] > search_string_data['Geometry']['BoundingBox']['Left'] - left_range]

    above_texts = [text_block['Text'] for text_block in all_texts
                   if text_block['Geometry']['BoundingBox']['Top'] < search_string_data['Geometry']['BoundingBox']['Top']
                   and text_block['Geometry']['BoundingBox']['Top'] > search_string_data['Geometry']['BoundingBox']['Top'] - above_range]

    below_texts = [text_block['Text'] for text_block in all_texts
                   if text_block['Geometry']['BoundingBox']['Top'] > search_string_data['Geometry']['BoundingBox']['Top']
                   and text_block['Geometry']['BoundingBox']['Top'] < search_string_data['Geometry']['BoundingBox']['Top'] + below_range]

    return left_texts, above_texts, below_texts

file_path = 'your_json_file.json'  # Replace this with your file path
search_string = 'YourSearchString'  # Replace this with your search string
page_num = 2  # Replace this with your desired page number

left_texts, above_texts, below_texts = get_text_near_search_string(file_path, search_string, page_num, 0.3, 0.3, 0.3)
print(f'Texts to the left of "{search_string}" on page {page_num}: {left_texts}')
print(f'Texts above "{search_string}" on page {page_num}: {above_texts}')
print(f'Texts below "{search_string}" on page {page_num}: {below_texts}')
