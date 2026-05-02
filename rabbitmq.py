import os
import pika
import json
from encryption import generate_signature

HOST = os.getenv("HOST", "localhost")
EXCHANGE = 'message_router' # Roteador de mensagens

channel = None

def get_channel():
    if channel is None:
        # BlockingConnection -> Espera a resposta para cada ação
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=HOST)
        )
        channel = connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE,  
            exchange_type='topic'
        )

    return channel

def publish(author, private_key, routing_key, content):
    body = json.dumps(content).encode() # Converte para bytes
    signature = generate_signature(private_key, body)

    event = {
        "content": content,
        "signature": signature,
        "producer": author
    }

    get_channel().basic_publish(
        exchange=EXCHANGE,
        routing_key=routing_key, # Cabeçalho da mensagem
        body=json.dumps(event)
    )
