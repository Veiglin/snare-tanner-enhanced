FROM python:3.9-slim

# Install dependencies
RUN pip install azure-storage-blob paramiko

# Copy application code
COPY fetch_and_upload_logs.py /app/fetch_and_upload_logs.py

# Set the working directory
WORKDIR /app

# Set the entry point
CMD ["python", "fetch_and_upload_logs.py"]
