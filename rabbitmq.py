import os
import pika
import json
from encryption import generate_signature

HOST = os.getenv("HOST", "localhost")
EXCHANGE = 'promotion' # Roteador de mensagens

class RabbitMQ:
    channel = None

    def __init__(self):
        # BlockingConnection -> Espera a resposta para cada ação
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=HOST)
        )
        self.channel = connection.channel()

        self.channel.exchange_declare(
            exchange=EXCHANGE,  
            exchange_type='topic'
        )
  
    def publish(self, author, private_key, routing_key, content):
        body = json.dumps(content).encode() # Converte para bytes
        signature = generate_signature(private_key, body)

        event = {
            "content": content,
            "signature": signature,
            "producer": author
        }

        self.channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key, # Cabeçalho da mensagem
            body=json.dumps(event)
        )
