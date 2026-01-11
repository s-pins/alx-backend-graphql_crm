#!/usr/bin/env python
import base64
import os
import sys
from datetime import datetime, timedelta, timezone

from dateutil.parser import parse
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

# It's a good practice to have the project root on the python path
# to ensure that Django settings are discoverable.
PROJECT_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql.settings')
import django
django.setup()


# --- GraphQL Client Setup ---
# The script assumes the Django development server is running at this address.
GQL_ENDPOINT = "http://localhost:8000/graphql"
transport = RequestsHTTPTransport(url=GQL_ENDPOINT)
client = Client(transport=transport, fetch_schema_from_transport=False)

# --- GraphQL Query ---
# Find all orders within the last 7 days.
# The schema uses relay-style cursors (edges/node).
GET_RECENT_ORDERS_QUERY = gql("""
    query getRecentOrders($date: DateTime!) {
      allOrders(orderDateGte: $date) {
        edges {
          node {
            id
            orderDate
            customer {
              email
            }
          }
        }
      }
    }
""")

LOG_FILE = "/tmp/order_reminders_log.txt"

def fetch_and_log_reminders():
    """
    Fetches recent orders via GraphQL and logs reminders.
    """
    # Calculate the date 7 days ago from now (using timezone-aware datetime)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    # Prepare variables for the query
    params = {"date": seven_days_ago.isoformat()}

    try:
        # Execute the query
        result = client.execute(GET_RECENT_ORDERS_QUERY, variable_values=params)
        
        orders = result.get("allOrders", {}).get("edges", [])
        
        if not orders:
            return

        with open(LOG_FILE, "a") as log:
            timestamp = datetime.now().isoformat()
            for order_edge in orders:
                node = order_edge.get("node", {})
                if not node:
                    continue

                # The 'id' from a relay spec is a base64 encoded string 'TypeName:ID'
                # We decode it to get the actual database ID for logging.
                try:
                    _, order_id_str = base64.b64decode(node["id"]).decode("utf-8").split(":")
                except (ValueError, TypeError):
                    order_id_str = "invalid_id"

                customer_email = node.get("customer", {}).get("email", "no-email")
                
                log.write(
                    f"{timestamp}: Sending reminder for Order ID {order_id_str} "
                    f"to customer {customer_email}.\n"
                )

    except Exception as e:
        # Log errors to stderr or a dedicated error log
        error_timestamp = datetime.now().isoformat()
        with open(LOG_FILE, "a") as log:
            log.write(f"{error_timestamp}: ERROR: Failed to process order reminders: {e}\n")
        sys.stderr.write(f"Error: {e}\n")

if __name__ == "__main__":
    fetch_and_log_reminders()
    print("Order reminders processed!")
