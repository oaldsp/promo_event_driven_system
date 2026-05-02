from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
import base64
import json

def generate_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,  # Cte no protocolo RSA
        key_size=2048
    )
    public_key = private_key.public_key()

    return private_key, public_key

def generate_signature(self, message):
    signature = self.private_key.sign(
        json.dumps(message).encode(), # Converte para bytes
        padding.PSS(), # Preenche a mensagem com bytes aleatórios
        hashes.SHA256(), # Formata a mensagem
    )

    decoded_signature = base64.b64encode(signature).decode() # Converte bytes para string com caracteres

    return decoded_signature

def verify_event(self, event):
    event = json.loads(event) # Converte o JSON para dicionário
    public_key = self.rabbitmq.service_public_keys.get(event["producer"]) # Busca a chave pública do produtor da mensagem

    try:
        public_key.verify(
            base64.b64decode(event["signature"]), # Converte string para bytes
            json.dumps(event["content"]).encode(), # Converte para bytes para fazer a verificação
            padding.PSS(),
            hashes.SHA256(),
        )
        return True
    except InvalidSignature:
        return False
    