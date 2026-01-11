import datetime
from celery import shared_task
from django.db.models import Sum, Count
from crm.models import Customer, Order

LOG_FILE = "/tmp/crm_report_log.txt"

@shared_task
def generate_crm_report():
    """
    A Celery task that generates a weekly CRM report, calculating total
    customers, orders, and revenue using the Django ORM.
    """
    # Use the ORM to get aggregate data efficiently.
    customer_count = Customer.objects.count()
    order_count = Order.objects.count()
    
    # Use aggregate to calculate the sum of 'total_amount' across all orders.
    # The result is a dictionary, e.g., {'total_revenue': Decimal('123.45')}
    revenue_data = Order.objects.aggregate(total_revenue=Sum('total_amount'))
    total_revenue = revenue_data['total_revenue'] or 0 # Handle case with no orders.

    # Format the report line
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report_line = (
        f"{timestamp} - Report: {customer_count} customers, {order_count} orders, "
        f"${total_revenue:.2f} revenue\n"
    )

    # Append the report to the log file
    try:
        with open(LOG_FILE, "a") as log:
            log.write(report_line)
        return f"Report generated successfully: {report_line.strip()}"
    except IOError as e:
        # Handle potential file writing errors
        return f"Error writing to log file: {e}"
