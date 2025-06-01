from google.cloud import aiplatform
from google.cloud.aiplatform import schema
from typing import List, Optional
import json

def train_hierarchical_timeseries_model(
    project_id: str,
    location: str,
    dataset_id: str,
    model_display_name: str,
    training_budget_hours: int = 2
):
    """
    Train a hierarchical time series forecasting model on Vertex AI
    
    Args:
        project_id: Google Cloud project ID
        location: Training location (e.g., 'us-central1')
        dataset_id: ID of the TimeSeriesDataset in Vertex AI
        model_display_name: Name for the trained model
        training_budget_hours: Maximum training time in hours
    """
    
    # Initialize Vertex AI
    aiplatform.init(project=project_id, location=location)
    
    # Get the dataset
    dataset = aiplatform.TimeSeriesDataset(dataset_name=dataset_id)
    
    # Define training configuration
    training_config = {
        # Target and time configuration
        "targetColumn": "monto",
        "timeColumn": "fecha",
        "timeSeriesIdentifierColumn": "transaction_id",
        
        # Forecasting parameters
        "forecastHorizon": 31,
        "dataGranularity": {
            "unit": "day",
            "quantity": 1
        },
        
        # Hierarchical forecasting configuration
        "hierarchyConfig": {
            "groupColumns": ["cliente_id"],
            "groupTotalWeight": 1.0,
            "temporalTotalWeight": 1.0,
            "groupTemporalTotalWeight": 1.0
        },
        
        # Feature columns
        "transformations": [
            # Categorical attributes
            {
                "categorical": {
                    "columnName": "tipo_venta"
                }
            },
            {
                "categorical": {
                    "columnName": "comercio"
                }
            },
            {
                "categorical": {
                    "columnName": "giro_comercio"
                }
            },
            {
                "categorical": {
                    "columnName": "id_estado"
                }
            },
            {
                "categorical": {
                    "columnName": "id_municipio"
                }
            },
            {
                "categorical": {
                    "columnName": "tipo_persona"
                }
            },
            {
                "categorical": {
                    "columnName": "actividad_empresarial"
                }
            },
            
            # Date-based attributes (will be treated as categorical for datetime features)
            {
                "categorical": {
                    "columnName": "fecha_nacimiento"
                }
            },
            {
                "categorical": {
                    "columnName": "fecha_alta"
                }
            },
            
            # Time-based covariates (numeric)
            {
                "numeric": {
                    "columnName": "day_month"
                }
            },
            {
                "numeric": {
                    "columnName": "day_week"
                }
            },
            {
                "numeric": {
                    "columnName": "day_year"
                }
            },
            {
                "numeric": {
                    "columnName": "week_year"
                }
            },
            {
                "numeric": {
                    "columnName": "quarter"
                }
            }
        ],
        
        # Optimization objective
        "optimizationObjective": "minimize-rmse",
        
        # Training budget
        "budgetMilliNodeHours": training_budget_hours * 1000,
        
        # Holiday configuration for Mexico
        "holidayRegions": ["MX"],  # Mexico
        
        # Additional model configurations
        "modelDisplayName": model_display_name,
        
        # Enable automatic feature engineering
        "enableProfiling": True,
        
        # Data splitting (automatic)
        "trainBudgetMilliNodeHours": int(training_budget_hours * 1000 * 0.8),  # 80% for training
        "validationBudgetMilliNodeHours": int(training_budget_hours * 1000 * 0.2),  # 20% for validation
        
        # Advanced options
        "exportModelStructure": True,
        "windowConfig": {
            "maxCount": 0,  # Use all available historical data
            "stride": 1
        }
    }
    
    # Create and start the training job
    print(f"Starting training job for model: {model_display_name}")
    print(f"Training budget: {training_budget_hours} hours")
    print(f"Dataset: {dataset.display_name}")
    
    try:
        # Create the AutoML forecasting training job
        job = aiplatform.AutoMLForecastingTrainingJob(
            display_name=f"{model_display_name}-training-job",
            optimization_objective="minimize-rmse",
            column_specs={
                "fecha": "timestamp",
                "monto": "target",
                "transaction_id": "time_series_identifier",
                # Categorical columns
                "tipo_venta": "categorical",
                "comercio": "categorical", 
                "giro_comercio": "categorical",
                "fecha_nacimiento": "categorical",
                "fecha_alta": "categorical",
                "id_estado": "categorical",
                "id_municipio": "categorical", 
                "tipo_persona": "categorical",
                "actividad_empresarial": "categorical",
                "cliente_id": "categorical",  # For hierarchy
                # Numeric covariates
                "day_month": "numeric",
                "day_week": "numeric", 
                "day_year": "numeric",
                "week_year": "numeric",
                "quarter": "numeric"
            }
        )
        
        # Run the training
        model = job.run(
            dataset=dataset,
            target_column="monto",
            time_column="fecha", 
            time_series_identifier_column="transaction_id",
            forecast_horizon=31,
            data_granularity_unit="day",
            data_granularity_count=1,
            budget_milli_node_hours=training_budget_hours * 1000,
            hierarchy_group_columns=["cliente_id"],
            holiday_regions=["MX"],
            sync=True,  # Wait for completion
            enable_probabilistic_inference=False,  # No prediction intervals
            model_display_name=model_display_name,
            # Columns available at forecast time (static attributes + known future covariates)
            available_at_forecast_columns=[
                "transaction_id",  # Time series identifier
                "cliente_id",      # Hierarchy column
                "tipo_venta",      # Static business attributes
                "comercio",
                "giro_comercio", 
                "fecha_nacimiento", # Static customer info
                "fecha_alta",
                "id_estado",       # Static location info
                "id_municipio",
                "tipo_persona",    # Static customer type
                "actividad_empresarial",
                "day_month",       # Known future time covariates
                "day_week",
                "day_year", 
                "week_year",
                "quarter"
            ],
            # Columns NOT available at forecast time (unknown future values)
            unavailable_at_forecast_columns=[
                "monto"  # Target variable - unknown in the future
            ]
        )
        
        print("✅ Training completed successfully!")
        print(f"Model name: {model.display_name}")
        print(f"Model resource name: {model.resource_name}")
        print(f"Model ID: {model.name}")
        
        return model
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        raise

def monitor_training_job(job_name: str, project_id: str, location: str):
    """
    Monitor the status of a training job
    
    Args:
        job_name: Name of the training job
        project_id: Google Cloud project ID  
        location: Training location
    """
    
    aiplatform.init(project=project_id, location=location)
    
    # Get training job by name
    jobs = aiplatform.AutoMLForecastingTrainingJob.list(
        filter=f'display_name="{job_name}"'
    )
    
    if jobs:
        job = jobs[0]
        if hasattr(job, 'state'):
          print(f"Job Status: {job.state}")
        print(f"Job Name: {job.display_name}")
        print(f"Create Time: {job.create_time}")
        
        if hasattr(job, 'model_to_upload'):
            print(f"Model: {job.model_to_upload}")
    else:
        print(f"No job found with name: {job_name}")

def get_model_evaluation_metrics(model_resource_name: str, project_id: str, location: str):
    """
    Get evaluation metrics for the trained model
    
    Args:
        model_resource_name: Resource name of the trained model
        project_id: Google Cloud project ID
        location: Training location
    """
    
    aiplatform.init(project=project_id, location=location)
    
    try:
        model = aiplatform.Model(model_name=model_resource_name)
        
        # Get model evaluations
        evaluations = model.list_model_evaluations()
        
        print("📊 Model Evaluation Metrics:")
        print("="*50)
        
        for evaluation in evaluations:
            print(f"Evaluation ID: {evaluation.name}")
            
            if hasattr(evaluation, 'metrics'):
                metrics = evaluation.metrics
                print("Metrics:")
                for key, value in metrics.items():
                    print(f"  {key}: {value}")
            
            print("-" * 30)
            
    except Exception as e:
        print(f"Error getting evaluation metrics: {e}")

# Example usage and main execution
def main():
    """Main execution function"""
    
    # Configuration - Replace with your actual values
    PROJECT_ID = "your-project-id"
    LOCATION = "us-central1"
    DATASET_ID = "your-dataset-id"  # From the dataset creation step
    MODEL_NAME = "hierarchical-timeseries-forecasting-model"
    TRAINING_HOURS = 2
    
    print("🚀 Starting Hierarchical Time Series Model Training")
    print("="*60)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Dataset: {DATASET_ID}")
    print(f"Model Name: {MODEL_NAME}")
    print(f"Training Budget: {TRAINING_HOURS} hours")
    print(f"Forecast Horizon: 31 days")
    print(f"Hierarchy: Bottom-up reconciliation by cliente_id")
    print(f"Holiday Region: Mexico")
    print("="*60)
    
    try:
        # Train the model
        model = train_hierarchical_timeseries_model(
            project_id=PROJECT_ID,
            location=LOCATION,
            dataset_id=DATASET_ID,
            model_display_name=MODEL_NAME,
            training_budget_hours=TRAINING_HOURS
        )
        
        # Get evaluation metrics
        print("\n📈 Getting model evaluation metrics...")
        get_model_evaluation_metrics(
            model_resource_name=model.resource_name,
            project_id=PROJECT_ID,
            location=LOCATION
        )
        
        print(f"\n✅ Training pipeline completed!")
        print(f"Your model is ready for deployment: {model.resource_name}")
        
        return model
        
    except Exception as e:
        print(f"❌ Training pipeline failed: {e}")
        return None

if __name__ == "__main__":
    # Run the training pipeline
    trained_model = main()
    
    if trained_model:
        print(f"\n🎉 Success! Model trained and ready to use.")
        print(f"Model Resource Name: {trained_model.resource_name}")
        print(f"\nNext steps:")
        print("1. Deploy the model to an endpoint for predictions")
        print("2. Use the model for batch predictions")
        print("3. Monitor model performance over time")