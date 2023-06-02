import json

def get_text_near_search_string(file_path, search_string, left_percent, above_percent, below_percent):
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

    if search_string_data is None:
        print(f'Search string "{search_string}" not found in the document.')
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

left_texts, above_texts, below_texts = get_text_near_search_string(file_path, search_string, 0.3, 0.3, 0.3)
print(f'Texts to the left of "{search_string}": {left_texts}')
print(f'Texts above "{search_string}": {above_texts}')
print(f'Texts below "{search_string}": {below_texts}')





import json

def get_text_from_page(file_path, page_number):
    with open(file_path, 'r') as f:
        textract_output = json.load(f)

    page_texts = []

    for block in textract_output['Blocks']:
        if block['BlockType'] in ['WORD', 'LINE'] and block['Page'] == page_number:
            page_texts.append(block['Text'])

    return ' '.join(page_texts)

file_path = 'your_json_file.json'  # Replace this with your file path
page_number = 2  # Replace this with your desired page number

page_text = get_text_from_page(file_path, page_number)
print(f'Text from page {page_number}: {page_text}')


import json
import re

def get_nearest_percentage(file_path, search_string):
    with open(file_path, 'r') as f:
        textract_output = json.load(f)

    # Regular expression to match percentage values
    percentage_pattern = re.compile(r'(\d+(\.\d{1,2})?%)')

    search_string_data = None
    all_texts = []

    for block in textract_output['Blocks']:
        if block['BlockType'] in ['WORD', 'LINE']:
            text = block['Text']
            all_texts.append(block)

            # Save the block data if it matches the search string
            if text == search_string:
                search_string_data = block

    if search_string_data is None:
        print(f'Search string "{search_string}" not found in the document.')
        return None

    search_box = search_string_data['Geometry']['BoundingBox']

    nearest_percentage = None
    nearest_distance = float('inf')

    # Check each text block for percentages and if it's nearer to the search string
    for text_block in all_texts:
        box = text_block['Geometry']['BoundingBox']
        # Calculate distance as Euclidean distance
        distance = ((box['Left'] - search_box['Left'])**2 + (box['Top'] - search_box['Top'])**2)**0.5

        # Check if there's a percentage in the text block
        percentages = percentage_pattern.findall(text_block['Text'])
        if percentages and distance < nearest_distance:
            nearest_distance = distance
            nearest_percentage = percentages[0]  # Assuming we only want the first match

    return nearest_percentage

file_path = 'your_json_file.json'  # Replace this with your file path
search_string = 'YourSearchString'  # Replace this with your search string

nearest_percentage = get_nearest_percentage(file_path, search_string)
print(f'Nearest percentage to "{search_string}": {nearest_percentage}')



import json

def get_text_in_range(file_path, left_range, above_range, x, y, w, h):
    with open(file_path, 'r') as f:
        textract_output = json.load(f)

    all_texts = []

    for block in textract_output['Blocks']:
        if block['BlockType'] in ['WORD', 'LINE']:
            all_texts.append(block)

    # Filter out only the texts that are within the specified range from the left and top and within the specified rectangle
    left_texts = [text_block['Text'] for text_block in all_texts
                  if text_block['Geometry']['BoundingBox']['Left'] < left_range 
                  and text_block['Geometry']['BoundingBox']['Left'] >= x
                  and text_block['Geometry']['BoundingBox']['Left'] <= x + w]

    above_texts = [text_block['Text'] for text_block in all_texts
                   if text_block['Geometry']['BoundingBox']['Top'] < above_range 
                   and text_block['Geometry']['BoundingBox']['Top'] >= y
                   and text_block['Geometry']['BoundingBox']['Top'] <= y + h]

    return ' '.join(left_texts), ' '.join(above_texts)

file_path = 'your_json_file.json'  # Replace this with your file path
x = 0.2  # Replace these with your rectangle coordinates
y = 0.2
w = 0.5
h = 0.5

left_text, above_text = get_text_in_range(file_path, 0.3, 0.2, x, y, w, h)
print(f'Text in the left 30% of the document: {left_text}')
print(f'Text in the top 20% of the document: {above_text}')






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
