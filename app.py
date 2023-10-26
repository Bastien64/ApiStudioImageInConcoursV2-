
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
app.config['MYSQL_HOST'] = 'bastien.sitetest.best'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = '123456Azerty!'
app.config['MYSQL_DB'] = 'studiophotov2'

mysql = MySQL(app)


@app.route('/votant', methods=['GET'])
def get_votants():
    with current_app.app_context(): 
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
