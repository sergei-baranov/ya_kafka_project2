import asyncio

# https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#adminclient
# но это практически не дружится из коробки с asyncio
# from confluent_kafka import Consumer
# https://aiokafka.readthedocs.io/en/stable/consumer.html
from aiokafka import AIOKafkaConsumer, ConsumerRecord

from .PayloadStructure import deserialize2payload, Payload


class KafkaConsumer:
    def __init__(self, bootstrap_servers: str, group: str,
                 topic: str, title: str,
                 auto_commit: bool = True, poll_records: int = 1,
                 ):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.title = title
        self.group = group
        self.auto_commit = auto_commit
        self.poll_records = poll_records

        self.consumer = AIOKafkaConsumer(
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group,
            auto_offset_reset='earliest',
            request_timeout_ms=(4 * 1000),
            enable_auto_commit=self.auto_commit,
            max_poll_records=self.poll_records,
        )

        print(f'[{self.title}] Инстанциирован.')

    async def process_msg_buffer(self, buffer: list[ConsumerRecord]):
        # sleep для удобства восприятия учебного приложения на консоли
        # (иначе оно как бы читает раньше, чем отправляет)
        await asyncio.sleep(0.5)

        print('\n')
        print(f'[{self.title}] Получен пакет сообщений: {len(buffer)} шт.')
        for msg in buffer:
            key_decoded = msg.key.decode()
            print(
                '{}:{:d}:{:d}: key={} timestamp_ms={}'.format(
                    msg.topic, msg.partition, msg.offset, key_decoded,
                    msg.timestamp)
            )
            payload: Payload = deserialize2payload(msg.value)
            print(f'payload.message: {payload.message}')
            print(f'payload.dummy: {payload.dummy}')
        print('\n')

    async def run(self):
        buffer = []

        self.consumer.subscribe([self.topic])
        print(f'[{self.title}] Подписан.')

        await self.consumer.start()
        print(f'[{self.title}] Запущен.')

        try:
            async for msg in self.consumer:
                buffer.append(msg)
                if len(buffer) >= self.poll_records:
                    await self.process_msg_buffer(buffer)
                    if not self.auto_commit:
                        await self.consumer.commit()
                    buffer = []
        finally:
            await self.consumer.stop()


class SingleMessageConsumer(KafkaConsumer):
    def __init__(self,
                 bootstrap_servers: str, group: str,
                 topic: str, title: str,
                 ):
        super().__init__(
            bootstrap_servers=bootstrap_servers, group=group,
            topic=topic, title=title,
            auto_commit=True, poll_records=1
        )


class BatchMessageConsumer(KafkaConsumer):
    def __init__(self,
                 bootstrap_servers: str, group: str,
                 topic: str, title: str,
                 ):
        super().__init__(
            bootstrap_servers=bootstrap_servers, group=group,
            topic=topic, title=title,
            auto_commit=False, poll_records=10
        )
