import boto3
import json
import pandas as pd
import re
import os

def process_text_analysis(bucket, document):
    s3_connection = boto3.resource("s3")
    client = boto3.client('s3')
    result = client.get_object(Bucket=bucket, Key=document)
    text = result['Body'].read().decode('utf-8')
    res = json.loads(text)

    left_cor = []
    top_cor = []
    width_cor = []
    height_cor = []
    page = []
    line_text = []

    for response in res:
        blocks = response["Blocks"]
        for block in blocks:
            if block["BlockType"] == "LINE":
                left_cor.append(float("{:.3f}".format(block["Geometry"]["BoundingBox"]["Left"])))
                top_cor.append(float("{:.3f}".format(block["Geometry"]["BoundingBox"]["Top"])))
                width_cor.append(float("{:.3f}".format(block["Geometry"]["BoundingBox"]["Width"])))
                height_cor.append(float("{:.3f}".format(block["Geometry"]["BoundingBox"]["Height"])))
                line_text.append(block["Text"])
                page.append(block["Page"])

    df_line = pd.DataFrame(list(zip(left_cor, top_cor, width_cor, height_cor, line_text, page)),
                           columns=["xmin", "ymin", "width_cor", "height_cor", "line_text", "page"])
    df_line["xmax"] = (df_line["xmin"] + df_line["width_cor"])
    df_line["ymax"] = (df_line["ymin"] + df_line["height_cor"])

    left_cor = []
    top_cor = []
    width_cor = []
    height_cor = []
    page = []
    word_text = []

    for response in res:
        blocks = response["Blocks"]
        for block in blocks:
            if block["BlockType"] == "WORD":
                left_cor.append(float("{:.3f}".format(block["Geometry"]["BoundingBox"]["Left"])))
                top_cor.append(float("{:.3f}".format(block["Geometry"]["BoundingBox"]["Top"])))
                width_cor.append(float("{:.3f}".format(block["Geometry"]["BoundingBox"]["Width"])))
                height_cor.append(float("{:.3f}".format(block["Geometry"]["BoundingBox"]["Height"])))
                word_text.append(block["Text"])
                page.append(block["Page"])

    df_word = pd.DataFrame(list(zip(left_cor, top_cor, width_cor, height_cor, word_text, page)),
                           columns=["xmin", "ymin", "width_cor", "height_cor", "word_text", "page"])
    df_word["xmax"] = (df_word["xmin"] + df_word["width_cor"])
    df_word["ymax"] = (df_word["ymin"] + df_word["height_cor"])

    pages = df_line.page.unique().tolist()
    text_dict = {}
    for p in pages:
        dfp = df_line[df_line.page == p]
        txt_list = dfp.line_text.tolist()
        txt = " ".join(txt_list)
        text_dict[p] = txt

    return text_dict, res, df_line, df_word


def get_reference_page(text_dict):
    reference_page = None
    pattern_security_details = r'(Security\s*Details?\s*:?)|(SECURITY\s*DETAILS?\s*:?)|(Security\s*details?\s*:?)|(SIGNED\s*UNDERWRITERS?\s*:?)|(Reinsured\s*Signing\s*Page?\s*:?)|(Reinsurer\s*Signing\s*Page?\s*:?)'
    pattern_wr = r'(WRITTEN\s*LINES\s*:?)|(Written\s*:?)'
    pattern_tmk = r'(TMK1880\s*:?)'
    pattern_kln = r'(KLN510\s*:?)'
    pattern_lloyd = r'(Lloyd’s?\s*:?)|(Lloyd’s\s*Underwriter\s*Synd.?\s*:?)'
    pattern = r'[A-Za-z]{1}\s*[A-Za-z]{1}\s*[A-Za-z]{1}\s*\d{1}\s*\d{1}\s*\d{1}\s*[A-Za-z]{1}\s*\d{1}\s*\d{1}\s*[A-Za-z]{1}\s*[A-Za-z]{1}'

    for page_no, page_text in text_dict.items():
        match_sec = re.search(pattern_security_details, page_text)
        match_wr = re.search(pattern_wr, page_text)
        match_tmk = re.search(pattern_tmk, page_text)
        match_kln = re.search(pattern_kln, page_text)
        match_lloyd = re.search(pattern_lloyd, page_text)
        match_pattern = re.search(pattern, page_text)

        if (match_sec and match_wr and match_pattern) or (
                match_sec and match_tmk and match_kln and match_pattern) or (
                match_sec and match_tmk and match_kln and match_lloyd and match_pattern) or (
                match_wr and match_tmk and match_kln and match_pattern):
            reference_page = page_no
            break

    return reference_page


def get_refernce_json_page(bucket, document, output_json, page_no):
    s3_connection = boto3.resource("s3")
    client = boto3.client('s3')
    result = client.get_object(Bucket=bucket, Key=document)
    text = result['Body'].read().decode('utf-8')
    res = json.loads(text)

    page_blocks = []
    for response in res:
        blocks = response["Blocks"]
        for block in blocks:
            if 'Page' in block and block['Page'] == page_no:
                page_blocks.append(block)
    page_data = {'Blocks': page_blocks}

    with open(output_json, 'w') as f:
        json.dump(page_data, f)


def add_space(reference_id):
    reference_id = ' '.join(reference_id)
    return reference_id


def get_coordinates_of_string(bucket, file_path, search_string):
    s3_connection = boto3.resource("s3")
    client = boto3.client('s3')
    result = client.get_object(Bucket=bucket, Key=file_path)
    text = result['Body'].read().decode('utf-8')
    textract_output = json.loads(text)

    try:
        for res in textract_output:
            for block in res['Blocks']:
                if block['BlockType'] in ['WORD', 'LINE'] and block['Text'] == search_string:
                    bounding_box = block['Geometry']['BoundingBox']
                    coordinates = {
                        'x': bounding_box['Left'],
                        'y': bounding_box['Top'],
                        'w': bounding_box['Width'],
                        'h': bounding_box['Height'],
                    }
                    return coordinates
                elif block['BlockType'] in ['WORD', 'LINE'] and block['Text'] == add_space(search_string):
                    bounding_box = block['Geometry']['BoundingBox']
                    coordinates = {
                        'x': bounding_box['Left'],
                        'y': bounding_box['Top'],
                        'w': bounding_box['Width'],
                        'h': bounding_box['Height'],
                    }
                    return coordinates
    except Exception as e:
        print('An error occurred:', e)
        return None


def extract_reference_ids_and_draw_bounding_boxes_from_json(json_file, regex_pattern):
    with open(json_file, "r") as file:
        response = json.load(file)

    blocks = response['Blocks']
    text = ''
    for item in response['Blocks']:
        if item["BlockType"] == 'LINE':
            text += item['Text'] + ' '

    reference_ids = []
    reference_id_coordinates = []
    for block in blocks:
        if block['BlockType'] == 'LINE':
            text = block['Text']
            match = re.search(regex_pattern, text)
            if match:
                reference_id = match.group(0)
                reference_ids.append(reference_id)
                reference_id_coordinates.append(block['Geometry']['BoundingBox'])

    x = reference_id_coordinates[0]['Left']
    y = reference_id_coordinates[0]['Top']
    w = reference_id_coordinates[0]['Width']
    h = reference_id_coordinates[0]['Height']

    return x, y, w, h


def get_surrounding_text(file_path, x, y, w, h):
    with open(file_path, 'r') as f:
        textract_output = json.load(f)

    left_texts, right_texts, top_texts, bottom_texts = [], [], [], []
    percentage_pattern = r'\b(?!(?:80|20)%)\d+(?:\.\d+)?\s*%'

    for block in textract_output['Blocks']:
        if block['BlockType'] in ['WORD', 'LINE']:
            left = block['Geometry']['BoundingBox']['Left']
            top = block['Geometry']['BoundingBox']['Top']
            width = block['Geometry']['BoundingBox']['Width']
            height = block['Geometry']['BoundingBox']['Height']

            if left < x and (y <= top <= y + h) or (y - 0.4 * h <= top <= y + 1 + h):
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

    left_percentages = [percentage for sublist in left_percentages for percentage in sublist]
    right_percentages = [percentage for sublist in right_percentages for percentage in sublist]
    top_percentages = [percentage for sublist in top_percentages for percentage in sublist]
    bottom_percentages = [percentage for sublist in bottom_percentages for percentage in sublist]

    return left_percentages


def merge_1(json_file):
    pattern_reference = r'[A-Za-z]{1}\s*[A-Za-z]{1}\s*[A-Za-z]{1}\s*\d{1}\s*\d{1}\s*\d{1}\s*[A-Za-z]{1}\s*\d{1}\s*\d{1}\s*[A-Za-z]{1}\s*[A-Za-z]{1}'
    x, y, w, h = extract_reference_ids_and_draw_bounding_boxes_from_json(json_file, pattern_reference)
    left_percentages = get_surrounding_text(json_file, x, y, w, h)

    pattern_lloyd = r"Lloyd's\sUnderwriter"
    x1, y1, w1, h1 = extract_reference_ids_and_draw_bounding_boxes_from_json(json_file, pattern_lloyd)
    left_percentages2 = get_surrounding_text(json_file, x1, y1, w1, h1)

    final_per = left_percentages + left_percentages2

    if final_per == []:
        return None
    else:
        return final_per[0]


def add_spaces(stri):
    stri = ' '.join(stri)
    return stri


def final_fn(bucket_name, json_path, reference_id):
    list1 = []
    text_dict, _, _, df_word = process_text_analysis(bucket_name, json_path)
    page = get_reference_page(text_dict)

    try:
        if page != None:
            text_page = text_dict[page]
            print(text_page)

            for i in range(len(reference_id)):
                search_string = reference_id[i]
                search_string = add_spaces(search_string)
                coordinates = get_coordinates_of_string(bucket_name, json_path, search_string)
                get_refernce_json_page(bucket_name, json_path, "AMU.json", page)
                per = merge_1("AMU.json")
                pattern_date = r'\b(?:\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-d{2}|(?:\d{1,2}|(?:(?:3[01]|[12][0-9]|0?[1-9])th)) \w+\d{2,4})\b'
                matches_date = re.findall(pattern_date, text_page)
                percentage_line = per.replace('%', '')
                written_line = ''
                entity = str(510)
                section_type = str("NON EEA")

                if coordinates != None:
                    dict1 = {
                        reference_id[i]: {
                            "overall_written_line": percentage_line,
                            'written_line': written_line,
                            'entity': entity,
                            "written_date": str(matches_date[0]),
                            'Risk_Code': [],
                            'page_number': str(page),
                            'coordinates': coordinates,
                            'Section_Type': section_type
                        }
                    }
                    list1.append(dict1)
                else:
                    print("Coordinates not found for reference number:", reference_id[i])

                os.remove("AMU.json")

    except Exception as e:
        print('An error occurred:', e)

    tuple_dict = (list1,)
    return tuple_dict

# Example usage
bucket_name = "your_bucket_name"
json_path = "path_to_your_json_file"
reference_numbers = ["ABC12345", "DEF67890"]

result = final_fn(bucket_name, json_path, reference_numbers)
print(result)
