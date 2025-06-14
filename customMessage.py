from twilio.rest import Client
import logging

logging.basicConfig(level=logging.INFO)

account_sid = 'XXXXXXXXXXXX'
auth_token = 'XXXXXXX'
client = Client(account_sid, auth_token)

try:
    call = client.calls.create(
        to='+918602684710',
        from_='+19103568715',
        url='https://handler.twilio.com/twiml/EH71b7e4c9fa07ae99b9cc86679072bbbd' 
    )
    logging.info(f"Call initiated. Call SID: {call.sid}")

except Exception as e:
    logging.error(f"Error initiating call: {e}")
