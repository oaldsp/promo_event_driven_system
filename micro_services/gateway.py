import json
from rabbitmq import get_channel, publish
from encryption import generate_keys

private_key, public_key = generate_keys()
channel = get_channel()

def register_promotion():
    promotion = {
        "id": 1,
        "name": None,
        "category": None
    }

    print("========CADASTRAR PROMOÇÃO========")
    promotion["name"] = input("Nome: ")
    promotion["category"] = input("Categoria:")
    
    publish("gateway", private_key, "promotion.received", promotion)
    print("Promoção enviada para cadastro.")

def vote():
    vote = {
        "id": 1,
        "promotion_id": None,
    }

    print("========CADASTRAR PROMOÇÃO========")
    vote["promotion_id"] = input("Promoção: ")

    publish("gateway", private_key, "promotion.voto", vote)
    print("Voto enviada para cadastro.")

if __name__ == "__main__":
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
            vote()
        case "3":
            register_promotion()
    