from mongoengine import (connect, Document, StringField, 
                         ImageField, IntField, EmbeddedDocumentField,
                         EmbeddedDocument, ReferenceField,
                         CASCADE, ListField, EmailField,
                         FloatField, DateTimeField
                        )
from dotenv import load_dotenv
import os
from datetime import datetime
import pytz
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
db_name = os.getenv('DB_NAME')
connect(db=db_name, host=mongo_uri)

gmt_plus_7 = pytz.timezone('Asia/Jakarta')
def get_current_time():
    return datetime.now(gmt_plus_7)
class Address(EmbeddedDocument):
    latitude = FloatField(required=True)
    longitude = FloatField(required=True)
    address_type = StringField(required=True)
    street_name = StringField(required=True)
    rt_rw = StringField(required=True)
    village = StringField(required=True)
    sub_district = StringField(required=True)
    district = StringField(required=True)
    full_address = StringField(required=True)
    plus_code = StringField(required=True)

class Kategori(Document):
    kategoriNama = StringField(required=True, unique=True)
    kategoriGambar = ImageField()
    
class Produk(Document):
    produkNama = StringField(required=True, unique=True)
    produkGambar = ImageField()
    produkHarga = IntField(required=True, min_value=0)
    minPembelian = IntField(required=True, min_value=0)
    kategori = ReferenceField(Kategori, reverse_delete_rule=CASCADE)
    variantsNama = ListField(StringField())
    
def search_products_by_name(query, page, limit):
    offset = (page - 1) * limit
    return Produk.objects(produkNama__icontains=query).skip(offset).limit(limit)

def count_products_by_name(query):
    return Produk.objects(produkNama__icontains=query).count()

    
class Users(Document):
    name = StringField(required=True, max_length=50)
    email = EmailField(required=True, unique=True)
    phone = StringField(required=True, max_length=20, min_length=11)
    password_hash = StringField(required=True)
    profile_image = ImageField()
    addresses = ListField(EmbeddedDocumentField(Address))
    created_at = DateTimeField(default=datetime.utcnow)  # Add this line

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_total_users(cls):
        return cls.objects.count()

    @classmethod
    def get_monthly_user_increase(cls, month=None, year=None):
        if month and year:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            return cls.objects(created_at__gte=start_date, created_at__lt=end_date).count()
        return 0
    
class Admin(Document):
    name = StringField(required=True, max_length=50)
    email = EmailField(required=True, unique=True)
    password_hash = StringField(required=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class CartItem(EmbeddedDocument):
    product = ReferenceField(Produk, required=True)
    quantity = IntField(required=True, min_value=1)
    variant = StringField()  # Optional field

class Cart(Document):
    user = ReferenceField(Users, required=True, unique=True)
    items = ListField(EmbeddedDocumentField(CartItem))

    def get_cart_total(self):
        total = 0
        for item in self.items:
            total += item.product.produkHarga * item.quantity
        return total

    def get_grand_total(self):
        vat = self.get_cart_total() * 0.11
        return self.get_cart_total() + vat


class Orders(Document):
    user = ReferenceField(Users, required=True)
    order_id = StringField()
    items = ListField(EmbeddedDocumentField(CartItem))
    grand_total = IntField()
    delivery_option = StringField()
    shipping_cost = IntField()
    vat = IntField()
    delivery_date = StringField()
    transaction_time = DateTimeField(default=get_current_time)
    transaction_id = StringField()
    payment_type = StringField()
    payment_status = StringField(default="menunggu")
    expiry_time = DateTimeField()
    token = StringField()
    order_status = StringField()
    address_index=IntField  (required=True)

    @classmethod
    def get_total_paid(cls, month=None, year=None):
        filter_conditions = {'payment_status': 'berhasil'}

        if month and year:
            start_date = gmt_plus_7.localize(datetime(year, month, 1))
            if month == 12:
                end_date = gmt_plus_7.localize(datetime(year + 1, 1, 1))
            else:
                end_date = gmt_plus_7.localize(datetime(year, month + 1, 1))

            # Convert to UTC
            start_date_utc = start_date.astimezone(pytz.utc)
            end_date_utc = end_date.astimezone(pytz.utc)

            filter_conditions['transaction_time__gte'] = start_date_utc
            filter_conditions['transaction_time__lt'] = end_date_utc

        transactions = cls.objects(**filter_conditions)

        total = sum(transaction.grand_total - transaction.vat - transaction.shipping_cost for transaction in transactions)
        return total

    @classmethod
    def get_monthly_revenue_and_change(cls, month=None, year=None):
        total_current = cls.get_total_paid(month=month, year=year)

        if month == 1:
            previous_month = 12
            previous_year = year - 1
        else:
            previous_month = month - 1
            previous_year = year

        total_previous = cls.get_total_paid(month=previous_month, year=previous_year)
        percentage_change = cls.calculate_percentage_change(total_current, total_previous)

        return total_current, percentage_change

    @classmethod
    def get_total_orders(cls, month=None, year=None):
        """Get the total number of orders."""
        filter_conditions = {}

        if month and year:
            start_date = gmt_plus_7.localize(datetime(year, month, 1))
            if month == 12:
                end_date = gmt_plus_7.localize(datetime(year + 1, 1, 1))
            else:
                end_date = gmt_plus_7.localize(datetime(year, month + 1, 1))

            # Convert to UTC
            start_date_utc = start_date.astimezone(pytz.utc)
            end_date_utc = end_date.astimezone(pytz.utc)

            filter_conditions['transaction_time__gte'] = start_date_utc
            filter_conditions['transaction_time__lt'] = end_date_utc

        total_orders = cls.objects(**filter_conditions).count()
        return total_orders

    @classmethod
    def get_monthly_orders_and_change(cls, month=None, year=None):
        total_current = cls.get_total_orders(month=month, year=year)

        if month == 1:
            previous_month = 12
            previous_year = year - 1
        else:
            previous_month = month - 1
            previous_year = year

        total_previous = cls.get_total_orders(month=previous_month, year=previous_year)
        percentage_change = cls.calculate_percentage_change(total_current, total_previous)

        return total_current, percentage_change

    @staticmethod
    def calculate_percentage_change(current_value, previous_value):
        if previous_value == 0:
            if current_value == 0:
                return 0.0
            else:
                return 100.0

        change = current_value - previous_value
        percentage_change = (change / previous_value) * 100
        return round(percentage_change, 2)




def get_all_categories():
    return Kategori.objects()

def get_products_by_category(kategori_id, page, limit):
    skip = (page - 1) * limit
    return Produk.objects(kategori=kategori_id).skip(skip).limit(limit)

def get_all_products(page, limit):
    skip = (page - 1) * limit
    return Produk.objects().skip(skip).limit(limit)

def get_product_count_by_category(kategori_id):
    return Produk.objects(kategori=kategori_id).count()

def get_total_product_count():
    return Produk.objects().count()
