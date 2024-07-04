from minio import Minio
from minio.error import S3Error
import math
import requests
from requests.auth import HTTPBasicAuth
import json

# Definition of necessary functions

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

# Read the JSON configuration file
with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)

# Take configuration values
MinIO_url,MinIO_access_key,MinIO_secret_key = connect_to_minio(config_data['MinIO'])
bucket_name, folder_prefix = use_bucket(config_data['bucket'])
output_file=setup_output(config_data['output'])
service_name=use_service(config_data['service'])
oscar_cluster, username, password,token_cluster, basic = connect_to_oscar_cluster(config_data['oscar_cluster'])

# Configure the MinIO client
client = Minio(
    MinIO_url,  # MinIO server
    access_key=MinIO_access_key,  
    secret_key=MinIO_secret_key,  
    secure=True  
)

output_path = folder_prefix + output_file

try:
    # List objects in the bucket
    objects = client.list_objects(bucket_name,  prefix=folder_prefix)
    
    # Count the number of objects
    object_list = []
    for obj in objects:
         if obj.object_name.endswith('.jpg'):
            #print(obj.object_name)
            object_list.append(obj.object_name)

    num_imag = len(object_list)
  
    # Open the file in write mode
    with open(output_file, 'w') as file:
        for obj in object_list:
            #print(f"{obj}\n")
            file.write(f"{obj}\n")

    # Upload the text file to the bucket
    client.fput_object(
        bucket_name, 
        output_path,
        output_file,
        content_type="text/plain"
    )

    print(f"File {output_file} uploaded to {bucket_name}")

except S3Error as exc:
    print("Error occurred: ", exc)
    
# URL to which you want to make the request
cpu_Alloc=0
memory_Alloc=0

url_status = "https://" + oscar_cluster + "/system/status"

# Make the GET request with basic authentication or token authentication
if basic:
    response = requests.get(url_status, auth=HTTPBasicAuth(username, password))
else:
    headers = {
    'Authorization': "Bearer " + token_cluster
    }
    response = requests.get(url_status, headers=headers)

# Check the status of the response
if response.status_code == 200:
    # Convert the response to JSON
    try:
        data = response.json()
        print(data)
        
        # Verify that the response is an array of objects
        if isinstance(data, list):
            nodos = len(data)
            # Iterate over each object in the array
            if nodos > 1:
                # Iterate over each object in the array, except the front node
                for obj in data[1:]:
                    # Calculate the available CPU and memory (sum of each node)
                    cpu_Alloc += int(obj['cpuCapacity']) - int(obj['cpuUsage'])
                    memory_Alloc += int(obj['memoryCapacity']) - int(obj['memoryUsage'])
        else:
            print("The response is not a JSON array of objects.")
    
    except ValueError as e:
        print("Error converting the response to JSON:", e)
else:
    print(f"Request error: {response.status_code}")
    print("Error message:")
    print(response.text)

cpu_Alloc = cpu_Alloc * 0.8  # take 80% of the CPU so as not to completely saturate the cluster
memory_Alloc = (memory_Alloc / 1000000000) * 0.8  # take 80% of the Memory so as not to completely saturate the cluster and convert to GB

# Search for the CPU needed to run the service defined in its creation (FDL)
service_info = "https://" + oscar_cluster + "/system/services/" + service_name

# GET request via basic authentication or token
if basic:
    response = requests.get(service_info, auth=HTTPBasicAuth(username, password))
else:
    response = requests.get(service_info, headers=headers)

# Check the status of the response
if response.status_code == 200:
    resp = response.text
    # Calculate CPU, Memory and token of the service
    cpu_service = get_cpuService(resp)
    memory_service = get_memoryService(resp) * 0.8  # take 80% of the memory so as not to completely saturate the cluster
    token_service = get_token(resp)
else:
    print(f"Request error: {response.status_code}")
    print("Error message:")
    print(response.text)

# Calculate the number of service invocations according to the available CPU in the cluster and the service's CPU
cpu_invoke = math.floor(cpu_Alloc / cpu_service)
memory_invoke = math.floor(memory_Alloc / memory_service)

# Min value between invocations by CPU and by memory
cant_invoke = min(cpu_invoke, memory_invoke)
print(cant_invoke)

# Calculate the number of images per invocation
resto = (num_imag) % cant_invoke
img_invoke = int(num_imag / cant_invoke)
print(f"Images per invocation: {img_invoke}")

headers_invoke = {    
    'Authorization': "Bearer " + token_service,
    'Content-Type': 'application/json',
}

url_invoke = "https://" + oscar_cluster + "/job/" + service_name

# Range of images to process (start-end)
for i in range(cant_invoke):
    # Range of images
    start = i * img_invoke + 1
    end = (i + 1) * img_invoke

    if i == cant_invoke - 1:
        end = end + resto

    data = {
        "start": start,
        "end": end
    }
    try:
        response = requests.post(url_invoke, headers=headers_invoke, json=data)
        if response.status_code == 200:
            print("Services OK")
        else:
            print(response.status_code)
    except Exception as ex:
        print("Error running service: ", ex)
        print(response.text)

    print(f"Start value: {start}")
    print(f"End value: {end}")
    print(f"Invocation {i + 1} to the service")
