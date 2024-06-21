from minio import Minio
from minio.error import S3Error
import math
import requests
from requests.auth import HTTPBasicAuth

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


# Configure the MinIO client
client = Minio(
    "minio.eloquent-chaum4.im.grycap.net",  # MinIO server
    access_key="",  
    secret_key="",  
    secure=True  
)

# Bucket name
bucket_name = "fishdetector"
folder_prefix = "input/"

# Name of the file where the object names will be saved
output_file = "index.txt"

output_path = "input/index.txt"

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
    #print(num_imag) 

    # Open the file in write mode
    #print(f"Names of the objects saved in {output_file}")
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
url_status = ""


# Authentication credentials
username = ""
password = "" 

cpu_Alloc=0
memory_Alloc=0

# Make the GET request with basic authentication
response = requests.get(url_status, auth=HTTPBasicAuth(username, password))

"""
# Make GET request with token authentication
token_cluster=''
headers = {
    'Authorization': "Bearer "+token_cluster
}
response = requests.get(url_status, headers=headers)
"""

# Check the status of the response
if response.status_code == 200:
      
    # Convert the response to JSON
    try:
        data = response.json()
        print(data)
        
        # Verify that the response is an array of objects
        if isinstance(data, list):
            nodos=len(data)
            # Iterate over each object in the array
            if nodos > 1:
                # Iterate over each object in the array, except the front node
                for obj in data[1:]:
                    # Calculate the available CPU and memory (sum of each node)
                    cpu_Alloc+=int(obj['cpuCapacity']) - int(obj['cpuUsage'])
                    memory_Alloc+=int(obj['memoryCapacity']) - int(obj['memoryUsage'])
        else:
            print("The response is not a JSON array of objects.")
    
    except ValueError as e:
        print("Error converting the response to JSON:", e)
else:
    print(f"Request error: {response.status_code}")
    print("Error message:")
    print(response.text)
memory_Alloc=memory_Alloc/1000000000  # convert to GB


# Search for the CPU needed to run the service defined in its creation (FDL)

url_service = ""

response = requests.get(url_service, auth=HTTPBasicAuth(username, password))

"""
# GET request via token
response = requests.get(url_service, headers=headers)
"""

if response.status_code == 200:
    resp=response.text
    # Calculate CPU, Memory and token of the service
    cpu_service= get_cpuService(resp)
    memory_service=get_memoryService(resp)
    token_service=get_token(resp)
else:
    print(f"Request error: {response.status_code}")
    print("Error message:")
    print(response.text)

# Calculate the number of service invocations according to the available CPU in the cluster and the service's CPU
cpu_invoke=math.floor(cpu_Alloc/cpu_service)
memory_invoke=math.floor(memory_Alloc/(memory_service))

# Min value between invocations by CPU and by memory
cant_invoke=min(cpu_invoke,memory_invoke)
print(cant_invoke)

# Calculate the number of images per invocation

resto=(num_imag)%cant_invoke
img_invoke=int(num_imag/cant_invoke)
print(f"Images per invocation: {img_invoke}")


headers_invoke = {    
    'Authorization': "Bearer " + token_service,
    'Content-Type': 'application/json',
}

url_invoke=''

# Range of images to process (start-end)
for i in range(cant_invoke):
    # Range of images
    start=i*img_invoke+1
    end=(i+1)*img_invoke

    if i==cant_invoke-1:
        fin=fin+resto
    data={
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
    print(f"Invocation {i+1} to the service")
