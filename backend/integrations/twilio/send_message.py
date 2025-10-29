from twilio.rest import Client
import os
from dotenv import load_dotenv

#Padrão de conexão twilio, SID, Token e Client
load_dotenv()
account_sid = os.getenv('TWILIO_SID')
auth_token  = os.getenv('TWILIO_API_KEY')
client = Client(account_sid, auth_token)

#Chama instancia de mensagem
message = client.messages.create(
    from_='whatsapp:+14155238886',
    to='whatsapp:+5515991367797',
    body="How are you?!")

print(message.sid)