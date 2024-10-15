import fitz  # PyMuPDF
import boto3
import json
import mysql.connector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer, util

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_metadata_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    metadata = doc.metadata
    return metadata

def chunk_text_with_langchain(text, chunk_size=1000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_text(text)
    return chunks

def generate_embeddings(chunks):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(chunks, convert_to_tensor=True)
    return embeddings

def save_chunks_to_s3(chunks, docu_id):
    s3_client = boto3.client('s3')
    bucket_name = 'your-bucket-name'
    for i, chunk in enumerate(chunks):
        s3_key = f'specific-folder/{docu_id}_chunk_{i}.json'
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps({"chunk": chunk}),
            ContentType='application/json'
        )
        print(f"Chunk {i} saved to S3")

def save_metadata_to_mysql(metadata, docu_id):
    try:
        connection = mysql.connector.connect(
            host='your-mysql-host',
            user='your-mysql-username',
            password='your-mysql-password',
            database='your-database-name'
        )
        cursor = connection.cursor()
        sql = "INSERT INTO metadata (docu_id, metadata) VALUES (%s, %s)"
        cursor.execute(sql, (docu_id, json.dumps(metadata)))
        connection.commit()
        print("Metadata inserted into MySQL")
    except Exception as e:
        print(str(e))
    finally:
        cursor.close()
        connection.close()

def save_embeddings_to_vector_db(embeddings, docu_id):
    # Placeholder function to save embeddings to a vector database
    # Implement this function based on your vector database
    pass

def retrieve_embeddings_from_vector_db(docu_id):
    # Placeholder function to retrieve embeddings from a vector database
    # Implement this function based on your vector database
    pass

def compare_documents(main_doc_embeddings, uploaded_doc_embeddings):
    similarities = util.pytorch_cos_sim(main_doc_embeddings, uploaded_doc_embeddings)
    return similarities

def process_pdf(pdf_path, docu_id):
    try:
        text = extract_text_from_pdf(pdf_path)
        metadata = extract_metadata_from_pdf(pdf_path)
        chunks = chunk_text_with_langchain(text)
        embeddings = generate_embeddings(chunks)
        save_chunks_to_s3(chunks, docu_id)
        save_metadata_to_mysql(metadata, docu_id)
        save_embeddings_to_vector_db(embeddings, docu_id)
        print("All data saved successfully")
        return 'Success'
    except Exception as e:
        print(str(e))
        return 'Error in processing PDF'

def compare_main_and_uploaded_docs(main_doc_path, uploaded_doc_path):
    main_docu_id = 'main_document_id'
    uploaded_docu_id = 'uploaded_document_id'
    
    process_pdf(main_doc_path, main_docu_id)
    process_pdf(uploaded_doc_path, uploaded_docu_id)
    
    # Retrieve embeddings from vector database
    main_doc_embeddings = retrieve_embeddings_from_vector_db(main_docu_id)
    uploaded_doc_embeddings = retrieve_embeddings_from_vector_db(uploaded_docu_id)
    
    similarities = compare_documents(main_doc_embeddings, uploaded_doc_embeddings)
    return similarities

# Example usage
main_doc_path = 'path/to/main_document.pdf'
uploaded_doc_path = 'path/to/uploaded_document.pdf'
similarities = compare_main_and_uploaded_docs(main_doc_path, uploaded_doc_path)
print(similarities)
