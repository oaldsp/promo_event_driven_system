import os
import json
import pika
import base64

from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

EXCHANGE = 'promotions' # Roteador de mensagens
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT"))

class Service:
    def __init__(self, name, routing_keys=[], consume=True):
        self.name = name
        self.channel = self._setup_rabbitmq_exchange()
        self.private_key, self.public_key = self._generate_keys()      
        
        self._register_public_key()
        self._configure_queues(routing_keys)

        print(f"[{self.name}]Serviço rodando...")
        if consume:
            self.channel.start_consuming()

    def _setup_rabbitmq_exchange(self):
        # BlockingConnection -> Espera a resposta para cada ação
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq", port=RABBITMQ_PORT)
        )
        channel = connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE,  
            exchange_type='topic'
        )

        return channel

    def _generate_keys(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,  # Cte no protocolo RSA
            key_size=2048
        )
        public_key = private_key.public_key()

        return private_key, public_key

    def _register_public_key(self):
        with open(f"micro_services/public_keys/{self.name}_public_key.pem", "wb") as f:
            f.write(self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM, # Tipo de codificação
                format=serialization.PublicFormat.SubjectPublicKeyInfo # Estrutura da chave pública
            ))
    
    def _get_public_key(self, service_name):
        path = f"micro_services/public_keys/{service_name}_public_key.pem"

        with open(path, "rb") as f:
            return serialization.load_pem_public_key(f.read())
        
    def _configure_queues(self, routing_keys):
        name_queue = f'{self.name}_queue'

        self.channel.queue_declare(queue=name_queue)

        for routing_key in routing_keys:
            self.channel.queue_bind(exchange=EXCHANGE, queue=name_queue, routing_key=routing_key)

        self.channel.basic_consume(queue=name_queue, on_message_callback=self.callback, auto_ack=True)

    def _generate_signature(self, message):
        signature = self.private_key.sign(
            json.dumps(message).encode(), # Converte para bytes
            # Preenche a mensagem com bytes aleatórios
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), # Gera máscaras pseudoaleatórias usando SHA-256.
                salt_length=padding.PSS.MAX_LENGTH # Utiliza o maior salt permitido pela chave, aumentando a segurança.
            ),
            hashes.SHA256(), # Formata a mensagem
        )

        decoded_signature = base64.b64encode(signature).decode() # Converte bytes para string com caracteres

        return decoded_signature

    def _verify_event(self, event):
        event = json.loads(event) # Converte o JSON para dicionário
        public_key = self._get_public_key(event["producer"]) # Busca a chave pública do produtor da mensagem
    
        try:
            public_key.verify(
                base64.b64decode(event["signature"]), # Converte string para bytes
                json.dumps(event["content"]).encode(), # Converte para bytes para fazer a verificação
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()), 
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256(),
            )
            return True
        except InvalidSignature:
            return False

    def _publish(self, author, routing_key, content):
        signature = self._generate_signature(content)

        event = {
            "content": content,
            "signature": signature,
            "producer": author
        }

        self.channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key, # Cabeçalho da mensagem
            body=json.dumps(event)
        )
        print(f"[{content['id']}] Evento publicado")

    def callback(self, ch, method, properties, body):
        # É necessário implementar o callback em cada serviço para processar as mensagens recebidas
        pass
    