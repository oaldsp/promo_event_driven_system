import os
import pika
import json

HOST = os.getenv("HOST", "localhost")
EXCHANGE = 'message_router' # Roteador de mensagens

def get_channel():
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

def publish(channel, routing_key, message):
    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=routing_key, # Cabeçalho da mensagem
        body=json.dumps(message)
    )