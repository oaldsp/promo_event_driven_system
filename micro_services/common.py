import asyncio
import base64
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aio_pika
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "promocoes")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
KEY_DIR = Path(os.getenv("KEY_DIR", "micro_services/public_keys"))
STORE_SIGNED_FIELDS = ("id", "title", "description", "category", "price", "store_email")


def canonical_json(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def store_signature_payload(promotion: dict[str, Any]) -> dict[str, Any]:
    return {field: promotion[field] for field in STORE_SIGNED_FIELDS}


class CryptoBox:
    def __init__(self, service_name: str):
        self.service_name = service_name
        KEY_DIR.mkdir(parents=True, exist_ok=True)
        self.private_path = KEY_DIR / f"{service_name}_private_key.pem"
        self.public_path = KEY_DIR / f"{service_name}_public_key.pem"
        self.private_key = self._load_or_create_private_key()
        self.public_key = self.private_key.public_key()
        self._write_public_key()

    def _load_or_create_private_key(self):
        if self.private_path.exists():
            return serialization.load_pem_private_key(self.private_path.read_bytes(), password=None)

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.private_path.write_bytes(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        return private_key

    def _write_public_key(self) -> None:
        self.public_path.write_bytes(
            self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

    def sign(self, payload: Any) -> str:
        signature = self.private_key.sign(
            canonical_json(payload),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode()

    @staticmethod
    def verify_with_public_pem(public_key_pem: str, payload: Any, signature: str) -> bool:
        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            public_key.verify(
                base64.b64decode(signature),
                canonical_json(payload),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )
            return True
        except (InvalidSignature, ValueError):
            return False

    def verify_event(self, event: dict[str, Any]) -> bool:
        producer = event.get("producer")
        if not producer:
            return False

        public_key_path = KEY_DIR / f"{producer}_public_key.pem"
        if not public_key_path.exists():
            return False

        return self.verify_with_public_pem(
            public_key_path.read_text(),
            event.get("content"),
            event.get("signature", ""),
        )

    def public_key_pem(self) -> str:
        return self.public_path.read_text()


class RabbitService:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.crypto = CryptoBox(service_name)
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.RobustChannel | None = None
        self.exchange: aio_pika.RobustExchange | None = None

    async def connect(self) -> None:
        for attempt in range(1, 31):
            try:
                self.connection = await aio_pika.connect_robust(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    login=os.getenv("RABBITMQ_USER", "guest"),
                    password=os.getenv("RABBITMQ_PASSWORD", "guest"),
                )
                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=20)
                self.exchange = await self.channel.declare_exchange(
                    EXCHANGE,
                    aio_pika.ExchangeType.TOPIC,
                    durable=True,
                )
                return
            except Exception as exc:
                if attempt == 30:
                    raise
                print(f"[{self.service_name}] RabbitMQ indisponivel ({exc}); tentativa {attempt}/30")
                await asyncio.sleep(2)

    async def publish(self, routing_key: str, content: dict[str, Any]) -> None:
        if self.exchange is None:
            raise RuntimeError("RabbitMQ nao conectado")

        event = {
            "id": str(uuid.uuid4()),
            "type": routing_key,
            "producer": self.service_name,
            "produced_at": now_iso(),
            "content": content,
            "signature": self.crypto.sign(content),
        }
        await self.exchange.publish(
            aio_pika.Message(
                body=json.dumps(event, ensure_ascii=False).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )
        print(f"[{self.service_name}] publicou {routing_key}: {content.get('id')}")

    async def consume(self, queue_name: str, routing_keys: list[str], handler) -> None:
        if self.channel is None or self.exchange is None:
            raise RuntimeError("RabbitMQ nao conectado")

        queue = await self.channel.declare_queue(queue_name, durable=True)
        for routing_key in routing_keys:
            await queue.bind(self.exchange, routing_key)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    event = json.loads(message.body.decode())
                    if not self.crypto.verify_event(event):
                        print(f"[{self.service_name}] assinatura invalida em {event.get('type')}")
                        continue
                    await handler(event)
