import asyncio
from typing import Any

from common import CryptoBox, RabbitService, now_iso, store_signature_payload


class PromotionService(RabbitService):
    def __init__(self):
        super().__init__("promocao")
        self.promotions: dict[str, dict[str, Any]] = {}

    async def handle_promotion_received(self, event: dict[str, Any]) -> None:
        promotion = event["content"]
        store_public_key = promotion.get("store_public_key")
        store_signature = promotion.get("store_signature")

        if not store_public_key or not store_signature:
            print("[promocao] cadastro rejeitado: assinatura da loja ausente")
            return

        if not CryptoBox.verify_with_public_pem(
            store_public_key,
            store_signature_payload(promotion),
            store_signature,
        ):
            print(f"[promocao] cadastro rejeitado: assinatura da loja invalida ({promotion.get('id')})")
            return

        published = {
            **promotion,
            "status": "publicada",
            "score": 0,
            "hot_deal": False,
            "published_at": now_iso(),
        }
        self.promotions[published["id"]] = published
        await self.publish("promocao.publicada", published)
        print(f"[promocao] publicada: {published['id']} - {published['title']}")


async def main() -> None:
    service = PromotionService()
    await service.connect()
    print("[promocao] aguardando promocao.recebida")
    await service.consume(
        "promocao_service_queue",
        ["promocao.recebida"],
        service.handle_promotion_received,
    )


if __name__ == "__main__":
    asyncio.run(main())
