import boto3
import pandas as pd
from PyPDF2 import PdfFileReader
from pdf2image import convert_from_path
import io

# Replace this with the S3 bucket name
bucket_name = 'YOUR_BUCKET_NAME'

# Create a DataFrame with PDF file paths and start and end page numbers
data = {
    'pdf_file_key': [
        'path/to/your/pdf/file1.pdf',
        'path/to/your/pdf/file2.pdf',
    ],
    'start_page': [3, 1],
    'end_page': [5, 4],
}

pdf_page_ranges = pd.DataFrame(data)

# Set up the S3 client
s3 = boto3.client('s3')

# Loop through the DataFrame rows
for index, row in pdf_page_ranges.iterrows():
    pdf_file_key = row['pdf_file_key']
    start_page = row['start_page']
    end_page = row['end_page']

    # Download the PDF file from the S3 bucket
    pdf_file = io.BytesIO()
    s3.download_fileobj(bucket_name, pdf_file_key, pdf_file)
    pdf_file.seek(0)

    # Get the number of pages in the PDF
    pdf_reader = PdfFileReader(pdf_file)
    num_pages = pdf_reader.getNumPages()

    # Check if the specified range is within the total number of pages
    if start_page <= 0 or end_page > num_pages:
        raise ValueError("Invalid page range. Check the start_page and end_page values.")

    # Convert the specified pages of the PDF file to images
    images = convert_from_path(pdf_file, first_page=start_page, last_page=end_page)

    # Save the images and upload to S3
    for i, image in enumerate(images, start=start_page):
        image_file_name = f'{pdf_file_key}_image_page_{i}.png'
        image.save(image_file_name, 'PNG')

        # Upload the image to S3
        with open(image_file_name, 'rb') as image_file:
            s3.upload_fileobj(image_file, bucket_name, f'path/to/save/{image_file_name}')
            
            
            
import boto3
import layoutparser as lp
from PIL import Image

# Load your custom-trained Layout Parser model
model_checkpoint = "YOUR_MODEL_CHECKPOINT"
config_file = "YOUR_CONFIG_FILE"
model = lp.Detectron2LayoutModel(config_path=config_file,
                                  model_path=model_checkpoint,
                                  label_map={0: "Text"})

def extract_text_from_coordinates(image_file_path, coordinates):
    # Initialize the Textract client
    textract_client = boto3.client("textract", region_name="YOUR_AWS_REGION")

    # Read the image file
    with open(image_file_path, "rb") as image_file:
        image_data = image_file.read()

    # Analyze the document using Textract
    response = textract_client.analyze_document(Document={"Bytes": image_data}, FeatureTypes=["TABLES", "FORMS"])

    # Load the image for Layout Parser
    image = Image.open(image_file_path)

    # Predict the layout using your custom-trained model
    layout = model.detect(image)

    extracted_texts = []
    for coord in coordinates:
        # Create a block representing the field coordinates
        field_block = lp.Rectangle(coord)

        # Extract the text within the field coordinates
        field_text = lp.Layout([t for t in layout if field_block.contains(t)])
        extracted_texts.append(field_text.get_text())

    return extracted_texts

# Replace "YOUR_IMAGE_FILE_PATH" with the path to your image file
image_file_path = "YOUR_IMAGE_FILE_PATH"

# Replace with the coordinates of the fields you want to extract text from
coordinates = [
    [x0, y0, x1, y1],
    [x2, y2, x3, y3],
    # ...
]

extracted_texts = extract_text_from_coordinates(image_file_path, coordinates)
print(extracted_texts)

