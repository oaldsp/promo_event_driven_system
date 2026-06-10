from service import Service

class GatewayService(Service):
    def __init__(self):
        self.promotions = {}
        super().__init__("gateway", ['promotion.received', 'promotion.voto'], consume=False)

    def list_promotions(self):
        print("========PROMOÇÕES========")
        for promotion in self.promotions.values():
            print(
                f"[{promotion['id']}] "
                f"{promotion['name']} "
                f"({promotion['category']})"
            )

    def vote(self):
        print("==============VOTAR===============")
        promotion_id = int(input("ID da Promoção: "))
        promotion = self.promotions[promotion_id]

        self._publish("gateway", "promotion.vote", promotion)
        print("Voto enviada para cadastro.")

    def register_promotion(self):
        promotion = {
            "id": len(self.promotions),
            "name": None,
            "category": None
        }

        print("========CADASTRAR PROMOÇÃO========")
        promotion["name"] = input("Nome: ")
        promotion["category"] = input("Categoria:")

        self.promotions[promotion["id"]] = promotion
        self._publish("gateway", "promotion.received", promotion)
        print("Promoção enviada para cadastro.")   

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
                gateway.list_promotions()
            case "2":
                gateway.vote()
            case "3":
                gateway.register_promotion()
    