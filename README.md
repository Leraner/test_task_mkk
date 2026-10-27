# Сервис процессинга платежей

Асинхронный микросервис: принимает платежи по API, обрабатывает их через эмуляцию платёжного шлюза и уведомляет клиента о результате через webhook.

**Стек:** Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), PostgreSQL, RabbitMQ (FastStream), Alembic, dishka, Docker Compose.

## Быстрый старт

```bash
cp .env.example .env   # задать пароли и API_KEY
docker compose up -d --build
```

Поднимаются:

| Сервис | Назначение |
|---|---|
| `database` | PostgreSQL |
| `rabbitmq` | RabbitMQ, management UI на http://localhost:15672 |
| `migrations` | применяет миграции Alembic и завершается |
| `api` | HTTP API на http://localhost:8000, Swagger - http://localhost:8000/docs |
| `outbox-relay` | публикует события из outbox в RabbitMQ |
| `consumer` | обрабатывает платежи и отправляет webhook |

## API

Все эндпоинты `/api/v1` требуют заголовок `X-API-Key` со значением `API_KEY` из `.env`; без него или с неверным ключом - `401`. Для примеров ниже:

```bash
export API_KEY=$(grep '^API_KEY=' .env | cut -d= -f2-)
```

### Создание платежа

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: 6f1c2a3e-order-42" \
  -H "Content-Type: application/json" \
  -d '{
        "amount": "1500.00",
        "currency": "RUB",
        "description": "Заказ №42",
        "metadata": {"order_id": 42},
        "webhook_url": "https://example.com/webhooks/payments"
      }'
```

`202 Accepted`:

```json
{
  "success": true,
  "data": {
    "payment_id": "01a17eba-e40f-77e8-ae7d-01b7015f8abb",
    "status": "pending",
    "created_at": "2026-10-27T18:58:59.741917Z"
  },
  "error_code": null,
  "error_message": null
}
```

- `Idempotency-Key` обязателен. Повтор с тем же ключом и тем же телом возвращает тот же платёж, новый не создаётся.
- Тот же ключ с другим телом - `422 IdempotencyKeyReusedError`.
- `currency`: `RUB`, `USD`, `EUR`; `amount` - положительное, не больше 2 знаков после запятой; `metadata` необязательно.

### Получение платежа

```bash
curl http://localhost:8000/api/v1/payments/01a17eba-e40f-77e8-ae7d-01b7015f8abb \
  -H "X-API-Key: $API_KEY"
```

```json
{
  "success": true,
  "data": {
    "payment_id": "01a17eba-e40f-77e8-ae7d-01b7015f8abb",
    "amount": "1500.00",
    "currency": "RUB",
    "description": "Заказ №42",
    "metadata": {"order_id": 42},
    "status": "succeeded",
    "created_at": "2026-10-27T18:58:59.741917Z",
    "processed_at": "2026-10-27T18:59:04.729545Z"
  },
  "error_code": null,
  "error_message": null
}
```

Нет платежа - `404 PaymentNotFoundError`.

### Webhook

После обработки сервис отправляет `POST` на `webhook_url`:

```json
{
  "payment_id": "01a17eba-e40f-77e8-ae7d-01b7015f8abb",
  "status": "succeeded",
  "amount": "1500.00",
  "currency": "RUB",
  "processed_at": "2026-10-27T18:59:04.729545+00:00"
}
```

Webhook может прийти повторно, получатель отсекает дубли по `payment_id`. Для ручной проверки удобно взять адрес на https://webhook.site.

## Как это работает

```
POST /payments ─► payments + outbox ─► outbox-relay ─► exchange "payments" ─► payments.new ─► consumer
                  (одна транзакция)                     routing key                          │
                                                        payment.created                      ▼
                                                                         шлюз (2-5 с, 90% успех) → статус в БД → webhook
```

1. **API** в одной транзакции сохраняет платёж в статусе `pending` и событие в таблицу `outbox`.
2. **Outbox relay** забирает неотправленные события пачками (`FOR UPDATE SKIP LOCKED`, можно запускать несколько экземпляров), публикует их в exchange `payments` и отмечает отправленными только после подтверждения брокера (publisher confirms). Если очередь для события ещё не объявлена, брокер возвращает сообщение, и событие остаётся в outbox до следующей попытки.
3. **Consumer** получает событие из `payments.new`, вызывает эмулятор шлюза, записывает `succeeded`/`failed` и отправляет webhook. 10% «ошибок» шлюза - это отказ в платеже: статус `failed`, webhook уходит с ним же.

### Идемпотентность

- **Создание платежа.** Insert-first с уникальным ограничением на `idempotency_key`, без предварительного SELECT и гонок. Тело запроса сравнивается по SHA-256 отпечатку.
- **Обработка.** Доставка сообщений at-least-once, поэтому дубли возможны. Статус записывается условным `UPDATE ... WHERE status = 'PENDING'`: уже обработанный платёж не проводится повторно, а только повторяет webhook.

### Повторы и DLQ

| Ситуация | Что происходит |
|---|---|
| Webhook не дошёл: сеть, таймаут, 5xx, 408, 429 | 1 попытка + 3 повтора через retry-очереди: `payments.new.retry.1` (2 с), `.retry.2` (4 с), `.retry.3` (8 с); после 4-й неудачной попытки - `payments.new.dlq` |
| Получатель отклонил webhook: прочие 4xx и 3xx | сразу в DLQ, повтор не поможет |
| Недоступна БД | повторы внутри consumer с экспоненциальной паузой (tenacity) до 60 с, затем сообщение возвращается в очередь; в DLQ не уходит |
| Битое сообщение, платёж не найден | сразу в DLQ |

Число попыток задаёт `PAYMENTS_MAX_ATTEMPTS` (включая первую), retry-очередей на одну меньше. Retry-очереди - очереди без подписчиков с TTL: по истечении срока RabbitMQ возвращает сообщение в `payments.new`. Номер попытки хранится в заголовке `x-retry-count` и переживает рестарт consumer. DLQ подключена к `payments.new` через dead-letter exchange.

Consumer берёт в работу не больше `CONSUMER_PREFETCH_COUNT` сообщений одновременно (по умолчанию 100), остальные ждут в очереди. Пропускная способность одного consumer - около 30 платежей в секунду, больше - `docker compose up -d --scale consumer=N`.

## Конфигурация

Все параметры - в `.env.example` с комментариями. Обязательные: имя БД, логины и пароли PostgreSQL и RabbitMQ, `API_KEY`. Остальные (размер пачки relay, число попыток и задержки webhook, prefetch и т.д.) можно не задавать - используются значения по умолчанию.

После изменения задержек повторов уже созданные retry-очереди нужно удалить в RabbitMQ: аргументы очереди нельзя поменять после создания.

## Структура

```
src/
├── payments/                 # bounded context платежей
│   ├── domain/               # сущность Payment, value objects, доменные ошибки, интерфейсы
│   ├── application/          # use cases: создание, получение и обработка платежа
│   └── infrastructure/
│       ├── api/              # роуты FastAPI, web-модели
│       ├── db/               # ORM-модели, репозитории, спецификации, Unit of Work
│       ├── messaging/        # топология RabbitMQ: exchange, очереди, DLQ, retry
│       ├── outbox/           # outbox relay
│       ├── consumer/         # consumer payments.new
│       ├── gateway/          # эмулятор платёжного шлюза
│       └── webhook/          # отправка webhook
├── shared/                   # каркас: FastAPI-приложение, DI, база для БД, миграции
└── shared_kernel/            # базовые доменные ошибки и интерфейс Unit of Work
```

## Нагрузочный тест

```bash
docker compose -f docker-compose.yml -f tests/load/docker-compose.load.yml up -d --build
uv run locust -f tests/load/locustfile.py --host http://localhost:8000
```

UI locust - http://127.0.0.1:8089. Override добавляет приёмник webhook `webhook-sink` (путь `/flaky` отвечает 500 на 10% запросов, чтобы работали повторы) и разрешает consumer отправку на адреса внутренней сети. Сценарий: создание платежей, чтение и повтор с тем же `Idempotency-Key`.

Результаты на одной машине (300 пользователей): API - около 900 RPS, медиана 16 мс, p95 110 мс, без ошибок; потерянных сообщений и попаданий в DLQ от перегрузки нет.

## Разработка

```bash
uv sync
uv run ruff check src tests
uv run ruff format src tests
```

Новая миграция - с запущенной БД, под владельцем БД. Настройки читаются из переменных окружения, а не из `.env`, поэтому его нужно экспортировать:

```bash
set -a; source .env; set +a
POSTGRES_HOST=localhost uv run alembic revision --autogenerate -m "описание"
```
