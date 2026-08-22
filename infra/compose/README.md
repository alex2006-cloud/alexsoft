# Docker Compose

Локальный контур на ноутбуке. Порядок появления сервисов: PostgreSQL → Redis → MinIO → Loki/Prometheus/Grafana → продукты → RabbitMQ.

Файл `docker-compose.yml` добавляется, когда поднимаем первую зависимость (этап данных).
