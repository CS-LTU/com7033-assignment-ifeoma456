import os
import csv
import argparse
from pymongo import MongoClient, UpdateOne

def parse_value(key, value):
    if value is None:
        return None
    value = value.strip()
    if value == '' or value.upper() in ('N/A', 'NA'):
        return None

    if key in ('id', 'hypertension', 'heart_disease', 'stroke'):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    if key in ('age', 'avg_glucose_level', 'bmi'):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    # keep text fields as-is
    return value

def load_csv(file_path, mongo_uri, db_name='secure_app', collection_name='patients', batch_size=1000, drop=False):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    coll = db[collection_name]

    if drop:
        print(f'Dropping collection {db_name}.{collection_name}')
        coll.drop()

    ops = []
    total = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            doc = {k: parse_value(k, v) for k, v in row.items()}
            # require id to be present and non-None
            id_val = doc.get('id')
            if id_val is None:
                continue
            ops.append(UpdateOne({'id': id_val}, {'$set': doc}, upsert=True))
            total += 1
            if len(ops) >= batch_size:
                coll.bulk_write(ops)
                ops = []

    if ops:
        coll.bulk_write(ops)

    print(f'Inserted/updated {total} documents into {db_name}.{collection_name}')
    client.close()


if __name__ == '__main__':
    default_csv = os.path.join(os.path.dirname(__file__), '..', '..', 'healthcare-dataset-stroke-data.csv')
    parser = argparse.ArgumentParser(description='Load CSV into MongoDB (upsert by id).')
    parser.add_argument('--file', '-f', default=default_csv, help='Relative or absolute path to CSV file')
    parser.add_argument('--uri', '-u', default=os.getenv('MONGO_URI', 'mongodb://localhost:27017'), help='MongoDB URI')
    parser.add_argument('--db', default='secure_app', help='MongoDB database name')
    parser.add_argument('--collection', '-c', default='patients', help='MongoDB collection name')
    parser.add_argument('--drop', action='store_true', help='Drop collection before import')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        raise SystemExit(f'CSV file not found: {args.file}')

    load_csv(args.file, args.uri, db_name=args.db, collection_name=args.collection, drop=args.drop)
# ...existing code...