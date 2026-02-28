from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# ==================== CONFIGURATION X-COMMAND ====================
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
products = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ==================== ROUTES X-COMMAND ====================
@app.route('/publish', methods=['POST'])
def publish_product():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', '').strip()
    shipping_fee = request.form.get('shipping_fee', '').strip()
    description = request.form.get('description', '').strip()
    whatsapp_raw = request.form.get('whatsapp', '').strip()
    image = request.files.get('image')
    whatsapp = ''.join(c for c in whatsapp_raw if c.isdigit())

    if not all([name, price, shipping_fee, description, whatsapp, image]):
        return jsonify({'error': 'Tous les champs sont obligatoires'}), 400
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

# ==================== ROUTES CHRONOS (inchangées) ====================
@app.route("/")
def home():
    apps = [
        {
            "name": "Mon App",
            "apk": "mon_app_v2.apk",
            "icon": "mon_app.png"
        }
    ]
    return render_template("index.html", apps=apps)

@app.route("/download/<apk>")
def download(apk):
    return send_from_directory("static/apks", apk, as_attachment=True)

# ==================== NOUVELLE ROUTE : X-COMMAND (pour l'app + bouton du site) ====================
@app.route("/xcommand")
def xcommand():
    return send_from_directory('web', 'style.html')

# ==================== LANCEMENT ====================
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/apks', exist_ok=True)      # pour ton APK
    os.makedirs('web', exist_ok=True)              # pour style.html
    app.run(host='0.0.0.0', port=5000)             # un seul port maintenant
