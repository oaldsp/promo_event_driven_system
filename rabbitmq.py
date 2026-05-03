import os
import pika
import json

HOST = os.getenv("HOST", "localhost")
EXCHANGE = 'promotions' # Roteador de mensagens

class RabbitMQ:
    def __init__(self):
        self.service_public_keys = {}

        # BlockingConnection -> Espera a resposta para cada ação
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=HOST)
        )
        self.channel = connection.channel()

        self.channel.exchange_declare(
            exchange=EXCHANGE,  
            exchange_type='topic'
        )
  
    def publish(self, author, signature, routing_key, content):
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
        print(f"[{content['id']}] Evento publicado")
    
    def register_service_public_key(self,service_name, public_key):
        self.service_public_keys[service_name] = public_key
