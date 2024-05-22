import boto3

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Specify your table name
table = dynamodb.Table('your_table_name')

# Specify the product name
product_name = 'your_product_name'

# Initialize an empty list to hold the document IDs
doc_ids_with_logo = []

# Initialize the scan parameters
scan_kwargs = {
    'FilterExpression': Attr('productname').eq(product_name) & Attr('chunk_info.section_of_wording').contains('logo')
}

done = False
start_key = None
while not done:
    if start_key:
        scan_kwargs['ExclusiveStartKey'] = start_key
    response = table.scan(**scan_kwargs)
    # Iterate over each item in the table
    for item in response['Items']:
        # Append the document ID to the list
        doc_ids_with_logo.append(item['doc_id'])
    start_key = response.get('LastEvaluatedKey', None)
    done = start_key is None

# Print the list of document IDs
print(doc_ids_with_logo)
