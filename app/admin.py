from flask import Blueprint, render_template,request, redirect,jsonify,flash,url_for,abort,session, send_file
import gridfs
from .models import Kategori,Produk,Orders,Users,Notification,News
from mongoengine.errors import NotUniqueError,ValidationError
from werkzeug.utils import secure_filename
from gridfs.errors import NoFile
from math import ceil
from collections import defaultdict
from twilio.rest import Client
import os
from .decorators import login_required, admin_required
from datetime import datetime
from babel.dates import format_datetime
from bson import ObjectId

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_SANDBOX_NUMBER = os.getenv("TWILIO_WHATSAPP_SANDBOX_NUMBER")

# Inisialisasi Twilio Client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

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
    
@admin_bp.route('/produk/tambah-produk', methods=['GET', 'POST'])
def tambah_produk():
    if request.method == 'POST':
        nama = request.form['productTitle']
        gambar = request.files['productImg']
        harga = int(request.form['productPrice'])
        minPembelian = int(request.form['minPembelian'])
        kategori = request.form['productCategory']
        variants = [variant.strip() for variant in request.form.getlist('variant_name[]') if variant.strip()]

        old_data = {
            'productTitle': nama,
            'productPrice': harga,
            'minPembelian': minPembelian,
            'productCategory': kategori,
            'variant_name': variants
        }

        # Validasi harga dan kuantitas
        if harga <= 0:
            flash('Harga produk tidak boleh kurang dari atau sama dengan 0.', 'danger')
            session['old_data'] = old_data
            session['old_image_id'] = session.get('old_image_id', None)  # Simpan gambar lama ke session
            return redirect(url_for('admin.tambah_produk'))

        if minPembelian < 1:
            flash('Kuantitas minimal adalah 1.', 'danger')
            session['old_data'] = old_data
            session['old_image_id'] = session.get('old_image_id', None)  # Simpan gambar lama ke session
            return redirect(url_for('admin.tambah_produk'))

        # Validasi apakah produk sudah ada
        existing_product = Produk.objects(produkNama=nama).first()
        if existing_product:
            flash('Nama produk sudah ada, gunakan nama lain.', 'danger')
            session['old_data'] = old_data
            session['old_image_id'] = session.get('old_image_id', None)  # Simpan gambar lama ke session
            return redirect(url_for('admin.tambah_produk'))

        # Menyimpan produk baru
        product = Produk(
            produkNama=nama,
            minPembelian=minPembelian,
            kategori=kategori,
            produkHarga=harga,
            variantsNama=variants
        )
        product.save()

        # Menyimpan gambar produk jika ada
        if gambar:
            filename = secure_filename(gambar.filename)
            fs = gridfs.GridFS(product.db)  # Menggunakan GridFS pada database produk yang digunakan
            file_id = fs.put(gambar, filename=filename, content_type=gambar.content_type)  # Menyimpan gambar

            # Menyimpan ID gambar ke field produkGambar
            product.produkGambar = file_id
            product.save()

            # Menyimpan ID gambar dalam session untuk old image
            session['old_image_id'] = product.produkGambar

        flash('Produk berhasil ditambahkan!', 'success')
        session.pop('old_data', None)  # Hapus old_data setelah berhasil
        session.pop('old_image_id', None)  # Hapus old_image_id setelah berhasil
        return redirect(url_for('admin.produk'))

    # Jika tidak ada data lama, ambil old_data dan old_image_id dari session
    old_data = session.get('old_data', None)
    old_image_id = session.get('old_image_id', None)

    return render_template('admin/tambah_produk.html',
                           kategoris=Kategori.objects.all(),
                           old_data=old_data,
                           old_image_id=old_image_id)



@admin_bp.route('/produk/edit/<produk_id>', methods=['POST'])
def edit_produk(produk_id):
    try:
        produk = Produk.objects.get(id=produk_id)
    except Produk.DoesNotExist:
        flash('Produk tidak ditemukan.', 'danger')
        return redirect(url_for('admin.produk'))

    produk.produkNama = request.form.get('produkNama', produk.produkNama)
    produk.produkHarga = float(request.form.get('produkHarga', produk.produkHarga))
    produk.minPembelian = int(request.form.get('minPembelian', produk.minPembelian))
    produk.kategori = Kategori.objects.get(id=request.form.get('productCategory'))
    produk.variantsNama  = [variant for variant in request.form.getlist('variant_name[]') if variant.strip()]

    # Validating the input
    if produk.produkHarga <= 0:
        flash('Harga produk tidak boleh kurang dari atau sama dengan 0.', 'danger')
        return redirect(url_for('admin.produk', produk_id=produk_id))

    if produk.minPembelian < 1:
        flash('Kuantitas minimal adalah 1.', 'danger')
        return redirect(url_for('admin.produk', produk_id=produk_id))

    # Handling image upload
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
        return redirect(url_for('admin.edit_produk', produk_id=produk_id))

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

    pendapatan_per_kategori = defaultdict(int)

    # Iterasi semua pesanan
    for order in Orders.objects(payment_status="berhasil"):
        for item in order.items:
            # Cari kategori produk yang sesuai dengan item
            produk = Produk.objects.get(id=item.product.id)  # Pastikan `item.produk.id` mengarah pada produk yang benar
            kategori = produk.kategori  # Ambil kategori produk
            pendapatan_per_item = item.quantity * produk.produkHarga
            # Tambahkan pendapatan grand_total ke kategori yang sesuai
            pendapatan_per_kategori[kategori.id] += pendapatan_per_item

    # Menyusun data kategori dengan total pendapatan
    for kategori in kategoris:
        total_menu = Produk.objects(kategori=kategori.id).count()
        total_pendapatan = pendapatan_per_kategori.get(kategori.id, 0)  # Dapatkan pendapatan kategori, default 0

        kategori_data.append({
            'kategori': kategori,
            'total_menu': total_menu,
            'total_pendapatan': total_pendapatan
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
            # Update status pesanan
            order.update(set__order_status=new_status)  
            flash("Status pesanan berhasil diperbarui!", "success")

            # Buat notifikasi untuk pengguna
            if order.user:
                user = Users.objects(id=order.user.id).first()
                if user:
                    # Membuat entri notifikasi baru
                    notification = Notification(
                        user=user,
                        order_id=str(order.order_id),  # Menyimpan order_id sebagai string
                        title="Status Pesanan Diperbarui",
                        message=f"Status pesanan Anda telah diperbarui menjadi: {new_status}",
                        created_at=datetime.utcnow(),
                        is_read=False
                    )
                    notification.save()  # Simpan notifikasi ke database

                    # Kirim pesan WhatsApp hanya jika status pesanan adalah 'dikirim'
                    if new_status == "dikirim":
                        user_phone = user.phone  # Nomor telepon pengguna (pastikan sudah dalam format internasional)
                        if user_phone:
                            # Konversi nomor telepon ke format internasional
                            if user_phone.startswith('0'):
                                user_phone = '+62' + user_phone[1:]
                            
                            # Tentukan pesan WhatsApp berdasarkan opsi pengiriman
                            if order.delivery_option == "delivery":
                                message = (f"Halo, { user.name }!\n\n"
                                           f"Pesanan Anda dengan ID *{order.order_id}* sedang dikirim ke *{ order.user.addresses[order.address_index].full_address}*\n\n" 
                                           f"Terima kasih telah mempercayai *Langgeng Catering*. 😊")
                            elif order.delivery_option == "pickup":
                                message = (f"Halo, { user.name }!\n\n"
                                           f"Pesanan Anda dengan ID *{ order.order_id }* sudah siap untuk diambil. Silakan datang ke toko kami untuk mengambil pesanan Anda. Kami sangat menghargai kepercayaan Anda kepada *Langgeng Catering* dan senang dapat melayani Anda.\n\n"
                                           f"Klik tautan berikut untuk melihat lokasi kami di peta:\n"  
                                           f"https://maps.app.goo.gl/D9uSatv49dp1adYF7  \n\n"
                                           f"Terima kasih, dan kami tunggu kedatangan Anda! 😊")

                            # Kirim pesan WhatsApp melalui Twilio
                            try:
                                twilio_client.messages.create(
                                    body=message,  # Isi pesan
                                    from_='whatsapp:' + TWILIO_WHATSAPP_SANDBOX_NUMBER,  # Nomor Twilio WhatsApp Sandbox
                                    to='whatsapp:' + user_phone  # Nomor pengguna yang ingin dikirimi pesan
                                )
                            except Exception as e:
                                flash(f"Gagal mengirim pesan WhatsApp: {e}", "warning")
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




@admin_bp.route('/laporan-penjualan', methods=['GET'])
def laporan():
    # Ambil parameter dari request
    year_filter = request.args.get('year_filter')
    month_filter = request.args.get('month_filter')
    # Ambil parameter halaman dari query string, default halaman pertama
    page = int(request.args.get('page', 1))
    per_page = 10  # Jumlah item per halaman

    # Ambil data produk dengan paginasi
    produk_data_query = Produk.objects().order_by('produkNama')
    total_items = produk_data_query.count()
    produk_data_paginated = produk_data_query.skip((page - 1) * per_page).limit(per_page)

    
    # Ambil semua kategori
    kategoris = Kategori.objects.all()
    produk_data = []
    kategori_data = []
    total_pendapatan_all = 0

    # Struktur untuk menyimpan pendapatan per kategori dan per produk
    pendapatan_per_kategori = defaultdict(int)
    pendapatan_per_produk = defaultdict(int)
    kuantitas_per_produk = defaultdict(int)


    # Iterasi semua pesanan dengan status pembayaran 'berhasil' dan sesuai rentang tanggal
    for order in Orders.objects(payment_status="berhasil"):
        
        # Filter berdasarkan tahun dan bulan
        if year_filter and order.transaction_time.year != int(year_filter):
            continue
        if month_filter and order.transaction_time.month != int(month_filter):
            continue

        for item in order.items:
            # Cari produk yang sesuai dengan item
            produk = Produk.objects.get(id=item.product.id)  # Pastikan `item.product.id` mengarah pada produk yang benar
            
            # Ambil kategori produk
            kategori = produk.kategori
            
            # Hitung pendapatan per item (quantity * harga produk)
            pendapatan_per_item = item.quantity * produk.produkHarga
            
            # Tambahkan pendapatan per item ke kategori dan produk yang sesuai
            pendapatan_per_kategori[kategori.id] += pendapatan_per_item
            pendapatan_per_produk[produk.id] += pendapatan_per_item
            
            # Tambahkan kuantitas produk yang dipesan
            kuantitas_per_produk[produk.id] += item.quantity
            total_pendapatan_all += pendapatan_per_item
    # Menyusun data kategori dengan total pendapatan
    for kategori in kategoris:
        total_menu = Produk.objects(kategori=kategori.id).count()
        total_pendapatan = pendapatan_per_kategori.get(kategori.id, 0)  # Dapatkan pendapatan kategori, default 0

        kategori_data.append({
            'kategori': kategori,
            'total_menu': total_menu,
            'total_pendapatan': total_pendapatan
        })

    # Menyusun data produk dengan total pendapatan dan kuantitas
    for produk in Produk.objects.all():
        total_pendapatan = pendapatan_per_produk.get(produk.id, 0)  # Dapatkan pendapatan produk, default 0
        total_kuantitas = kuantitas_per_produk.get(produk.id, 0)  # Dapatkan total kuantitas produk, default 0
        
        produk_data.append({
            'produk': produk,
            'quantity': total_kuantitas,  # Menampilkan kuantitas total yang dipesan
            'total_pendapatan': total_pendapatan,
        })

    # Hitung jumlah halaman menggunakan ceil
    total_pages = ceil(total_items / per_page)
    # Kembalikan data ke template untuk ditampilkan
    return render_template('admin/laporan.html', kategori_data=kategori_data, produk_data=produk_data,semua_pendapatan=total_pendapatan_all,page=page,
        total_pages=total_pages)


@admin_bp.route('/revenue/<int:year>')
def revenue(year):
    monthly_revenue = []
    for month in range(1, 13):  # Loop through all months
        total_revenue, _ = Orders.get_monthly_revenue_and_change(month, year)
        monthly_revenue.append(total_revenue)

    return jsonify(monthly_revenue)

@admin_bp.route('/news')
def daftar_news():
    news = News.objects.all()  # Mengambil semua berita dari database
    return render_template('admin/news.html', news=news)


@admin_bp.route('/news/tambah-news', methods=['GET', 'POST'])
def tambah_news():
    if request.method == 'POST':
        judul = request.form['newsTitle']
        deskripsi = request.form['newsDesc']
        gambar = request.files['newsImg']
        

        # Cek apakah judul berita sudah ada
        existing_news = News.objects(title=judul).first()
        if existing_news:
            flash('Judul berita sudah ada, gunakan judul lain.', 'danger')
            return redirect(url_for('admin.tambah_news'))
        
        # Buat objek News
        news = News(
            title=judul,
            description=deskripsi,
        )
        news.save()

        # Simpan gambar jika ada
        if gambar:
            filename = secure_filename(gambar.filename)
            news.image.put(gambar, content_type=gambar.content_type)
            news.save()
        
        flash('Berita berhasil ditambahkan!', 'success')
        return redirect(url_for('admin.daftar_news'))

    return render_template('admin/add_news.html',
                           kategoris=Kategori.objects.all())

@admin_bp.route('/news/edit-news/<news_id>', methods=['GET', 'POST'])
def edit_news(news_id):
    news = News.objects(id=news_id).first()
    if not news:
        flash('Berita tidak ditemukan.', 'danger')
        return redirect(url_for('admin.daftar_news'))

    if request.method == 'POST':
        judul = request.form['newsTitle']
        deskripsi = request.form['newsDesc']
        gambar = request.files.get('newsImg', None)

        # Cek apakah judul sudah digunakan oleh berita lain
        existing_news = News.objects(title=judul, id__ne=news.id).first()
        if existing_news:
            flash('Judul berita sudah ada, gunakan judul lain.', 'danger')
            return redirect(url_for('admin.edit_news', news_id=news.id))

        # Update data berita
        news.title = judul
        news.description = deskripsi

        # Update gambar jika ada
        if gambar:
            filename = secure_filename(gambar.filename)
            news.image.replace(gambar, content_type=gambar.content_type)
        
        news.save()

        flash('Berita berhasil diperbarui!', 'success')
        return redirect(url_for('admin.daftar_news'))

    return render_template('admin/edit_news.html', news=news)

@admin_bp.route('/news/delete-news/<news_id>', methods=['POST'])
def delete_news(news_id):
    news = News.objects(id=news_id).first()
    if not news:
        flash('Berita tidak ditemukan.', 'danger')
        return redirect(url_for('admin.daftar_news'))

    news.delete()
    flash('Berita berhasil dihapus!', 'success')
    return redirect(url_for('admin.daftar_news'))
