import logging
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

account_sid = 'XXXXXXXXXXXXX'
auth_token = 'XXXXXXXXXXX'
client = Client(account_sid, auth_token)

try:
    # Create TwiML instructions locally
    response = VoiceResponse()
    response.say("Hello Riyaz, this is a custom message from Twilio!", voice='alice', language='en-US')
    twiml_str = str(response)

    # Make the call with TwiML inline
    call = client.calls.create(
        to='+918602684710',
        from_='+19103568715',
        twiml=twiml_str
    )

    logging.info(f"Call initiated. Call SID: {call.sid}")

    # Optional: fetch call status immediately (will usually be 'queued' or 'ringing')
    call_status = client.calls(call.sid).fetch().status
    logging.info(f"Call {call.sid} initial status: {call_status}")

except Exception as e:
    logging.error(f"Error initiating call: {e}")
