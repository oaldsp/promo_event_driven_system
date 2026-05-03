from encryption import generate_keys, generate_signature

class Gateway:
    def __init__(self, rabbitmq):
        self.private_key, self.public_key = generate_keys()
        self.rabbitmq = rabbitmq
        rabbitmq.register_service_public_key("gateway", self.public_key)

    def register_promotion(self):
        promotion = {
            "id": 1,
            "name": None,
            "category": None
        }

        print("========CADASTRAR PROMOÇÃO========")
        promotion["name"] = input("Nome: ")
        promotion["category"] = input("Categoria:")

        signature = generate_signature(promotion)
        self.rabbitmq.publish("gateway", signature, "promotion.received", promotion)
        print("Promoção enviada para cadastro.")

    def vote(self):
        vote = {
            "id": 1,
            "promotion_id": None,
        }

        print("========CADASTRAR PROMOÇÃO========")
        vote["promotion_id"] = input("Promoção: ")

        signature = generate_signature(vote)
        self.rabbitmq.publish("gateway", signature, "promotion.voto", vote)
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
    