import json
from encryption import generate_keys, generate_signature, verify_event

THRESHOLD = 2

class Ranking:
    rabbitmq = None
    private_key = None
    public_key = None
    votes = {}

    def __init__(self, rabbitmq):
        self.private_key, self.public_key = generate_keys()
        self.rabbitmq = rabbitmq
        rabbitmq.register_service_public_key("ranking", self.public_key)

    def callback(self, event_json):
        if verify_event(event_json):
            event = json.loads(event_json) # Converte o JSON para dicionário
            content = event["content"]

            # Computa o voto
            promotion_id = content["promotion_id"]
            self.votes[promotion_id] = self.votes.get(promotion_id, 0) + 1
            print(f"[{promotion_id}] Eecebeu 1 voto totalizando: {self.votes[promotion_id]} votos")

            # Verifica se a promoção atingiu destaque
            if self.votes[promotion_id] >= THRESHOLD:
                print(f"[{promotion_id}] Entrou em Destaque")
                # publicar promocao.hot_deal
                signature = generate_signature(content)
                self.rabbitmq.publish("ranking", signature, "promocao.hot_deal", content)
        else:
            print("Assinatura inválida")
            return

if __name__ == "__main__":
    ranking = Ranking()
    channel = ranking.rabbitmq.channel

    channel.queue_declare(queue='ranking_queue')
    channel.queue_bind(exchange='promotions', queue='ranking_queue', routing_key='promocao.vote')

    channel.basic_consume(queue='ranking_queue', on_message_callback=ranking.callback, auto_ack=True)

    print("Ranking rodando...")
    channel.start_consuming()
    