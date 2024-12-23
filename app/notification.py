from flask import Blueprint, jsonify, request, session, redirect, url_for, flash
from .models import Notification  # Pastikan path sesuai dengan struktur aplikasi

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/notifications', methods=['GET'])
def get_notifications():
    user_id = session.get('user_id')  # Ambil user_id dari session
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401  # Kembalikan error jika user_id tidak ditemukan
    
    notifications = Notification.objects(user=user_id).order_by('-created_at')
    return jsonify([{
        'id': str(notif.id),
        'title': notif.title,
        'message': notif.message,
        'created_at': notif.created_at.isoformat(),
        'is_read': notif.is_read
    } for notif in notifications])

@notification_bp.route('/notifications/<notification_id>/read', methods=['POST'])
def mark_as_read(notification_id):
    user_id = session.get('user_id')  # Ambil user_id dari session
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401  # Kembalikan error jika user_id tidak ditemukan
    
    notification = Notification.objects(id=notification_id, user=user_id).first()  # Pastikan notifikasi milik user
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    notification.is_read = True
    notification.save()
    return jsonify({'message': 'Notification marked as read'})

def delete_notification(notification_id):
    notification = Notification.objects(id=notification_id).first()
    if notification:
        notification.delete()
        
@notification_bp.route('/notifications/read_all', methods=['POST'])
def mark_all_as_read():
    user_id = session.get('user_id')  # Ambil user_id dari session
    if not user_id:
        flash('User not logged in', 'error')  # Menggunakan flash untuk pesan error
        return redirect(url_for('auth.login'))  # Redirect ke halaman login jika user belum login
    
    notifications = Notification.objects(user=user_id, is_read=False)  # Ambil notifikasi yang belum dibaca
    if not notifications:
        flash('No unread notifications found', 'info')  # Pesan informasi jika tidak ada notifikasi
        return redirect(url_for('notification.get_notifications'))  # Redirect ke halaman notifikasi
    
    # Tandai semua notifikasi sebagai dibaca
    for notif in notifications:
        notif.is_read = True
        notif.save()
    delete_notification(notif.id)

    flash('All notifications marked as read', 'primary') 
    next_url = request.args.get('next_url')
    if next_url:
        return redirect(next_url)  
    else:
        return redirect(url_for('main.order')) 


