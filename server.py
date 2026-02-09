# server.py - Central Python Server using Flask and SocketIO for real-time updates with gevent

from gevent import monkey
monkey.patch_all()

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")

# In-memory product storage (for simplicity; use a DB like SQLite/Mongo for production)
products = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/publish', methods=['POST'])
def publish_product():
    name = request.form.get('name')
    price = request.form.get('price')
    description = request.form.get('description')
    image = request.files.get('image')

    if not all([name, price, description, image]):
        return jsonify({'error': 'Missing fields'}), 400

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        image_url = f'/static/uploads/{filename}'
    else:
        return jsonify({'error': 'Invalid image'}), 400

    product = {
        'id': len(products) + 1,
        'name': name,
        'price': price,
        'description': description,
        'image_url': image_url
    }
    products.append(product)

    # Emit real-time update
    socketio.emit('new_product', product)

    return jsonify({'success': True, 'product': product})

@app.route('/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def serve_html():
    return send_from_directory('web', 'style.html')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
