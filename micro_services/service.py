import os
import json
import pika
import base64

from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

EXCHANGE = 'promotions' # Roteador de mensagens
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")

class Service:
    def __init__(self, name, routing_keys):
        self.name = name
        self.channel = self._setup_rabbitmq_exchange()
        self.private_key, self.public_key = self._generate_keys()      
        
        self._register_public_key()
        self._configure_queues(routing_keys)

        print(f"[{self.name}]Serviço rodando...")
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
        with open(f"public_keys/{self.name}_public_key.pem", "wb") as f:
            f.write(self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM, # Tipo de codificação
                format=serialization.PublicFormat.SubjectPublicKeyInfo # Estrutura da chave pública
            ))
    
    def get_public_key(service_name):
        path = f"/keys/{service_name}_public.pem"

        with open(path, "rb") as f:
            return serialization.load_pem_public_key(f.read())
        
    def _configure_queues(self, routing_keys):
        name_queue = f'{self.name}_queue'

        self.channel.queue_declare(queue=name_queue)

        for routing_key in routing_keys:
            self.channel.queue_bind(exchange=EXCHANGE, queue=name_queue, routing_key=routing_key)

        self.channel.basic_consume(queue=name_queue, on_message_callback=self.callback(), auto_ack=True)

    def _generate_signature(self, message):
        signature = self.private_key.sign(
            json.dumps(message).encode(), # Converte para bytes
            padding.PSS(), # Preenche a mensagem com bytes aleatórios
            hashes.SHA256(), # Formata a mensagem
        )

        decoded_signature = base64.b64encode(signature).decode() # Converte bytes para string com caracteres

        return decoded_signature

    def verify_event(self, event):
        event = json.loads(event) # Converte o JSON para dicionário
        public_key = self.get_public_key(event["producer"]) # Busca a chave pública do produtor da mensagem
    
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

    def publish(self, author, routing_key, content):
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

    def callback(self):
        # É necessário implementar o callback em cada serviço para processar as mensagens recebidas
        pass
    