from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

products = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/publish', methods=['POST'])
def publish_product():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', '').strip()
    description = request.form.get('description', '').strip()
    whatsapp_raw = request.form.get('whatsapp', '').strip()
    image = request.files.get('image')

    # Nettoyage strict du numéro WhatsApp
    whatsapp = ''.join(c for c in whatsapp_raw if c.isdigit())

    if not all([name, price, description, whatsapp, image]):
        return jsonify({'error': 'Tous les champs sont obligatoires'}), 400

    if len(whatsapp) < 8 or len(whatsapp) > 15:
        return jsonify({'error': 'Numéro WhatsApp invalide'}), 400

    if not allowed_file(image.filename):
        return jsonify({'error': 'Format d\'image non supporté (png, jpg, jpeg, gif)'}), 400

    filename = secure_filename(image.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(path)

    product = {
        'id': len(products) + 1,
        'name': name,
        'price': price,
        'description': description,
        'whatsapp': whatsapp,
        'image_url': f'/static/uploads/{filename}'
    }

    products.append(product)

    return jsonify({'message': 'Produit publié avec succès', 'product': product})

@app.route('/products')
def get_products():
    return jsonify(products)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/")
def home():
    return send_from_directory('web', 'style.html')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
