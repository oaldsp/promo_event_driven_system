import os
import json
import pika

EXCHANGE = 'promotions' # Roteador de mensagens
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
CLIENT_ID = os.getenv("CLIENT_ID")
ROUTING_KEYS = json.loads(os.getenv("ROUTING_KEYS"))
class Client:
    def __init__(self, routing_keys=ROUTING_KEYS):
        self.id = CLIENT_ID
        self.channel = self._setup_rabbitmq_exchange()
    
        self._configure_queues(routing_keys)

        print("Cliente aguardando mensagens...")
        self.channel.start_consuming()

    def _setup_rabbitmq_exchange(self):
        # BlockingConnection -> Espera a resposta para cada ação
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq", port=RABBITMQ_PORT)
        )
        channel = connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE,  
            exchange_type='topic'
        )

        return channel
    
    def _configure_queues(self, routing_keys):
        name_queue = f'client{self.id}_queue'

        self.channel.queue_declare(queue=name_queue, exclusive=True)

        for routing_key in routing_keys:
            self.channel.queue_bind(exchange=EXCHANGE, queue=name_queue, routing_key=routing_key)

        self.channel.basic_consume(queue=name_queue, on_message_callback=self.callback, auto_ack=True)

    def callback(self, ch, method, properties, body):
        event = json.loads(body.decode()) # Converte o JSON para dicionário
        content = event["content"]
        print(f"Recebido promoção [{content['name']}] da categoria [{content['category']}]")

if __name__ == "__main__":
    client = Client()
