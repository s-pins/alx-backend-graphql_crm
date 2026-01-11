import datetime
import requests

LOG_FILE = "/tmp/crm_heartbeat_log.txt"
GQL_ENDPOINT = "http://localhost:8000/graphql"

def log_crm_heartbeat():
    """
    Logs a heartbeat message to a file and optionally checks the GraphQL endpoint.
    """
    timestamp = datetime.datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    message = f"{timestamp} CRM is alive"

    # Optional: Check if the GraphQL endpoint is responsive
    try:
        # A simple query that should always work if the schema is correctly set up.
        # The default 'hello' field is often present in example schemas.
        # We need to find what the actual schema has.
        # Based on schema.py, there is no 'hello' field.
        # I will just query for all customers with a limit of 1.
        gql_query = {"query": "{ allCustomers(first: 1) { edges { node { id } } } }"}
        response = requests.post(GQL_ENDPOINT, json=gql_query, timeout=5) # 5-second timeout
        if response.status_code == 200 and "errors" not in response.json():
            message += " (GraphQL endpoint is responsive)"
        else:
            error_details = response.json().get("errors", "Unknown error")
            message += f" (GraphQL endpoint check failed with status {response.status_code}: {error_details})"

    except requests.exceptions.RequestException as e:
        message += f" (GraphQL endpoint is unresponsive: {e})"
    except Exception as e:
        message += f" (An unexpected error occurred during GraphQL check: {e})"

    # Append the final message to the log file
    with open(LOG_FILE, "a") as log:
        log.write(message + "\n")

if __name__ == '__main__':
    # This allows running the script directly for testing
    log_crm_heartbeat()

def update_low_stock():
    """
    Executes a GraphQL mutation to restock low-stock products and logs the result.
    """
    log_file = "/tmp/low_stock_updates_log.txt"
    mutation = {
        "query": """
            mutation {
                updateLowStockProducts {
                    updatedProducts {
                        name
                        stock
                    }
                    message
                }
            }
        """
    }
    
    try:
        response = requests.post(GQL_ENDPOINT, json=mutation, timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes
        
        data = response.json()
        if "errors" in data:
            error_message = data["errors"][0]["message"]
            raise Exception(f"GraphQL query failed: {error_message}")
            
        result = data.get("data", {}).get("updateLowStockProducts", {})
        updated_products = result.get("updatedProducts", [])
        
        if updated_products:
            with open(log_file, "a") as log:
                timestamp = datetime.datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
                log.write(f"--- {timestamp} Low Stock Update ---\\n")
                for product in updated_products:
                    log.write(f"Restocked {product['name']} to new stock level of {product['stock']}\\n")
                log.write(f"Summary: {result.get('message', 'No message.')}\\n")
                log.write("-------------------------------------\\n")

    except requests.exceptions.RequestException as e:
        with open(log_file, "a") as log:
            timestamp = datetime.datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
            log.write(f"{timestamp} ERROR: Failed to connect to GraphQL endpoint: {e}\\n")
    except Exception as e:
        with open(log_file, "a") as log:
            timestamp = datetime.datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
            log.write(f"{timestamp} ERROR: An error occurred during stock update: {e}\\n")
