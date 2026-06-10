import json
from service import Service

class PromotionService(Service):
    def __init__(self):
        super().__init__("promotion", ["promotion.received"])

    def callback(self, ch, method, properties, body):
        event_json = body.decode() # Converte bytes para string

        if self._verify_event(event_json):
            event = json.loads(event_json) # Converte o JSON para dicionário
            content = event["content"]

            print(f"[{content['id']}]Promoção validada:")

            # publicar promotion.publishe
            self._publish("promotion", "promotion.published", content)
        else:
            print("Assinatura inválida")
            return

if __name__ == "__main__":
    PromotionService()
