
from flask import Flask, jsonify, request, make_response, current_app
from flask_mysqldb import MySQL
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from werkzeug.serving import WSGIRequestHandler
import base64
import io
from io import BytesIO
from PIL import Image
import csv
import os  

WSGIRequestHandler.protocol_version = "HTTP/1.1"
app = Flask(__name__)
port = int(os.environ.get('PORT', 5000))
# Configuration de la base de données sur CONCOURS PHOTO
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['MYSQL_HOST'] = '162.19.67.246'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = '123456Azerty!'
app.config['MYSQL_DB'] = 'studiophotov2'

mysql = MySQL(app)


@app.route('/votant', methods=['GET'])
def get_votants():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM votant''')
    result = cur.fetchall()
    votants = []
    for votant in result:
        votant_data = {}
        votant_data['id'] = votant[0]
        votant_data['Nom'] = votant[1]
        votant_data['Prenom'] = votant[2]
        votant_data['Email'] = votant[3]
        votant_data['Telephone'] = votant[4]
        votants.append(votant_data)
    return jsonify(votants)

@app.route('/categorie', methods=['GET'])
def get_categorie():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM categorie''')
    result = cur.fetchall()
    categories = []
    for categorie in result:
        categorie_data = {}
        categorie_data['id'] = categorie[0]
        categorie_data['Type'] = categorie[1]
        categories.append(categorie_data)
    return jsonify(categories)


@app.route('/votant', methods=['POST'])
def add_votant():
    Nom = request.json['Nom']
    Prenom = request.json['Prenom']
    Email = request.json['Email']
    Telephone = request.json['Telephone']
    cur = mysql.connection.cursor()
    cur.execute('''INSERT INTO votant (Nom, Prenom, Email, Telephone) VALUES(%s, %s, %s, %s)''',
                (Nom, Prenom, Email, Telephone))
    mysql.connection.commit()
    return jsonify({'message': 'votant added successfully'})

@app.route('/votant/delete', methods=['DELETE'])
def delete_all_votant():
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM votant')
        mysql.connection.commit()
    return


@app.route('/photo', methods=['GET'])
def get_photos():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM photoconcours''')
    result = cur.fetchall()
    photos = []
    for photo in result:
        photo_data = {}
        photo_data['id'] = photo[0]
        photo_data['Nom'] = photo[1]
        photo_data['Prenom'] = photo[2]
        photo_data['Email'] = photo[3]
        photo_data['Telephone'] = photo[4]
        image_binary_data = photo[5]
        image = Image.open(BytesIO(image_binary_data))
        image_buffer = BytesIO()
        image.save(image_buffer, format=image.format)
        photo_data['Photo'] = base64.b64encode(image_buffer.getvalue()).decode('utf-8')
        photo_data['Vote'] = photo[6]
        photo_data['Categorie_id'] = photo[7]
        photos.append(photo_data)
    return jsonify(photos)

@app.route('/photo', methods=['POST'])
def add_photo():
    nom = request.form['Nom']
    prenom = request.form['Prenom']
    email = request.form['Email']
    telephone = request.form['Telephone']
    file = request.files['Link']
    
    # Ouvrir l'image avec Pillow
    img = Image.open(file)
    
    # Redimensionner l'image en largeur maximale de 100 pixels et hauteur automatique
    max_width = 500
    width_percent = (max_width / float(img.size[0]))
    new_height = int((float(img.size[1]) * float(width_percent)))
    img = img.resize((max_width, new_height), Image.LANCZOS)
    
    # Compression JPEG avec une qualité de 85 (vous pouvez ajuster la qualité selon vos besoins)
    jpeg_quality = 100
    img_byte_array = BytesIO()
    img.save(img_byte_array, format='JPEG', quality=jpeg_quality, optimize=True)
    
    # Réduire la taille du fichier pour ne pas dépasser 200 Ko
    while img_byte_array.tell() > 400 * 1024:  # 200 Ko en octets
        jpeg_quality -= 5
        img_byte_array = BytesIO()
        img.save(img_byte_array, format='JPEG', quality=jpeg_quality, optimize=True)
    
    file_read = img_byte_array.getvalue()
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO photoconcours (Nom, Prenom, Email, Telephone, Link, Vote, Categorie_id) VALUES (%s, %s, %s, %s, %s, %s, %s)", (nom, prenom, email, telephone, file_read, 0, 2))
    mysql.connection.commit()
    cur.close()
    return 'success'

@app.route('/photo/update_categorie/<int:photo_id>', methods=['POST'])
def update_photo_categorie(photo_id):
    try:
        nouvelle_categorie_id = request.json['nouvelle_categorie_id']
        cur = mysql.connection.cursor()
        cur.execute('UPDATE photoconcours SET Categorie_id = %s WHERE id = %s', (nouvelle_categorie_id, photo_id))
        mysql.connection.commit()
        return jsonify({'message': 'Categorie_id modifié avec succès'})
    except Exception as e:
        return jsonify({'error': str(e)}, 500)

@app.route('/photo/<int:photo_id>/vote', methods=['PUT'])
def update_photo_vote(photo_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM photoconcours WHERE id=%s", (photo_id,))
    photo = cur.fetchone()
    if not photo:
        return jsonify({'error': 'Photo not found'}), 404
    cur.execute("UPDATE photoconcours SET Vote=%s WHERE id=%s", (photo[6] + 1, photo_id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Vote updated successfully'})

@app.route('/photo/delete', methods=['DELETE'])
def delete_all_photos():
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute('''DELETE FROM photos WHERE id NOT IN (1, 2)''')
        mysql.connection.commit()
    return

@app.route('/photo/delete/<int:photo_id>', methods=['DELETE'])
def delete_photo_by_id(photo_id):
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute('''DELETE FROM photos WHERE id = %s''', (photo_id,))
        mysql.connection.commit()
    return jsonify(message=f'La photo avec l\'ID {photo_id} a été supprimée avec succès')


@app.route('/download', methods=['GET'])
def download_admins():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM votant''')
    result = cur.fetchall()

    # Génération du fichier CSV
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['id', 'Nom', 'Prenom', 'Email', 'Telephone'])
    cw.writerows(result)

    # Construction de la réponse HTTP
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=admins.csv"
    output.headers["Content-type"] = "text/csv"
    return output
@app.route('/date', methods=['GET'])
def get_date():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM dateconcours''')
    result = cur.fetchall()
    dates = []
    for date in result:
        date_data = {}
        date_data['id'] = date[0]
        date_data['Datedebut'] = date[1]
        date_data['Datedefin'] = date[2]
        dates.append(date_data)
    return jsonify(dates)

@app.route('/date', methods=['DELETE'])
def delete_all_dates():
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM dateconcours')
    mysql.connection.commit()
    return jsonify({'message': 'Toutes les dates ont été supprimées avec succès'})

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/date', methods=['POST'])
def add_date():
    Datedebut = request.json['Datedebut']
    Datedefin = request.json['Datedefin']
    cur = mysql.connection.cursor()
    cur.execute('''INSERT INTO dateconcours (Datedebut, Datedefin) VALUES(%s, %s)''',
                (Datedebut, Datedefin))
    mysql.connection.commit()
    return jsonify({'message': 'date added successfully'})

if __name__ == '__main__':
    # Utilisez os.environ.get pour obtenir le port depuis la variable d'environnement
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
