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

directory_path = use_directory(config_data)
output_txt = directory_path+"/index.txt"          
num_imag,object_list=list_directory(directory_path, output_txt)

service_info = "https://" + oscar_cluster + "/system/services/" + service_name
print(service_info)
 
if basic:
    response = requests.get(service_info, auth=HTTPBasicAuth(username, password),verify=True)
else:
    headers = {
    'Authorization': "Bearer " + token_cluster
    }
    response = requests.get(service_info, headers=headers,verify=True)
 
if response.status_code == 200:
    resp = response.text
    print(resp)
    cpu_service = get_cpuService(resp)
    memory_service = get_memoryService(resp)
    print(cpu_service)
    print(memory_service)
    token_service = get_token(resp)
else:
    print(f"Request error: {response.status_code}")
    print("Error message:")
    print(response.text)
cpu_Alloc=0
cpu_invoke=0
memory_Alloc=0
memory_invoke=0

if not oscar_cluster.startswith("https://"):
    url_status = "https://" + oscar_cluster + "/system/status"
else:
    url_status = oscar_cluster + "/system/status"

try:
    if basic:
        response = requests.get(url_status, auth=HTTPBasicAuth(username, password), verify=False)
    else:
        headers = {
            'Authorization': "Bearer " + token_cluster
        }
        response = requests.get(url_status, headers=headers, verify=True)

    if response.status_code == 200:
        try:
            data = response.json()
            if isinstance(data, dict):
                nodos = len(data['detail'])
                data = data['detail']
                if nodos >= 1:
                    for obj in data:
                        cpu_Alloc=(int(obj['cpuCapacity']))*0.8 - int(obj['cpuUsage'])
                        cpu_invoke += int((cpu_Alloc/cpu_service))
                        memory_Alloc=(int(obj['memoryCapacity'])*0.8) - int(obj['memoryUsage'])
                        memory_invoke += int((memory_Alloc/(1000000000*memory_service)))
            else:
                print("The response is not a JSON array of objects.")
        
        except ValueError as e:
            print("Error converting the response to JSON:", e)
    else:
        print(f"Request error: {response.status_code}")
        print("Error message:")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"Connection error: {e}")

print(f"CPU invocations: {cpu_invoke}")
print(f"Memory invocations: {memory_invoke}")


if not oscar_cluster.startswith("https://"):
    service_info = "https://" + oscar_cluster + "/system/services/" + service_name
else:
    service_info = oscar_cluster + "/system/services/" + service_name
    

if basic:
    response = requests.get(service_info, auth=HTTPBasicAuth(username, password),verify=True)
else:
    response = requests.get(service_info, headers=headers,verify=True)


if response.status_code == 200:
    resp = response.text

    cpu_service = get_cpuService(resp)
    memory_service = get_memoryService(resp)  # take 80% of the memory so as not to completely saturate the cluster
    token_service = get_token(resp)
else:
    print(f"Request error: {response.status_code}")
    print("Error message:")
    print(response.text)

cant_invoke = min(cpu_invoke, memory_invoke)
print(f"Invocations: {cant_invoke}")

#num_imag=108
resto = (num_imag) % cant_invoke
img_invoke = int(num_imag / cant_invoke)
print(f"Images per invocation: {img_invoke}")

output_bucket = bucket_name

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

    

client = Minio(
    MinIO_url,
    access_key=MinIO_access_key,  
    secret_key=MinIO_secret_key,  
    secure=True  
    )

if not oscar_cluster.startswith("https://"):
    url_invoke = "https://" + oscar_cluster + "/job/" + service_name
else:
    url_invoke = oscar_cluster + "/job/" + service_name

end=0
start=0

t1=time.time()
for i in range(cant_invoke):
    
    t=time.time()
    start = end+1
    end = end+ img_invoke
    if i < resto:
        end = end+1
    name_zip=str(i+1)+".zip"

    data = {
        "zip": name_zip
        
    }
    print(data)

    list=object_list[int(start)-1:int(end)]
    zip_file_name = str(i+1)+".zip"
    output_path = "zip/" + name_zip
    print(name_zip)
    local_files=[]
    
    try:
       
        with zipfile.ZipFile(zip_file_name, 'w') as file_zip:

            for file in list:

                if file.lower().endswith('.jpg'):
                    full_path = os.path.join(directory_path, file)
                    

                    file_zip.write(full_path, file)
                    
        print(f"ZIP file successfully created: {zip_file_name}")

        client.fput_object(
            output_bucket, 
            output_path,
            zip_file_name
          )

        print(f"{name_zip} successfully uploaded to the bucket {output_bucket}")
    finally:
      
        for file in local_files:
            if os.path.exists(file):
                os.remove(file)
        if os.path.exists(zip_file_name):
                os.remove(zip_file_name)
    
    print(f"Start value: {start}")
    print(f"End value: {end}")
    print(f"Invocation {i + 1} to the service")
    print(url_invoke)
    
    time.sleep(5)
   
    output_path = folder_prefix + output_file
    
   
    try:
        response = requests.post(url_invoke, headers=headers, json=data,verify=True)
        if response.status_code == 200 or response.status_code == 201:
            print("Services OK")
        else:
            print(response.text)
    except Exception as ex:
        print("Error running service: ", ex)
        print(response.text)

    t2=time.time()
    print(f"Total time of service launch: {round(t2-t1,2)} seconds")
    
t=time.time()
print(f"Total time of the execution process: {round(t-t1,2)} seconds")    

   


