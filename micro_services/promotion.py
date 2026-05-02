import json
from encryption import generate_keys, generate_signature, verify_event

class Promotion:
    rabbitmq = None
    private_key = None
    public_key = None

    def __init__(self, rabbitmq):
        self.private_key, self.public_key = generate_keys()
        self.rabbitmq = rabbitmq
        rabbitmq.register_service_public_key("promotion", self.public_key)

    def callback(self, event_json):
        if verify_event(event_json):
            event = json.loads(event_json) # Converte o JSON para dicionário
            content = event["content"]

            print(f"[{content['id']}]Promoção validada:")

            # publicar promotion.published
            signature = generate_signature(content)
            self.rabbitmq.publish("promotion", signature, "promotion.published", content)
        else:
            print("Assinatura inválida")
            return

if __name__ == "__main__":
    promotion = Promotion()
    channel = promotion.rabbitmq.channel

    channel.queue_declare(queue='promotion_queue')
    channel.queue_bind(exchange='promotions', queue='promotion_queue', routing_key='promotion.received')

    channel.basic_consume(queue='promotion_queue', on_message_callback=promotion.callback, auto_ack=True)

    print("Serviço promoção rodando...")
    channel.start_consuming()
