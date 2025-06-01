from google.cloud import aiplatform
from dotenv import load_dotenv
import os

import time

if __name__ == "__main__":
    # Load secret stuff
    load_dotenv()
    
    # Replace with your actual values
    PROJECT_ID = os.environ['VERTEX_PROJECT_ID']
    LOCATION = "us-central1"    # Replace with the actual location of your model
    MODEL_ID = '001' # Replace with your actual project ID
    MODEL_NAME = f'projects/{PROJECT_ID}/locations/{LOCATION}/models/{MODEL_ID}'
    GOOGLE_INPUT = 'gs://input'     # Replace with the gcloud folder where the model will fetch your data
    GOOGLE_OUTPUT = 'gs://output'   # Replace with the gcloud folder where the model will send your predictions
    LOCAL_INPUT = '/data/test'             # Replace where the local file where the data that is going to be predicted on is
    LOCAL_OUTPUT = '/data/predictions'      # Replace with where would you like to store locally your predictions
    
    # Initialize Vertex AI
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    
    # Example prediction
    try:
        # Upload data
        os.system(f"gsutil cp -r {LOCAL_INPUT} {GOOGLE_INPUT}")
        
        # Predict
            # Configure the predict_config.json before running this
        os.system(f"""
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d @predict_config.json \
  "https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/batchPredictionJobs" """)
        
        # Download results once the result are ready
        time.sleep(1800)    # Less than 30 minutes by rule of thumb
        
        # Download data
        os.system(f"gcloud storage cp --recursive {GOOGLE_OUTPUT} {LOCAL_OUTPUT}")
        
    except Exception as e:
        print(f"Error: {e}")
        