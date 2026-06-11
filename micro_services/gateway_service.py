import asyncio
import json
import uuid
from contextlib import suppress
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field

from common import CryptoBox, RabbitService, now_iso
from promotion_service import store_signature_payload


app = FastAPI(title="Promo Event Driven Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromotionCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=2, max_length=500)
    category: str = Field(min_length=2, max_length=60)
    price: float = Field(gt=0)
    store_email: EmailStr
    store_public_key: str | None = None
    store_signature: str | None = None


class VoteCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=80)
    vote: Literal["positivo", "negativo"]


class InterestCreate(BaseModel):
    category: str = Field(min_length=2, max_length=60)


class GatewayState:
    def __init__(self):
        self.rabbit = RabbitService("gateway")
        self.store_crypto = CryptoBox("loja_demo")
        self.promotions: dict[str, dict[str, Any]] = {}
        self.interests: dict[str, set[str]] = {}
        self.sse_clients: dict[str, set[asyncio.Queue[dict[str, Any]]]] = {}
        self.lock = asyncio.Lock()
        self.consume_task: asyncio.Task | None = None

    def normalize_category(self, category: str) -> str:
        return category.strip().lower()

    def demo_store_signature(self, promotion: dict[str, Any]) -> tuple[str, str]:
        public_key = self.store_crypto.public_key_pem()
        signature = self.store_crypto.sign(store_signature_payload(promotion))
        return public_key, signature

    async def start(self) -> None:
        await self.rabbit.connect()
        self.consume_task = asyncio.create_task(
            self.rabbit.consume(
                "gateway_service_queue",
                ["promocao.publicada", "promocao.destaque", "promocao.categoria", "notificacao.hotdeal"],
                self.handle_event,
            )
        )

    async def stop(self) -> None:
        if self.consume_task:
            self.consume_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.consume_task
        if self.rabbit.connection:
            await self.rabbit.connection.close()

    async def handle_event(self, event: dict[str, Any]) -> None:
        event_type = event["type"]
        content = event["content"]

        if event_type == "promocao.publicada":
            async with self.lock:
                self.promotions[content["id"]] = content
            print(f"[gateway] promocao publicada recebida: {content['id']}")
            return

        if event_type == "promocao.destaque":
            async with self.lock:
                promotion = self.promotions.get(content["id"], {})
                promotion.update(content)
                promotion["hot_deal"] = True
                self.promotions[content["id"]] = promotion
            return

        if event_type in {"promocao.categoria", "notificacao.hotdeal"}:
            await self.forward_sse(content)

    async def forward_sse(self, notification: dict[str, Any]) -> None:
        category = self.normalize_category(notification["category"])
        kind = notification.get("kind")

        async with self.lock:
            targets: list[asyncio.Queue[dict[str, Any]]] = []
            for user_id, queues in self.sse_clients.items():
                user_interests = self.interests.get(user_id, set())
                if kind == "hotdeal" or category in user_interests:
                    targets.extend(queues)

        payload = {
            "id": str(uuid.uuid4()),
            "sent_at": now_iso(),
            **notification,
        }
        for queue in targets:
            await queue.put(payload)


state = GatewayState()


@app.on_event("startup")
async def startup() -> None:
    await state.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    await state.stop()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/promocoes", status_code=202)
async def create_promotion(data: PromotionCreate) -> dict[str, Any]:
    promotion = {
        "id": str(uuid.uuid4()),
        "title": data.title,
        "description": data.description,
        "category": state.normalize_category(data.category),
        "price": data.price,
        "store_email": data.store_email,
        "created_at": now_iso(),
    }

    if data.store_public_key and data.store_signature:
        promotion["store_public_key"] = data.store_public_key
        promotion["store_signature"] = data.store_signature
    else:
        public_key, signature = state.demo_store_signature(promotion)
        promotion["store_public_key"] = public_key
        promotion["store_signature"] = signature

    await state.rabbit.publish("promocao.recebida", promotion)
    return {"status": "recebida", "promotion": promotion}


@app.get("/promocoes")
async def list_promotions() -> list[dict[str, Any]]:
    async with state.lock:
        return sorted(state.promotions.values(), key=lambda item: item.get("published_at", ""), reverse=True)


@app.post("/promocoes/{promotion_id}/votos", status_code=202)
async def vote(promotion_id: str, data: VoteCreate) -> dict[str, Any]:
    async with state.lock:
        promotion = state.promotions.get(promotion_id)

    if not promotion:
        raise HTTPException(status_code=404, detail="Promocao nao encontrada ou ainda nao publicada")

    vote_event = {
        "promotion_id": promotion_id,
        "user_id": data.user_id,
        "vote": data.vote,
        "title": promotion["title"],
        "category": promotion["category"],
        "store_email": promotion["store_email"],
        "voted_at": now_iso(),
    }
    await state.rabbit.publish("promocao.voto", vote_event)
    return {"status": "voto_recebido", "vote": vote_event}


@app.post("/usuarios/{user_id}/interesses")
async def register_interest(user_id: str, data: InterestCreate) -> dict[str, Any]:
    category = state.normalize_category(data.category)
    async with state.lock:
        state.interests.setdefault(user_id, set()).add(category)
        categories = sorted(state.interests[user_id])
    return {"user_id": user_id, "categories": categories}


@app.delete("/usuarios/{user_id}/interesses/{category}")
async def remove_interest(user_id: str, category: str) -> dict[str, Any]:
    normalized = state.normalize_category(category)
    async with state.lock:
        state.interests.setdefault(user_id, set()).discard(normalized)
        categories = sorted(state.interests[user_id])
    return {"user_id": user_id, "categories": categories}


@app.get("/usuarios/{user_id}/interesses")
async def list_interests(user_id: str) -> dict[str, Any]:
    async with state.lock:
        categories = sorted(state.interests.get(user_id, set()))
    return {"user_id": user_id, "categories": categories}


@app.get("/sse/{user_id}")
async def sse(user_id: str) -> StreamingResponse:
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    async with state.lock:
        state.sse_clients.setdefault(user_id, set()).add(queue)

    async def event_stream():
        try:
            yield "event: conectado\ndata: {\"status\":\"ok\"}\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=20)
                    yield f"event: notificacao\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            async with state.lock:
                queues = state.sse_clients.get(user_id, set())
                queues.discard(queue)
                if not queues:
                    state.sse_clients.pop(user_id, None)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
