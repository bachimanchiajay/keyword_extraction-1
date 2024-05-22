import boto3

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Specify your table name
table = dynamodb.Table('your_table_name')

# Scan the table
response = table.scan()

# Initialize an empty list to hold the document IDs
doc_ids_with_logo = []

# Iterate over each item in the table
for item in response['Items']:
    # Check if 'chunk_info' and 'section_of_wording' exist and 'logo' is in 'section_of_wording'
    if 'chunk_info' in item and 'section_of_wording' in item['chunk_info'] and 'logo' in item['chunk_info']['section_of_wording']:
        # If so, append the document ID to the list
        doc_ids_with_logo.append(item['doc_id'])

# Print the list of document IDs
print(doc_ids_with_logo)
