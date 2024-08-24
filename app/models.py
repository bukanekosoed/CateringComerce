from mongoengine import connect, Document, StringField, ImageField, IntField,ReferenceField,CASCADE,ListField,EmailField
from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
db_name = os.getenv('DB_NAME')
connect(db=db_name, host=mongo_uri)

class Kategori(Document):
    kategoriNama = StringField(required=True,unique=True)
    kategoriGambar = ImageField()
    
class Produk(Document):
    produkNama = StringField(required=True, unique=True)
    # produkDeskripsi = StringField()
    produkGambar = ImageField()
    produkHarga = IntField(required=True, min_value=0)
    minPembelian = IntField(required=True, min_value=0)
    kategori = ReferenceField(Kategori, reverse_delete_rule=CASCADE)
    variantsNama =ListField(StringField())
    
class Users(Document):
    name = StringField(required=True, max_length=50)
    email = EmailField(required=True, unique=True)
    phone = StringField(required=True, max_length=20,min_length=11)
    password_hash = StringField(required=True)
    profile_image = ImageField()
    
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


