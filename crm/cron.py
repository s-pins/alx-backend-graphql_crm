import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

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
        transport = RequestsHTTPTransport(url=GQL_ENDPOINT, timeout=5)
        client = Client(transport=transport, fetch_schema_from_transport=True)
        query = gql("{ allCustomers(first: 1) { edges { node { id } } } }")
        client.execute(query)
        message += " (GraphQL endpoint is responsive)"

    except Exception as e:
        message += f" (GraphQL endpoint is unresponsive: {e})"

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
    mutation = gql('''
        mutation {
            updateLowStockProducts {
                updatedProducts {
                    name
                    stock
                }
                message
            }
        }
    ''')
    
    try:
        transport = RequestsHTTPTransport(url=GQL_ENDPOINT, timeout=15)
        client = Client(transport=transport, fetch_schema_from_transport=True)
        result = client.execute(mutation)
        
        updated_products = result.get("updateLowStockProducts", {}).get("updatedProducts", [])
        
        if updated_products:
            with open(log_file, "a") as log:
                timestamp = datetime.datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
                log.write(f"--- {timestamp} Low Stock Update ---\n")
                for product in updated_products:
                    log.write(f"Restocked {product['name']} to new stock level of {product['stock']}\n")
                log.write(f"Summary: {result.get('updateLowStockProducts', {}).get('message', 'No message.')}\n")
                log.write("-------------------------------------\n")

    except Exception as e:
        with open(log_file, "a") as log:
            timestamp = datetime.datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
            log.write(f"{timestamp} ERROR: An error occurred during stock update: {e}\n")
