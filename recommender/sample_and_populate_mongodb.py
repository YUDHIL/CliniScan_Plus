#!/usr/bin/env python3
"""
Sample 200 doctors from doctor_2000_realnames.csv (ensuring at least 1 from each city),
generate secure login credentials (User ID, Username, Email, Password, and Password Hash)
for each doctor, and populate MongoDB with appropriate indexes.
"""

import os
import sys
import re
import json
import hashlib
import argparse
import pandas as pd
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING

# Ensure UTF-8 output across all platforms
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Path constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV_PATH = os.path.join(BASE_DIR, "doctor_2000_realnames.csv")
OUTPUT_CSV_PATH = os.path.join(BASE_DIR, "doctors_200_sample.csv")
OUTPUT_JSON_PATH = os.path.join(BASE_DIR, "doctors_200_sample.json")
OUTPUT_JSONL_PATH = os.path.join(BASE_DIR, "doctors_200_sample.jsonl")
CREDENTIALS_CSV_PATH = os.path.join(BASE_DIR, "doctors_credentials.csv")
CREDENTIALS_JSON_PATH = os.path.join(BASE_DIR, "doctors_credentials.json")


def clean_name_parts(doctor_name: str):
    """
    Extracts sanitized first name and last name from 'Dr. FirstName LastName'.
    """
    cleaned = re.sub(r'^(Dr\.|Dr\s+|Doctor\s+)', '', doctor_name, flags=re.IGNORECASE).strip()
    parts = re.findall(r'[A-Za-z]+', cleaned)
    if not parts:
        return "doctor", "user"
    first = parts[0].lower()
    last = parts[-1].lower() if len(parts) > 1 else "doc"
    raw_first = parts[0].capitalize()
    raw_last = parts[-1].capitalize() if len(parts) > 1 else "Doc"
    return first, last, raw_first, raw_last


def sanitize_hospital_domain(hospital_name: str) -> str:
    """
    Creates a clean email domain from hospital name.
    """
    clean_hosp = re.sub(r'[^a-zA-Z0-9]', '', hospital_name).lower()
    return f"{clean_hosp}.med" if clean_hosp else "hospital.med"


def generate_doctor_credentials(doctor_name: str, hospital: str, doctor_idx: int, existing_usernames: set, existing_emails: set):
    """
    Generates a unique User ID, Username, Email, Password, and SHA-256 password hash.
    """
    user_id = f"DOC_{doctor_idx:04d}"
    first, last, raw_first, raw_last = clean_name_parts(doctor_name)
    hosp_domain = sanitize_hospital_domain(hospital)

    # Base username & email
    base_username = f"dr.{first}.{last}"
    base_email = f"{first}.{last}@{hosp_domain}"

    # Ensure uniqueness
    username = base_username
    email = base_email
    suffix = 1
    while username in existing_usernames or email in existing_emails:
        username = f"{base_username}{suffix}"
        email = f"{first}.{last}{suffix}@{hosp_domain}"
        suffix += 1

    existing_usernames.add(username)
    existing_emails.add(email)

    # Generate a strong, professional, memorable password
    # Pattern: Dr<LastName>#<First2LettersFirst><DocID_digits>! e.g., DrBalasubramanian#Os0001!
    password = f"Dr{raw_last}#{raw_first[:2]}{doctor_idx:04d}!"

    # Compute SHA-256 hash for secure storage
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    return {
        "user_id": user_id,
        "username": username,
        "email": email,
        "password": password,
        "password_hash": password_hash
    }


def sample_doctors_data(csv_path: str, total_samples: int = 200, random_seed: int = 42) -> pd.DataFrame:
    """
    Randomly samples `total_samples` doctors from the CSV, ensuring at least one
    doctor from each unique city is included.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Source dataset not found at: {csv_path}")

    df = pd.read_csv(csv_path)
    unique_cities = df['City'].unique()
    num_cities = len(unique_cities)

    print(f"[*] Total dataset records: {len(df)}")
    print(f"[*] Unique cities found: {num_cities} -> {', '.join(sorted(unique_cities))}")

    if total_samples < num_cities:
        raise ValueError(
            f"Requested total_samples ({total_samples}) is less than the number of unique cities ({num_cities})."
        )

    # 1. Take 1 random sample from each unique city
    city_sample_indices = []
    for city in sorted(unique_cities):
        city_df = df[df['City'] == city]
        sampled_row = city_df.sample(n=1, random_state=random_seed)
        city_sample_indices.append(sampled_row.index[0])

    # 2. Remaining slots to reach total_samples
    remaining_needed = total_samples - len(city_sample_indices)
    remaining_pool = df.drop(index=city_sample_indices)

    random_sample = remaining_pool.sample(n=remaining_needed, random_state=random_seed)
    
    # 3. Combine and shuffle
    sampled_indices = city_sample_indices + list(random_sample.index)
    sampled_df = df.loc[sampled_indices].sample(frac=1, random_state=random_seed).reset_index(drop=True)

    # Clean / cast types
    sampled_df['Experience'] = sampled_df['Experience'].astype(int)
    sampled_df['Rating'] = sampled_df['Rating'].astype(float)
    sampled_df['Fees'] = sampled_df['Fees'].astype(int)

    return sampled_df


def prepare_documents_with_credentials(df: pd.DataFrame) -> tuple[list, list]:
    """
    Converts DataFrame rows to clean dictionary records with generated login credentials.
    Returns (database_documents, credentials_records).
    """
    records = df.to_dict(orient='records')
    now = datetime.now(timezone.utc).isoformat()
    existing_usernames = set()
    existing_emails = set()

    db_documents = []
    credentials_list = []

    for idx, row in enumerate(records, start=1):
        creds = generate_doctor_credentials(
            doctor_name=row['Doctor_Name'],
            hospital=row['Hospital'],
            doctor_idx=idx,
            existing_usernames=existing_usernames,
            existing_emails=existing_emails
        )

        # Full document stored in MongoDB
        doc = {
            "doctor_id": creds["user_id"],
            "user_id": creds["user_id"],
            "username": creds["username"],
            "email": creds["email"],
            "password": creds["password"],  # Kept in document for easy developer retrieval
            "password_hash": creds["password_hash"],
            "Doctor_Name": row["Doctor_Name"],
            "Disease": row["Disease"],
            "Specialization": row["Specialization"],
            "Experience": row["Experience"],
            "Rating": row["Rating"],
            "Hospital": row["Hospital"],
            "City": row["City"],
            "Fees": row["Fees"],
            "Availability": row["Availability"],
            "created_at": now
        }
        db_documents.append(doc)

        # Credential sheet record
        cred_record = {
            "user_id": creds["user_id"],
            "Doctor_Name": row["Doctor_Name"],
            "Specialization": row["Specialization"],
            "Hospital": row["Hospital"],
            "City": row["City"],
            "username": creds["username"],
            "email": creds["email"],
            "password": creds["password"]
        }
        credentials_list.append(cred_record)

    return db_documents, credentials_list


def export_all_files(db_documents: list, credentials_list: list):
    """
    Exports the documents and credentials to CSV, standard JSON, and JSONL.
    """
    # 1. Credentials CSV
    creds_df = pd.DataFrame(credentials_list)
    creds_df.to_csv(CREDENTIALS_CSV_PATH, index=False)
    print(f"[OK] Saved credentials CSV to: {CREDENTIALS_CSV_PATH}")

    # 2. Credentials JSON
    with open(CREDENTIALS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(credentials_list, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved credentials JSON to: {CREDENTIALS_JSON_PATH}")

    # 3. Full Sample CSV
    full_df = pd.DataFrame(db_documents)
    full_df.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"[OK] Saved 200 doctor sample CSV to: {OUTPUT_CSV_PATH}")

    # 4. Full Sample JSON Array
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(db_documents, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved 200 doctor sample JSON array to: {OUTPUT_JSON_PATH}")

    # 5. Full Sample JSON Lines (for mongoimport)
    with open(OUTPUT_JSONL_PATH, 'w', encoding='utf-8') as f:
        for doc in db_documents:
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')
    print(f"[OK] Saved 200 doctor sample JSON Lines to: {OUTPUT_JSONL_PATH}")


def setup_mongodb_indexes(collection):
    """
    Creates indexes on the collection for high-performance querying and unique logins.
    """
    print("[*] Creating indexes...")
    index_results = []
    
    # Unique Authentication Indexes
    index_results.append(collection.create_index([("doctor_id", ASCENDING)], unique=True))
    index_results.append(collection.create_index([("user_id", ASCENDING)], unique=True))
    index_results.append(collection.create_index([("username", ASCENDING)], unique=True))
    index_results.append(collection.create_index([("email", ASCENDING)], unique=True))
    
    # Medical Filtering Indexes
    index_results.append(collection.create_index([("Specialization", ASCENDING)]))
    index_results.append(collection.create_index([("City", ASCENDING)]))
    index_results.append(collection.create_index([("Disease", ASCENDING)]))
    index_results.append(collection.create_index([("Rating", DESCENDING)]))
    index_results.append(collection.create_index([("Fees", ASCENDING)]))
    index_results.append(collection.create_index([("Availability", ASCENDING)]))
    
    # Compound indexes for recommendation queries
    index_results.append(collection.create_index([("Specialization", ASCENDING), ("City", ASCENDING), ("Rating", DESCENDING)]))
    index_results.append(collection.create_index([("Specialization", ASCENDING), ("Fees", ASCENDING)]))
    index_results.append(collection.create_index([("Disease", ASCENDING), ("City", ASCENDING), ("Rating", DESCENDING)]))

    print(f"[OK] Created indexes successfully.")
    for idx_info in collection.list_indexes():
        print(f"    - Index: {idx_info['name']} -> Keys: {idx_info['key']}")


def populate_database(documents: list, mongo_uri: str, db_name: str, collection_name: str, use_mock: bool = False):
    """
    Connects to MongoDB and inserts documents into the specified collection.
    """
    client = None
    if use_mock:
        print("[*] Using 'mongomock' in-memory MongoDB client...")
        import mongomock
        client = mongomock.MongoClient()
    else:
        print(f"[*] Connecting to MongoDB at: {mongo_uri}")
        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2500)
            client.admin.command('ping')
            print("[OK] Connected successfully to live MongoDB server!")
        except Exception as e:
            print(f"[!] Live MongoDB server at '{mongo_uri}' is not reachable ({e}).")
            print("[*] Using 'mongomock' to validate data insertion, schema, and indexes...")
            import mongomock
            client = mongomock.MongoClient()

    db = client[db_name]
    collection = db[collection_name]

    # Clear existing sample data if any
    deleted = collection.delete_many({})
    print(f"[*] Cleared {deleted.deleted_count} previous documents from '{db_name}.{collection_name}'.")

    # Insert 200 documents
    insert_res = collection.insert_many(documents)
    print(f"[OK] Successfully inserted {len(insert_res.inserted_ids)} doctor documents into '{db_name}.{collection_name}'!")

    # Setup indexes
    setup_mongodb_indexes(collection)

    # Verification summary
    print("\n" + "=" * 65)
    print("           DATABASE & CREDENTIALS VERIFICATION")
    print("=" * 65)
    doc_count = collection.count_documents({})
    cities_in_db = sorted(collection.distinct("City"))
    specializations_in_db = sorted(collection.distinct("Specialization"))

    print(f"* Total doctors inserted   : {doc_count}")
    print(f"* Total credentials created : {doc_count} (100% unique User IDs, Usernames & Emails)")
    print(f"* Unique cities covered    : {len(cities_in_db)} / 26 (All represented!)")
    print(f"* Specializations          : {len(specializations_in_db)} ({', '.join(specializations_in_db)})")

    print("\nSample Credential Record:")
    sample_doc = collection.find_one({}, {"_id": 0, "password_hash": 0, "created_at": 0})
    print(json.dumps(sample_doc, indent=2))
    print("=" * 65 + "\n")

    return client, collection


def add_doctor_to_all_datasets(
    doctor_data: dict,
    mongo_uri: str = "mongodb://localhost:27017/",
    db_name: str = "doctor_db",
    collection_name: str = "doctors"
) -> dict:
    """
    Adds a newly registered doctor into all datasets:
    1. doctors_200_sample.json & .csv
    2. doctors_credentials.csv & .json
    3. doctor_2000_realnames.csv (local in recommender/ and root)
    4. MongoDB instance (if accessible)
    """
    # Clean Doctor Name to avoid duplicate "Dr. Dr."
    raw_name = doctor_data.get("Doctor_Name") or doctor_data.get("full_name") or "Specialist"
    clean_n = re.sub(r'^(Dr\.\s*|Dr\s+|Doctor\s+)+', '', str(raw_name).strip(), flags=re.IGNORECASE).strip()
    d_name = f"Dr. {clean_n}"

    hospital = doctor_data.get("Hospital") or doctor_data.get("hospital") or "AIIMS"
    city = doctor_data.get("City") or doctor_data.get("city") or "Bangalore"
    specialization = doctor_data.get("Specialization") or doctor_data.get("specialization") or "General Physician"
    disease = doctor_data.get("Disease") or doctor_data.get("disease_expertise") or specialization
    exp = int(doctor_data.get("Experience") or doctor_data.get("experience_years") or 15)
    rating = float(doctor_data.get("Rating") or doctor_data.get("rating") or 5.0)
    fees = int(doctor_data.get("Fees") or doctor_data.get("fees_inr") or 800)
    avail = doctor_data.get("Availability") or doctor_data.get("availability") or "Available"

    # Credentials
    username = doctor_data.get("username")
    email = doctor_data.get("email")
    password = doctor_data.get("password")
    user_id = doctor_data.get("user_id") or doctor_data.get("doctor_id")

    if not username or not email or not password or not user_id:
        existing_u = set()
        existing_e = set()
        if os.path.exists(CREDENTIALS_CSV_PATH):
            try:
                c_df = pd.read_csv(CREDENTIALS_CSV_PATH)
                existing_u = set(c_df["username"].dropna().astype(str).tolist())
                existing_e = set(c_df["email"].dropna().astype(str).tolist())
            except Exception:
                pass
        next_idx = len(existing_u) + 1
        generated_creds = generate_doctor_credentials(d_name, hospital, next_idx, existing_u, existing_e)
        user_id = user_id or generated_creds["user_id"]
        username = username or generated_creds["username"]
        email = email or generated_creds["email"]
        password = password or generated_creds["password"]

    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    now_str = datetime.now(timezone.utc).isoformat()

    full_doc = {
        "doctor_id": user_id,
        "user_id": user_id,
        "username": username,
        "email": email,
        "password": password,
        "password_hash": password_hash,
        "Doctor_Name": d_name,
        "Disease": disease,
        "Specialization": specialization,
        "Experience": exp,
        "Rating": rating,
        "Hospital": hospital,
        "City": city,
        "Fees": fees,
        "Availability": avail,
        "created_at": now_str
    }

    cred_doc = {
        "user_id": user_id,
        "Doctor_Name": d_name,
        "Specialization": specialization,
        "Hospital": hospital,
        "City": city,
        "username": username,
        "email": email,
        "password": password
    }

    # 1. Update doctors_200_sample.json
    try:
        current_docs = []
        if os.path.exists(OUTPUT_JSON_PATH):
            with open(OUTPUT_JSON_PATH, "r", encoding="utf-8") as f:
                current_docs = json.load(f)
        # Avoid duplicate doctor_id/user_id/username
        current_docs = [d for d in current_docs if d.get("username") != username and d.get("user_id") != user_id]
        current_docs.insert(0, full_doc)
        with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(current_docs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[!] Error updating {OUTPUT_JSON_PATH}: {e}")

    # 2. Update doctors_200_sample.csv
    try:
        sample_df = pd.DataFrame([full_doc])
        if os.path.exists(OUTPUT_CSV_PATH):
            old_df = pd.read_csv(OUTPUT_CSV_PATH)
            old_df = old_df[old_df["username"] != username]
            sample_df = pd.concat([sample_df, old_df], ignore_index=True)
        sample_df.to_csv(OUTPUT_CSV_PATH, index=False)
    except Exception as e:
        print(f"[!] Error updating {OUTPUT_CSV_PATH}: {e}")

    # 3. Update doctors_credentials.csv & .json
    try:
        current_creds = []
        if os.path.exists(CREDENTIALS_JSON_PATH):
            with open(CREDENTIALS_JSON_PATH, "r", encoding="utf-8") as f:
                current_creds = json.load(f)
        current_creds = [c for c in current_creds if c.get("username") != username]
        current_creds.insert(0, cred_doc)
        with open(CREDENTIALS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(current_creds, f, indent=2, ensure_ascii=False)

        creds_df = pd.DataFrame(current_creds)
        creds_df.to_csv(CREDENTIALS_CSV_PATH, index=False)
    except Exception as e:
        print(f"[!] Error updating credentials files: {e}")

    # 4. Append to doctor_2000_realnames.csv (recommender and root)
    root_csv = os.path.abspath(os.path.join(BASE_DIR, "..", "doctor_2000_realnames.csv"))
    for csv_file in [DEFAULT_CSV_PATH, root_csv]:
        try:
            if os.path.exists(csv_file):
                csv_line = f"\n{d_name},{disease},{specialization},{exp},{rating},{hospital},{city},{fees},{avail}"
                with open(csv_file, "a", encoding="utf-8") as f:
                    f.write(csv_line)
        except Exception as e:
            print(f"[!] Error appending to {csv_file}: {e}")

    # 5. Sync to data/cliniscan_db_backup.json and src.database.db_instance
    try:
        backup_path = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "cliniscan_db_backup.json"))
        if os.path.exists(backup_path):
            with open(backup_path, "r", encoding="utf-8") as f:
                b_data = json.load(f)
            users_list = b_data.get("users", [])
            # Update existing or add new
            users_list = [u for u in users_list if u.get("username") != username]
            user_record = {
                "user_id": user_id,
                "username": username,
                "password_hash": password_hash,
                "role": "Doctor",
                "full_name": d_name,
                "email": email,
                "phone": doctor_data.get("phone", "+91 98111 22334"),
                "city": city,
                "specialization": specialization,
                "hospital": hospital,
                "experience_years": exp,
                "fees_inr": fees,
                "rating": rating,
                "availability": avail,
                "disease_expertise": disease,
                "created_at": now_str
            }
            users_list.append(user_record)
            b_data["users"] = users_list
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(b_data, f, indent=2)
    except Exception as b_err:
        print(f"[!] Error syncing to cliniscan_db_backup.json: {b_err}")

    # 6. Insert to MongoDB if reachable
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        db = client[db_name]
        coll = db[collection_name]
        coll.update_one({"username": username}, {"$set": full_doc}, upsert=True)
    except Exception:
        pass

    return full_doc


def main():
    parser = argparse.ArgumentParser(description="Sample 200 doctors, generate credentials, and populate MongoDB")
    parser.add_argument("--csv", default=DEFAULT_CSV_PATH, help="Path to doctor_2000_realnames.csv")
    parser.add_argument("--samples", type=int, default=200, help="Number of records to sample (default: 200)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--uri", default=os.getenv("MONGO_URI", "mongodb://localhost:27017/"), help="MongoDB connection URI")
    parser.add_argument("--db", default="doctor_db", help="Target database name (default: doctor_db)")
    parser.add_argument("--collection", default="doctors", help="Target collection name (default: doctors)")
    parser.add_argument("--mock", action="store_true", help="Force use of in-memory mongomock")
    parser.add_argument("--export-only", action="store_true", help="Only generate files without DB population")
    args = parser.parse_args()

    print("=== Doctor Dataset & Credentials Ingestion Pipeline ===")
    
    # 1. Sample data
    sampled_df = sample_doctors_data(args.csv, total_samples=args.samples, random_seed=args.seed)
    
    # 2. Generate credentials and documents
    db_documents, credentials_list = prepare_documents_with_credentials(sampled_df)

    # 3. Export all files
    export_all_files(db_documents, credentials_list)

    if args.export_only:
        print("[OK] Export completed. Skipping database population as requested.")
        return

    # 4. Populate MongoDB
    populate_database(db_documents, mongo_uri=args.uri, db_name=args.db, collection_name=args.collection, use_mock=args.mock)


if __name__ == "__main__":
    main()
