import json
from encryption import generate_keys, generate_signature

class Notification:
    def __init__(self, rabbitmq):
        self.private_key, self.public_key = generate_keys()
        self.rabbitmq = rabbitmq
        rabbitmq.register_service_public_key("notification", self.public_key)

    def callback(self, event_json):
        event = json.loads(event_json) # Converte o JSON para dicionário
        content = event["content"]

        category = content.get("category", "geral")
        routing_key = f"promocao.{category}"

        signature = generate_signature(content)
        self.rabbitmq.publish("notification", signature, routing_key, content)

        print(f"Notificação enviada: {routing_key}")

if __name__ == "__main__":
    notification = Notification()
    channel = notification.rabbitmq.channel

    channel.queue_declare(queue='notification_queue')

    channel.queue_bind(exchange='promotions', queue='notification_queue', routing_key='promotion.published')
    channel.queue_bind(exchange='promotions', queue='notification_queue', routing_key='promocao.hot_deal')

    channel.basic_consume(queue='notification_queue', on_message_callback=notification.callback, auto_ack=True)

    print("Notificacao rodando...")
    channel.start_consuming()
    