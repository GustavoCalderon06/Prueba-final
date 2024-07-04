from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

# Almacenamiento de los datos del sensor
data = {
    'gz': [],
    'az': [],
    'activo': [],
    'timestamp': []
}

# Cargar configuración desde el archivo config.json
with open('config.json') as f:
    config = json.load(f)

# Función para enviar correo electrónico
def enviar_correo(subject, body):
    smtp_server = "smtp.gmail.com"
    port = 587  # Puerto para TLS

    sender_email = config["cuenta_gmail"]
    receiver_email = config["alert_recipient"]
    password = config["contraseña"]

    mensaje = MIMEMultipart()
    mensaje['From'] = sender_email
    mensaje['To'] = receiver_email
    mensaje['Subject'] = subject
    mensaje.attach(MIMEText(body, 'plain'))

    try:
        # Establecer conexión SMTP
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()  # Iniciar conexión segura
            server.login(sender_email, password)

            # Envío del correo
            server.sendmail(sender_email, receiver_email, mensaje.as_string())
            print("Correo electrónico enviado exitosamente.")
    except Exception as e:
        print(f"No se pudo enviar el correo electrónico. Error: {e}")

# Ruta para recibir datos del sensor
@app.route('/api/data', methods=['POST'])
def receive_data():
    new_data = request.json
    gz = new_data.get('gz')
    az = new_data.get('az')
    current_time = None  # Inicializa current_time fuera del bloque condicional

    if gz is not None and az is not None:
        data['gz'].append(gz)
        data['az'].append(az)

        # Determinar el estado activo anterior
        if len(data['activo']) > 0:
            last_activo = data['activo'][-1]
        else:
            last_activo = None

        # Determinar si la caldera está activa o detenida
        activo = not (0.95 <= az <= 1.05)
        data['activo'].append(activo)
        
        # Agregar el timestamp solo si el estado activo cambia a activo
        if activo and (last_activo is None or not last_activo):
            current_time = datetime.now().strftime('%H:%M:%S')
            data['timestamp'].append(current_time)

        # Verificar las condiciones anormales
        if gz > 1.4 or az > 1.4:
            enviar_correo('Alerta: Condiciones Anormales Detectadas',
                          'Se han detectado condiciones anormales en los datos del sensor.')

    # Emitir evento a todos los clientes conectados (fuera del bloque condicional)
    socketio.emit('update_data', {'gz': gz, 'az': az, 'activo': activo, 'timestamp': current_time})

    if gz is not None and az is not None:
        return jsonify({'message': 'Datos recibidos correctamente!'}), 200
    else:
        return jsonify({'message': 'Datos inválidos!'}), 400

# Ruta para obtener los datos del sensor
@app.route('/gustavo', methods=['GET'])
def get_data():
    return jsonify(data), 200

# Ruta principal para renderizar el template
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
