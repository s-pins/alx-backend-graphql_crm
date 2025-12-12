import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.core.exceptions import ValidationError
from graphql import GraphQLError
from django.db import transaction
from phonenumber_field.phonenumber import to_python
from graphene_django.filter import DjangoFilterConnectionField
from .filters import CustomerFilter, ProductFilter, OrderFilter

# Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")
        interfaces = (graphene.relay.Node,)

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        interfaces = (graphene.relay.Node,)

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount")
        interfaces = (graphene.relay.Node,)

# Queries
class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter)
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter)
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter)
    
    customer_by_id = graphene.Field(CustomerType, id=graphene.Int(required=True))
    product_by_id = graphene.Field(ProductType, id=graphene.Int(required=True))
    order_by_id = graphene.Field(OrderType, id=graphene.Int(required=True))

    def resolve_customer_by_id(root, info, id):
        return Customer.objects.get(pk=id)
    
    def resolve_product_by_id(root, info, id):
        return Product.objects.get(pk=id)
    
    def resolve_order_by_id(root, info, id):
        return Order.objects.get(pk=id)

# Inputs
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        if Customer.objects.filter(email=input.email).exists():
            raise GraphQLError("Email already exists.")
        
        phone_number = None
        if input.phone:
            try:
                phone_number = to_python(input.phone)
                if not phone_number.is_valid():
                    raise GraphQLError("Invalid phone number.")
            except Exception:
                raise GraphQLError("Invalid phone number format.")

        customer = Customer(name=input.name, email=input.email)
        if phone_number:
            customer.phone = phone_number
        customer.save()
        
        return CreateCustomer(customer=customer, message="Customer created successfully.")

class BulkCustomerError(graphene.ObjectType):
    index = graphene.Int()
    field = graphene.String()
    message = graphene.String()

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(BulkCustomerError)

    @staticmethod
    def mutate(root, info, input):
        created_customers = []
        error_list = []
        
        with transaction.atomic():
            for i, customer_data in enumerate(input):
                if Customer.objects.filter(email=customer_data.email).exists():
                    error_list.append(BulkCustomerError(index=i, field="email", message=f"Email {customer_data.email} already exists."))
                    continue
                
                phone_number = None
                if customer_data.phone:
                    try:
                        phone_number = to_python(customer_data.phone)
                        if not phone_number.is_valid():
                            error_list.append(BulkCustomerError(index=i, field="phone", message="Invalid phone number."))
                            continue
                    except Exception:
                        error_list.append(BulkCustomerError(index=i, field="phone", message="Invalid phone number format."))
                        continue
                
                customer = Customer(name=customer_data.name, email=customer_data.email)
                if phone_number:
                    customer.phone = phone_number
                customer.save()
                created_customers.append(customer)
        
        return BulkCreateCustomers(customers=created_customers, errors=error_list)

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    @staticmethod
    def mutate(root, info, input):
        if input.price <= 0:
            raise GraphQLError("Price must be positive.")
        if input.stock and input.stock < 0:
            raise GraphQLError("Stock cannot be negative.")
        
        product = Product.objects.create(**input)
        return CreateProduct(product=product)

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    @staticmethod
    def mutate(root, info, input):
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            raise GraphQLError("Invalid customer ID.")

        if not input.product_ids:
            raise GraphQLError("At least one product must be selected.")

        products = []
        for pid in input.product_ids:
            try:
                product = Product.objects.get(pk=pid)
                products.append(product)
            except Product.DoesNotExist:
                raise GraphQLError(f"Invalid product ID: {pid}")

        order = Order.objects.create(customer=customer)
        order.products.set(products)
        order.calculate_total_amount()
        
        return CreateOrder(order=order)

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
