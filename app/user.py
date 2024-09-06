from flask import Blueprint, render_template,request,redirect,flash,url_for,session,jsonify
import requests
from .models import (Kategori,Produk, get_products_by_category, 
                     get_all_categories, get_product_count_by_category, 
                     get_total_product_count,get_all_products,
                     Users, Cart,CartItem,Address
                    )
from .decorators import login_required, user_required
from math import ceil
from mongoengine import DoesNotExist
from flask_login import current_user
import midtransclient
from dotenv import load_dotenv
import os
from openlocationcode import openlocationcode as olc

load_dotenv()
STORE_LATITUDE = os.getenv('STORE_LATITUDE')
STORE_LONGITUDE = os.getenv('STORE_LONGITUDE')
user_bp = Blueprint('main', __name__)

@user_bp.context_processor
def inject_cart_count():
    cart_count = 0
    user_id = session.get('user_id')  # Assuming you store user_id in session
    
    if user_id:
        user = Users.objects(id=user_id).first()
        if user:
            cart = Cart.objects(user=user).first()
            if cart:
                 cart_count = len(cart.items)
    
    return {'cart_count': cart_count}

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
    page = int(request.args.get('page', 1))  # Ambil parameter page dari URL, default ke 1
    limit = 6
    produk = []
    total_produk = 0
    if kategori_id:
        produk = get_products_by_category(kategori_id, page, limit)
        total_produk = get_product_count_by_category(kategori_id)
    else:
        produk = get_all_products(page, limit)
        total_produk = get_total_product_count()  # Ambil semua produk jika tidak ada kategori yang dipilih
    total_pages = ceil(total_produk / limit)
    total_produk = len(produk)  # Jumlah produk yang diambil
    kategoris = get_all_categories()  # Ambil semua kategori
    kategori_counts = {kategori.id: get_product_count_by_category(kategori.id) for kategori in kategoris}
    total_all_products = get_total_product_count()
    return render_template('user/shop.html',
                           produk=produk, kategoris=kategoris, 
                           kategori_counts=kategori_counts, 
                           total=total_produk,
                           total_all_products=total_all_products,
                           total_pages=total_pages, 
                           current_page=page,
                           page='another')

@user_bp.route('/order')
def order():
    return render_template('user/index.html')

@user_bp.route('/add-to-cart', methods=['POST'])
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
def cart():
    user_id = session.get('user_id')
    
    if not user_id:
        flash('User not logged in.', 'warning')
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    # Fetch the user's cart
    user = Users.objects(id=user_id).first()
    user_cart = Cart.objects(user=user).first()

    if not user_cart or not user_cart.items:
        flash('Your cart is empty.', 'info')
        return render_template('user/cart.html', cart_items=[], total_price=0)


    
    total_price = sum(item.product.produkHarga * item.quantity for item in user_cart.items)

    return render_template('user/cart.html', cart_items=user_cart.items, total_price=total_price,
                           )


def get_driving_distance(lat1, lon1, lat2, lon2):
    osrm_url = f'https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false'
    response = requests.get(osrm_url)
    data = response.json()
    
    if response.status_code == 200 and 'routes' in data and len(data['routes']) > 0:
        distance = data['routes'][0]['distance']  # Distance in meters
        distance_km = distance / 1000
        return distance_km
    else:
        return 0
    
@user_bp.route('/profile')
@login_required
def profile():
    return render_template('user/index.html')

@user_bp.route('/cart/delete/<product_id>', methods=['POST'])
def cart_delete(product_id):
    # Mendapatkan user_id dari session
    user_id = session.get('user_id')

    # Mendapatkan user dan cart-nya
    user = Users.objects(id=user_id).first()
    user_cart = Cart.objects(user=user).first()

    # Mengecek apakah cart ada
    if not user_cart:
        flash('Cart not found.', 'error')
        return redirect(url_for('main.cart'))

    # Mencari item yang ingin dihapus berdasarkan product_id
    item_to_delete = None
    for item in user_cart.items:
        if str(item.product.id) == product_id:
            item_to_delete = item
            break

    # Menghapus item dari cart jika ditemukan
    if item_to_delete:
        user_cart.items.remove(item_to_delete)
        user_cart.save()
        flash('Item berhasil dihapus dari keranjang.', 'primary')
    else:
        flash('Item tidak ditemukan dalam keranjang.', 'danger')

    return redirect(url_for('main.cart'))

@user_bp.route('/update_quantity/<product_id>', methods=['POST'])
def update_quantity(product_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = Users.objects(id=user_id).first()
    if not user:
        return redirect(url_for('main.cart'))

    user_cart = Cart.objects(user=user).first()
    if not user_cart:
        return redirect(url_for('main.cart'))

    action = request.form.get('action')
    delivery_option = request.form.get('delivery_option', 'pickup')  # Default to 'pickup' if not provided

    # Find the item in the cart
    cart_item = next((item for item in user_cart.items if str(item.product.id) == product_id), None)

    if not cart_item:
        return redirect(url_for('main.cart'))

    if action == 'increment':
        cart_item.quantity += 1
    elif action == 'decrement' and cart_item.quantity > cart_item.product.minPembelian:
        cart_item.quantity -= 1
    elif action == 'update':
        # Update the quantity based on the form input
        new_quantity = request.form.get('quantity')
        if new_quantity.isdigit():
            new_quantity = int(new_quantity)
            if new_quantity >= cart_item.product.minPembelian:
                cart_item.quantity = new_quantity

    user_cart.save()

    # Redirect back to the cart with the delivery_option preserved
    return redirect(url_for('main.cart', delivery_option=delivery_option))



@user_bp.route('/save_address', methods=['POST'])
def save_address():
    user_id = session.get('user_id')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    full_address = request.form.get('full_address')
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        flash('Invalid latitude or longitude value.', 'danger')
        return redirect(url_for('main.cart'))

    # Encode the latitude and longitude to a plus code
    plus_code = olc.encode(latitude, longitude)
    if not latitude or not longitude or not full_address:
        flash('Semua kolom harus diisi.', 'danger')
        return redirect(url_for('main.cart'))

    address = Address(
        user=user_id,
        latitude=float(latitude),
        longitude=float(longitude),
        full_address=full_address,
        plus_code = plus_code
    )
    address.save()

    flash('Alamat berhasil disimpan.', 'success')
    return redirect(url_for('main.cart'))
# Midtrans Client Initialization
midtrans_client = midtransclient.CoreApi(
    is_production=False,
    server_key = os.getenv('MIDTRANS_SERVER_KEY'),
    client_key = os.getenv('MIDTRANS_CLIENT_KEY')
)

