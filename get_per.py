import json

def get_text_in_range(file_path, search_string, left_range, above_range):
    with open(file_path, 'r') as f:
        textract_output = json.load(f)

    search_string_data = None
    all_texts = []

    for block in textract_output['Blocks']:
        if block['BlockType'] in ['WORD', 'LINE']:
            text = block['Text']
            all_texts.append(block)

            # Save the block data if it matches the search string
            if text == search_string:
                search_string_data = block

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

left_text, above_text = get_text_in_range(file_path, search_string, 0.3, 0.2)
print(f'Text to the left of "{search_string}": {left_text}')
print(f'Text above "{search_string}": {above_text}')
