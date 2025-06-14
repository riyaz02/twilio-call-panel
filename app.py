import configparser
import logging
import logging.config
from flask import Flask, render_template, request, redirect
from twilio.rest import Client
import pandas as pd
import os

# Load Twilio config
config = configparser.ConfigParser()
config.read('twilio_config.cfg')
ACCOUNT_SID = config['twilio']['account_sid']
AUTH_TOKEN = config['twilio']['auth_token']
TWILIO_FROM_NUMBER = config['twilio']['from_number']

# Load application config
app_config = configparser.ConfigParser()
app_config.read('application.properties')
HOST = app_config['DEFAULT'].get('host', '127.0.0.1')
PORT = int(app_config['DEFAULT'].get('port', 5000))

# Load logging config
logging.config.fileConfig('logging.conf')
logger = logging.getLogger()

app = Flask(__name__)

client = Client(ACCOUNT_SID, AUTH_TOKEN)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            file = request.files['file']
            if not file:
                logger.error('No file uploaded')
                return "No file uploaded", 400
            # Save uploaded file
            filepath = os.path.join('uploads', file.filename)
            file.save(filepath)
            logger.info(f'Uploaded file saved at: {filepath}')

            # Read CSV with pandas
            df = pd.read_csv(filepath)

            # Add +91 if missing
            def format_number(num):
                num = str(num).strip()
                if not num.startswith('+'):
                    return '+91' + num
                return num

            numbers = df.iloc[:, 0].apply(format_number).tolist()
            logger.info(f'Numbers to call: {len(numbers)}')

            for to_number in numbers:
                try:
                    call = client.calls.create(
                        url='http://demo.twilio.com/docs/voice.xml',
                        to=to_number,
                        from_=TWILIO_FROM_NUMBER
                    )
                    logger.info(f'Call initiated to {to_number} | SID: {call.sid}')
                except Exception as e:
                    logger.error(f'Error calling {to_number}: {e}')

            return redirect('/')
        except Exception as e:
            logger.exception(f'Error in call processing: {e}')
            return "Internal server error", 500
    return render_template('index.html')

if __name__ == '__main__':
    logger.info(f'Starting app on {HOST}:{PORT}')
    app.run(host=HOST, port=PORT)
