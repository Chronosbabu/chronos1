from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import json
import uuid

app = Flask(__name__)

# ================= CONFIG =================
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
    else:
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
    whatsapp_raw = request.form.get('whatsapp', '').strip()
    city = request.form.get('city', '').strip().upper()
    image = request.files.get('image')

    whatsapp = ''.join(c for c in whatsapp_raw if c.isdigit())

    if not all([name, price, shipping_fee, description, whatsapp, image, city]):
        return jsonify({'error': 'Tous les champs sont obligatoires'}), 400

    if city not in ALLOWED_CITIES:
        return jsonify({'error': 'Type invalide'}), 400

    if not whatsapp.startswith('243'):
        return jsonify({'error': 'Numéro WhatsApp invalide'}), 400

    if not allowed_file(image.filename):
        return jsonify({'error': 'Format image non supporté'}), 400

    filename = f"{uuid.uuid4()}.{image.filename.rsplit('.', 1)[1].lower()}"
    image.save(os.path.join(UPLOAD_FOLDER, filename))

    product = {
        'id': len(products) + 1,
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

    return jsonify({'message': 'Produit publié', 'product': product})

@app.route('/products')
def get_products():
    city = request.args.get('city', '').upper()

    if city in ALLOWED_CITIES:
        filtered = [p for p in products if p['city'] == city]
    else:
        filtered = products

    return jsonify(sorted(filtered, key=lambda x: x['id'], reverse=True))

@app.route('/my_products')
def my_products():
    whatsapp = request.args.get('whatsapp', '').strip()
    return jsonify([p for p in products if p['whatsapp'] == whatsapp])

@app.route('/delete_product', methods=['POST'])
def delete_product():
    data = request.form

    try:
        pid = int(data.get('id'))
        whatsapp = data.get('whatsapp')

        global products
        for i, p in enumerate(products):
            if p['id'] == pid and p['whatsapp'] == whatsapp:
                try:
                    os.remove(p['image_url'].replace('/static/', 'static/'))
                except:
                    pass

                del products[i]
                save_products()
                return jsonify({'message': 'Supprimé'})

        return jsonify({'error': 'Introuvable'}), 404

    except:
        return jsonify({'error': 'Erreur'}), 400

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ================= START =================
if __name__ == '__main__':
    load_products()
    app.run(host='0.0.0.0', port=5000)
