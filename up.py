import fitz  # PyMuPDF
import boto3
import json
import mysql.connector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer, util
import openai
import faiss
import numpy as np

# Initialize OpenAI API
openai.api_key = 'your-openai-api-key'

# Initialize FAISS index
dimension = 384  # Dimension of the embeddings
index = faiss.IndexFlatL2(dimension)
metadata_store = {}

def extract_text_and_metadata_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    metadata = doc.metadata
    for page in doc:
        text += page.get_text()
    return text, metadata

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

def save_chunks_and_embeddings_to_vector_db(chunks, embeddings, docu_id):
    global metadata_store
    embeddings_np = embeddings.cpu().numpy()
    index.add(embeddings_np)
    for i, chunk in enumerate(chunks):
        vector_id = f"{docu_id}_chunk_{i}"
        metadata_store[vector_id] = {'chunk': chunk, 'docu_id': docu_id}
    print("Chunks and embeddings saved to FAISS")

def retrieve_embeddings_from_vector_db(docu_id):
    global metadata_store
    embeddings = []
    for vector_id, metadata in metadata_store.items():
        if metadata['docu_id'] == docu_id:
            embeddings.append(index.reconstruct(int(vector_id.split('_')[-1])))
    return np.array(embeddings)

def search_similar_chunks(main_doc_embeddings, uploaded_doc_embeddings):
    similarities = util.pytorch_cos_sim(main_doc_embeddings, uploaded_doc_embeddings)
    return similarities

def cot_reasoning_for_omissions_and_dissimilarities(main_chunk, uploaded_chunk):
    prompt = f"Compare the following two chunks and identify omissions and key dissimilarities:\n\nMain Chunk:\n{main_chunk}\n\nUploaded Chunk:\n{uploaded_chunk}\n\nProvide a detailed explanation:"
    response = openai.Completion.create(
        engine="davinci-codex",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()

def process_pdf(pdf_path, docu_id):
    try:
        text, metadata = extract_text_and_metadata_from_pdf(pdf_path)
        chunks = chunk_text_with_langchain(text)
        embeddings = generate_embeddings(chunks)
        save_chunks_and_embeddings_to_vector_db(chunks, embeddings, docu_id)
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
    
    similarities = search_similar_chunks(main_doc_embeddings, uploaded_doc_embeddings)
    
    # Compare matched chunks
    for i, similarity in enumerate(similarities):
        main_chunk = main_doc_embeddings[i]
        uploaded_chunk = uploaded_doc_embeddings[i]
        explanation = cot_reasoning_for_omissions_and_dissimilarities(main_chunk, uploaded_chunk)
        print(f"Comparison for chunk {i}:\n{explanation}\n")
    
    return similarities

# Example usage
main_doc_path = 'path/to/main_document.pdf'
uploaded_doc_path = 'path/to/uploaded_document.pdf'
similarities = compare_main_and_uploaded_docs(main_doc_path, uploaded_doc_path)
print(similarities)
