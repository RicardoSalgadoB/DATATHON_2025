from dotenv import load_dotenv
import os

if __name__ == '__main__':
  PROJECT_ID = os.environ['VERTEX_PROJECT_ID']
  LOCATION = "us-central1"    # Replace with the location of your endpoint
  ENDPOINT_ID = ''            # Replace with your endpoit id
  
  try:
    # I didn't run this because I couldn't endpoint my model :)
      # So if your run this lad, be sure to set up a prediction_input.json
    os.system(f"""
gcloud ai endpoints predict {ENDPOINT_ID} \
  --region={LOCATION} \
  --json-request=prediction_input.json""")
    
  except Exception as e:
    print("Error: ", e)