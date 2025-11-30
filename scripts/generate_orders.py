import json
import logging
import uuid

import requests

# Set up logging for better error visibility
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# --- CONFIGURATION SECTION ---
# !!! IMPORTANT: Replace these placeholder values with your specific data !!!

# 1. API Endpoint URL
URL = "https://alilee.hossamstore.store/api/orders/"  # e.g., "http://localhost:8000/api/orders/"
URL = "http://localhost:8000/api/orders/"  # Example for local testing
# 2. Authorization Token (Bearer Token)
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxODE2ODU0OTYxLCJpYXQiOjE3NjI4NTQ5NjEsImp0aSI6IjViYmRmZGRiOWIzNDRmZGZhMjkyNWZkYjQ1ZjdkMTU3IiwidXNlcl9pZCI6IjEifQ.xs3CL4n0WwDJrmQGugyKqWVtSRxTyOPZjRRieX3cjeE"

AUTH_TOKEN = "Bearer " + token

# 3. JSON Payload (Data to be sent in the request body)

# -----------------------------


def create_order_request():
    """
    Sends a POST request to the configured API endpoint with the specified headers and data.
    """

    # 4. Request Headers (Replicating the -H flags from the curl command)
    headers = {
        "accept": "application/json",
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
    }
    reference_code = f"ref_{uuid.uuid4().hex[:10]}"
    PAYLOAD = {
        "reference_code": reference_code[:14],
        "product_cost": "50",  # Note: These might need to be floats/numbers if the API expects them
        "extra_delivery_cost": "60",
        "status": "created",
        "payment_method": "paid",
        "product_payment_status": "paid",
        "note": "string",
        "longitude": "50",
        "latitude": "50",
        # "driver": "113",
        "trader": "12",
        "customer": {"name": "string", "address": "string", "phone": "string"},
        "delivery_zone": 4,
    }
    try:
        logging.info("Attempting to send POST request...")

        response = requests.post(URL, headers=headers, data=json.dumps(PAYLOAD))

        # Check for success (2xx status codes)
        if response.ok:
            logging.info(f"SUCCESS: Order created. Status Code: {response.status_code}")
            try:
                # Print the JSON response from the server
                logging.info(
                    f"Response JSON : \n{json.dumps(response.json(), indent=4)}"
                )
            except json.JSONDecodeError:
                # Handle cases where the response is not valid JSON
                logging.info(f"Response text (not JSON) : \n{response.text}")
        else:
            # Handle client or server errors (4xx or 5xx)
            logging.error(
                f"FAILED: Request returned status code {response.status_code}"
            )
            try:
                logging.error(
                    f"Error Details : \n{json.dumps(response.json(), indent=4)}"
                )
            except json.JSONDecodeError:
                logging.error(f"Raw Error Response : \n{response.text}")

    except requests.exceptions.RequestException as e:
        # Handle connection errors (e.g., DNS failure, server unreachable)
        logging.critical(f"CONNECTION ERROR: Could not connect to the server: {e}")


if __name__ == "__main__":
    # Ensure the 'requests' library is installed: pip install requests
    for _i in range(15):  # Example: create 5 orders
        create_order_request()
