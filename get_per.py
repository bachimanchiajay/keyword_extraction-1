import json
import boto3
import re

def load_textract_json(bucket_name, file_name):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket_name, Key=file_name)
    data = json.loads(obj['Body'].read().decode('utf-8'))  # decode the bytes to string and then load as json
    return data

def add_spaces(string):
    return ' '.join(string)

def find_string_and_percentage_and_dates(response, search_string, page):
    search_string_box = None
    percentages_near_search = []
    dates_near_search = []
    current_page = 0
    date_pattern = r"\b(0?[1-9]|[12][0-9]|3[01])/(0?[1-9]|1[0-2])/(19|20)\d\d\b"
    percentage_pattern = r"\b\d{1,3}\.\d{1,2}%\b"
    for item in response["Blocks"]:
        if item["BlockType"] == "PAGE":
            current_page += 1
        if current_page == page and item["BlockType"] == "LINE":
            text = item.get("Text", "")
            if search_string in text:
                search_string_box = item["Geometry"]["BoundingBox"]
            else:
                percentage_matches = re.findall(percentage_pattern, text)
                if percentage_matches and search_string_box is not None:
                    percentage_box = item["Geometry"]["BoundingBox"]
                    # If the percentage_box is to the left side of the search_string_box
                    if search_string_box["Top"] <= percentage_box["Top"] and percentage_box["Left"] + percentage_box["Width"] <= search_string_box["Left"]:
                        percentages_near_search.append((percentage_matches, percentage_box))
                else:
                    date_matches = re.findall(date_pattern, text)
                    if date_matches:
                        date_box = item["Geometry"]["BoundingBox"]
                        dates_near_search.append((date_matches, date_box))

    return percentages_near_search, dates_near_search

bucket_name = '<your_bucket_name>'  # replace with your bucket name
file_name = '<your_file_name>'  # replace with your file name

search_string = "hello"
search_string = add_spaces(search_string)
page = 2  # The page number you want to search

response = load_textract_json(bucket_name, file_name)
percentages, dates = find_string_and_percentage_and_dates(response, search_string, page)

for percentage in percentages:
    print(f"Found '{percentage[0]}' at coordinates {percentage[1]}")

for date in dates:
    print(f"Found '{date[0]}' at coordinates {date[1]}")

    
    import json

def get_page_from_textract_json(textract_json_path, page_number):
    # Load the Textract JSON file
    with open(textract_json_path, 'r') as json_file:
        textract_data = json.load(json_file)

    # Get the desired page number
    pages = textract_data['Blocks']
    page_blocks = [block for block in pages if block['BlockType'] == 'PAGE']
    if page_number <= len(page_blocks):
        desired_page = page_blocks[page_number - 1]
        return desired_page
    else:
        return None

# Path to the Textract JSON file
textract_json_path = '/path/to/textract.json'

# Page number to extract (e.g., 1, 2, 3)
page_number = 2

# Get the desired page from the Textract JSON file
page = get_page_from_textract_json(textract_json_path, page_number)

if page is not None:
    # Process the desired page
    print(f"Processing page number {page_number}")
    # ... further processing of the page data
else:
    print(f"Page number {page_number} not found in the Textract JSON file.")
    
    
    
import json

def extract_left_text_from_textract_json(textract_json_path, search_string):
    # Load the Textract JSON file
    with open(textract_json_path, 'r') as json_file:
        textract_data = json.load(json_file)

    # Extract the text blocks from the Textract JSON
    text_blocks = [block for block in textract_data['Blocks'] if block['BlockType'] == 'WORD']

    # Find the block with the search string
    search_block = next((block for block in text_blocks if block['Text'] == search_string), None)

    if search_block is not None:
        # Get the bounding box coordinates of the search block
        left = search_block['Geometry']['BoundingBox']['Left']
        top = search_block['Geometry']['BoundingBox']['Top']
        width = search_block['Geometry']['BoundingBox']['Width']
        height = search_block['Geometry']['BoundingBox']['Height']

        # Calculate the coordinates for the left text
        left_text_left = left - width  # Adjust this value based on your requirements
        left_text_top = top
        left_text_width = width
        left_text_height = height

        # Find the text blocks within the left text coordinates
        left_text_blocks = [block for block in text_blocks if
                            block['Geometry']['BoundingBox']['Left'] >= left_text_left and
                            block['Geometry']['BoundingBox']['Top'] >= left_text_top and
                            block['Geometry']['BoundingBox']['Left'] <= left_text_left + left_text_width and
                            block['Geometry']['BoundingBox']['Top'] <= left_text_top + left_text_height]

        # Extract the left text data
        left_text_data = ' '.join([block['Text'] for block in left_text_blocks])
        return left_text_data
    else:
        return None

# Path to the Textract JSON file
textract_json_path = '/path/to/textract.json'

# Search string to find the index and extract the left text data
search_string = 'your search string'

# Extract the left text data from the search string coordinates
left_text_data = extract_left_text_from_textract_json(textract_json_path, search_string)

if left_text_data is not None:
    print(f"Left Text Data: {left_text_data}")
else:
    print(f"Search string '{search_string}' not found in the Textract JSON file.")

