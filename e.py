import boto3
from boto3.dynamodb.conditions import Attr

def get_items_with_logo_and_productname(table_name, product_name):
    # Initialize a DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    # Scan the table and filter items where 'chunk_info.section_of_wording.logo' exists and product_name matches
    response = table.scan(
        FilterExpression=Attr('chunk_info.section_of_wording.logo').exists() & Attr('product_name').eq(product_name)
    )
    
    items = response.get('Items', [])
    
    results = []
    
    for item in items:
        chunk_info = item.get('chunk_info', {})
        section_of_wording = chunk_info.get('section_of_wording', {})
        if 'logo' in section_of_wording:
            filename = section_of_wording.get('filename')
            productname = item.get('product_name')
            results.append({
                'filename': filename,
                'productname': productname
            })
    
    return results

# Call the function directly and print the results
table_name = 'your_table_name'  # Replace with your table name
product_name = 'property_money'  # Replace with the product name you are looking for
items_with_logo = get_items_with_logo_and_productname(table_name, product_name)

for item in items_with_logo:
    print(f"Filename: {item['filename']}, Productname: {item['productname']}")

