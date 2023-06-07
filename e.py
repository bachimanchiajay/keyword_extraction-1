def get_coordinates_of_string(bucket, file_path, search_string):
    s3_connection = boto3.resource("s3")
    client = boto3.client('s3')
    result = client.get_object(Bucket=bucket, Key=file_path)
    text = result['Body'].read().decode('utf-8')
    textract_output = json.loads(text)

    try:
        for res in textract_output:
            for block in res['Blocks']:
                if block['BlockType'] in ['WORD', 'LINE']:
                    text = block['Text']
                    # Check for exact match
                    if text == search_string:
                        bounding_box = block['Geometry']['BoundingBox']
                        coordinates = {
                            'x': bounding_box['Left'],
                            'y': bounding_box['Top'],
                            'w': bounding_box['Width'],
                            'h': bounding_box['Height'],
                        }
                        return coordinates

                    # Check for match with extra spaces and characters
                    if search_string in text:
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

    return None



def final_fn(bucket_name, json_path, reference_numbers):
    list1 = []
    text_dict, _, _, df_word = process_text_analysis(bucket_name, json_path)
    page = get_reference_page(text_dict)

    try:
        if page is not None:
            text_page = text_dict[page]
            print(text_page)

            for i in range(len(reference_numbers)):
                search_string = reference_numbers[i]
                search_string = add_spaces(search_string)
                coordinates = get_coordinates_of_string(bucket_name, json_path, search_string)

                if coordinates is None:
                    # Handle case where exact match is not found, but there might be slight variations
                    if search_string in text_page:
                        matched_string = search_string
                        coordinates = get_coordinates_of_string(bucket_name, json_path, matched_string)

                get_refernce_json_page(bucket_name, json_path, "AMU.json", page)
                per = merge_1("AMU.json")
                pattern_date = r'\b(?:\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-d{2}|(?:\d{1,2}|(?:(?:3[01]|[12][0-9]|0?[1-9])th)) \w+\d{2,4})\b'
                matches_date = re.findall(pattern_date, text_page)
                percentage_line = per.replace('%', '')
                written_line = ''
                entity = str(510)
                section_type = str("NON EEA")

                if coordinates is not None:
                    dict1 = {
                        reference_numbers[i]: {
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
                    print("Coordinates not found for reference number:", reference_numbers[i])

                os.remove("AMU.json")

    except Exception as e:
        print('An error occurred:', e)

    tuple_dict = (list1,)
    return tuple_dict
