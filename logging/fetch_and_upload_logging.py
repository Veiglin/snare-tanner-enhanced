import os
from azure.storage.blob import BlobServiceClient
import paramiko

# Azure Blob Storage configuration
AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
CONTAINER_NAME = os.getenv('CONTAINER_NAME')

# SFTP server configuration
SFTP_HOST = os.getenv('SFTP_HOST')
SFTP_PORT = int(os.getenv('SFTP_PORT'))
SFTP_USERNAME = os.getenv('SFTP_USERNAME')
SSH_PRIVATE_KEY_PATH = os.getenv('SSH_PRIVATE_KEY_PATH')
LOG_FILES = os.getenv('LOG_FILES').split(',')

def fetch_logs_via_sftp():
    private_key = paramiko.RSAKey.from_private_key_file(SSH_PRIVATE_KEY_PATH)
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USERNAME, pkey=private_key)
    sftp = paramiko.SFTPClient.from_transport(transport)
    logs = {}
    for log_file in LOG_FILES:
        with sftp.file(log_file, 'r') as file:
            logs[os.path.basename(log_file)] = file.read()
    sftp.close()
    transport.close()
    return logs

def upload_logs_to_blob(logs):
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    for log_name, log_content in logs.items():
        blob_client = container_client.get_blob_client(log_name)
        blob_client.upload_blob(log_content, overwrite=True)

if __name__ == "__main__":
    logs = fetch_logs_via_sftp()
    upload_logs_to_blob(logs)
