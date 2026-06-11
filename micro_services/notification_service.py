import asyncio
import os
from typing import Any

import httpx

from common import RabbitService


RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Promo Deals <onboarding@resend.dev>")


class NotificationService(RabbitService):
    def __init__(self):
        super().__init__("notificacao")

    async def send_email(self, to_email: str, subject: str, html: str) -> None:
        if not to_email:
            return

        if not RESEND_API_KEY:
            print(f"[notificacao] e-mail simulado para {to_email}: {subject}")
            return

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
                json={
                    "from": EMAIL_FROM,
                    "to": [to_email],
                    "subject": subject,
                    "html": html,
                },
            )
            response.raise_for_status()
        print(f"[notificacao] e-mail enviado para {to_email}: {subject}")

    async def handle_published(self, event: dict[str, Any]) -> None:
        promotion = event["content"]
        await self.send_email(
            promotion.get("store_email", ""),
            "Promocao aprovada",
            f"<p>Sua promocao <strong>{promotion['title']}</strong> foi aprovada.</p>",
        )
        await self.publish(
            "promocao.categoria",
            {
                "kind": "categoria",
                "promotion": promotion,
                "category": promotion["category"],
                "message": f"Nova promocao em {promotion['category']}: {promotion['title']}",
            },
        )

    async def handle_hot_deal(self, event: dict[str, Any]) -> None:
        hot_deal = event["content"]
        await self.send_email(
            hot_deal.get("store_email", ""),
            "Promocao tornou-se hot deal",
            f"<p>Sua promocao <strong>{hot_deal['title']}</strong> virou destaque.</p>",
        )
        await self.publish(
            "notificacao.hotdeal",
            {
                "kind": "hotdeal",
                "promotion": hot_deal,
                "category": hot_deal["category"],
                "message": f"Hot deal: {hot_deal['title']} atingiu {hot_deal['score']} votos.",
            },
        )

    async def handle_event(self, event: dict[str, Any]) -> None:
        if event["type"] == "promocao.publicada":
            await self.handle_published(event)
        elif event["type"] == "promocao.destaque":
            await self.handle_hot_deal(event)


async def main() -> None:
    service = NotificationService()
    await service.connect()
    print("[notificacao] aguardando promocao.publicada e promocao.destaque")
    await service.consume(
        "notification_service_queue",
        ["promocao.publicada", "promocao.destaque"],
        service.handle_event,
    )


if __name__ == "__main__":
    asyncio.run(main())
