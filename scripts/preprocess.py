from google.cloud import storage
import json
from dotenv import load_dotenv
import os
from typing import Optional
from pathlib import Path

def create_bucket_if_not_exists(
    bucket_name: str,
    project_id: str,
    location: str = "us-central1"
) -> bool:
    """
    Create a GCS bucket if it doesn't already exist
    
    Args:
        bucket_name: Name of the bucket to create
        project_id: Google Cloud project ID
        location: GCS location for the bucket
    
    Returns:
        True if bucket was created or already exists
    """
    
    client = storage.Client(project=project_id)
    
    try:
        # Check if bucket exists
        bucket = client.bucket(bucket_name)
        bucket.reload()
        print(f"Bucket {bucket_name} already exists")
        return True
        
    except Exception:
        # Bucket doesn't exist, create it
        try:
            bucket = client.create_bucket(bucket_name, location=location)
            print(f"Bucket {bucket_name} created in {location}")
            return True
            
        except Exception as e:
            print(f"Error creating bucket: {e}")
            return False


def upload_csv_to_gcs(
    bucket_name: str,
    source_file_path: str,
    destination_blob_name: str,
    project_id: Optional[str] = None
) -> str:
    """
    Upload a CSV file to Google Cloud Storage
    
    Args:
        bucket_name: Name of the GCS bucket
        source_file_path: Local path to the CSV file
        destination_blob_name: Name for the file in GCS (e.g., 'data/my_file.csv')
        project_id: Google Cloud project ID (optional)
    
    Returns:
        GCS URI of the uploaded file
    """
    
    # Initialize the storage client
    if project_id:
        client = storage.Client(project=project_id)
    else:
        client = storage.Client()
    
    # Get the bucket
    bucket = client.bucket(bucket_name)
    
    # Create a blob object
    blob = bucket.blob(destination_blob_name)
    
    # Upload the file
    try:
        blob.upload_from_filename(source_file_path)
        gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"
        print(f"File {source_file_path} uploaded to {gcs_uri}")
        return gcs_uri
    
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise


def upload_multiple_csvs_to_gcs(
    bucket_name: str,
    local_folder_path: str,
    gcs_folder_prefix: str = "",
    project_id: Optional[str] = None
) -> list:
    """
    Upload all CSV files from a local folder to GCS
    
    Args:
        bucket_name: Name of the GCS bucket
        local_folder_path: Local folder containing CSV files
        gcs_folder_prefix: Prefix for GCS folder (e.g., 'datasets/')
        project_id: Google Cloud project ID (optional)
    
    Returns:
        List of GCS URIs for uploaded files
    """
    
    client = storage.Client(project=project_id) if project_id else storage.Client()
    bucket = client.bucket(bucket_name)
    
    uploaded_files = []
    local_path = Path(local_folder_path)
    
    # Find all CSV files in the folder
    csv_files = list(local_path.glob("*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {local_folder_path}")
        return uploaded_files
    
    for csv_file in csv_files:
        # Create GCS blob name
        if gcs_folder_prefix:
            blob_name = f"{gcs_folder_prefix.rstrip('/')}/{csv_file.name}"
        else:
            blob_name = csv_file.name
        
        try:
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(str(csv_file))
            
            gcs_uri = f"gs://{bucket_name}/{blob_name}"
            uploaded_files.append(gcs_uri)
            print(f"Uploaded: {csv_file.name} -> {gcs_uri}")
            
        except Exception as e:
            print(f"Error uploading {csv_file.name}: {e}")
    
    return uploaded_files
    
if __name__ == '__main__':
  # Get secret stuff
  load_dotenv()
  PROJECT_ID = os.environ['VERTEX_PROJECT_ID']
  LOCATION = 'us_central1'
  BUCKET_NAME = 'Italian Medieval Bucket'   # Replace with your actual bucket naem
  LOCAL_FOLDER = 'data/processed_data'      # Folder from where to get the data
  GS_PREFIX = 'data/'                       # Gcloud folder where to store the data
  
  # Create bucket
  create_bucket_if_not_exists(
    BUCKET_NAME, 
    PROJECT_ID, 
    LOCATION
  )
  
  # Get data into the bucket
  upload_multiple_csvs_to_gcs(
    BUCKET_NAME, 
    LOCAL_FOLDER, 
    GS_PREFIX, 
    PROJECT_ID
  )
  
  