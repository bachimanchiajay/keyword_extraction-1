import json
import boto3

def load_textract_json(bucket_name, file_name):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket_name, Key=file_name)
    data = json.loads(obj['Body'].read().decode('utf-8'))  # decode the bytes to string and then load as json
    return data

def add_spaces(string):
    return ' '.join(string)

def find_string_and_percentage(response, search_string, page):
    search_string_box = None
    percentages_near_search = []
    current_page = 0
    for item in response["Blocks"]:
        if item["BlockType"] == "PAGE":
            current_page += 1
        if current_page == page and item["BlockType"] == "LINE":
            text = item.get("Text", "")
            if search_string in text:
                search_string_box = item["Geometry"]["BoundingBox"]
            elif '%' in text and search_string_box is not None:
                percentage_box = item["Geometry"]["BoundingBox"]
                if search_string_box["Top"] <= percentage_box["Top"] and search_string_box["Left"] < percentage_box["Left"] <= search_string_box["Left"] + 0.1:
                    percentages_near_search.append((text, percentage_box))

    return percentages_near_search

bucket_name = '<your_bucket_name>'  # replace with your bucket name
file_name = '<your_file_name>'  # replace with your file name

search_string = "hello"
search_string = add_spaces(search_string)
page = 2  # The page number you want to search

response = load_textract_json(bucket_name, file_name)
percentages = find_string_and_percentage(response, search_string, page)

for percentage in percentages:
    print(f"Found '{percentage[0]}' at coordinates {percentage[1]}")
    
    
import re

# The regular expression pattern for dd/m/yyyy and dd/mm/yyyy
pattern = r"\b(0?[1-9]|[12][0-9]|3[01])/(0?[1-9]|1[0-2])/(19|20)\d\d\b"

text = """
    This is some text with a date 12/1/2023 embedded in it.
    And here's another date: 31/05/2023.
"""

matches = re.findall(pattern, text)
for match in matches:
    print("/".join(match))

