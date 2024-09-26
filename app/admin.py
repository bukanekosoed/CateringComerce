from flask import Blueprint, render_template,request, redirect,send_file,flash,url_for,abort
from .models import Kategori,Produk
from mongoengine.errors import NotUniqueError,ValidationError
from werkzeug.utils import secure_filename
from gridfs.errors import NoFile
import io
from .decorators import login_required, admin_required


admin_bp = Blueprint('admin', __name__)
@admin_bp.before_request
@login_required
@admin_required
def before_request():
    # This function will be executed before every request to ensure user is logged in and is an admin
    pass

@admin_bp.route('/')
def index():
    return render_template('admin/index.html',kategoris = Kategori.objects.all())

################################## Produk ###############################
@admin_bp.route('/produk')
def produk():
    page = request.args.get('page', 1, type=int)  # Get the current page number from the query string, default to 1
    per_page = 10  # Set the number of items per page
    total_produks = Produk.objects.count()  # Get the total count of items
    
    paginated_produks = Produk.objects.skip((page - 1) * per_page).limit(per_page)
    

    return render_template('admin/produk.html',
                           produk=paginated_produks,
                           total_produks=total_produks,
                           page=page, per_page=per_page,
                           kategoris = Kategori.objects.all())

@admin_bp.route('/produk/tambah-produk' , methods = ['GET', 'POST'])
def tambah_produk():
    if request.method == 'POST':
        nama = request.form['productTitle']
        # deskripsi = request.form['productDesc']
        gambar = request.files['productImg']
        harga = int(request.form['productPrice'])
        minPembelian = int(request.form['minPembelian'])
        kategori = request.form['productCategory']
        variants = [variant for variant in request.form.getlist('variant_name[]') if variant.strip()]

        existing_product = Produk.objects(produkNama=nama).first()
        if existing_product:
            flash('Nama produk sudah ada, gunakan nama lain.', 'danger')
            return redirect(url_for('admin.tambah_produk'))
        
        product = Produk(
            produkNama=nama,
            minPembelian = minPembelian,
            kategori=kategori,
            produkHarga=harga,
            variantsNama=variants
        )
        
        product.save()
        
        if gambar:
            filename = secure_filename(gambar.filename)
            product.produkGambar.put(gambar, content_type=gambar.content_type)
            product.save()
        flash('Produk berhasil ditambahkan!', 'success')
        return redirect(url_for('admin.produk'))
        

    return render_template('admin/tambah_produk.html',
                           kategoris = Kategori.objects.all())


@admin_bp.route('/produk/edit/<produk_id>', methods=['POST'])
def edit_produk(produk_id):
    produk = Produk.objects.get(id=produk_id)
    produk.produkNama = request.form.get('produkNama', produk.produkNama)
    produk.produkHarga = request.form.get('produkHarga', produk.produkHarga)
    produk.minPembelian = request.form.get('minPembelian', produk.minPembelian)
    produk.kategori = Kategori.objects.get(id=request.form.get('productCategory'))
    produk.variantsNama  = [variant for variant in request.form.getlist('variant_name[]') if variant.strip()]
    if 'productImg' in request.files:
        produkGambar = request.files['productImg']
        if produkGambar and produkGambar.filename != '':
            # Remove the old image if it exists
            if produk.produkGambar:
                try:
                    produk.produkGambar.delete()
                except Exception as e:
                    flash(f"Error deleting old image: {str(e)}", "warning")

            # Save the new image
            try:
                produk.produkGambar.put(produkGambar, content_type=produkGambar.content_type)
            except Exception as e:
                flash(f"Error saving new image: {str(e)}", "danger")

    try:
        produk.save()
        flash("Produk berhasil diperbarui!", "success")
    except (NotUniqueError, ValidationError):
        flash("Nama produk sudah ada, gunakan nama lain.", "danger")
        return redirect(url_for('admin.produk'))
    return redirect(url_for('admin.produk'))

@admin_bp.route('/produk/delete/<produk_id>', methods=['POST'])
def delete_produk(produk_id):
    produk = Produk.objects(id=produk_id).first()
    
    # Hapus gambar dari GridFS jika ada
    if produk.produkGambar:
        produk.produkGambar.delete()
    
    # Hapus kategori
    produk.delete()

    flash('Menu dan gambar berhasil dihapus!', 'success')
    return redirect(url_for('admin.produk'))
######################### Kategori #########################################
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
    kategori_data = []

    for kategori in kategoris:
        total_menu = Produk.objects(kategori=kategori.id).count()  # Count the number of products in this category
        kategori_data.append({
            'kategori': kategori,
            'total_menu': total_menu,
        })
    return render_template('admin/kategori.html',kategoris=kategori_data)

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

@admin_bp.route('/kategori/delete/<kategori_id>', methods=['POST'])
def delete_kategori(kategori_id):
    kategori = Kategori.objects(id=kategori_id).first()
    
    if not produk:
        abort(404)
    else :
        
    # Hapus gambar dari GridFS jika ada
        if kategori.kategoriGambar:
            kategori.kategoriGambar.delete()
        
        # Set kategori ke null untuk semua produk yang memiliki kategori ini
        Produk.objects(kategori=kategori).update(set__kategori=None)
        
        # Hapus kategori
        kategori.delete()
    
        flash('Kategori dan gambar berhasil dihapus!', 'success')
    return redirect(url_for('admin.kategori'))

