from service import Service

class GatewayService(Service):
    def __init__(self):
        super().__init__("gateway", ['promotion.received', 'promotion.voto'], consume=False)

    def register_promotion(self):
        promotion = {
            "id": 1,
            "name": None,
            "category": None
        }

        print("========CADASTRAR PROMOÇÃO========")
        promotion["name"] = input("Nome: ")
        promotion["category"] = input("Categoria:")

        self._publish("gateway", "promotion.received", promotion)
        print("Promoção enviada para cadastro.")

    def vote(self):
        vote = {
            "id": 1,
            "promotion_id": None,
        }

        print("========CADASTRAR PROMOÇÃO========")
        vote["promotion_id"] = input("Promoção: ")

        self._publish("gateway", "promotion.voto", vote)
        print("Voto enviada para cadastro.")

if __name__ == "__main__":
    gateway = GatewayService()

    while(True):
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
    