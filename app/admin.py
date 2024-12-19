from flask import Blueprint, render_template,request, redirect,jsonify,flash,url_for,abort,make_response, send_file
from .models import Kategori,Produk,Orders,Users
from mongoengine.errors import NotUniqueError,ValidationError
from werkzeug.utils import secure_filename
from gridfs.errors import NoFile
from math import ceil
import io
from openpyxl import Workbook
from .decorators import login_required, admin_required
from datetime import datetime
from babel.dates import format_datetime
from bson import ObjectId


admin_bp = Blueprint('admin', __name__)
@admin_bp.before_request
@login_required
@admin_required
def before_request():
    # This function will be executed before every request to ensure user is logged in and is an admin
    pass

@admin_bp.route('/')
def index():
    now = datetime.now()
    month = request.args.get('month', now.month, type=int)
    year = request.args.get('year', now.year, type=int)

    total_revenue, percentage_change = Orders.get_monthly_revenue_and_change(month=month, year=year)
    total_orders, orders_change = Orders.get_monthly_orders_and_change(month=month, year=year)
    # Fetch total users
    total_users = Users.get_total_users()
    # Fetch monthly user increase
    monthly_increase = Users.get_monthly_user_increase(month=month, year=year)
    return render_template('admin/index.html',kategoris = Kategori.objects.all(),
                           total_revenue=total_revenue, 
                           percentage_change=percentage_change, 
                           total_users=total_users,
                           monthly_increase=monthly_increase,
                           total_orders=total_orders,
                           orders_change=orders_change,
                           month=month, 
                           year=year)

################################## Produk ###############################
@admin_bp.route('/produk', methods=['GET'])
def produk():
    search_query = request.args.get('search', '')  # Pencarian berdasarkan nama produk
    category_filter = request.args.get('categoryFilter', '')  # Filter berdasarkan kategori
    page = request.args.get('page', 1, type=int)  # Get current page, default to 1 if not specified
    per_page = 10  # Jumlah item per halaman

    # Membuat query dasar
    query = Produk.objects.order_by('-created_at')  # Urutkan berdasarkan produk terbaru

    # Pencarian berdasarkan nama produk
    if search_query:
        query = query.filter(produkNama__icontains=search_query)

    # Filter berdasarkan kategori (memastikan category_filter adalah ObjectId)
    if category_filter:
        query = query.filter(kategori=ObjectId(category_filter))

    # Hitung jumlah total produk yang sesuai filter
    total_produks = query.count()

    # Paginasi query
    paginated_produks = query.skip((page - 1) * per_page).limit(per_page)

    # Ambil daftar kategori untuk dropdown filter
    kategoris = Kategori.objects.all()

    # Render template dengan data produk, kategori, dan lainnya
    return render_template(
        'admin/produk.html',
        produk=paginated_produks,
        total_produks=total_produks,
        page=page,
        per_page=per_page,
        kategoris=kategoris,
        search_query=search_query,
        category_filter=category_filter
    )
    

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


@admin_bp.route('/pesanan', methods=['GET', 'POST'])
def pesanan():
    # Mendapatkan parameter filter dari query string
    status_filter = request.args.get('status')  # Filter berdasarkan status
    delivery_filter = request.args.get('delivery_option', None)
    date_start = request.args.get('date_start', None)  # Filter tanggal mulai
    date_end = request.args.get('date_end', None)      # Filter tanggal akhir
    page = request.args.get('page', default=1, type=int)  # Pagination, default halaman 1
    per_page = 10  # Jumlah data per halaman

    # Query dasar untuk Orders
    query = Orders.objects.order_by('-transaction_time')

    # Filter status pembayaran
    if status_filter:
        query = query.filter(payment_status=status_filter)

    # Filter opsi pengiriman
    if delivery_filter:
        query = query.filter(delivery_option=delivery_filter)

    # Filter tanggal pengiriman (delivery_date)
    if date_start:
        try:
            start_date = datetime.strptime(date_start, '%Y-%m-%d')
            start_date_str = start_date.strftime('%Y-%m-%d')  # Format sesuai dengan format di database
            query = query.filter(delivery_date__gte=f"{start_date_str} 00:00")  # Menambahkan jam 00:00
        except ValueError:
            pass  # Abaikan jika format tanggal salah

    if date_end:
        try:
            end_date = datetime.strptime(date_end, '%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')  # Format sesuai dengan format di database
            query = query.filter(delivery_date__lte=f"{end_date_str} 23:59")  # Menambahkan jam 23:59
        except ValueError:
            pass  # Abaikan jika format tanggal salah

    # Total jumlah pesanan untuk pagination
    total_orders = query.count()

    # Menghitung offset dan mendapatkan data
    orders = query.skip((page - 1) * per_page).limit(per_page)

    # Memformat tanggal dengan lokal Indonesia
    for order in orders:
        delivery_date = order['delivery_date']
        if isinstance(delivery_date, str):
            delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d %H:%M')
        formatted_date = format_datetime(delivery_date, format='EEEE, dd MMMM yyyy HH:mm', locale='id_ID')
        order['delivery_date'] = formatted_date

    # Proses POST untuk mengubah status pesanan
    if request.method == 'POST':
        order_id = request.form.get('order_id')  # Ambil order_id dari form
        new_status = request.form.get('order_status')  # Ambil status baru dari form

        # Validasi apakah status yang diterima sesuai dengan pilihan yang valid
        valid_statuses = ["sedang_diproses", "dikirim", "selesai"]
        if new_status not in valid_statuses:
            flash("Status pesanan tidak valid", "danger")
            return redirect(url_for('admin.pesanan'))  # Redirect kembali ke halaman pesanan

        # Cari pesanan berdasarkan order_id
        order = Orders.objects(id=order_id).first()
        if order:
            order.update(set__order_status=new_status)  # Update status pesanan
            flash("Status pesanan berhasil diperbarui!", "success")
        else:
            flash("Pesanan tidak ditemukan", "danger")

        return redirect(url_for('admin.pesanan'))  # Redirect kembali ke halaman pesanan

    # Total halaman untuk navigasi
    total_pages = ceil(total_orders / per_page)

    return render_template(
        'admin/pesanan.html',
        orders=orders,
        total_pages=total_pages,
        current_page=page,
        status_filter=status_filter,
        delivery_filter=delivery_filter,
        date_start=date_start,
        date_end=date_end
    )




@admin_bp.route('/user', methods=['GET'])
def user():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search', '')

    # Membuat query untuk menampilkan daftar user
    query = Users.objects()

    if search_query:
        query = query.filter(name__icontains=search_query)

    # Mengambil total user untuk pagination
    total_users = query.count()

    # Pagination
    paginated_users = query.skip((page - 1) * per_page).limit(per_page)

    return render_template('admin/user.html', 
                           users=paginated_users, 
                           total_users=total_users, 
                           page=page, 
                           per_page=per_page, 
                           search_query=search_query)

@admin_bp.route('/user/delete/<string:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        # Cari pengguna berdasarkan ID
        user = Users.objects.get(id=user_id)
        
        # Hapus pengguna
        user.delete()
        
        # Berikan pesan sukses
        flash(f'Pengguna {user.name} berhasil dihapus.', 'success')
    except Users.DoesNotExist:
        # Jika pengguna tidak ditemukan
        flash('Pengguna tidak ditemukan.', 'error')
    except Exception as e:
        # Tangani kesalahan lainnya
        flash(f'Kesalahan saat menghapus pengguna: {str(e)}', 'error')
    
    # Redirect kembali ke halaman daftar pengguna
    return redirect(url_for('admin.user'))


@admin_bp.route('/laporan-penjualan')
def laporan():
    return render_template('admin/laporan.html')

@admin_bp.route('/revenue/<int:year>')
def revenue(year):
    monthly_revenue = []
    for month in range(1, 13):  # Loop through all months
        total_revenue, _ = Orders.get_monthly_revenue_and_change(month, year)
        monthly_revenue.append(total_revenue)

    return jsonify(monthly_revenue)

