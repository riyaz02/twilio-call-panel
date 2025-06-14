import os
import logging
import logging.config
import configparser
from flask import Flask, request, render_template, redirect, url_for
from twilio.rest import Client
import pandas as pd

# === Load Logging ===
logging.config.fileConfig('config/logging.conf')
logger = logging.getLogger()

# === Load App Properties ===
app_config = configparser.ConfigParser()
app_config.read('config/application.properties')
HOST = app_config['DEFAULT'].get('host', '0.0.0.0')
PORT = int(app_config['DEFAULT'].get('port', 5000))
PUBLIC_URL = app_config['DEFAULT'].get('public_url', 'http://localhost:5000')

# === Load Twilio Config (env first, then file) ===
ACCOUNT_SID = os.getenv('ACCOUNT_SID')
AUTH_TOKEN = os.getenv('AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')

if not ACCOUNT_SID or not AUTH_TOKEN or not TWILIO_FROM_NUMBER:
    logger.info("Loading Twilio config from file...")
    config = configparser.ConfigParser()
    config.read('config/twilio_config.cfg')
    ACCOUNT_SID = config['twilio']['account_sid']
    AUTH_TOKEN = config['twilio']['auth_token']
    TWILIO_FROM_NUMBER = config['twilio']['from_number']

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# === Flask App ===
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file or file.filename == '':
                logger.error("No file uploaded")
                return "No file uploaded", 400

            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            logger.info(f"File uploaded: {filename}")

            df = pd.read_csv(filepath)
            if df.empty:
                logger.warning("CSV is empty.")
                return "Empty file", 400

            def format_number(num):
                num = str(num).strip()
                if not num.startswith('+'):
                    return '+91' + num
                return num

            numbers = df.iloc[:, 0].dropna().apply(format_number).tolist()
            logger.info(f"Total numbers to call: {len(numbers)}")

            for number in numbers:
                try:
                    call = client.calls.create(
                        to=number,
                        from_=TWILIO_FROM_NUMBER,
                        url=f"{PUBLIC_URL}/twiml",
                        status_callback=f"{PUBLIC_URL}/status_callback",
                        status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                        status_callback_method='POST'
                    )
                    logger.info(f"Call initiated: To={number} | SID={call.sid}")
                except Exception as e:
                    logger.error(f"Call failed | To={number} | Error={e}")
            return redirect(url_for('index'))
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return "Internal Server Error", 500
    return render_template('index.html')


@app.route('/twiml', methods=['POST', 'GET'])
def twiml():
    from flask import Response
    response_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice" language="en-US">Hello Riyaz, this is your campaign message from Twilio.</Say>
</Response>"""
    return Response(response_xml, mimetype='text/xml')


@app.route('/status_callback', methods=['POST'])
def status_callback():
    try:
        call_sid = request.values.get('CallSid')
        call_status = request.values.get('CallStatus')
        call_duration = request.values.get('CallDuration', 'N/A')
        to_number = request.values.get('To')
        from_number = request.values.get('From')

        logger.info(f"Call Status Update | SID={call_sid} | Status={call_status} | Duration={call_duration} | To={to_number} | From={from_number}")
        return ('', 204)
    except Exception as e:
        logger.error(f"Status callback error: {e}")
        return ('', 500)

if __name__ == '__main__':
    logger.info(f"Starting Flask app on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT)
