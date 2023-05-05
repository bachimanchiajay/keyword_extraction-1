from flask import Flask, request
import openai
import json

# Set up Flask app and OpenAI API key
app = Flask(__name__)
openai.api_key = "YOUR_API_KEY_HERE"

# Define route for ChatGPT endpoint
@app.route("/chat", methods=["POST"])
def chat():
    # Get input from request body
    input_text = request.get_data(as_text=True)

    # Use OpenAI's API to generate a response
    response = openai.Completion.create(
        engine="davinci",
        prompt=input_text,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.7,
    )

    # Extract response text from OpenAI API response
    response_text = response.choices[0].text.strip()

    # Return response as JSON
    return json.dumps({"response": response_text})

# Run the app
if __name__ == "__main__":
    app.run(debug=True)



























































import boto3
import io
import pandas as pd
from PIL import Image

# Create a Textract client
textract = boto3.client('textract')

# Specify the S3 bucket and key of the image
s3_bucket = 'your_s3_bucket'
s3_key = 'your_s3_key.jpg'

# Load a DataFrame containing the coordinates of the regions to extract text from
region_df = pd.read_csv('region_coordinates.csv')

# Loop over each row in the DataFrame and extract text from the specified region
for i, row in region_df.iterrows():
    x1, y1, x2, y2 = row['x1'], row['y1'], row['x2'], row['y2']
    print(f"Extracting text from region {i+1} ({x1}, {y1}) - ({x2}, {y2})...")
    
    # Download the image from S3
    s3 = boto3.resource('s3')
    image_obj = s3.Object(s3_bucket, s3_key).get()
    image = Image.open(io.BytesIO(image_obj['Body'].read()))

    # Crop the image to the specified region
    region_image = image.crop((x1, y1, x2, y2))

    # Convert the image to JPEG format and save it to a bytes buffer
    jpeg_buffer = io.BytesIO()
    region_image.save(jpeg_buffer, format='JPEG')
    image_bytes = jpeg_buffer.getvalue()

    # Create a Textract request to analyze the specified region of the image
    textract_request = {
        'Document': {
            'Bytes': image_bytes
        },
        'FeatureTypes': ['TABLES', 'FORMS']
    }

    # Call Textract to analyze the image and extract the specified region of text
    response = textract.analyze_document(Document=textract_request)

    # Extract the raw text from the Textract response
    raw_text = ''
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            for word in block['Relationships'][0]['Ids']:
                for item in response['Blocks']:
                    if item['Id'] == word and item['BlockType'] == 'WORD':
                        raw_text += item['Text'] + ' '

    print(f"Text extracted from region {i+1}:")
    print(raw_text)
    print()
    
    # Specify the bucket and folder
bucket_name = 'your-bucket-name'
folder_name = 'your-folder-name'

# List all objects in the folder
objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)

# Iterate over the objects
for obj in objects['Contents']:
    key = obj['Key']
    if key.lower().endswith('.pdf'):  # Check if the object is a PDF file
        # Download the PDF file into memory
        response = s3.get_object(Bucket=bucket_name, Key=key)
        file_data = response['Body'].read()

        # Read the PDF content using PyPDF2
        with BytesIO(file_data) as file:
            pdf_reader = PyPDF2.PdfFileReader(file)

            # Iterate over the pages and extract the text
            for page_num in range(pdf_reader.numPages):
                page = pdf_reader.getPage(page_num)
                text = page.extractText()
                print(f"Content of {key} - Page {page_num + 1}:\n{text}\n")

