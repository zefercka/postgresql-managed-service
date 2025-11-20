import dramatiq
from app.config import settings
from dramatiq.brokers.rabbitmq import RabbitmqBroker

rabbitmq_broker = RabbitmqBroker(
    url=settings.RABBITMQ_CONNECTION_URL,
    confirm_delivery=True,
)

dramatiq.set_broker(rabbitmq_broker)
