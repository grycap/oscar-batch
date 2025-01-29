import json

config_data = {
    "MinIO": {
        "url": "minio.gracious-varahamihira6.im.grycap.net",
        "access_key": "",
        "secret_key": ""
    },
    "bucket": {
        "name": "fish-detector",
        "folder_prefix": "input/"
    },
    "output": {
        "file": "index.txt"
    },
    "local": {
        "folder": "Imag"
    },
    "oscar_cluster": {
        "url": "inference-walton.cloud.imagine-ai.eu",
        "auth_basic": {
            "username": "",
            "password": ""
        },
        "auth_token": { 
            "token":""
        }
    },
    "service": {
        "name": "fish-detector-test"
    }
}

with open('config-walton-direct.json', 'w') as config_file:
    json.dump(config_data, config_file, indent=4)

print("Configuration file 'config.json' created.")