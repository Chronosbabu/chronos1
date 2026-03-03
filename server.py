from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import os
import json

app = Flask(__name__)

# ==================== CONFIGURATION ====================
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
PRODUCTS_FILE = 'products.json'

ALLOWED_CITIES = ['BUKAVU', 'LUBUMBASHI', 'KINDI']

products = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ==================== CHARGER / SAUVEGARDER ====================
def load_products():
    global products
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                products = json.load(f)
            print(f"✅ {len(products)} produits chargés")
        except:
            products = []
    else:
        products = []

def save_products():
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

# ==================== ROUTES ====================
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
        return jsonify({'error': f'Ville invalide. Choisissez parmi : {", ".join(ALLOWED_CITIES)}'}), 400

    if len(whatsapp) < 8 or len(whatsapp) > 15 or not whatsapp.startswith('243'):
        return jsonify({'error': 'Le numéro WhatsApp doit commencer par 243'}), 400

    if not allowed_file(image.filename):
        return jsonify({'error': 'Format d\'image non supporté (png, jpg, jpeg, gif)'}), 400

    filename = secure_filename(image.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(path)

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

    return jsonify({'message': 'Produit publié avec succès', 'product': product})

@app.route('/products')
def get_products():
    city_filter = request.args.get('city', '').strip().upper()
    if city_filter and city_filter in ALLOWED_CITIES:
        filtered = [p for p in products if p.get('city') == city_filter]
        return jsonify(filtered)
    return jsonify(products)

@app.route('/my_products')
def my_products():
    whatsapp = request.args.get('whatsapp', '').strip()
    if not whatsapp:
        return jsonify([])
    my_prods = [p for p in products if p['whatsapp'] == whatsapp]
    return jsonify(my_prods)

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
                # Suppression du fichier image (optionnel mais propre)
                try:
                    img_path = p['image_url'].replace('/static/uploads/', '')
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img_path))
                except:
                    pass
                del products[i]
                save_products()
                return jsonify({'message': 'Produit supprimé avec succès'})
        return jsonify({'error': 'Produit non trouvé ou vous n\'êtes pas autorisé'}), 403
    except:
        return jsonify({'error': 'Erreur lors de la suppression'}), 400

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== ROUTES CHRONOS ====================
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

# ==================== LANCEMENT ====================
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/apks', exist_ok=True)
    load_products()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
