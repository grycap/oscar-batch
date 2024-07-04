import json

# Define the configuration data
config_data = {
    "MinIO": {
        "url": "minio.crazy-kowalevski5.im.grycap.net",
        "access_key": "minio",
        "secret_key": "minio-ai4eosc-uEQqQ"
    },
    "bucket": {
        "name": "fish-detector",
        "folder_prefix": "input/"
    },
    "output": {
        "file": "index.txt"
    },
    "oscar_cluster": {
        "url": "inference.cloud.ai4eosc.eu",
        "auth_basic": {
            "username": "oscar",
            "password": "oscar-ai4eosc-dzFcy"
        },
        "auth_token": {
            "token": "1234fd"
        }
    },
    "service": {
        "name": "fish-detector"
    }
}

# Create the Configuration File.
with open('config.json', 'w') as config_file:
    json.dump(config_data, config_file, indent=4)

print("Configuration file 'config.json' created.")