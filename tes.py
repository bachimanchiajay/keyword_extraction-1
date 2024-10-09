comp_mod
import boto3
import json
import logging
import os
import pymysql
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3', region_name='eu-west-2')
BUCKET = "output-bucket-hiscox-uat"

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Convert Decimal to float
        return super(DecimalEncoder, self).default(obj)

def get_db_connection():
    return pymysql.connect(
        host=os.environ['RDS_HOST'],
        user=os.environ['RDS_USER'],
        password=os.environ['RDS_PASSWORD'],
        database=os.environ['RDS_DB']
    )

def put_comp_map(meta_data, comparison_table, comparison_mapping_table):
    comparison_id = meta_data.get('comparison_id')
    transaction_id = meta_data.get('transaction_id')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Insert into comparison_table
        columns = ', '.join(meta_data.keys())
        placeholders = ', '.join(['%s'] * len(meta_data))
        sql = f"INSERT INTO {comparison_table} ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, list(meta_data.values()))
        connection.commit()
    except Exception as e:
        logger.info(f'Error while Inserting in {comparison_table} Table= {str(e)}')
        try:
            s3_key = transaction_id + '.json'
            s3_client.put_object(Bucket=BUCKET, Key=s3_key, Body=json.dumps(meta_data, cls=DecimalEncoder))
            logger.info('Comparison result inserted into output bucket')
        except Exception as e:
            logger.info('Insertion of output failed for both in bucket and MySQL')
            raise Exception('Insertion of output failed for both in bucket and MySQL')
    
    try:
        # Insert into comparison_mapping_table
        sql = f"INSERT INTO {comparison_mapping_table} (comparison_id, transaction_id) VALUES (%s, %s)"
        cursor.execute(sql, (comparison_id, transaction_id))
        connection.commit()
    except Exception as e:
        logger.info(f'Error while Inserting into Mapping Table = {str(e)}')
        raise Exception("Error while Inserting into Mapping Table")
    finally:
        cursor.close()
        connection.close()
    
    return 200

def connect_to_table(docu_id, product_name):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    try:
        sql = "SELECT * FROM documeta_data WHERE docu_id = %s AND product_name = %s"
        cursor.execute(sql, (docu_id, product_name))
        val = cursor.fetchall()
    except Exception as e:
        val = {'Error': f'Error: did not find any data corresponding to docu_id: {docu_id}'}
    finally:
        cursor.close()
        connection.close()
    
    return val

def scan_table(table_name):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    try:
        sql = f"SELECT * FROM {table_name}"
        cursor.execute(sql)
        response = cursor.fetchall()
    except Exception as e:
        response = {'Error': str(e)}
    finally:
        cursor.close()
        connection.close()
    
    return response

def save_to_s3(bucket, destination, data):
    s3 = boto3.resource('s3', region_name='eu-west-2')
    obj = s3.Object(bucket, destination)
    obj.put(Body=data)

def landing_page_update(result):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    op = {
        'comparison_id': result['comparison_id'],
        'agent_name': result['agent_name'],
        'comparison_score': result['comparison_score'],
        'product_name': result['product_name'],
        'docu_id_1': result['docu_id_1'],
        'docu_id_2': result['docu_id_2'],
        'modified_datetime': result['modified_datetime'],
        'comparison_status': result['comparison_status'],
        'document_1_type': result['document_1_type'],
        'document_2_type': result['document_2_type'],
        'sample_attr': 'query_test',
        'document_scheme_1': result['document_scheme_1'],
        'document_scheme_2': result['document_scheme_2']
    }
    
    try:
        columns = ', '.join(op.keys())
        placeholders = ', '.join(['%s'] * len(op))
        sql = f"INSERT INTO home_page ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, list(op.values()))
        connection.commit()
    except Exception as e:
        logger.info(f'Error while Inserting in Landing Page Table= {str(e)}')
        raise Exception("Error while Inserting in Landing Table")
    finally:
        cursor.close()
        connection.close()
    
    return 200

comp mod main

import os
import pathlib
import yaml
import json
from time import gmtime, strftime
from decimal import Decimal
import timeit
import re
import logging

import pandas as pd
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from comparison_pipeline import compare
from utils import format_ouput, format_metadata
from connections import connect_to_table, scan_table, put_comp_map, save_to_s3, landing_page_update

default_config_dir = pathlib.Path(__file__).parent


def generate_comparison(docu_id_1, docu_id_2, product_name, config):
    start = timeit.timeit()
    prompt_text = config.get('prompt_text')
    response_1 = connect_to_table(docu_id_1, product_name)
    response_2 = connect_to_table(docu_id_2, product_name)
    
    if not response_1.get('Error') and response_1[0].get('chunk_info'):
        chunk_info_1 = response_1[0]['chunk_info']
        poped = response_1[0].pop('chunk_info')
    else:
        val = {'Error': f'Error: did not find any data corresponding to docu_id: {docu_id_1}'}
        return val
    if not response_2.get('Error') and response_2[0].get('chunk_info'):
        chunk_info_2 = response_2[0]['chunk_info']
        poped = response_2[0].pop('chunk_info')
    else:
        val = {'Error': f'Error: did not find any data corresponding to docu_id: {docu_id_1}'}
        return val
   
    metadata_1 = response_1[0]
    df_doc_1 = pd.DataFrame(chunk_info_1)
    for i, row in df_doc_1.iterrows():
        if row['section_of_wording'] == 'Header':
            row['doc_chunk'] = row['doc_chunk'].replace("<table><tr><td></td><td>", "")
            row['doc_chunk'] = row['doc_chunk'].replace("</td></tr></table>", "")
            row['doc_chunk'] = row['doc_chunk'].replace("<table><tr><td>", "")
            row['subsection_of_wording'] = ''
        if isinstance(row['subsection_of_wording'], type(None)):
            row['subsection_of_wording'] = ''
  
    metadata_2 = response_2[0]
    df_doc_2 = pd.DataFrame(chunk_info_2)
    for i, row in df_doc_2.iterrows():
        if row['section_of_wording'] == 'Header':
            row['doc_chunk'] = row['doc_chunk'].replace("<table><tr><td></td><td>", "")
            row['doc_chunk'] = row['doc_chunk'].replace("</td></tr></table>", "")
            row['doc_chunk'] = row['doc_chunk'].replace("<table><tr><td>", "")
            row['subsection_of_wording'] = ''
        if isinstance(row['subsection_of_wording'], type(None)):
            row['subsection_of_wording'] = ''
              
    df_compare_final, df_compare_reverse = compare(df_doc_1, df_doc_2, prompt_text)
 
    metadata_1, metadata_2 = format_metadata(metadata_1, metadata_2)
    
    compare_output, reverse_compare_output = format_ouput(metadata_1, metadata_2, df_compare_final, df_compare_reverse)
    
    final_output = {f"{metadata_1['docu_id_1']}_{metadata_2['docu_id_2']}": compare_output,
                    f"{metadata_2['docu_id_2']}_{metadata_1['docu_id_1']}": reverse_compare_output}
    
    end = timeit.timeit()
    print(end - start)
    t1 = f"{metadata_1['docu_id_1']}_{metadata_2['docu_id_2']}"
    t2 = f"{metadata_2['docu_id_2']}_{metadata_1['docu_id_1']}"
    overall_score = 0.0
    total_elements = 0
    comparison_score = 0
    for key, value in final_output[t1].items():
        if key == "comparison_results":
            for element in value:
                if element["text_in_section_for_doc_1"]:
                    element["text_in_section_for_doc_1"] = re.sub(r"\\", "", element["text_in_section_for_doc_1"])
                if element["text_in_section_for_doc_2"]:
                    element["text_in_section_for_doc_2"] = re.sub(r"\\", "", element["text_in_section_for_doc_2"])
                if element["section_of_wording"]:
                    element["section_of_wording"] = re.sub(r"\\", "", element["section_of_wording"])
                if element["subsection_of_wording"]:
                    element["subsection_of_wording"] = re.sub(r"\\", "", element["subsection_of_wording"])
                if element["status_of_difference"]:
                    element["status_of_difference"] = re.sub(r"\n", "", element["status_of_difference"])
                    if element["status_of_difference"] == "high difference":
                        element["section_score"] = 1.0
                    elif element["status_of_difference"] == "no difference":
                        element["section_score"] = 0.0
                    elif element["status_of_difference"] == "low difference":
                        element["section_score"] = 0.25
                    elif element["status_of_difference"] == "medium difference":
                        element["section_score"] = 0.5
                if element["section_score"]:
                    overall_score = overall_score + element["section_score"]
                for k, v in element.items():
                    if v == '':
                        element[k] = 'NA'
            total_elements = len(value)
            comparison_score = round((overall_score / total_elements) * 100, 2)
    final_output[t1]["comparison_score"] = comparison_score
    final_output[t1]["total_word_count"] = total_elements
    final_output[t1]["count_of_total_differences"] = overall_score
    overall_score = 0.0
    total_elements = 0
    comparison_score = 0          
    for key, value in final_output[t2].items():
        if key == "comparison_results":
            for element in value:
                if element["text_in_section_for_doc_1"]:
                    element["text_in_section_for_doc_1"] = re.sub(r"\\", "", element["text_in_section_for_doc_1"])
                if element["text_in_section_for_doc_2"]:
                    element["text_in_section_for_doc_2"] = re.sub(r"\\", "", element["text_in_section_for_doc_2"])
                if element["section_of_wording"]:
                    element["section_of_wording"] = re.sub(r"\\", "", element["section_of_wording"])
                if element["subsection_of_wording"]:
                    element["subsection_of_wording"] = re.sub(r"\\", "", element["subsection_of_wording"])
                if element["status_of_difference"]:
                    element["status_of_difference"] = re.sub(r"\n", "", element["status_of_difference"])
                    if element["status_of_difference"] == "high difference":
                        element["section_score"] = 1.0
                    elif element["status_of_difference"] == "no difference":
                        element["section_score"] = 0.0
                    elif element["status_of_difference"] == "low difference":
                        element["section_score"] = 0.25
                    elif element["status_of_difference"] == "medium difference":
                        element["section_score"] = 0.5
                if element["section_score"]:
                    overall_score = overall_score + element["section_score"]
                for k, v in element.items():
                    if v == '':
                        element[k] = 'NA'
            total_elements = len(value)
            comparison_score = round((overall_score / total_elements) * 100, 2)
    final_output[t2]["comparison_score"] = comparison_score
    final_output[t2]["total_word_count"] = total_elements
    final_output[t2]["count_of_total_differences"] = overall_score
    return final_output

def Initiating_comparison(meta_data, config):
    print("2. Inside Initiating_comparison entrypoint")
    docu_id_1 = meta_data.get('docu_id_1')
    docu_id_2 = meta_data.get('docu_id_2')
    product_name = meta_data.get('product_name')
    comparison_id = meta_data.get('comparison_id')
    transaction_id = meta_data.get('transaction_id')
    comparison_table = config.get('comparison_table')
    comparison_mapping_table = config.get('comparison_mapping_table')
    
    try:
        llm_response = generate_comparison(docu_id_1, docu_id_2, product_name, config)
    except Exception as e:
        print(e)
        meta_data["comparison_status"] = "FAILED"
        date_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        meta_data["modified_datetime"] = date_time
        r = json.dumps(meta_data)
        loaded_r = json.loads(r)
        result_json = json.loads(json.dumps(loaded_r), parse_float=Decimal)
        response = put_comp_map(result_json, comparison_table, comparison_mapping_table)
        if response != 200:
            return response

        ## for saving to homepage table
        result_json.pop("transaction_id")
        result_json.pop("doc_1_path")
        result_json.pop("doc_2_path")
        try:
            landing_page_update(result_json)
        except Exception as e:
            logger.info(f'Error while inserting in Landing page table= {str(e)}')
            print("Error while inserting in landing table")

        print("Initiating comparison function: Error while comparing file")
        return {"Message": "Error while comparing file - initiating comparison", 'status_code': 400}, 'FALSE'
    
    llm_result = llm_response[transaction_id]
    date_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    for key, value in meta_data.items():
        llm_result[key] = value
        
    llm_result["modified_datetime"] = date_time
    llm_result["comparison_status"] = "IN REVIEW"
    r = json.dumps(llm_result)
    loaded_r = json.loads(r)
    result_json = json.loads(json.dumps(loaded_r), parse_float=Decimal)
    print("Inside Initiating_comparison: putting the compared result in tables")
    try:
        response = put_comp_map(result_json, comparison_table, comparison_mapping_table)
    except Exception as e:
        print(str(e))
    rep = landing_page_update(llm_result)
    print("Insertion complete.")
    if rep != 200:
        return rep, 'FALSE'
    if response != 200:
        return response, 'FALSE'
    return response, 'TRUE'


if __name__ == '__main__':
    print("inside main entrypoint")
    config_path = os.path.join(default_config_dir, 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    payload_table = config.get('comparison_payload_table')
    try:
        response = scan_table(payload_table)
    except Exception as e:
        raise(e)
    payloads = response
    for element in payloads:
        payload = element['payload']
        meta_data = eval(payload)
        processed_flag = element['processed_flag']
        if processed_flag == 'FALSE':
            response, flag = Initiating_comparison(meta_data, config)
            data = b''
            destination = 'dummy.txt'
            bucket = config.get('notification_bucket')
            save_to_s3(bucket, destination, data)
            push_payload = {'payload': payload, 'processed_flag': flag}
            try:
                connection = get_db_connection()
                cursor = connection.cursor()
                columns = ', '.join(push_payload.keys())
                placeholders = ', '.join(['%s'] * len(push_payload))
                sql = f"INSERT INTO {payload_table} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, list(push_payload.values()))
                connection.commit()
            except Exception as e:
                raise(e)
            finally:
                cursor.close()
                connection.close()

ingestion_main mod

import os
import json
import pathlib
import yaml
import time
import boto3
import pymysql
from data_ingestion_pipeline import connector
from utils import convert_to_json, remove_files, download_s3_folder, get_metadata
from connections import download_from_s3, save_to_s3
from utils import check_extension, download_and_extract_libreoffice, convert_docx_to_pdf, convert_pdf_to_docx, check_file_exist, conversion

default_config_dir = pathlib.Path(__file__).parent
default_data_dir = pathlib.Path(__file__).parent

def get_db_connection():
    return pymysql.connect(
        host=os.environ['RDS_HOST'],
        user=os.environ['RDS_USER'],
        password=os.environ['RDS_PASSWORD'],
        database=os.environ['RDS_DB']
    )

def main(meta_data):
    config_path = os.path.join(default_config_dir, 'config.yaml')
    dir_path = os.path.join(default_data_dir, 'data/input_file')
    out_dir_path = os.path.join(default_data_dir, 'data/output_file')
    batch_dir_path = os.path.join(default_data_dir, 'data/input_batch_files')

    pathlib.Path(dir_path).mkdir(parents=True, exist_ok=True)
    pathlib.Path(batch_dir_path).mkdir(parents=True, exist_ok=True)
    pathlib.Path(out_dir_path).mkdir(parents=True, exist_ok=True)
    remove_files(dir_path)
    remove_files(batch_dir_path)
    value = ''
    file_name = meta_data['filename']
    poped = meta_data.pop('filename')
    product = meta_data['product_name']
    docu_id = file_name.split('.')[0]
    meta_data['docu_id'] = docu_id
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    table_sections = config.get(product)
    mode = config.get('mode')
    bucket = 'hiscox-policywording-prod'
    s3_client = boto3.client('s3', region_name='eu-west-2')
    read_from_dir = dir_path
    if mode == 'single':
        file_to_convert = {
            "Records": [
                {
                    "s3": {"bucket": {"name": "hiscox-policywording-prod"},
                    "object": {"key": f"{product}/{file_name}"}}
                }
            ]
        }
        start_time = time.time()
        print('before conversion')
        # Conversion function for files
        conversion(file_to_convert)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time for conversion: {execution_time:.6f} seconds")
        source_docx = f'{product}/{docu_id}.docx'
        destination_docx = f'{dir_path}/{docu_id}.docx'
        source_pdf = f'{product}/{docu_id}.pdf'
        destination_pdf = f'{dir_path}/{docu_id}.pdf'
        val_docx = download_from_s3(source_docx, destination_docx)
        val_pdf = download_from_s3(source_pdf, destination_pdf)
    else:
        destination = batch_dir_path
        read_from_dir = batch_dir_path
        try:
            download_s3_folder(bucket, product, destination)
        except Exception as e:
            print(str(e))
            value = 'error in reading files from S3'
            return value
    print("before df-connector", read_from_dir)
    df = connector(dir_path=read_from_dir, table_sections=table_sections)
    data = convert_to_json(df)
    print("chunk_info created")
    if mode == 'single':
        chunk_json = data.get(docu_id)
        chunk_info = {'chunk_info': chunk_json}
        chunk_output = meta_data | chunk_info
        file_mapping_output = meta_data
        # Saving the output chunks to the MySQL database
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            columns = ', '.join(chunk_output.keys())
            placeholders = ', '.join(['%s'] * len(chunk_output))
            sql = f"INSERT INTO docu_metadata ({columns}) VALUES ({placeholders})"
            cursor.execute(sql, list(chunk_output.values()))
            connection.commit()
            print("chunk_info inserted into metadata")
            columns = ', '.join(file_mapping_output.keys())
            placeholders = ', '.join(['%s'] * len(file_mapping_output))
            sql = f"INSERT INTO file_mapping ({columns}) VALUES ({placeholders})"
            cursor.execute(sql, list(file_mapping_output.values()))
            connection.commit()
            print("metadata inserted into file_mapping")
            value = 'Success'
        except Exception as e:
            print(str(e))
            value = 'error in pushing data to MySQL'
            return value
        finally:
            cursor.close()
            connection.close()
    elif mode == 'batch':
        remove_files(batch_dir_path)
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            for docu_id, chunk_info in data.items():
                time.sleep(3)
                meta_data_batch = get_metadata(docu_id, product)
                if meta_data_batch.get('Error') is None:
                    chunk_output = meta_data_batch | {'chunk_info': chunk_info}
                    try:
                        columns = ', '.join(chunk_output.keys())
                        placeholders = ', '.join(['%s'] * len(chunk_output))
                        sql = f"INSERT INTO docu_metadata ({columns}) VALUES ({placeholders})"
                        cursor.execute(sql, list(chunk_output.values()))
                        connection.commit()
                    except Exception as e:
                        print(str(e))
                        value = 'error in pushing data to MySQL'
                        return value
                else:
                    continue
        except Exception as e:
            print(str(e))
            value = 'error in pushing data to MySQL'
            return value
        finally:
            cursor.close()
            connection.close()
    else:
        file_path = os.path.join(out_dir_path, f'{product}.csv')
        df.to_csv(file_path, index=None)
        remove_files(batch_dir_path)
    return value

def get_column_values(value):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    try:
        sql = "SELECT * FROM docu_metadata WHERE product_name = %s"
        cursor.execute(sql, (value,))
        response = cursor.fetchall()
    except Exception as e:
        response = {'Error': str(e)}
    finally:
        cursor.close()
        connection.close()
    
    return response

if __name__ == '__main__':
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT * FROM ingestion_payload"
        cursor.execute(sql)
        response = cursor.fetchall()
    except Exception as e:
        print(str(e))
    finally:
        cursor.close()
        connection.close()
    
    payload = response
    for element in payload:
        payload = element['payload']
        meta_data = eval(payload)
        processed_flag = element['processed_flag']
        if processed_flag == 'FALSE':
            try:
                val = main(meta_data)
                data = b''
                destination = 'dummy.txt'
                bucket = 'dummy-notification-prod'
                save_to_s3(bucket, destination, data)
                push_payload = {
                    'product_name': element['product_name'],
                    'doc_type': element['doc_type'],
                    'coverage': element['coverage'],
                    'schemes_bespoke': element['schemes_bespoke'],
                    'filename': element['filename'],
                    'processed_flag': 'TRUE'
                }
                try:
                    connection = get_db_connection()
                    cursor = connection.cursor()
                    columns = ', '.join(push_payload.keys())
                    placeholders = ', '.join(['%s'] * len(push_payload))
                    sql = f"INSERT INTO ingestion_payload ({columns}) VALUES ({placeholders})"
                    cursor.execute(sql, list(push_payload.values()))
                    connection.commit()
                except Exception as e:
                    print(str(e))
                finally:
                    cursor.close()
                    connection.close()
            except Exception as e:
                print(str(e))
                continue

lambda:
comparision detail
import pymysql
import os
import json
from datetime import datetime

comparison_table = os.environ.get('comparison_table')
comparison_mapping_table = os.environ.get('mapping_table')
env_url = os.environ.get('env_url')
s3_bucket = os.environ.get('s3_bucket')

s3 = boto3.client('s3')

def get_transaction_id_from_comparison_id(comparison_id, connection):
    with connection.cursor() as cursor:
        sql = "SELECT transaction_id FROM comp_mapping_bulk WHERE comparison_id = %s"
        cursor.execute(sql, (comparison_id,))
        result = cursor.fetchone()
        if result:
            return result['transaction_id']
        else:
            return None

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': env_url,
        'Access-Control-Allow-Credentials': 'true',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'",
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }

    try:
        connection = pymysql.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            db=os.environ.get('DB_NAME'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except:
        response = {'error': 'DB Connection timeout'}
        return {
            'statusCode': 502,
            'headers': headers,
            'body': json.dumps(response, default=str),
            'isBase64Encoded': False
        }

    query_params = event.get('queryStringParameters')
    comparison_id = int(query_params.get('comparison_id', "0"))
    transaction_id = get_transaction_id_from_comparison_id(comparison_id, connection)

    try:
        if not transaction_id:
            response = {'error': 'Comparison ID not found.'}
            statusCode = 400
        else:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM comparision_output_bulk WHERE transaction_id = %s"
                cursor.execute(sql, (transaction_id,))
                data = cursor.fetchone()
                if data:
                    for key, value in data.items():
                        if key in ['doc_1_path', 'doc_2_path']:
                            data[key] = s3.generate_presigned_url('get_object', Params={'Bucket': s3_bucket, 'Key': value}, ExpiresIn=300)
                    response = {'data': data}
                    statusCode = 200
                else:
                    response = {'error': 'Comparison ID not found.'}
                    statusCode = 400

        return {
            'statusCode': statusCode,
            'headers': headers,
            'body': json.dumps(response, default=str),
            'isBase64Encoded': False
        }

    except Exception as e:
        print(str(e))
        response = {'error': 'Internal Server Error'}
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps(response, default=str),
            'isBase64Encoded': False
        }

filemapping:
import json
import logging
import os
import pymysql

env_url = os.environ.get('env_url')
file_mapping_table = os.environ.get('file_mapping_table')
rds_host = os.environ.get('rds_host')
rds_user = os.environ.get('rds_user')
rds_password = os.environ.get('rds_password')
rds_db = os.environ.get('rds_db')

logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger()

def lambda_handler(event, context):
    logger.info(event)
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': env_url,
        'Access-Control-Allow-Credentials': 'true',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'",
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }
    
    query_params = event.get('queryStringParameters')
    if query_params is None:
        query_params = {}
    product_name = query_params["product_name"]
    words = product_name.split()
    product_name = "_".join(word.lower() for word in words)
    scheme1 = query_params["scheme1"]
    scheme2 = query_params["scheme2"]

    try:
        connection = pymysql.connect(
            host=rds_host,
            user=rds_user,
            password=rds_password,
            database=rds_db
        )
        
        with connection.cursor() as cursor:
            # Query for scheme1
            cursor.execute(f"""
                SELECT docu_id FROM {file_mapping_table}
                WHERE product_name = %s AND doc_type = %s
            """, (product_name, scheme1))
            list1 = [row[0] for row in cursor.fetchall()]

            # Query for scheme2
            cursor.execute(f"""
                SELECT docu_id FROM {file_mapping_table}
                WHERE product_name = %s AND doc_type = %s
            """, (product_name, scheme2))
            list2 = [row[0] for row in cursor.fetchall()]

        my_dict = {scheme1: list1, scheme2: list2}
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(my_dict, default=str),
            'isBase64Encoded': False
        }
    except Exception as e:
        logger.info(f'Error = {str(e)}')
        error_message = str(e)
        if "ResourceNotFoundException" in error_message:
            statusCode = 400
            response = {"error": "No such table found. Please contact the system administrator and try again later."}
        elif "InternalError" in error_message:
            statusCode = 500
            response = {"error": "API is offline, please contact the system administrator and try again later."}
        else:
            statusCode = 503
            response = {"error": "The engine is currently overloaded, please try again later."}
        return {
            'statusCode': statusCode,
            'headers': headers,
            'body': json.dumps(response, default=str),
            'isBase64Encoded': False
        }
    finally:
        connection.close()

initiate comp lambda:
import boto3
import logging
import os
import json
import base64
from time import gmtime, strftime
from botocore.errorfactory import ClientError
from utils import update_table_attribute, generate_comparison_id, put_comp_map, connect_to_table
import psycopg2

comp_table = os.environ.get('comp_table')
mapping_table = os.environ.get('mapping_table')
BUCKET = os.environ.get('bucket')
TABLE = os.environ.get('table')
cluster = os.environ.get('cluster')
sg_group = os.environ.get('sg_group')
subnet = os.environ.get('subnet')
task_definition = os.environ.get('task_definition')
homepage_table = os.environ.get('homepage_table')
env_url = os.environ.get('env_url')
rds_host = os.environ.get('rds_host')
rds_user = os.environ.get('rds_user')
rds_password = os.environ.get('rds_password')
rds_dbname = os.environ.get('rds_dbname')

s3_client = boto3.client('s3')
ecs = boto3.client('ecs')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def save_to_s3(bucket, key, data):
    s3_client.put_object(Bucket=bucket, Key=key, Body=json.dumps(data))
    return f"s3://{bucket}/{key}"

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': env_url,
        'Access-Control-Allow-Credentials': 'true',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'",
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }

    query_params = event.get('querystringparams', {})
    product_name = query_params.get('product_name')
    document_type1 = query_params.get('document_type1')
    document_type2 = query_params.get('document_type2')
    reevaluate = query_params.get('reevaluate')
    agent_name = query_params.get('agent_name')
    doc_id_1 = query_params.get('doc_id_1')
    doc_id_2 = query_params.get('doc_id_2')

    if document_type1:
        document_type1 = "_".join(word.lower() for word in document_type1.split())
    if document_type2:
        document_type2 = "_".join(word.lower() for word in document_type2.split())
    if product_name:
        product_name = "_".join(word.lower() for word in product_name.split())

    if document_type1 == 'bespoke_wording':
        document_type1 = 'bespoke'
    if document_type2 == 'bespoke_wording':
        document_type2 = 'bespoke'

    metadata1 = connect_to_table(doc_id_1, product_name)
    metadata2 = connect_to_table(doc_id_2, product_name)

    document_scheme_1 = metadata1['Items'][0].get('schemes_bespoke', '')
    document_scheme_2 = metadata2['Items'][0].get('schemes_bespoke', '')

    transaction_id = f"{doc_id_1}_{doc_id_2}"
    date_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    result = {
        'transaction_id': transaction_id,
        'coverage': "",
        'doc_1_path': f'{product_name}/{doc_id_1}.pdf',
        'doc_2_path': f'{product_name}/{doc_id_2}.pdf',
        'agent_name': agent_name,
        'modified_datetime': date_time,
        'marked_review': False,
        'sample_attr': 'query_test',
        'docu_id_1': doc_id_1,
        'docu_id_2': doc_id_2,
        'document_1_type': document_type1,
        'document_2_type': document_type2,
        'product_name': product_name,
        'document_scheme_1': document_scheme_1,
        'document_scheme_2': document_scheme_2
    }

    initiate_comp_payload = result.copy()

    try:
        conn = psycopg2.connect(
            host=rds_host,
            user=rds_user,
            password=rds_password,
            dbname=rds_dbname
        )
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"Error connecting to RDS: {str(e)}")
        raise Exception("Failed to connect to RDS")

    try:
        cursor.execute("SELECT * FROM comp_table WHERE transaction_id = %s", (transaction_id,))
        comp_output_response = cursor.fetchone()
    except Exception as e:
        logger.error(f"Error querying RDS: {str(e)}")
        raise Exception("Failed to query RDS")

    if reevaluate:
        comparison_id = comp_output_response[14]  # Assuming comparison_id is the 15th column
        try:
            result['comparison_id'] = comparison_id
            result["comparison_status"] = 'IN QUEUE'
            initiate_comp_payload['comparison_id'] = comparison_id
            initiate_comp_payload['comparison_status'] = 'IN QUEUE'

            result_json = json.loads(json.dumps(result))
            initiate_comp_payload_json = json.loads(json.dumps(initiate_comp_payload))

            response = put_comp_map(result_json, initiate_comp_payload_json, comparison_id, transaction_id)

            logger.info("Inserted into HomePage and Payload Table")
            logger.info('ECS triggered')

            params = {
                'cluster': cluster,
                'count': 1,
                'launchType': 'FARGATE',
                'networkConfiguration': {
                    'awsvpcConfiguration': {
                        'assignPublicIp': 'DISABLED',
                        'securityGroups': [sg_group],
                        'subnets': [subnet]
                    }
                },
                'taskDefinition': task_definition
            }

            ecs.run_task(**params)
            logger.info('Comparison re-started successfully')
            response = {'message': f'Reinitiated comparison for id : {comparison_id}'}
            statusCode = 200
            return {
                'statusCode': statusCode,
                'headers': headers,
                'body': json.dumps(response, default=str),
                'isBase64Encoded': False
            }
        except Exception as e:
            error_message = str(e)
            logger.info(f'Error = {str(e)}')
            if "NoSuchBucket" in error_message:
                statusCode = 400
                return {"error": "Bad request, please contact the system administrator and try again later."}
            elif "InternalError" in error_message:
                statusCode = 500
                return {"error": "API is offline, please contact the system administrator and try again later."}
            else:
                statusCode = 503
                response = {"error": "The engine is currently overloaded, please try again later."}
            return {
                'statusCode': statusCode,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(response, default=str),
                'isBase64Encoded': False
            }

    elif comp_output_response and comp_output_response[8] in ['REVIEWED', 'IN REVIEW', 'IN QUEUE']:  # Assuming comparison_status is the 9th column
        comparison_id = comp_output_response[14]  # Assuming comparison_id is the 15th column
        response = {'message': f'Comparison already present in table with id: {comparison_id}'}
        logger.info(f'Comparison already present in table.')
        statusCode = 300
        return {
            'statusCode': statusCode,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(response, default=str),
            'isBase64Encoded': False
        }

    elif comp_output_response and comp_output_response[8] == 'FAILED':  # Assuming comparison_status is the 9th column
        logger.info('Inside Failed Case')
        comparison_id = comp_output_response[14]  # Assuming comparison_id is the 15th column

        try:
            result['comparison_id'] = comparison_id
            result["comparison_status"] = 'IN QUEUE'
            initiate_comp_payload['comparison_id'] = comparison_id
            initiate_comp_payload['comparison_status'] = 'IN QUEUE'

            result_json = json.loads(json.dumps(result))
            initiate_comp_payload_json = json.loads(json.dumps(initiate_comp_payload))

            response = put_comp_map(result_json, initiate_comp_payload_json, comparison_id, transaction_id)
            logger.info('Inserted into homepage table and payload table')

            params = {
                'cluster': cluster,
                'count': 1,
                'launchType': 'FARGATE',
                'networkConfiguration': {
                    'awsvpcConfiguration': {
                        'assignPublicIp': 'DISABLED',
                        'securityGroups': [sg_group],
                        'subnets': [subnet]
                    }
                },
                'taskDefinition': task_definition
            }
            ecs.run_task(**params)
            logger.info(f'Success')
            response = {'message': f'Reinitiated comparison for id : {comparison_id}'}
            statusCode = 200
            return {
                'statusCode': statusCode,
                'headers': headers,
                'body': json.dumps(response, default=str),
                'isBase64Encoded': False
            }
        except Exception as e:
            error_message = str(e)
            logger.info(f'Error = {str(e)}')
            if "NoSuchBucket" in error_message:
                statusCode = 400
                return {"error": "Bad request, please contact the system administrator and try again later."}
            elif "InternalError" in error_message:
                statusCode = 500
                return {"error": "API is offline, please contact the system administrator and try again later."}
            else:
                statusCode = 503
                response = {"error": "The engine is currently overloaded, please try again later."}
            return {
                'statusCode': statusCode,
                'headers': headers,
                'body': json.dumps(response, default=str),
                'isBase64Encoded': False
            }

    else:
        gen_comp_id = generate_comparison_id(transaction_id)
        if isinstance(gen_comp_id, list) and gen_comp_id[0] == 200:
            comparison_id = gen_comp_id[1]
        else:
            return gen_comp_id

        result['comparison_id'] = comparison_id
        result["comparison_status"] = 'IN QUEUE'
        initiate_comp_payload['comparison_id'] = comparison_id
        initiate_comp_payload['comparison_status'] = 'IN QUEUE'

        result_json = json.loads(json.dumps(result))
        initiate_comp_payload_json = json.loads(json.dumps(initiate_comp_payload))

        response = put_comp_map(result_json, initiate_comp_payload_json, comparison_id, transaction_id)

        params = {
            'cluster': cluster,
            'count': 1,
            'launchType': 'FARGATE',
            'networkConfiguration': {
                'awsvpcConfiguration': {
                    'assignPublicIp': 'DISABLED',
                    'securityGroups': [sg_group],
                    'subnets': [subnet]
                }
            },
            'taskDefinition': task_definition
        }
        ecs.run_task(**params)

        if response == 200:
            response = {'message': f'Comparison Initiated for id : {comparison_id}'}
            logger.info(f'Comparison Initiated for id : {comparison_id}')
            statusCode = 200
            return {
                'statusCode': statusCode,
                'headers': headers,
                'body': json.dumps(response, default=str),
                'isBase64Encoded': False
            }
        else:
            return response

initiate comp utils:
import logging
import boto3
import json
import os
import timeit
import pymysql

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rds_host = os.environ.get('rds_host')
rds_user = os.environ.get('rds_user')
rds_password = os.environ.get('rds_password')
rds_dbname = os.environ.get('rds_dbname')

s3_client = boto3.client('s3')

def connect_to_rds():
    return pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        db=rds_dbname,
        cursorclass=pymysql.cursors.DictCursor
    )

def connect_to_table(docu_id, product_name):
    try:
        connection = connect_to_rds()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM docu_metadata WHERE docu_id = %s AND product_name = %s"
            cursor.execute(sql, (docu_id, product_name))
            val = cursor.fetchall()
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        val = {'Error': f'Error: did not find any data corresponding to docu_id: {docu_id}'}
    finally:
        connection.close()
    return val

def put_comp_map(result, initiate_comp_payload, comparison_id, transaction_id):
    try:
        connection = connect_to_rds()
        with connection.cursor() as cursor:
            sql_payload = """
                INSERT INTO comparison_payload (product_name, agent_name, docu_id_1, docu_id_2, document_1_type, document_2_type, transaction_id, doc_1_path, doc_2_path, marked_review, sample_attr, modified_datetime, document_scheme_1, document_scheme_2, comparison_id, comparison_status, processed_flag)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'FALSE')
            """
            cursor.execute(sql_payload, (
                initiate_comp_payload['product_name'], initiate_comp_payload['agent_name'], initiate_comp_payload['docu_id_1'], initiate_comp_payload['docu_id_2'],
                initiate_comp_payload['document_1_type'], initiate_comp_payload['document_2_type'], transaction_id, initiate_comp_payload['doc_1_path'],
                initiate_comp_payload['doc_2_path'], initiate_comp_payload['marked_review'], initiate_comp_payload['sample_attr'], initiate_comp_payload['modified_datetime'],
                initiate_comp_payload['document_scheme_1'], initiate_comp_payload['document_scheme_2'], comparison_id, initiate_comp_payload['comparison_status']
            ))

            sql_homepage = """
                INSERT INTO homepage_table (document_2_type, agent_name, document_scheme_1, coverage, product_name, document_scheme_2, comparison_status, docu_id_2, modified_datetime, docu_id_1, sample_attr, comparison_id, comparison_score, document_1_type, marked_review)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_homepage, (
                result['document_2_type'], result['agent_name'], result['document_scheme_1'], result['coverage'], result['product_name'], result['document_scheme_2'],
                result['comparison_status'], result['docu_id_2'], result['modified_datetime'], result['docu_id_1'], result['sample_attr'], result['comparison_id'],
                result['comparison_score'], result['document_1_type'], result['marked_review']
            ))

        connection.commit()
    except Exception as e:
        logger.error(f"Error while inserting into tables: {str(e)}")
        raise Exception("Error while inserting into tables")
    finally:
        connection.close()
    return 200

def update_table_attribute(transaction_id, update_expression, update_value, table, retry=2):
    for attempt in range(retry + 1):
        try:
            connection = connect_to_rds()
            with connection.cursor() as cursor:
                sql = f"UPDATE {table} SET {update_expression} WHERE transaction_id = %s"
                cursor.execute(sql, (update_value, transaction_id))
            connection.commit()
            return cursor.rowcount
        except Exception as e:
            if attempt >= retry:
                logger.error(f"Error updating table: {str(e)}")
                raise e
        finally:
            connection.close()

def generate_comparison_id(transaction_id):
    start = timeit.default_timer()
    try:
        connection = connect_to_rds()
        with connection.cursor() as cursor:
            sql = "SELECT MAX(comparison_id) AS max_id FROM homepage_table WHERE sample_attr = 'query_test'"
            cursor.execute(sql)
            result = cursor.fetchone()
            comparison_id = result['max_id'] + 1 if result['max_id'] else 1
    except Exception as e:
        logger.error(f"Error generating comparison ID: {str(e)}")
        raise Exception("Error in creating Comparison Id")
    finally:
        connection.close()
    end = timeit.default_timer()
    logger.info(f"Time taken to generate comparison ID: {end - start}")
    return [200, comparison_id]

landing page:
import pymysql
import concurrent.futures
import csv
from io import StringIO
import pandas as pd
from constants import schemes_mapping
from decimal import Decimal
import os

# Establish MySQL connection
def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        db=os.environ.get('DB_NAME'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_multiple_filter_condition(query_params):
    index_name = os.environ.get('comparison_table_index')
    key_condition = "sample_attr = 'query_test'"
    if query_params:
        if "comparison_id" in query_params:
            key_condition += f" AND comparison_id = '{query_params['comparison_id']}'"
            query_params.pop('comparison_id')
            
    filter_exp = ""
    expression_attrb_value = {}
    
    for key, value in query_params.items():
        if isinstance(value, list):
            if filter_exp:
                filter_exp += " AND "
            filter_exp += f"{key} BETWEEN %({key}_start)s AND %({key}_end)s"
            if type(value[0]) is float:
                value[0] = Decimal(str(value[0]))
            if type(value[1]) is float:
                value[1] = Decimal(str(value[1]))
            expression_attrb_value[f"{key}_start"] = value[0]
            expression_attrb_value[f"{key}_end"] = value[1]
        elif key not in ['docu_id_1','product_name','document_scheme_1', 'agent_name', 'coverage']:
            if filter_exp:
                filter_exp += " AND "
            filter_exp += f"{key} = %({key})s"
            expression_attrb_value[key] = value
        else:
            if filter_exp:
                filter_exp += " AND "
            
            if key not in ['docu_id_1', 'document_scheme_1']:
                filter_exp += f"LOWER({key}) LIKE %({key})s"
                expression_attrb_value[key] = f"%{value.lower()}%"
            elif key == 'docu_id_1':
                filter_exp += "(LOWER(docu_id_1) LIKE %(doc_name)s OR LOWER(docu_id_2) LIKE %(doc_name)s)"
                expression_attrb_value["doc_name"] = f"%{value.lower()}%"
            else:
                filter_exp += "(LOWER(document_scheme_1) LIKE %(scheme_name)s OR LOWER(document_scheme_2) LIKE %(scheme_name)s)"
                expression_attrb_value["scheme_name"] = f"%{value.lower()}%"
    
    filter_condition = {
        'filter_exp': filter_exp,
        'expression_attrb_value': expression_attrb_value
    }
    
    return index_name, key_condition, filter_condition

def get_data_with_multiple_filters(partition_key, index_name, key_condition, filter_condition, table):
    items = []
    projected_expression = "comparison_id, modified_datetime, docu_id_1, docu_id_2, product_name, agent_name, comparison_status, comparison_score, document_1_type, document_2_type, document_scheme_1, document_scheme_2"
    
    query = f"SELECT {projected_expression} FROM {table} WHERE {key_condition} AND {filter_condition['filter_exp']}"
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, filter_condition['expression_attrb_value'])
            items = cursor.fetchall()
    finally:
        connection.close()
    
    return items

def get_export_data_with_multiple_filters(index_name, key_condition, filter_condition, table):
    return get_data_with_multiple_filters(None, index_name, key_condition, filter_condition, table)

def get_total_data_count(index_name, key_condition, filter_condition, table):
    query = f"SELECT COUNT(*) as cnt FROM {table} WHERE {key_condition} AND {filter_condition['filter_exp']}"
    
    connection = get_db_connection()
    cnt = 0
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, filter_condition['expression_attrb_value'])
            result = cursor.fetchone()
            cnt = result['cnt']
    finally:
        connection.close()
    
    return cnt

def get_csv_file(response):
    output = StringIO()
    required_columns_order = ['comparison_id', 'modified_datetime', 'docu_id_1',
                              'document_scheme_1', 'docu_id_2',  'document_scheme_2',
                              'product_name', 'comparison_status', 'comparison_score']
                              
    if response:
        csv_writer = csv.DictWriter(output, fieldnames=required_columns_order, extrasaction='ignore')
        csv_writer.writeheader()
        csv_writer.writerows(response)
        csv_data = output.getvalue()
        df = pd.read_csv(StringIO(csv_data))
        df = df[required_columns_order]
    else:
        df = pd.DataFrame(columns=required_columns_order)
    
    rename_columns = {'comparison_id': 'Comparison Id', 'modified_datetime': 'Date',
                      'docu_id_1': 'Document 1', 'document_scheme_1': 'Scheme 1',
                      'docu_id_2': 'Document 2', 'document_scheme_2': 'Scheme 2',
                      'product_name': 'Product', 'comparison_status': 'Status',
                      'comparison_score': 'Comparison (%)'}
                      
    df['document_scheme_1'] = df['document_scheme_1'].apply(lambda x: schemes_mapping.get(x, x))
    df['document_scheme_2'] = df['document_scheme_2'].apply(lambda x: schemes_mapping.get(x, x))
    df['product_name'] = df['product_name'].fillna('')
    df['product_name'] = df['product_name'].apply(lambda x: x.replace('_', ' ').title())
    df.rename(columns=rename_columns, inplace=True)
    csv_data = df.to_csv(index=False)

    return csv_data

def parallel_query(partition_keys, index_name, key_condition, filter_condition, table):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_partition = {
            executor.submit(get_data_with_multiple_filters, pk, index_name, key_condition, filter_condition, table): pk for pk in partition_keys
        }
        for future in concurrent.futures.as_completed(future_to_partition):
            partition_key = future_to_partition[future]
            try:
                data = future.result()
                results.extend(data)
            except Exception as e:
                print(e)
    return results

def get_sort_value(item, attrb_name, reverse_flag):
    if reverse_flag:
        valid = 1
    else:
        valid = 0
        
    if attrb_name in item:
        value = item[attrb_name]
        
        if isinstance(value, (int, str, float)):
            return (valid, value)
        else:
            return (1-valid, None)
    else:
        if not reverse_flag:
            return (1-valid, 'zzzzz')
        
        return (1-valid, None)

landing page lambda:
import pymysql
import os
from functions import get_multiple_filter_condition, \
                      parallel_query,\
                      get_export_data_with_multiple_filters,\
                      get_total_data_count, get_csv_file, get_sort_value
import json

default_page_size = os.environ.get('default_page_size')
comparison_table = os.environ.get('comparision-output-bulk')
env_url = os.environ.get('env_url')

def lambda_handler(event, context):
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': env_url,
        'Access-Control-Allow-Credentials': 'true',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'",
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }
    
    try:
        connection = pymysql.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            db=os.environ.get('DB_NAME'),
            cursorclass=pymysql.cursors.DictCursor
        )
    except:
        response = {'error': 'DB Connection timeout'}
        return {
            'statusCode': 502,
            'headers': headers,
            'body': json.dumps(response, default=str),
            'isBase64Encoded': False
        }

    query_params = event.get('queryStringParameters')
    if query_params is None:
        query_params = {}
    page_number = int(query_params.pop("page_number", 1))
    page_size = int(query_params.pop("page_size", default_page_size))
    export_data = eval(query_params.pop("export_data", "False"))
    sorting_column = query_params.pop("sort_column", "")
    sorting_order = query_params.pop("sort_order", "asc")
    
    if 'modified_datetime' in query_params:
        query_params['modified_datetime'] = eval(query_params['modified_datetime'])
        
    if 'comparison_score' in query_params:
        query_params['comparison_score'] = eval(query_params['comparison_score'])
    
    if 'comparison_id' in query_params:
        query_params['comparison_id'] = int(query_params['comparison_id'])
    
    try:
        index_name, key_condition, filter_condition = get_multiple_filter_condition(query_params)
        partition_keys = ['comparison_id']
        
        with connection.cursor() as cursor:
            sql_query = f"SELECT * FROM {comparison_table} WHERE {filter_condition}"
            cursor.execute(sql_query)
            data = cursor.fetchall()
        
        if sorting_column:
            reverse_flag = True if sorting_order == 'desc' else False
            replacement_value = float('-inf') if reverse_flag else float('inf')
            if sorting_column not in ['comparison_score', 'comparison_id']:
                data = sorted(data, key=lambda item: get_sort_value(item, sorting_column, reverse_flag), reverse=reverse_flag)
                if sorting_column == 'docu_id_1':
                    data = sorted(data, key=lambda item: get_sort_value(item, 'docu_id_2', reverse_flag), reverse=reverse_flag)
                elif sorting_column == 'document_scheme_1':
                    data = sorted(data, key=lambda item: get_sort_value(item, 'document_scheme_2', reverse_flag), reverse=reverse_flag)
            else:
                data = sorted(data, key=lambda item: item.get(sorting_column, replacement_value), reverse=reverse_flag)
                    
        if export_data:
            csv_data = get_csv_file(data)
            headers['Content-Type'] = "text/csv"
            headers['Content-Disposition'] = "attachment;filename=data.csv"
            return {
                "statusCode": 200,
                "headers": headers,
                "body": csv_data,
                'isBase64Encoded': False
            }
        else:
            count = len(data)
            start_index = (page_number - 1) * page_size
            end_index = start_index + page_size
                    
            data = data[start_index:end_index]
            response = {'count': count, 'data': data}
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response, default=str),
                'isBase64Encoded': False
            }
            
    except Exception as e:
        print(str(e))
        response = {'error': 'Internal Server Error'}
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps(response, default=str),
            'isBase64Encoded': False
        }
    finally:
        connection.close()

unique prod lambda:
import json
import logging
import os
import pymysql

env_url = os.environ.get('env_url')
file_mapping_table = os.environ.get('file_mapping_table')
mysql_host = os.environ.get('mysql_host')
mysql_user = os.environ.get('mysql_user')
mysql_password = os.environ.get('mysql_password')
mysql_database = os.environ.get('mysql_database')

logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger()

def get_unique_items(cursor, table, attrb_name):
    query = f"SELECT DISTINCT {attrb_name} FROM {table} WHERE {attrb_name} IS NOT NULL"
    cursor.execute(query)
    result = cursor.fetchall()
    unique_items = [item[0] for item in result]
    return unique_items

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': env_url,
        'Access-Control-Allow-Credentials': 'true',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'",
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }
    
    try:
        connection = pymysql.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        cursor = connection.cursor()
    except pymysql.MySQLError as e:
        logger.error(f"Error connecting to MySQL: {e}")
        response = {'error': 'DB Connection timeout'}
        return {
            'statusCode': 502,
            'headers': headers,
            'body': json.dumps(response, default=str),
            'isBase64Encoded': False
        }
    
    unique_product = get_unique_items(cursor, file_mapping_table, 'product_name')
    unique_schemas = get_unique_items(cursor, file_mapping_table, 'schemes_bespoke')
    unique_schemas.append("other_scheme")
    
    response = {
        'product': unique_product,
        'schemas': unique_schemas
    }
    
    cursor.close()
    connection.close()
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(response, default=str),
        'isBase64Encoded': False
    }
update review function:
import pymysql
from datetime import datetime

def get_transaction_id_from_comparison_id(comparison_id, connection):
    with connection.cursor() as cursor:
        sql = "SELECT transaction_id FROM comp_mapping_bulk WHERE comparison_id = %s"
        cursor.execute(sql, (comparison_id,))
        result = cursor.fetchone()
        if result:
            return result['transaction_id']
        else:
            return None

def validate_comparison_id(comparison_id, connection):
    with connection.cursor() as cursor:
        sql = "SELECT COUNT(*) as cnt FROM comp_mapping_bulk WHERE comparison_id = %s"
        cursor.execute(sql, (comparison_id,))
        result = cursor.fetchone()
        return result['cnt']

def update_table_attribute(transaction_id, comparison_id, update_expression, update_value, homepage_table, connection, flag, retry=2):
    for attempt in range(retry + 1):
        try:
            with connection.cursor() as cursor:
                # Update the main table
                sql = f"UPDATE comparision_output_bulk SET {update_expression} WHERE transaction_id = %s"
                cursor.execute(sql, (transaction_id,))
                
                if flag:
                    # Update the homepage table
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    sql = """
                        UPDATE homepage_table 
                        SET modified_datetime = %s, comparison_status = %s 
                        WHERE comparison_id = %s
                    """
                    cursor.execute(sql, (current_time, "REVIEWED", comparison_id))
                    flag = False
                
                connection.commit()
                return cursor.rowcount
        except Exception as e:
            connection.rollback()
            if attempt >= retry:
                raise e

update review lambda:
import json
import pymysql
import os
from datetime import datetime
from functions import validate_comparison_id, update_table_attribute, get_transaction_id_from_comparison_id

comparison_table = os.environ.get('comparison_table')
homepageTable = os.environ.get('homepage_table')
comparison_mapping_table = os.environ.get('mapping_table')
env_url = os.environ.get('env_url')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': env_url,
        'Access-Control-Allow-Credentials': 'true',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'",
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }

    try:
        connection = pymysql.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            db=os.environ.get('DB_NAME'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except:
        response = {'error': 'DB Connection timeout'}
        return {
            'statusCode': 502,
            'headers': headers,
            'body': json.dumps(response, default=str),
            'isBase64Encoded': False
        }

    payload = json.loads(event['body'])
    comparison_id = int(payload.get('comparison_id', 0))

    if 'comparison_id' in payload:
        payload['comparison_id'] = comparison_id

    transaction_id = get_transaction_id_from_comparison_id(comparison_id, connection)

    query_params = event['queryStringParameters']
    if query_params:
        action_type = query_params.get('action_type', 'draft')

    try:
        if not transaction_id:
            response = {'error': 'Comparison ID Not Found'}
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps(response, default=str),
                'isBase64Encoded': False
            }
        flag = False
        if action_type == 'draft':
            if payload['comparison_status'] == 'REVIEWED':
                flag = True
            update_expression = 'modified_datetime = %s, '
            update_value = [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]

            for key, value in payload.items():
                if key not in ['modified_datetime', 'doc_1_path', 'doc_2_path', 'transaction_id', 'status', 'comparison_score', 'comparison_id']:
                    update_expression += f'{key} = %s, '
                    update_value.append(value)

            update_expression = update_expression[:-2]
            update_value.append(transaction_id)
            update_response = update_table_attribute(transaction_id, comparison_id, update_expression, update_value, homepageTable, connection, flag)

            response = {'data': 'Updated Successfully'}
        elif action_type == 'marked_review':
            update_expression = 'modified_datetime = %s, marked_review = %s'
            update_value = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), True]
            update_response = update_table_attribute(transaction_id, comparison_id, update_expression, update_value, homepageTable, connection, flag)
            response = {'data': 'Updated Successfully'}
        else:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM comparision_output_bulk WHERE transaction_id = %s"
                cursor.execute(sql, (transaction_id,))
                data = cursor.fetchone()
                response = {'data': data}
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response, default=str),
            'isBase64Encoded': False
        }

    except Exception as e:
        print(str(e))
        response = {'error': 'Internal Server Error'}
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps(response, default=str),
            'isBase64Encoded': False
        }
upload lambda:
import pymysql
import os
import json
import logging
import base64
from time import gmtime, strftime
import boto3

# Environment variables
TABLE = os.environ.get('table_name')
TABLE_PAYLOAD = os.environ.get('table_name_payload')
BUCKET = os.environ.get('bucket')
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')
cluster = os.environ.get('cluster')
subnet = os.environ.get('subnet')
sg_group = os.environ.get('sg_group')
task_definition = os.environ.get('task_definition')
env_url = os.environ.get('env_url')

# Initialize clients
s3 = boto3.client('s3')
ecs = boto3.client('ecs')

# Logging setup
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger()

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': env_url,
        'Access-Control-Allow-Credentials': 'true',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'",
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }

    logger.info(event)
    if 'body' in event:
        content = event['body']
        decoded_content = base64.b64decode(content)
    else:
        decoded_content = None

    query_params = event.get('queryStringParameters', {})

    insert_payload = {}

    product_name = query_params.get('product_name')
    filename = query_params.get('filename')
    document_type = query_params.get('document_type')
    coverage = query_params.get('coverage')
    schemes_bespoke = query_params.get('schemes_bespoke')
    replace = query_params.get('replace')

    document_type = "_".join(word.lower() for word in document_type.split())
    product_name = "_".join(word.lower() for word in product_name.split())

    filename, extension = filename.split('.')
    filename = filename + '.' + (extension.lower())
    logger.info(f'filename : {filename}')

    if coverage:
        coverage = "_".join(word.lower() for word in coverage.split())
        product_name = product_name + "_" + coverage
        logger.info(f'{coverage}')
    else:
        coverage = ""

    if schemes_bespoke:
        schemes_bespoke = str(schemes_bespoke)
    else:
        schemes_bespoke = ""

    upload_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    insert_payload.update({
        'product_name': product_name,
        'doc_type': document_type,
        'coverage': coverage,
        'schemes_bespoke': schemes_bespoke,
        'filename': filename
    })

    insert_payload = str(insert_payload)

    logger.info(f'{product_name}')
    logger.info(f'{document_type}')

    parts = filename.split('.')
    filetype = parts[-1]
    document_id = filename[:-len(filetype) - 1]

    if filetype not in ['pdf', 'docx']:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({"message": "Invalid file type. Kindly upload .pdf or .docx files."}),
            'isBase64Encoded': False
        }

    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        logger.error(f'DB Connection error: {str(e)}')
        return {
            'statusCode': 502,
            'headers': headers,
            'body': json.dumps({'error': 'DB Connection timeout'}),
            'isBase64Encoded': False
        }

    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM documeta_data WHERE docu_id = %s AND product_name = %s"
            cursor.execute(sql, (document_id, product_name))
            db_response = cursor.fetchone()

            if not db_response or replace == 'True':
                s3_key = f"{product_name}/{filename}"
                s3.put_object(Bucket=BUCKET, Key=s3_key, Body=decoded_content)
                logger.info(f'Object inserted into BUCKET')

                sql = """
                    INSERT INTO ingestion_payload (product_name, doc_type, coverage, schemes_bespoke, filename)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (product_name, document_type, coverage, schemes_bespoke, filename))
                connection.commit()

                sql = """
                    INSERT INTO documeta_data (docu_id, product_name, schemes_bespoke, coverage, doc_type)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (document_id, product_name, schemes_bespoke, coverage, document_type))
                connection.commit()

                logger.info(f'Updated into metadata')

                params = {
                    'cluster': cluster,
                    'count': 1,
                    'launchType': 'FARGATE',
                    'networkConfiguration': {
                        'awsvpcConfiguration': {
                            'assignPublicIp': 'DISABLED',
                            'securityGroups': [sg_group],
                            'subnets': [subnet]
                        }
                    },
                    'taskDefinition': task_definition
                }

                ecs.run_task(**params)
                logger.info(f'Success')
                response = {'message': 'Document uploaded successfully and is being processed. Please check your email for completion notification.'}
                statusCode = 200
            else:
                response = {"message": "This document already exists in the database."}
                statusCode = 300

            return {
                'statusCode': statusCode,
                'headers': headers,
                'body': json.dumps(response, default=str),
                'isBase64Encoded': False
            }

    except Exception as e:
        error_message = str(e)
        logger.error(f'Error: {error_message}')
        if "NoSuchBucket" in error_message:
            statusCode = 400
            response = {"error": "Bad request, please contact the system administrator and try again later."}
        elif "InternalError" in error_message:
            statusCode = 500
            response = {"error": "API is offline, please contact the system administrator and try again later."}
        else:
            statusCode = 503
            response = {"error": "The engine is currently overloaded, please try again later."}

        return {
            'statusCode': statusCode,
            'headers': headers,
            'body': json.dumps(response, default=str),
            'isBase64Encoded': False
        }
