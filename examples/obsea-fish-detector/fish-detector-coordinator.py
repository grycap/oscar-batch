# Librerias necesarias

from minio import Minio
from minio.error import S3Error
import math
import requests
from requests.auth import HTTPBasicAuth

#Definición de funciones necesarias

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
        print('Error in conection')
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
        print('Error in conection')
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
        print('Error in conection')
        return None
    else:
        return (float(text[pos[0]+9:pos[1]]))


# Configura el cliente MinIO
client = Minio(
    "minio.eloquent-chaum4.im.grycap.net",  # servidor MinIO
    access_key="minio",  
    secret_key="minio123",  
    secure=True  
)

# Nombre del bucket
bucket_name = "fishdetector"
folder_prefix = "input/"

# Nombre del archivo donde se guardarán los nombres de los objetos
output_file = "index.txt"

output_path = "input/index.txt"

try:
    # Lista los objetos en el bucket
    objects = client.list_objects(bucket_name,  prefix=folder_prefix)
    
    # Contar la cantidad de objetos
    object_list = []
    for obj in objects:
         if obj.object_name.endswith('.jpg'):
            #print(obj.object_name)
            object_list.append(obj.object_name)

    num_imag = len(object_list)
    #print(num_imag) 

    # Abre el archivo en modo escritura
    #print(f"Nombres de los objetos guardados en {output_file}")
    with open(output_file, 'w') as file:

        for obj in object_list:
            #print(f"{obj}\n")
            file.write(f"{obj}\n")

    # Subir el archivo de texto al bucket
    client.fput_object(
        bucket_name, 
        output_path,
        output_file,
        content_type="text/plain"
    )

    print(f"Archivo {output_file} subido a {bucket_name}")

except S3Error as exc:
    print("Error ocurrido: ", exc)


# URL a la que quieres hacer la petición
url_status = "https://eloquent-chaum4.im.grycap.net/system/status"


# Credenciales de autenticación
username = "oscar"
password = "oscar123" 

cpu_Alloc=0
memory_Alloc=0

# Hacer la petición GET con autenticación básica
response = requests.get(url_status, auth=HTTPBasicAuth(username, password))

"""
# Hacer petición GET con autentificación con token
token_cluster=''
headers = {
    'Authorization': "Bearer "+token_cluster
}
response = requests.get(url_status, headers=headers)
"""


# Comprobar el estado de la respuesta
if response.status_code == 200:
      
    # Convertir la respuesta a JSON
    try:
        data = response.json()
        print(data)
        
        # Verificar que la respuesta sea un array de objetos
        if isinstance(data, list):
            nodos=len(data)
            # Iterar sobre cada objeto en el array
            if nodos > 1:
                # Iterar sobre cada objeto en el array, excepto el nodo front
                for obj in data[1:]:
                    # Calcular la cpu y memoria disponible (sumatoria de cada nodo)
                    cpu_Alloc+=int(obj['cpuCapacity']) - int(obj['cpuUsage'])
                    memory_Alloc+=int(obj['memoryCapacity']) - int(obj['memoryUsage'])
        else:
            print("La respuesta no es un array de objetos JSON.")
    
    except ValueError as e:
        print("Error al convertir la respuesta a JSON:", e)
else:
    print(f"Error en la petición: {response.status_code}")
    print("Mensaje de error:")
    print(response.text)
memory_Alloc=memory_Alloc/1000000000  # convertir a GB


# buscar la cpu necesaria para ejecutar el servicio definida en su creacion (FDL)

url_service = "https://eloquent-chaum4.im.grycap.net/system/services/fish-detector"

response = requests.get(urlservice, auth=HTTPBasicAuth(username, password))

"""
#Petición GET via token
response = requests.get(url_service, headers=headers)
"""

if response.status_code == 200:
    resp=response.text
    # Calcular CPU, Memoria y token  del servicio
    cpu_service= get_cpuService(resp)
    memory_service=get_memoryService(resp)
    token_service=get_token(resp)
else:
    print(f"Error en la petición: {response.status_code}")
    print("Mensaje de error:")
    print(response.text)

# Calcular la cantidad de invocaciones al servicio según la cpu disponible en el cluster y la del servicio
cpu_invoke=math.floor(cpu_Alloc/cpu_service)
memory_invoke=math.floor(memory_Alloc/(memory_service))

# min valor entre las invocaciones por cpu y por memoria
cant_invoke=min(cpu_invoke,memory_invoke)
print(cant_invoke)

# Calcular cantidad de imagenes por invocaciones

resto=(num_imag)%cant_invoke
img_invoke=int(num_imag/cant_invoke)
print(f"Imagenes por invocacion: {img_invoke}")


headers_invoke = {    
    'Authorization': "Bearer " + token_service,
    'Content-Type': 'application/json',
}

url_invoke='https://eloquent-chaum4.im.grycap.net/job/fish-detector'

# Rango de imagenes a procesar (inicio-fin)
for i in range(cant_invoke):
    #Rango de imágenes
    inicio=i*img_invoke+1
    fin=(i+1)*img_invoke

    if i==cant_invoke-1:
        fin=fin+resto
    data={
            "start": inicio,
           "end": fin
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
    print(f"Valor_Inicio: {inicio}")
    print(f"Valor_Fin: {fin}")
    print(f"Invocacion {i+1} al servicio")