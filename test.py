from twilio.rest import Client

client = Client('ACf744b4a8a52498b8f7d2f69d287d1814', 'f1f1d1c6b73c9d41286a7837d27fae43')

call = client.calls.create(
    to='+17275945570',
    from_='+254700392123',
    url='https://agnostic-atrocious-luckily.ngrok-free.dev/api/twilio/incoming-call/'
)

print(call.sid)