# Promo Event Driven System

Sistema distribuido para gerenciamento e divulgacao de promocoes, implementado com microsservicos, RabbitMQ, REST, SSE e assinaturas RSA.

## Arquitetura

- **Frontend:** React + Vite + Axios + SSE.
- **MS Gateway/API:** FastAPI. Expoe REST, publica acoes no RabbitMQ, consome eventos dos demais servicos e entrega SSE filtrado por interesse.
- **MS Promocao:** consome `promocao.recebida`, valida a assinatura da loja e publica `promocao.publicada`.
- **MS Ranking:** consome `promocao.voto`, calcula score e publica `promocao.destaque` quando `HOT_DEAL_THRESHOLD` e atingido.
- **MS Notificacao:** consome `promocao.publicada` e `promocao.destaque`, envia e-mail por Resend quando configurado, e publica eventos para o Gateway.
- **RabbitMQ:** broker topic usado exclusivamente entre microsservicos.

Nao ha chamadas diretas entre microsservicos. Toda comunicacao interna passa pelo RabbitMQ.

## Eventos RabbitMQ

- Gateway publica: `promocao.recebida`, `promocao.voto`
- Gateway consome: `promocao.publicada`, `promocao.destaque`, `promocao.categoria`, `notificacao.hotdeal`
- Promocao consome: `promocao.recebida`
- Promocao publica: `promocao.publicada`
- Ranking consome: `promocao.voto`
- Ranking publica: `promocao.destaque`
- Notificacao consome: `promocao.publicada`, `promocao.destaque`
- Notificacao publica: `promocao.categoria`, `notificacao.hotdeal`

## Assinaturas digitais

Cada evento publicado no RabbitMQ e assinado pelo produtor com RSA/PSS/SHA-256. As chaves ficam em `micro_services/public_keys/`.

O cadastro de promocao tambem contem assinatura da loja. Para facilitar a demonstracao pelo frontend, o Gateway assina o payload com uma chave `loja_demo` quando a requisicao REST nao traz `store_public_key` e `store_signature`. O MS Promocao so publica a promocao se essa assinatura da loja for valida.

## Execucao

Copie o arquivo de ambiente, se necessario:

```bash
cp .env.example .env
```

Suba a aplicacao:

```bash
docker compose up --build
```

Acesse:

- Frontend: http://localhost:5173
- API Gateway: http://localhost:8000
- Swagger: http://localhost:8000/docs
- RabbitMQ Management: http://localhost:15672 (`guest` / `guest`)

## API REST principal

- `POST /promocoes`
- `GET /promocoes`
- `POST /promocoes/{promotion_id}/votos`
- `POST /usuarios/{user_id}/interesses`
- `DELETE /usuarios/{user_id}/interesses/{category}`
- `GET /sse/{user_id}`

## E-mail externo

Para usar Resend, configure no `.env`:

```env
RESEND_API_KEY=re_xxx
EMAIL_FROM=Promo Deals <onboarding@resend.dev>
```

Sem `RESEND_API_KEY`, o MS Notificacao imprime o envio simulado no log para permitir execucao local completa.
