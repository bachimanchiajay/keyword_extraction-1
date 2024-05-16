import subprocess
import os
import boto3

def convert_doc_to_docx(input_bucket, input_key):
    s3_client = boto3.client('s3')
    
    # Download the file from S3
    tmp_file_path = f"/tmp/{os.path.basename(input_key)}"
    s3_client.download_file(input_bucket, input_key, tmp_file_path)
    
    # Define the output file path
    output_docx_path = f"{tmp_file_path.rsplit('.', 1)[0]}.docx"
    
    # Pandoc command to convert doc to docx
    command = ['pandoc', '-o', output_docx_path, tmp_file_path]
    
    # Execute the command
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"File converted successfully and saved as {output_docx_path}")
        
        # Optionally upload the converted file back to S3
        # s3_client.upload_file(output_docx_path, input_bucket, output_docx_path)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to convert DOC to DOCX: {e.stderr.decode()}")

# Example usage
convert_doc_to_docx("your-bucket-name", "path/to/your/document.doc")
