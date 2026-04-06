from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import os
import json
import uuid

app = Flask(__name__)

# ==================== CONFIGURATION ====================
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
PRODUCTS_FILE = 'products.json'
ALLOWED_CITIES = ['BUKAVU', 'LUBUMBASHI', 'KINDU', 'UNKNOWN']

products = []

# ==================== FONCTIONS ====================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ==================== CHARGER / SAUVEGARDER ====================
def load_products():
    global products
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                products = json.load(f)
            print(f"{len(products)} produits chargés")
        except:
            products = []
    else:
        products = []

def save_products():
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

# ==================== ROUTE PUBLIER PRODUIT ====================
@app.route('/publish', methods=['POST'])
def publish_product():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', '').strip()
    shipping_fee = request.form.get('shipping_fee', '').strip()
    description = request.form.get('description', '').strip()
    whatsapp_raw = request.form.get('whatsapp', '').strip()
    city = request.form.get('city', '').strip().upper()
    category = request.form.get('category', '').strip()
    image = request.files.get('image')

    whatsapp = ''.join(c for c in whatsapp_raw if c.isdigit())

    if not all([name, price, shipping_fee, description, whatsapp, image, category]):
        return jsonify({'error': 'Tous les champs sont obligatoires'}), 400

    if city and city not in ALLOWED_CITIES:
        return jsonify({'error': 'Ville invalide'}), 400

    if category not in ['Fast Food', 'Ready Meals']:
        return jsonify({'error': 'Catégorie invalide (Fast Food ou Ready Meals)'}), 400

    if len(whatsapp) < 8 or len(whatsapp) > 15 or not whatsapp.startswith('243'):
        return jsonify({'error': 'Le numéro WhatsApp doit commencer par 243'}), 400

    if not allowed_file(image.filename):
        return jsonify({'error': 'Format image non supporté'}), 400

    ext = image.filename.rsplit('.', 1)[1].lower()
    filename = str(uuid.uuid4()) + "." + ext
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(path)

    product = {
        'id': len(products) + 1,
        'name': name,
        'price': price,
        'shipping_fee': shipping_fee,
        'description': description,
        'whatsapp': whatsapp,
        'city': city or 'UNKNOWN',
        'category': category,
        'image_url': f'/static/uploads/{filename}'
    }

    products.append(product)
    save_products()
    return jsonify({'message': 'Produit publié avec succès', 'product': product})

# ==================== ROUTE TOUS PRODUITS ====================
@app.route('/products')
def get_products():
    filtered_sorted = sorted(products, key=lambda p: p['id'], reverse=True)
    return jsonify(filtered_sorted)

# ==================== MES PRODUITS ====================
@app.route('/my_products')
def my_products():
    whatsapp = request.args.get('whatsapp', '').strip()
    if not whatsapp:
        return jsonify([])
    my_prods = [p for p in products if p['whatsapp'] == whatsapp]
    return jsonify(sorted(my_prods, key=lambda p: p['id'], reverse=True))

# ==================== SUPPRIMER ====================
@app.route('/delete_product', methods=['POST'])
def delete_product():
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        prod_id = int(data.get('id'))
        whatsapp = data.get('whatsapp', '').strip()
        global products
        for i, p in enumerate(products):
            if p['id'] == prod_id and p['whatsapp'] == whatsapp:
                try:
                    img_name = p['image_url'].replace('/static/uploads/', '')
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img_name))
                except:
                    pass
                del products[i]
                save_products()
                return jsonify({'message': 'Produit supprimé avec succès'})
        return jsonify({'error': 'Produit non trouvé'}), 403
    except:
        return jsonify({'error': 'Erreur suppression'}), 400

# ==================== IMAGES ====================
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== PAGES ====================
@app.route("/")
def home():
    apps = [{"name": "Mon App", "apk": "mon_app_v2.apk", "icon": "mon_app.png"}]
    return render_template("index.html", apps=apps)

@app.route("/download/<apk>")
def download(apk):
    return send_from_directory("static/apks", apk, as_attachment=True)

@app.route("/xcommand")
def xcommand():
    return render_template("style.html")

@app.route("/post")
def post():
    return render_template("post.html")

# ==================== LANCEMENT ====================
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/apks', exist_ok=True)
    load_products()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
