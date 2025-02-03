from minio import Minio
from minio.error import S3Error
import math
import requests
from requests.auth import HTTPBasicAuth
import json
import zipfile
import time
import os

def get_token(text):
    browser=['token":"','","file_stage_in']
    pos=[]
    for n in browser:
        k =text.find(n)
        if k!=-1:
            pos.append(k)
        else:
            break
    if k==-1:
        print('Error in connection')
        return None
    else:
        return text[pos[0]+8:pos[1]]

def get_cpuService(text):
    browser=['cpu":"','","total_memory']
    pos=[]
    for n in browser:
        k=text.find(n)
        if k!=-1:
            pos.append(k)
        else:
            break
    if k==-1:
        print('Error in connection')
        return None
    else:
        return 1000*float(text[pos[0]+6:pos[1]])

def get_memoryService(text):
    browser=['memory":"','Gi']
    pos=[]
    for n in browser:
        k=text.find(n)
        if k!=-1:
            pos.append(k)
        else:
            break
    if k==-1:
        print('Error in connection')
        return None
    else:
        return (float(text[pos[0]+9:pos[1]]))

def connect_to_minio(config):
    MinIO_url = config['url']
    MinIO_access_key = config['access_key']
    MinIO_secret_key = config['secret_key']
    #print(f"Connecting to MinIO at {url_minio} with access key {access_key}")
    return MinIO_url,MinIO_access_key,MinIO_secret_key 

def use_bucket(config):
    bucket_name = config['name']
    folder_prefix = config['folder_prefix']
    #print(f"Using bucket {bucket_name} with folder prefix {folder_prefix}")
    return bucket_name, folder_prefix

def setup_output(config):
    output_file = config['file']
    return output_file

def use_service(config):
    service_name = config['name']
    return service_name

def connect_to_oscar_cluster(config):
    token_cluster=''
    oscar_cluster= config['url']
    if 'username' in config_data.get('oscar_cluster', {}).get('auth_basic', {}):
        username = config['auth_basic']['username']
    if 'password' in config_data.get('oscar_cluster', {}).get('auth_basic', {}):
        password = config['auth_basic']['password']
    if username !="" and password != "":
        basic= True 
    else:
        if 'token' in config_data.get('oscar_cluster', {}).get('auth_token', {}):
            token_cluster = config['auth_token']['token']
            if token_cluster !='':
                basic=False
             
    return oscar_cluster,username,password,token_cluster,basic
def use_directory(config):
    directory=config['local'].get('folder')
    return directory

def list_directory(directory_path, output_file):
    try:

        files = os.listdir(directory_path)

        images = [file for file in files if file.lower().endswith('.jpg')]

        print(f"Found {len(images)} images in the directory '{directory_path}'.")

        with open(output_file, 'w') as file:
            file.write('\n'.join(images))
        
        print(f"The names of the images have been saved to '{output_file}'.")
    except Exception as e:
        print(f"Error: {e}")
    return len(images), images

with open('config-walton-direct.json', 'r') as config_file:
    config_data = json.load(config_file)


MinIO_url,MinIO_access_key,MinIO_secret_key = connect_to_minio(config_data['MinIO'])
bucket_name, folder_prefix = use_bucket(config_data['bucket'])
output_file=setup_output(config_data['output'])
service_name=use_service(config_data['service'])
oscar_cluster, username, password,token_cluster, basic = connect_to_oscar_cluster(config_data['oscar_cluster'])

if basic:
    headers = {    
    'Authorization': "Bearer " + token_service,
    'Content-Type': 'application/json',
}
else:
    headers = {
    'Authorization': "Bearer " + token_cluster,
    'Content-Type': 'application/json',
    }

if not oscar_cluster.startswith("https://"):
    url_invoke = "https://" + oscar_cluster + "/job/" + service_name
else:
    url_invoke = oscar_cluster + "/job/" + service_name
  
name_zip="test.zip"    


print(url_invoke)

data = {
        "zip": name_zip
        
    }
print(data)

try:
    response = requests.post(url_invoke, headers=headers, json=data,verify=True)
    print(response.text)
    print(response.status_code)
    if response.status_code == 200 or response.status_code == 201 :
        print("Services OK")
    else:
        print(response.text)
except Exception as ex:
        print("Error running service: ", ex)
        print(response.text)

