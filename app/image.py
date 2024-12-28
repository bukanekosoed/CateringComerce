from flask import Blueprint, send_file, abort, current_app, session
import io
from .models import Kategori, Produk, News

image_bp = Blueprint('image', __name__)

@image_bp.route('/image/<image_id>')
def image(image_id):
    try:
        # Cek apakah ada old_image_id di session
        old_image_id = session.get('old_image_id', None)
        if old_image_id:
            # Jika ada, kita coba ambil gambar berdasarkan ID tersebut
            produk = Produk.objects(id=old_image_id).first()
            if produk and produk.produkGambar:
                image_stream = io.BytesIO(produk.produkGambar.read())
                return send_file(image_stream, mimetype=produk.produkGambar.content_type)

        # Try to find the image in Kategori
        kategori = Kategori.objects(id=image_id).first()
        if kategori and kategori.kategoriGambar:
            image_stream = io.BytesIO(kategori.kategoriGambar.read())
            return send_file(image_stream, mimetype=kategori.kategoriGambar.content_type)

        # If not found in Kategori, try to find it in Produk
        produk = Produk.objects(id=image_id).first()
        if produk and produk.produkGambar:
            image_stream = io.BytesIO(produk.produkGambar.read())
            return send_file(image_stream, mimetype=produk.produkGambar.content_type)

        # Try to find the image in News
        news = News.objects(id=image_id).first()
        if news and news.image:
            image_stream = io.BytesIO(news.image.read())
            return send_file(image_stream, mimetype=news.image.content_type)

        # If the image is not found in either collection, return 404
        abort(404, description="Image not found")
    
    except Exception as e:
        current_app.logger.error(f"Error serving image {image_id}: {e}")
        abort(500, description=str(e))
