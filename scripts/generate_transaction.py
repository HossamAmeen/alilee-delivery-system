# This is a conceptual, non-executable example for educational purposes ONLY.
# DO NOT run this against any live, external website.
import requests
import random
import json

# *** Replace with your LOCAL test server endpoint (e.g., http://localhost:8000/api/test) ***
TEST_URL = "https://alilee.hossamstore.store/api/transactions/user/" 

# *** Use your OWN test/dummy credentials for your local server ***
TEST_HEADERS = {
    'accept': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxODE1NDA4NTk5LCJpYXQiOjE3NjE0MDg1OTksImp0aSI6Ijk4MzcyNjE0Mzk3MzRjMDhhMTBlZmNhOTliNTRmZjQyIiwidXNlcl9pZCI6IjEifQ.fR_xgCYrU_mg3k27ORgkNTyciECwIUDIKzBKsH_OAnw',
    'Content-Type': 'application/json',
}

# --- Concept for Generating Test Data ---
def generate_random_transaction(i):
    """Generates a dictionary with random transaction data."""
    # Random amount between 10 and 1000
    amount = random.randint(10, 1000)
    # Randomly select a transaction type
    type = random.choice(["deposit", "withdraw"])
    # Cycle through a few dummy user IDs
    user_id = 12 
    
    return {
        "user_account": user_id,
        "amount": amount,
        "transaction_type": type
    }

# --- Conceptual Request Loop ---
NUM_RECORDS = 50
print(f"Starting conceptual data generation for {NUM_RECORDS} records...")

for i in range(1, NUM_RECORDS + 1):
    data = generate_random_transaction(i)
    
    # In a real scenario, you would send the request like this:
    try:
        response = requests.post(TEST_URL, headers=TEST_HEADERS, data=json.dumps(data))
        print(f"Record {i}: Status {response.status_code}")
    except Exception as e:
        print(f"Record {i}: Failed with error {e}")

    print(f"Simulating request {i}: {data}")

print("Conceptual data generation complete.")