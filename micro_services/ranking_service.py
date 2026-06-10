import json
from service import Service

THRESHOLD = 2

class RankingService(Service):
    def __init__(self):
        self.votes = {}
        super().__init__("ranking", ['promotion.vote'])

    def callback(self, ch, method, properties, body):
        event_json = body.decode() # Converte bytes para string
        
        if self._verify_event(event_json):
            event = json.loads(event_json) # Converte o JSON para dicionário
            content = event["content"]

            # Computa o voto
            promotion_id = content["id"]
            self.votes[promotion_id] = self.votes.get(promotion_id, 0) + 1
            print(f"[{promotion_id}] Eecebeu 1 voto totalizando: {self.votes[promotion_id]} votos")

            # Verifica se a promoção atingiu destaque
            if self.votes[promotion_id] >= THRESHOLD:
                print(f"[{promotion_id}] Entrou em Destaque")
                # publicar promotion.hot_deal
                self._publish("ranking", "promotion.hot_deal", content)
        else:
            print("Assinatura inválida")
            return

if __name__ == "__main__":
    RankingService()
    