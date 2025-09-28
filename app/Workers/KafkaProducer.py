import asyncio
import random
import sys
import uuid

# https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#adminclient
# но это почти не дружится из коробки с asyncio
# https://www.confluent.io/blog/kafka-python-asyncio-integration/
# from confluent_kafka import Producer
# https://aiokafka.readthedocs.io/en/stable/producer.html
from aiokafka import AIOKafkaProducer
from aiokafka.errors import BrokerResponseError, RequestTimedOutError

from .PayloadStructure import Payload


def error_callback(err):
    print(f'{__name__}: Something went wrong: {err}')


class KafkaProducer:
    def __init__(
            self,
            bootstrap_servers: str, timeouts: float,
            topic: str, title: str
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.timeouts = timeouts
        self.topic = topic
        self.title = title
        self.producer: AIOKafkaProducer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            request_timeout_ms=int(self.timeouts * 1000),
            # The default is acks=1 setting.
            # It will not wait for replica writes,
            # only for Leader to write the request.
            # The most durable setting is acks="all".
            # Broker will wait for all available replicas to write the request
            # before replying to Producer.
            # Broker will consult it’s min.insync.replicas setting
            # to know the minimal amount of replicas to write.
            acks='all',
            # As of Kafka 0.11 the Brokers support idempotent producing,that
            # will prevent the Producer from creating duplicates on retries.
            # This option will change a bit the logic on message delivery:
            # - ack="all" will be forced
            # (If any other value is passed, a ValueError will be raised)
            # - In contrast to general mode,
            # will not raise RequestTimedOutError errors and will not
            # expire batch delivery after request_timeout_ms passed.
            enable_idempotence=True,
        )

    async def produce(self, payload: str) -> None:
        # aiokafka will retry most errors automatically,
        # but only until request_timeout_ms.
        # If a request is expired,
        # the last error will be raised to the application.
        # Retrying messages on application level after an error
        # will potentially lead to duplicates,
        # so it’s up to the user to decide.
        #
        # сейчас в настройках мы выставили enable_idempotence=True,
        # но всё равно будем обрабатывать RequestTimedOutError "персонально".
        # ... aiokafka will retry most errors automatically,
        # but only until request_timeout_ms.
        # ... if RequestTimedOutError is raised,
        # Producer can’t be sure if the Broker wrote the request or not.
        try:
            # в данном случае делаю вид, что ключ партиционирования таков, что
            # равномерно распределяет сообщения по партициям топика
            # (думаю, это в следующих модулях будем изучать)
            key_encoded = (
                    self.title + ': rand: ' + str(random.randint(1, 10))
            ).encode()
            # сообщение сериализуем бессмысленно через PayloadStructure,
            # просто потренироваться: парсить ввод с консоли в структуру,
            # заставлять пользователя что-то набирать форматированное,
            # избыточно для этого проекта;
            # просто добавляем поле dummy бессмысленное
            payload_encoded = Payload(
                message=payload,
                dummy=str(uuid.uuid4()),
            ).serialize()
            await self.producer.send_and_wait(
                topic=self.topic,
                key=key_encoded,
                value=payload_encoded
            )
        except RequestTimedOutError as err:
            print(err)
        except BrokerResponseError as err:
            print(err)

    async def run(self):
        await self.producer.start()
        print(
            f'[{self.title}] Готов к чтению из stdin. '
            f'Печатайте сообщения, жмите Enter.'
        )
        loop = asyncio.get_event_loop()

        while True:
            # Асинхронное чтение из stdin
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:  # EOF (например, Ctrl+D)
                break
            line = line.rstrip('\n')
            print(f'[{self.title}] Прочитано из stdin: {line!r}')

            # Отправляем сообщение в топик
            await self.produce(line)
            print(f'[{self.title}] Отправлено в топик: {line!r}')

        await self.producer.stop()
        print(f'[{self.title}] Завершён.')
