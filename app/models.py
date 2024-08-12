from mongoengine import connect, Document, StringField, ImageField, DecimalField,ReferenceField,CASCADE
from dotenv import load_dotenv
import os

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
db_name = os.getenv('DB_NAME')
connect(db=db_name, host=mongo_uri)

class Kategori(Document):
    kategoriNama = StringField(required=True,unique=True)
    kategoriGambar = ImageField()
    
class Produk(Document):
    produkNama = StringField(required=True, unique=True)
    produkDeskripsi = StringField()
    produkHarga = DecimalField(required=True, min_value=0)
    kategori = ReferenceField(Kategori, reverse_delete_rule=CASCADE)