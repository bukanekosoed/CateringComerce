from flask import Blueprint, render_template,request, redirect,send_file,flash,url_for
from .models import Kategori
from mongoengine.errors import NotUniqueError,ValidationError
from werkzeug.utils import secure_filename
from gridfs.errors import NoFile
import io

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def index():
    return render_template('admin/index.html',kategoris = Kategori.objects.all())

@admin_bp.route('/produk')
def produk():
    return render_template('admin/produk.html')

@admin_bp.route('/produk/tambah-produk')
def tambah_produk():
    
    return render_template('admin/tambah_produk.html',kategoris = Kategori.objects.all())

@admin_bp.route('/produk/kategori', methods=['GET','POST'])
def kategori():
    if request.method == 'POST':
        nama = request.form['kategoriNama']
        gambar = request.files['kategoriGambar']
        
        try:
            # Inisiasi objek kategori tanpa menyimpan ke database
            kategori = Kategori(kategoriNama=nama)

            # Validasi kategoriNama untuk memastikan unik
            kategori.validate()  # Ini akan melempar ValidationError jika kategoriNama tidak unik
            
            # Simpan kategori terlebih dahulu
            kategori.save()

            # Setelah kategori berhasil disimpan, baru upload gambar
            if gambar:
                filename = secure_filename(gambar.filename)
                kategori.kategoriGambar.put(gambar, content_type=gambar.content_type)
                kategori.save()  # Simpan lagi setelah gambar di-upload

            flash("Kategori berhasil ditambahkan!", "success")
            return redirect(request.url)
        
        except (NotUniqueError, ValidationError):
            flash("Nama kategori sudah ada, gunakan nama lain.", "danger")
            return redirect(request.url)
        
        except Exception as e:
            flash(f"Terjadi kesalahan: {str(e)}", "danger")
            return redirect(request.url)
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    kategoris = Kategori.objects.all()
    return render_template('admin/kategori.html',kategoris=kategoris)

@admin_bp.route('/image/<image_id>')
def image(image_id):
    
    try:
        kategori = Kategori.objects.get(id=image_id)
        image_stream = io.BytesIO(kategori.kategoriGambar.read())
        return send_file(image_stream, mimetype='image/jpeg')
    except Exception as e:
        return str(e)

@admin_bp.route('/edit_kategori/<kategori_id>', methods=['POST'])
def edit_kategori(kategori_id):
    kategori = Kategori.objects.get(id=kategori_id)
    try:
        kategori.kategoriNama = request.form['kategoriNama']

        if 'kategoriGambar' in request.files:
            kategoriGambar = request.files['kategoriGambar']
            if kategoriGambar:
                # Check if the category already has an image
                if kategori.kategoriGambar:
                    try:
                        # Remove the old image and its chunks
                        kategori.kategoriGambar.delete()
                    except NoFile:
                        pass  # If there's no file, we can ignore the error
                
                # Save the new image
                kategori.kategoriGambar.put(kategoriGambar, content_type=kategoriGambar.content_type)

        kategori.save()
    except (NotUniqueError, ValidationError):
            flash("Nama kategori sudah ada, gunakan nama lain.", "danger")
            return redirect(url_for('admin.kategori'))

    
    flash("Kategori berhasil diupdate!", "success")
    return redirect(url_for('admin.kategori'))

