#!/bin/bash

# Get the absolute path to the project root directory
PROJECT_ROOT=$(realpath "$(dirname "$0")/../..")

# The python script to be executed by manage.py shell
# It finds customers with no orders in the last year, deletes them,
# and prints the count of deleted customers.
PYTHON_SCRIPT="
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer, Order

one_year_ago = timezone.now() - timedelta(days=365)

# Find IDs of customers who have placed an order in the last year
active_customer_ids = Order.objects.filter(date_ordered__gte=one_year_ago).values_list('customer_id', flat=True).distinct()

# Identify customers to be deleted by excluding the active ones
customers_to_delete = Customer.objects.exclude(id__in=active_customer_ids)

# Get the count and delete them
deleted_count = customers_to_delete.count()
customers_to_delete.delete()

print(deleted_count)
"

# Execute the python script within the django shell and capture the output
DELETED_COUNT=$(cd "$PROJECT_ROOT" && python manage.py shell -c "$PYTHON_SCRIPT")

# Log the result with a timestamp
echo "$(date): Deleted ${DELETED_COUNT} inactive customers." >> /tmp/customer_cleanup_log.txt
