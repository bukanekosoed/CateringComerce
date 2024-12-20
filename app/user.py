from flask import Blueprint, render_template,request,redirect,flash,url_for,session,jsonify,make_response
import requests
from .models import (Kategori,Produk, get_products_by_category, 
                     get_all_categories, get_product_count_by_category, 
                     get_total_product_count,get_all_products,
                     Users, Cart,CartItem,Address,Orders, search_products_by_name,
                     count_products_by_name
                    )
from .decorators import login_required, user_required
from math import ceil
from mongoengine import DoesNotExist
from flask_login import current_user
import midtransclient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import pytz
from babel.dates import format_datetime
from midtransclient import Snap
from openlocationcode import openlocationcode as olc
import pdfkit
from pdfkit.configuration import Configuration

load_dotenv()
STORE_LATITUDE = os.getenv('STORE_LATITUDE')
STORE_LONGITUDE = os.getenv('STORE_LONGITUDE')


# Midtrans Client Initialization
midtrans_client = Snap(
    is_production=False,
    server_key = os.getenv('MIDTRANS_SERVER_KEY'),
    client_key = os.getenv('MIDTRANS_CLIENT_KEY')
)

user_bp = Blueprint('main', __name__)

@user_bp.context_processor
def inject_cart_count():
    cart_count = 0
    cart_items = []  # Daftar untuk menyimpan item cart
    user_id = session.get('user_id')  # Mengambil user_id dari session
    
    if user_id:
        user = Users.objects(id=user_id).first()
        if user:
            cart = Cart.objects(user=user).first()
            if cart:
                cart_count = len(cart.items)
                cart_items = cart.items  # Ambil semua item dari cart
    
    return {
        'cart_count': cart_count,
        'cart_items': cart_items  # Mengembalikan item cart
    }


@user_bp.route('/')
@user_required
def index():
    produk_list = list(Produk.objects.aggregate([{'$sample': {'size': 4}}]))
    
    for item in produk_list:
        item['id'] = str(item['_id'])
        item['kategori'] = Kategori.objects.get(id=item['kategori']) 
        
    return render_template('user/index.html', kategoris = Kategori.objects.all(),
                           produk = produk_list,page='produk')



   
@user_bp.route('/shop')
@user_required
def shop():
    kategori_id = request.args.get('kategori')  # Ambil parameter kategori dari query string
    query = request.args.get('q')  # Ambil parameter pencarian dari query string
    page = int(request.args.get('page', 1))  # Ambil parameter page dari URL, default ke 1
    limit = 6

    produk = []
    total_produk = 0

    if query:  # Jika ada parameter pencarian
        produk = search_products_by_name(query, page, limit)  # Cari produk berdasarkan nama
        total_produk = count_products_by_name(query)  # Hitung jumlah hasil pencarian
    elif kategori_id:  # Jika ada parameter kategori
        produk = get_products_by_category(kategori_id, page, limit)
        total_produk = get_product_count_by_category(kategori_id)
    else:  # Jika tidak ada pencarian atau kategori, tampilkan semua produk
        produk = get_all_products(page, limit)
        total_produk = get_total_product_count()

    total_pages = ceil(total_produk / limit)
    total_produk = len(produk)  # Jumlah produk yang diambil
    kategoris = get_all_categories()  # Ambil semua kategori
    kategori_counts = {kategori.id: get_product_count_by_category(kategori.id) for kategori in kategoris}
    total_all_products = get_total_product_count()

    return render_template(
        'user/shop.html',
        produk=produk,
        kategoris=kategoris,
        kategori_counts=kategori_counts,
        total=total_produk,
        total_all_products=total_all_products,
        total_pages=total_pages,
        current_page=page,
        query=query,  # Kirimkan query pencarian ke template
        page='another'
    )




@user_bp.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity'))
    variant = request.form.get('variant')
    user_id = session.get('user_id')
    # Fetch the product
    product = Produk.objects(id=product_id).first()
    user = Users.objects(id=user_id).first()
    if not product:
        return redirect(url_for('main.not_found'))  # Redirect to a not found page or handle error

    # Fetch or create the user's cart
    user_cart = Cart.objects(user=user).first()  # Adjust this to get the current user's cart
    if not user_cart:
        user_cart = Cart(user=user, items=[])

    
    # Create or update cart item
    existing_item = next((item for item in user_cart.items if item.product == product and item.variant == variant), None)
    if existing_item:
        existing_item.quantity += quantity
    else:
        new_item = CartItem(product=product, quantity=quantity, variant=variant)
        user_cart.items.append(new_item)

    user_cart.save()
    if variant:
        flash(f'{product.produkNama} with variant "{variant}" successfully added to cart!', 'primary')
    else:
        flash(f'{product.produkNama} successfully added to cart!', 'primary')
    next_url = request.args.get('next')
    return redirect(next_url or request.referrer or url_for('main.index'))

@user_bp.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    user_id = session.get('user_id')
    client_key = os.getenv('MIDTRANS_CLIENT_KEY') 
    if not user_id:
        flash('User not logged in.', 'warning')
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    # Fetch the user's cart
    user = Users.objects(id=user_id).first()
    user_cart = Cart.objects(user=user).first()
    addresses = user.addresses
    if not user_cart or not user_cart.items:
        flash('Your cart is empty.', 'info')
        return render_template('user/cart.html', cart_items=[], total_price=0)
    
    total_price = sum(item.product.produkHarga * item.quantity for item in user_cart.items)
    shipping_cost = 0 
    
    return render_template('user/cart.html', cart_items=user_cart.items, total_price=total_price,
                           shipping_cost=shipping_cost,addresses=addresses,client_key=client_key
                           )


@user_bp.route('/update_delivery_option', methods=['POST'])
@login_required
def update_delivery_option():
    BASE_FARE = 10000  # Base fare in IDR
    COST_PER_KM = 3000  # Cost per kilometer in IDR
    delivery_option = request.form.get('delivery_option')
    address_index_str = request.form.get('address_index')
    user_id = session.get('user_id')
    user = Users.objects(id=user_id).first()

    # Validate and parse address_index
    if not address_index_str or not address_index_str.isdigit():
        return jsonify({'error': 'Invalid address index'}), 400

    address_index = int(address_index_str)

    if delivery_option == 'delivery':
        if address_index is not None:
            if not user:
                return jsonify({'error': 'User not found'}), 404

            addresses = user.addresses

            if address_index < 0 or address_index >= len(addresses):
                return jsonify({'error': 'Address index out of range'}), 404

            address = addresses[address_index]

            # Calculate distance using OSRM API
            osrm_url = f'http://router.project-osrm.org/route/v1/driving/{STORE_LONGITUDE},{STORE_LATITUDE};{address.longitude},{address.latitude}'

            # Function to get route with retries
            def get_route(osrm_url):
                for attempt in range(3):  # Retry up to 3 times
                    try:
                        response = requests.get(osrm_url)
                        response.raise_for_status()  # Raise an error for bad responses
                        return response.json()
                    except (requests.exceptions.RequestException, ValueError) as e:
                        print(f"Attempt {attempt + 1} failed: {e}")
                        
                return None  # Return None if all attempts fail

            data = get_route(osrm_url)

            if data is None or 'routes' not in data or not data['routes']:
                return jsonify({'error': 'Failed to calculate distance or no route found'}), 500

            distance = data['routes'][0]['distance'] / 1000  # Convert meters to kilometers
            shipping_cost = BASE_FARE + (COST_PER_KM * distance)  # Total cost
            shipping_cost = round(shipping_cost, -2)
            print(f"Distance: {distance:.2f} km")
        else:
            return jsonify({'error': 'Address index is required for delivery'}), 400
    elif delivery_option == 'pickup':
        shipping_cost = 0  # No cost for pickup
    else:
        return jsonify({'error': 'Invalid delivery option'}), 400

    user_cart = Cart.objects(user=user).first()

    if not user_cart:
        return jsonify({'error': 'Cart not found'}), 404

    # Calculate totals
    cart_total = sum(item.product.produkHarga * item.quantity for item in user_cart.items)
    vat = cart_total * 0.11
    grand_total = cart_total + vat + shipping_cost

    return jsonify({
        'success': True,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
    })

@user_bp.route('/profile')
@login_required
def profile():
    return render_template('user/index.html')

@user_bp.route('/cart/delete/<product_id>', methods=['POST'])
@login_required
def cart_delete(product_id):
    user_id = session.get('user_id')
    print(f"User ID from session: {user_id}")  # Debugging

    user = Users.objects(id=user_id).first()
    user_cart = Cart.objects(user=user).first()
    
    print(f"User cart: {user_cart}")  # Debugging

    if not user_cart:
        flash('Cart not found.', 'error')
        return redirect(url_for('main.cart'))

    item_to_delete = None
    for item in user_cart.items:
        if str(item.product.id) == product_id:
            item_to_delete = item
            break
    
    print(f"Item to delete: {item_to_delete}")  # Debugging

    if item_to_delete:
        user_cart.items.remove(item_to_delete)
        user_cart.save()
        flash('Item berhasil dihapus dari keranjang.', 'primary')
    else:
        flash('Item tidak ditemukan dalam keranjang.', 'danger')

    return redirect(url_for('main.cart'))


@user_bp.route('/update_quantity/<product_id>', methods=['POST'])
@login_required
def update_quantity(product_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401

    user = Users.objects(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_cart = Cart.objects(user=user).first()
    if not user_cart:
        return jsonify({'error': 'Cart not found'}), 404

    action = request.form.get('action')

    # Find the item in the cart
    cart_item = next((item for item in user_cart.items if str(item.product.id) == product_id), None)

    if not cart_item:
        return jsonify({'error': 'Cart item not found'}), 404

    if action == 'increment':
        cart_item.quantity += 1
    elif action == 'decrement' and cart_item.quantity > cart_item.product.minPembelian:
        cart_item.quantity -= 1
    elif action == 'update':
        new_quantity = request.form.get('quantity')
        if new_quantity.isdigit():
            new_quantity = int(new_quantity)
            if new_quantity >= cart_item.product.minPembelian:
                cart_item.quantity = new_quantity

    user_cart.save()

    # Respond with the updated quantity and total
    total_price = sum(item.quantity * item.product.produkHarga for item in user_cart.items)

    return jsonify({
        'quantity': cart_item.quantity,
        'total_price': total_price,
        'total_items': len(user_cart.items),
        'grand_total': total_price + (total_price * 0.11),  # Including VAT
        'ppn_cost': total_price * 0.11,  # VAT cost,
        'total_cost': cart_item.quantity * cart_item.product.produkHarga
        
    })


@user_bp.route('/save_address', methods=['POST'])
@login_required
def save_address():
    user_id = session.get('user_id')
    address_type = request.form.get('address_type')
    street_name = request.form.get('street_name')
    rt_rw = request.form.get('rt_rw')
    village = request.form.get('village')
    sub_district = request.form.get('sub_district')
    district = request.form.get('district')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    # Validate latitude and longitude
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        flash('Invalid latitude or longitude value.', 'danger')
        return redirect(url_for('main.cart'))

    # Check if all fields are filled
    if not (address_type and street_name and rt_rw and village and sub_district and district and latitude and longitude):
        flash('Semua kolom harus diisi.', 'danger')
        return redirect(url_for('main.cart'))

    # Create full address string
    full_address = f"{street_name}, RT {rt_rw}, {village}, {sub_district}, {district}"

    # Encode the latitude and longitude to a plus code
    plus_code = olc.encode(latitude, longitude)

    address = Address(
        address_type=address_type,
        street_name=street_name,
        rt_rw=rt_rw,
        village=village,
        sub_district=sub_district,
        district=district,
        latitude=latitude,
        longitude=longitude,
        full_address=full_address,
        plus_code=plus_code
    )

    # Retrieve the user and add the address
    user = Users.objects(id=user_id).first()
    if user:
        user.addresses.append(address)
        user.save()
        flash('Alamat berhasil disimpan.', 'success')
    else:
        flash('Pengguna tidak ditemukan.', 'danger')

    return redirect(url_for('main.cart'))



def to_roman(n):
    if n == 0:
        return "0"  # Menampilkan "0" untuk angka 0
    roman_numerals = {
    5000: 'ↁ', 1000: 'M', 900: 'CM', 500: 'D', 400: 'CD', 
    100: 'C', 90: 'XC', 50: 'L', 40: 'XL', 10: 'X', 9: 'IX', 
    5: 'V', 4: 'IV', 1: 'I'
    }
    result = ''
    for value, numeral in roman_numerals.items():
        while n >= value:
            result += numeral
            n -= value
    return result

@user_bp.route('/create-transaction', methods=['POST'])
@login_required
def create_transaction():
    user_id = session.get('user_id')
    delivery_option = request.form.get('delivery_option')
    address_index_str = request.form.get('address_index')
    delivery_date = request.form.get('delivery_date')  
    delivery_time = request.form.get('delivery_time')  

    
    if not user_id:
        flash('User not logged in.', 'warning')
        return redirect(url_for('auth.login'))

    if not delivery_option:
        flash('Delivery option not selected.', 'warning')
        return redirect(url_for('main.cart'))

    if delivery_option == 'delivery' and (address_index_str is None or not address_index_str.isdigit()):
        flash('Valid address index is required for delivery.', 'warning')
        return redirect(url_for('main.cart'))

    address_index = int(address_index_str) if address_index_str else None

    user = Users.objects(id=user_id).first()
    user_cart = Cart.objects(user=user).first()

    if not user_cart or not user_cart.items:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('main.cart'))

    cart_total = sum(item.product.produkHarga * item.quantity for item in user_cart.items)
    vat = cart_total * 0.11

    if delivery_option == 'delivery':
        if address_index is not None:
            addresses = user.addresses
            if 0 <= address_index < len(addresses):
                address = addresses[address_index]  # Ambil alamat berdasarkan indek

            address = addresses[address_index]

            osrm_url = f'http://router.project-osrm.org/route/v1/driving/{STORE_LONGITUDE},{STORE_LATITUDE};{address.longitude},{address.latitude}'
            response = requests.get(osrm_url)
            data = response.json()
            if 'routes' not in data or not data['routes']:
                flash('Failed to calculate shipping distance.', 'danger')
                return redirect(url_for('main.cart'))

            distance = data['routes'][0]['distance'] / 1000
            shipping_cost = 10000 + (3000 * distance)
            shipping_cost = round(shipping_cost, -2)
        else:
            shipping_cost = 0
    elif delivery_option == 'pickup':
        shipping_cost = 0
    else:
        flash('Invalid delivery option.', 'danger')
        return redirect(url_for('main.cart'))

    grand_total = cart_total + vat + shipping_cost

    midtrans_client = midtransclient.Snap(
        is_production=False,
        server_key=os.getenv('MIDTRANS_SERVER_KEY'),
        client_key=os.getenv('MIDTRANS_CLIENT_KEY')
    )

    today = datetime.now().date()
    year = datetime.now().year
    year_end = datetime.now().month
    roman_year = to_roman(year)
    roman_month = to_roman(year_end)
    # Get the current year and month for filtering by `created_at`
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_end = (datetime.now().replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(seconds=1)

    # Replace 'created_at' with 'transaction_time' for date filtering
    order_count_for_month = Orders.objects(transaction_time__gte=current_month_start, transaction_time__lt=current_month_end).count() + 1


    while True:
        # Menghasilkan order ID dengan counter bulanan
        order_id = f'LC/{today.strftime("%Y%m%d")}/{roman_year}/{roman_month}/{order_count_for_month}'

        # Cek apakah order ID sudah ada
        if not Orders.objects(order_id=order_id):
            break  # ID unik, keluar dari loop

        order_count_for_month += 1 


    # You can now use the `count` variable for your transaction logic

    
    transaction_details = {
        'order_id': order_id,
        'gross_amount': int(grand_total),
    }

    # Mengumpulkan data items dalam bentuk dictionary
    items = [
        {
            'id': str(item.product.id),  # ID produk
            'price': item.product.produkHarga,  # Harga
            'quantity': item.quantity,  # Jumlah
            'name': item.product.produkNama,  # Nama produk
            'category': str(item.product.kategori)  # Kategori
        }
        for item in user_cart.items
    ]

    # Menambahkan Biaya PPN (11%)
    items.append({
        'id': 'Biaya PPN (11%)',
        'price': int(vat),
        'quantity': 1,
        'name': 'Biaya PPN (11%)',
        'category': 'tax'
    })

    # Menambahkan Ongkir jika ada
    if shipping_cost > 0:
        items.append({
            'id': 'Ongkir',
            'price': int(shipping_cost),
            'quantity': 1,
            'name': 'Ongkir',
            'category': 'shipping'  # Kategori
        })

    customer_details = {
        'first_name': user.name,
        'email': user.email,
        'phone': user.phone,
        'billing_address': {
            'address': user.addresses[address_index].full_address if delivery_option == 'delivery' else 'Ambil Di Toko Langgeng Catering, Brebes',
            'city': 'Jawa Tengah',
            'country_code': 'IDN'
        }
    }

    transaction_data = {
        'transaction_details': transaction_details,
        'item_details': items,
        'customer_details': customer_details,
    }

    try:
        snap_response = midtrans_client.create_transaction(transaction_data)
        

        full_delivery_datetime = f"{delivery_date} {delivery_time}"
        # Replace this with your time zone handling if needed
        gmt_plus_7 = pytz.timezone('Asia/Jakarta')
        transaction_time = datetime.now(gmt_plus_7)

        # Set expiry time (for example, 1 hour after transaction time)
        expiry_time = transaction_time + timedelta(hours=1)

        # Simpan data pesanan ke database
        new_order = Orders(
            user=user,
            items = user_cart.items,
            order_id=transaction_details['order_id'],
            shipping_cost = shipping_cost,
            vat = vat,
            grand_total=grand_total,
            delivery_option=delivery_option,
            delivery_date=full_delivery_datetime,  # Simpan tanggal pengiriman
            token = snap_response['token'],
            transaction_time = transaction_time,
            expiry_time=expiry_time,
            address_index=address_index
        )
         # Simpan daftar order items
        new_order.save()  # Simpan order ke database

        # Hapus cart setelah transaksi berhasil
        user_cart.delete()
        
        return jsonify({'snap_token': snap_response['token']})
    except Exception as e:  # Tangani semua kesalahan
        flash(f'Failed to create transaction: {str(e)}', 'danger')
        
        return jsonify({'error': 'Failed to create transaction'}), 500



@user_bp.route('/order')
def order():
    # Mendapatkan user_id dari session
    user_id = session.get('user_id')
    if not user_id:
        flash('User not logged in.', 'warning')
        return redirect(url_for('auth.login'))  # Redirect ke login jika user belum login

    # Mendapatkan status filter dari query parameter, default 'all'
    status_filter = request.args.get('status', 'all')

    # Mengambil user berdasarkan user_id
    user = Users.objects(id=user_id).first()

    # Mengambil pesanan berdasarkan status filter
    if status_filter == 'all':
        orders = Orders.objects(user=user).order_by('-transaction_time')
    else:
        orders = Orders.objects(user=user, order_status=status_filter).order_by('-transaction_time')

    # Memformat tanggal pengiriman dan waktu transaksi untuk setiap pesanan
    for order in orders:
        # Mengonversi dan memformat delivery_date
        delivery_date = order['delivery_date']
        if isinstance(delivery_date, str):
            delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d %H:%M')  # Format yang benar

        # Memformat delivery_date
        formatted_date = format_datetime(delivery_date, format='EEEE, dd MMMM yyyy HH:mm', locale='id_ID')
        order['delivery_date'] = formatted_date

        # Memformat transaction_time
        transaction_time = order['transaction_time']
        if isinstance(transaction_time, str):
            transaction_time = datetime.fromisoformat(transaction_time)  # Mengonversi string ISO ke datetime

        # Mengubah timezone dari UTC ke GMT+7
        utc_zone = pytz.utc
        gmt_plus_7 = pytz.timezone('Asia/Jakarta')  # Ganti dengan zona waktu yang sesuai
        transaction_time = transaction_time.replace(tzinfo=utc_zone)  # Mengatur timezone UTC
        transaction_time = transaction_time.astimezone(gmt_plus_7)  # Mengubah ke GMT+7

        formatted_transaction_time = format_datetime(transaction_time, format='EEEE, dd MMMM yyyy HH:mm', locale='id_ID')
        order['transaction_time'] = formatted_transaction_time

    return render_template('user/order.html', orders=orders, status=status_filter)


@user_bp.route('/payment/get_snap_token/<int:order_id>', methods=['GET'])
def get_snap_token(order_id):
    # Cari pesanan berdasarkan order_id
    order = Orders.query.get(order_id)

    if order and order.payment_status == 'pending':
        # Ambil Snap token dari database
        snap_token = order.token
        return jsonify({'snap_token': snap_token})
    else:
        return jsonify({'error': 'Order not found or payment not pending'}), 404
    
@user_bp.route('/midtrans_webhook', methods=['POST'])
def midtrans_webhook():
    webhook_data = request.get_json()

    if not webhook_data:
        return jsonify({"error": "No data received"}), 400

    order_id = webhook_data.get('order_id')
    transaction_status = webhook_data.get('transaction_status')
    payment_type = webhook_data.get('payment_type')
    transaction_id = webhook_data.get('transaction_id')  # Ambil transaction_id
    fraud_status = webhook_data.get('fraud_status')
    settlement_time = webhook_data.get('settlement_time')
    
    # Logika untuk memproses data webhook
    if order_id:
        # Cari pesanan berdasarkan order_id
        order = Orders.objects(order_id=order_id).first()

        if not order:
            return jsonify({"error": "Order not found"}), 404

        # Perbarui status pembayaran berdasarkan transaction_status dari Midtrans
        if transaction_status == 'capture':
            if payment_type == 'credit_card':
                if fraud_status == 'challenge':
                    order.payment_status = 'challenge'
                else:
                    order.payment_status = 'paid'
                    order.order_status = 'sedang diproses'  # Set status pesanan menjadi 'sedang diproses'
            else:
                order.payment_status = 'paid'
                order.order_status = 'sedang diproses'  # Set status pesanan menjadi 'sedang diproses'
        elif transaction_status == 'settlement':
            order.payment_status = 'berhasil'
            order.order_status = 'sedang diproses'  # Set status pesanan menjadi 'sedang diproses'
        elif transaction_status == 'pending':
            order.payment_status = 'menunggu'
        elif transaction_status == 'deny':
            order.payment_status = 'gagal'
            order.order_status = 'dibatalkan'
        elif transaction_status == 'expire':
            order.payment_status = 'gagal'
            order.order_status = 'dibatalkan'
        elif transaction_status == 'cancel':
            order.payment_status = 'dibatalkan'
            order.order_status = 'dibatalkan'

        # Jika settlement_time ada, update waktu settlement di database
        if settlement_time:
            order.settlement_time = settlement_time
        
        # Simpan transaction_id dan payment_type
        if transaction_id:
            order.transaction_id = transaction_id
        if payment_type:
            order.payment_type = payment_type

        # Menghapus token jika payment_status bukan pending/menunggu
        if order.payment_status not in ['pending', 'menunggu']:
            order.token = None  # Atau gunakan mekanisme lain untuk menghapus token

        # Simpan perubahan ke database
        order.save()

        return jsonify({"message": "Webhook received and processed"}), 200
    else:
        return jsonify({"error": "Order ID not found in webhook data"}), 400



@user_bp.route('/print-pdf/<transaction_id>')
def print_pdf(transaction_id):
    # Replace this with your own database query
    order = Orders.objects(transaction_id=transaction_id).first()  # Fetch single order

    if not order:
        return "Order not found", 404

    # Process and format delivery_date and transaction_time
    if isinstance(order.delivery_date, str):
        delivery_date = datetime.strptime(order.delivery_date, '%Y-%m-%d %H:%M')
    else:
        delivery_date = order.delivery_date  # Assume it's already a datetime object

    # Format delivery_date
    formatted_date = format_datetime(delivery_date, format='EEEE, dd MMMM yyyy HH:mm', locale='id_ID')
    order.delivery_date = formatted_date

    # Format transaction_time
    transaction_time = order.transaction_time
    if isinstance(transaction_time, str):
        transaction_time = datetime.fromisoformat(transaction_time)  # Convert ISO string to datetime

    # Change timezone from UTC to GMT+7
    utc_zone = pytz.utc
    gmt_plus_7 = pytz.timezone('Asia/Jakarta')  # Adjust time zone as needed
    transaction_time = transaction_time.replace(tzinfo=utc_zone)  # Set timezone UTC
    transaction_time = transaction_time.astimezone(gmt_plus_7)  # Change to GMT+7

    formatted_transaction_time = format_datetime(transaction_time, format='EEEE, dd MMMM yyyy HH:mm', locale='id_ID')
    order.transaction_time = formatted_transaction_time

    # Render the HTML template with order data
    html = render_template('user/invoice.html', order=order)

    # Path to wkhtmltopdf executable
    wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

    # Configuring pdfkit
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    options = {
        'enable-local-file-access': None,
        'no-stop-slow-scripts': None,
        'debug-javascript': None,
    }

    try:
        # Generating PDF
        pdf = pdfkit.from_string(html, False, configuration=config, options=options)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=receipt_{transaction_id}.pdf'
        return response
    
    except IOError as e:
        return f"IOError: {str(e)}", 500
    except Exception as e:
        return f"An error occurred: {str(e)}", 500