import json
from service import Service

class NotificationService(Service):
    def __init__(self):
        super().__init__("notification", ['promotion.published', 'promotion.hot_deal'])

    def callback(self, ch, method, properties, body):
        event_json = body.decode() # Converte bytes para string

        if self._verify_event(event_json):
            event = json.loads(event_json) # Converte o JSON para dicionário
            content = event["content"]

            category = content.get("category", "geral")
            routing_key = f"promotion.{category}"

            self._publish("notification", routing_key, content)

            print(f"Notificação enviada: {routing_key}")
        else:
            print("Assinatura inválida")
            return

if __name__ == "__main__":
    NotificationService()
    