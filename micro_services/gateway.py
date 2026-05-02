from rabbitmq import RabbitMQ
from encryption import generate_keys

class Gateway:
    rabbitmq = None
    private_key = None
    public_key = None

    def __init__(self):
        self.rabbitmq = RabbitMQ()
        self.private_key, self.public_key = generate_keys()

    def register_promotion(self):
        promotion = {
            "id": 1,
            "name": None,
            "category": None
        }

        print("========CADASTRAR PROMOÇÃO========")
        promotion["name"] = input("Nome: ")
        promotion["category"] = input("Categoria:")

        self.rabbitmq.publish("gateway", self.private_key, "promotion.received", promotion)
        print("Promoção enviada para cadastro.")

    def vote(self):
        vote = {
            "id": 1,
            "promotion_id": None,
        }

        print("========CADASTRAR PROMOÇÃO========")
        vote["promotion_id"] = input("Promoção: ")

        self.rabbitmq.publish("gateway", self.private_key, "promotion.voto", vote)
        print("Voto enviada para cadastro.")

if __name__ == "__main__":
    gateway = Gateway()
    print("=======SELECIONE UMA OPÇÃO========")
    print("1 - Listar promoções")
    print("2 - Votar")
    print("3 - Cadastrar promoção")
    print("==================================")
    option = input("Opção: ")

    match option:
        case "1":
            print("IMPLEMENTAR")
        case "2":
            gateway.vote()
        case "3":
            gateway.register_promotion()
    