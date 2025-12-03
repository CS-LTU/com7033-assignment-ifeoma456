"""
Data Import Script for Stroke Prediction Dataset
This script imports patient data from the CSV file into MongoDB database
"""

import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
CSV_FILE = 'healthcare-dataset-stroke-data.csv'

def import_data():
    """Import CSV data into MongoDB"""
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client['stroke_prediction']
        patients_collection = db['patients']

        # Check if data already exists
        existing_count = patients_collection.count_documents({})
        if existing_count > 0:
            response = input(f"Database already contains {existing_count} records. Do you want to clear and reimport? (yes/no): ")
            if response.lower() != 'yes':
                print("Import cancelled.")
                return

            # Clear existing data
            patients_collection.delete_many({})
            print(f"Cleared {existing_count} existing records.")

        # Read CSV file
        print(f"Reading data from {CSV_FILE}...")
        df = pd.read_csv(CSV_FILE)

        # Convert DataFrame to dictionary records
        records = df.to_dict('records')

        # Convert numeric fields and handle N/A values
        for record in records:
            # Convert numeric fields
            record['id'] = int(record['id'])
            record['age'] = float(record['age'])
            record['hypertension'] = int(record['hypertension'])
            record['heart_disease'] = int(record['heart_disease'])
            record['avg_glucose_level'] = float(record['avg_glucose_level'])
            record['stroke'] = int(record['stroke'])

            # Handle BMI N/A values
            if pd.isna(record['bmi']) or record['bmi'] == 'N/A':
                record['bmi'] = 'N/A'
            else:
                record['bmi'] = float(record['bmi'])

        # Insert into MongoDB
        print(f"Importing {len(records)} patient records into MongoDB...")
        result = patients_collection.insert_many(records)

        print(f"Successfully imported {len(result.inserted_ids)} records!")

        # Create index on patient ID for faster lookups
        patients_collection.create_index('id', unique=True)
        print("Created index on patient ID field.")

        # Display some statistics
        print("\n=== Import Statistics ===")
        print(f"Total patients: {patients_collection.count_documents({})}")
        print(f"Patients with stroke: {patients_collection.count_documents({'stroke': 1})}")
        print(f"Patients without stroke: {patients_collection.count_documents({'stroke': 0})}")
        print(f"Male patients: {patients_collection.count_documents({'gender': 'Male'})}")
        print(f"Female patients: {patients_collection.count_documents({'gender': 'Female'})}")

        client.close()

    except FileNotFoundError:
        print(f"Error: Could not find {CSV_FILE}")
        print("Please ensure the CSV file is in the same directory as this script.")

    except Exception as e:
        print(f"Error during import: {str(e)}")


if __name__ == '__main__':
    print("=== Stroke Prediction Dataset Import Tool ===")
    print("This script will import patient data into MongoDB\n")
    import_data()
