import json

def get_coordinates_of_string(file_path, search_string):
    with open(file_path, 'r') as f:
        textract_output = json.load(f)

    for block in textract_output['Blocks']:
        if block['BlockType'] in ['WORD', 'LINE'] and block['Text'] == search_string:
            # Get the bounding box of the block
            bounding_box = block['Geometry']['BoundingBox']

            # Calculate the actual coordinates based on the bounding box
            coordinates = {
                'x': bounding_box['Left'],
                'y': bounding_box['Top'],
                'w': bounding_box['Width'],
                'h': bounding_box['Height'],
            }

            return coordinates

    print(f'Search string "{search_string}" not found in the document.')
    return None

file_path = 'your_json_file.json'  # Replace this with your file path
search_string = 'YourSearchString'  # Replace this with your search string

coordinates = get_coordinates_of_string(file_path, search_string)
print(f'Coordinates of "{search_string}": {coordinates}')





import json
import re

def get_surrounding_text(file_path, x, y, w, h):
    with open(file_path, 'r') as f:
        textract_output = json.load(f)

    left_texts, right_texts, top_texts, bottom_texts = [], [], [], []
    percentage_pattern = r'\b\d{1,3}(?:\.\d{1,2})?%\b'

    for block in textract_output['Blocks']:
        if block['BlockType'] in ['WORD', 'LINE']:
            left = block['Geometry']['BoundingBox']['Left']
            top = block['Geometry']['BoundingBox']['Top']
            width = block['Geometry']['BoundingBox']['Width']
            height = block['Geometry']['BoundingBox']['Height']

            if left < x and (y <= top <= y + h):
                left_texts.append(block['Text'])

            if left + width > x + w and (y <= top <= y + h):
                right_texts.append(block['Text'])

            if top < y and (x <= left <= x + w):
                top_texts.append(block['Text'])

            if top + height > y + h and (x <= left <= x + w):
                bottom_texts.append(block['Text'])

    left_percentages = [re.findall(percentage_pattern, text) for text in left_texts]
    right_percentages = [re.findall(percentage_pattern, text) for text in right_texts]
    top_percentages = [re.findall(percentage_pattern, text) for text in top_texts]
    bottom_percentages = [re.findall(percentage_pattern, text) for text in bottom_texts]

    # Flatten the lists of lists
    left_percentages = [percentage for sublist in left_percentages for percentage in sublist]
    right_percentages = [percentage for sublist in right_percentages for percentage in sublist]
    top_percentages = [percentage for sublist in top_percentages for percentage in sublist]
    bottom_percentages = [percentage for sublist in bottom_percentages for percentage in sublist]

    return (left_texts, left_percentages), (right_texts, right_percentages), (top_texts, top_percentages), (bottom_texts, bottom_percentages)

file_path = 'your_json_file.json'  # Replace this with your file path
x, y, w, h = 0.5, 0.5, 0.1, 0.1  # Replace this with your x, y, w, h

(left_texts, left_percentages), (right_texts, right_percentages), (top_texts, top_percentages), (bottom_texts, bottom_percentages) = get_surrounding_text(file_path, x, y, w, h)
print(f'Texts to the left of the region: {left_texts}, Percentages: {left_percentages}')
print(f'Texts to the right of the region: {right_texts}, Percentages: {right_percentages}')
print(f'Texts above the region: {top_texts}, Percentages: {top_percentages}')
print(f'Texts below the region: {bottom_texts}, Percentages: {bottom_percentages}')





import json
import re

def get_left_and_above_left_text(file_path, x, y, w, h):
    with open(file_path, 'r') as f:
        textract_output = json.load(f)

    left_texts = []
    above_left_texts = []

    for block in textract_output['Blocks']:
        if block['BlockType'] in ['WORD', 'LINE']:
            left = block['Geometry']['BoundingBox']['Left']
            top = block['Geometry']['BoundingBox']['Top']

            if left < x and (y <= top <= y + h):
                left_texts.append(block['Text'])

            if left < x and top < y:
                above_left_texts.append(block['Text'])

    # Find all percentage strings in the left_texts and above_left_texts
    percentage_pattern = r'\b\d{1,3}(?:\.\d{1,2})?%\b'
    left_percentages = [re.findall(percentage_pattern, text) for text in left_texts]
    above_left_percentages = [re.findall(percentage_pattern, text) for text in above_left_texts]

    # Flatten the lists of lists
    left_percentages = [percentage for sublist in left_percentages for percentage in sublist]
    above_left_percentages = [percentage for sublist in above_left_percentages for percentage in sublist]

    return left_percentages, above_left_percentages

file_path = 'your_json_file.json'  # Replace this with your file path
x, y, w, h = 0.5, 0.5, 0.1, 0.1  # Replace this with your x, y, w, h

left_percentages, above_left_percentages = get_left_and_above_left_text(file_path, x, y, w, h)
print(f'Percentage texts to the left of the region: {left_percentages}')
print(f'Percentage texts above and to the left of the region: {above_left_percentages}')



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
