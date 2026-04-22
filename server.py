from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import json
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
PRODUCTS_FILE = 'products.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_CITIES = ['FAST FOOD', 'TO PREPARE']

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

products = []

# ================= UTILS =================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_products():
    global products
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                products = json.load(f)
        except:
            products = []

def save_products():
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

# ================= ROUTES =================

@app.route("/")
@app.route("/xcommand")
def home():
    return render_template("style.html")

@app.route("/post")
def post():
    return render_template("post.html")

@app.route('/publish', methods=['POST'])
def publish_product():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', '').strip()
    shipping_fee = request.form.get('shipping_fee', '').strip()
    description = request.form.get('description', '').strip()
    whatsapp = ''.join(c for c in request.form.get('whatsapp', '') if c.isdigit())
    city = request.form.get('city', '').strip().upper()
    image = request.files.get('image')

    if not all([name, price, shipping_fee, description, whatsapp, city, image]):
        return jsonify({'error': 'Champs manquants'}), 400

    if city not in ALLOWED_CITIES:
        return jsonify({'error': 'Type invalide'}), 400

    if not whatsapp.startswith('243'):
        return jsonify({'error': 'Numéro invalide'}), 400

    if not allowed_file(image.filename):
        return jsonify({'error': 'Image invalide'}), 400

    filename = f"{uuid.uuid4()}.{image.filename.rsplit('.',1)[1]}"
    image.save(os.path.join(UPLOAD_FOLDER, filename))

    product = {
        'id': len(products)+1,
        'name': name,
        'price': price,
        'shipping_fee': shipping_fee,
        'description': description,
        'whatsapp': whatsapp,
        'city': city,
        'image_url': f'/static/uploads/{filename}'
    }

    products.append(product)
    save_products()

    return jsonify({'message': 'OK', 'product': product})

@app.route('/products')
def get_products():
    city = request.args.get('city','').upper()
    if city in ALLOWED_CITIES:
        data = [p for p in products if p['city']==city]
    else:
        data = products

    return jsonify(sorted(data, key=lambda x:x['id'], reverse=True))

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    load_products()
    app.run(host='0.0.0.0', port=5000)
