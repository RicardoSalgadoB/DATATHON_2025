from flask import Flask, request, jsonify
from google.cloud import aiplatform
from dotenv import load_dotenv
import os

from supabase import create_client

import time
import json
import csv

from llm_user import call_llm
from langchain.memory import ConversationBufferMemory

# Get secrets
load_dotenv()

MODEL_ID = '6866655724135514112'
#ENDPOINT_ID = "your-endpoint-id"
PROJECT_ID = os.environ['VERTEX_PROJECT_ID']
LOCATION = "us-central1"    # Replace with the actual location of your model
MODEL_ID = '001' # Replace with your actual project ID
MODEL_NAME = f'projects/{PROJECT_ID}/locations/{LOCATION}/models/{MODEL_ID}'
GOOGLE_INPUT = 'gs://input'     # Replace with the gcloud folder where the model will fetch your data
GOOGLE_OUTPUT = 'gs://output'   # Replace with the gcloud folder where the model will send your predictions
LOCAL_INPUT = '/data/test'             # Replace where the local file where the data that is going to be predicted on is
LOCAL_OUTPUT = '/data/predictions'      # Replace with where would you like to store locally your predictions

# Setup Flask
app = Flask(__name__)

# Setup supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key) # type: ignore


@app.route('/predict/single', methods=['POST']) # type: ignore
def make_predictions():
    data = request.get_json()
    
    with open(LOCAL_INPUT, 'w', newline='', encoding='utf-8') as csv_file:
        if isinstance(data, list) and len(data) > 0:
            writer = csv.DictWriter(csv_file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        else:
            print("JSON is not in expected format (a list of dictionaries).")
    
    # Initialize Vertex AI
    aiplatform.init(project=PROJECT_ID, location=LOCATION)  # type: ignore
    
    try:
        # Upload data
        os.system(f"gsutil cp -r {LOCAL_INPUT} {GOOGLE_INPUT}")
        
        # Predict
        os.system(f"""
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d @request.json \
  "https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/batchPredictionJobs" """)
        
        # Download results once the result are ready
        time.sleep(2000)
        #os.system(f"gcloud storage cp --recursive {GOOGLE_OUTPUT} {LOCAL_OUTPUT}")
        
    except Exception as e:
        print(f"Error: {e}")


@app.route('/raw_data/<client_id>', methods=['GET'])
def get_data(client_id):
    response = supabase.table('raw_data1').select('*').eq('client_id', client_id).execute()
    return jsonify(response.data)


@app.route('/insights/<client_id>')
def insights(client_id):
    d1 = {}
    try:
        high_frec = supabase.table('high_freq_insights1').select('comercio').eq('client_id', client_id).execute()
        d1['Frecuencias altas'] = high_frec.data
    except:
        pass
    
    try:
        high_stakes = supabase.table('high_stakes_insights1').select('comercio', 'fecha').eq('client_id', client_id).execute()
        d1['Movimientos grandes'] = high_stakes.data
    except:
        pass
    
    return jsonify(d1)
    
    
@app.route('/chat/user/<client_id>', methods=['POST'])  # type: ignore
def chat_user(client_id):
    d1 = {}
    try:
        high_frec = supabase.table('high_freq_insights1').select('comercio').eq('client_id', client_id).execute()
        d1['Frecuencias altas'] = high_frec.data
    except:
        pass
    
    try:
        high_stakes = supabase.table('high_stakes_insights1').select('comercio', 'fecha').eq('client_id', client_id).execute()
        d1['Movimientos grandes'] = high_stakes.data
    except:
        pass
    
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    user_input = request.get_json()
    user_input = user_input['content'] + f'Predicciones a futuro: {d1}'
    response, memory = call_llm(user_input, memory)
    return response
    
if __name__ == '__main__':
    app.run()