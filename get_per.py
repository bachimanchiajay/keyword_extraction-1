import json

def load_textract_json(json_file):
    with open(json_file) as f:
        data = json.load(f)
    return data

def find_percentage(response, page):
    found_percentage = []
    current_page = 0
    for item in response["Blocks"]:
        if item["BlockType"] == "PAGE":
            current_page += 1
        if item["BlockType"] == "LINE" and current_page == page:
            text = item["Text"]
            if '%' in text and item["Geometry"]["BoundingBox"]["Left"] < 0.5:
                found_percentage.append((text, item["Geometry"]["BoundingBox"]))

    return found_percentage

json_file = "<your_json_file_path>"
page = 2  # The page number you want to search
response = load_textract_json(json_file)
percentages = find_percentage(response, page)

for percentage in percentages:
    print(f"Found '{percentage[0]}' at coordinates {percentage[1]}")
