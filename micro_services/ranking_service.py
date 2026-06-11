import asyncio
import os
from typing import Any

from common import RabbitService, now_iso


HOT_DEAL_THRESHOLD = int(os.getenv("HOT_DEAL_THRESHOLD", "3"))


class RankingService(RabbitService):
    def __init__(self):
        super().__init__("ranking")
        self.scores: dict[str, int] = {}
        self.hot_deals: set[str] = set()

    async def handle_vote(self, event: dict[str, Any]) -> None:
        vote = event["content"]
        promotion_id = vote["promotion_id"]
        delta = 1 if vote["vote"] == "positivo" else -1
        score = self.scores.get(promotion_id, 0) + delta
        self.scores[promotion_id] = score

        print(f"[ranking] {promotion_id} recebeu voto {vote['vote']}; score={score}")

        if score >= HOT_DEAL_THRESHOLD and promotion_id not in self.hot_deals:
            self.hot_deals.add(promotion_id)
            await self.publish(
                "promocao.destaque",
                {
                    "id": promotion_id,
                    "title": vote["title"],
                    "category": vote["category"],
                    "store_email": vote["store_email"],
                    "score": score,
                    "threshold": HOT_DEAL_THRESHOLD,
                    "hot_deal": True,
                    "highlighted_at": now_iso(),
                },
            )
            print(f"[ranking] hot deal: {promotion_id}")


async def main() -> None:
    service = RankingService()
    await service.connect()
    print("[ranking] aguardando promocao.voto")
    await service.consume("ranking_service_queue", ["promocao.voto"], service.handle_vote)


if __name__ == "__main__":
    asyncio.run(main())
