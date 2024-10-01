from mongoengine import (connect, Document, StringField, 
                         ImageField, IntField, EmbeddedDocumentField,
                         EmbeddedDocument, ReferenceField,
                         CASCADE, ListField, EmailField,
                         FloatField,  DateTimeField
                        )
from dotenv import load_dotenv
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
db_name = os.getenv('DB_NAME')
connect(db=db_name, host=mongo_uri)

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
    
class Users(Document):
    name = StringField(required=True, max_length=50)
    email = EmailField(required=True, unique=True)
    phone = StringField(required=True, max_length=20, min_length=11)
    password_hash = StringField(required=True)
    profile_image = ImageField()
    addresses = ListField(EmbeddedDocumentField(Address))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
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
    user = ReferenceField(Users, required=True)  # Allow multiple orders per user
    order_id = StringField()
    items = ListField(EmbeddedDocumentField(CartItem))  # Menyimpan daftar item dalam format dictionary
    grand_total = IntField()
    delivery_option = StringField()
    shipping_cost = IntField()
    vat = IntField()
    delivery_date = StringField()
    created_at = DateTimeField(default=datetime.utcnow)  # Automatically store the timestamp when the order is created
    payment_status = StringField(default="pending")
    token = StringField()




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
