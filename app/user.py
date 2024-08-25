from flask import Blueprint, render_template,request,redirect,flash,url_for,session
from .models import (Kategori,Produk, get_products_by_category, 
                     get_all_categories, get_product_count_by_category, 
                     get_total_product_count,get_all_products,
                     Users, Cart
                    )
from .decorators import login_required, user_required
from math import ceil
from flask_login import current_user

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
                cart_count = sum(item.quantity for item in cart.items)
    
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

@user_bp.route('/profile')
@login_required
def profile():
    return render_template('user/index.html')


