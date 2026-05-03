import json

class Client:
    count = 0  # classe

    def __init__(self, rabbitmq, interests=[]):
        type(self).count += 1
        self.id = type(self).count
        self.rabbitmq = rabbitmq
        self.interests = interests

        self.queue = channel.queue_declare(queue=f'client{self.id}_queue', exclusive=True)
        for interest in interests:
            channel.queue_bind(exchange='promocoes', queue=self.queue.method.queue, routing_key=interest)
        
    def callback(event_json):
        event = json.loads(event_json) # Converte o JSON para dicionário
        content = event["content"]
        print(f"Recebido promoção [{content['name']}] da categoria [{content['category']}]")

if __name__ == "__main__":
    client = Client()
    channel = client.rabbitmq.channel

    channel.basic_consume(queue=client.queue.method.queue, on_message_callback=client.callback, auto_ack=True)

    print("Cliente aguardando mensagens...")
    channel.start_consuming()
