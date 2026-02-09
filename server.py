from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Config
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# IMPORTANT : threading (PAS eventlet)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

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
        return jsonify({'error': 'Champs manquants'}), 400

    if not allowed_file(image.filename):
        return jsonify({'error': 'Image invalide'}), 400

    filename = secure_filename(image.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(image_path)

    product = {
        'id': len(products) + 1,
        'name': name,
        'price': price,
        'description': description,
        'image_url': f'/static/uploads/{filename}'
    }

    products.append(product)

    # Envoi temps réel
    socketio.emit('new_product', product)

    return jsonify(product)

@app.route('/products')
def get_products():
    return jsonify(products)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def home():
    return send_from_directory('web', 'style.html')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    socketio.run(app, host='0.0.0.0', port=5000)

