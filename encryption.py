from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
import base64

def generate_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,  # Cte no protocolo RSA
        key_size=2048
    )
    public_key = private_key.public_key()

    return private_key, public_key

def sign(private_key, message):
    signature = private_key.sign(
        message,
        padding.PSS(), # Preenche a mensagem com bytes aleatórios
        hashes.SHA256(), # Formata a mensagem
    )

    decoded_signature = base64.b64encode(signature).decode() # Converte bytes para string com caracteres

    return decoded_signature

def verify(public_key, message, signature):
    try:
        public_key.verify(
            base64.b64decode(signature), # Converte string para bytes
            message,
            padding.PSS(),
            hashes.SHA256(),
        )
        return True
    except InvalidSignature:
        return False
    