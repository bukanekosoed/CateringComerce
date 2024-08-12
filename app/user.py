from flask import Blueprint, render_template
from .models import Kategori
user_bp = Blueprint('main', __name__)

@user_bp.route('/')
def index():
    return render_template('user/index.html', kategoris = Kategori.objects.all())

@user_bp.route('/shop')
def shop():
    return render_template('user/index.html')

@user_bp.route('/order')
def order():
    return render_template('user/index.html')

@user_bp.route('/profile')
def profile():
    return render_template('user/index.html')


