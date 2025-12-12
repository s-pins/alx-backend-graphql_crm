import random
from django.core.management.base import BaseCommand
from crm.models import Customer, Product, Order

class Command(BaseCommand):
    help = 'Seeds the database with initial data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting old data...")
        Order.objects.all().delete()
        Customer.objects.all().delete()
        Product.objects.all().delete()

        self.stdout.write("Creating new data...")

        # Create Customers
        customers = [
            Customer.objects.create(name='Alice', email='alice@example.com', phone='+1234567890'),
            Customer.objects.create(name='Bob', email='bob@example.com', phone='123-456-7890'),
            Customer.objects.create(name='Charlie', email='charlie@example.com'),
        ]

        # Create Products
        products = [
            Product.objects.create(name='Laptop', price=999.99, stock=10),
            Product.objects.create(name='Mouse', price=25.50, stock=50),
            Product.objects.create(name='Keyboard', price=75.00, stock=30),
            Product.objects.create(name='Monitor', price=300.00, stock=15),
        ]

        # Create Orders
        for customer in customers:
            num_orders = random.randint(1, 3)
            for _ in range(num_orders):
                order = Order.objects.create(customer=customer)
                num_products = random.randint(1, len(products))
                random_products = random.sample(products, num_products)
                order.products.set(random_products)
                order.calculate_total_amount()

        self.stdout.write(self.style.SUCCESS('Successfully seeded the database.'))
