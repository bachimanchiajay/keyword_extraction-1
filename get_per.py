import json

def load_textract_json(json_file):
    with open(json_file) as f:
        data = json.load(f)
    return data

def find_string_and_percentage(response, search_string):
    search_string_box = None
    percentages_near_search = []
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            text = item["Text"]
            if search_string in text:
                search_string_box = item["Geometry"]["BoundingBox"]
            elif '%' in text and search_string_box is not None:
                percentage_box = item["Geometry"]["BoundingBox"]
                if percentage_box["Left"] < search_string_box["Left"] + 0.1:  # Adjust this value based on your requirements
                    percentages_near_search.append((text, percentage_box))

    return percentages_near_search

json_file = "<your_json_file_path>"
search_string = "<your_search_string>"
response = load_textract_json(json_file)
percentages = find_string_and_percentage(response, search_string)

for percentage in percentages:
    print(f"Found '{percentage[0]}' at coordinates {percentage[1]}")
