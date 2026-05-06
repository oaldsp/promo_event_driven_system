import json
from service import Service

class NotificationService(Service):
    def __init__():
        super().__init__("notification", ['promotion.published', 'promocao.hot_deal'])

    def callback(self, event_json):
        event = json.loads(event_json) # Converte o JSON para dicionário
        content = event["content"]

        category = content.get("category", "geral")
        routing_key = f"promocao.{category}"

        self.rabbitmq.publish("notification", routing_key, content)

        print(f"Notificação enviada: {routing_key}")

if __name__ == "__main__":
    NotificationService()
    