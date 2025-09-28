import asyncio

from Workers.KafkaAdm import KafkaAdm
from Workers.KafkaConsumer import BatchMessageConsumer, SingleMessageConsumer
from Workers.KafkaProducer import KafkaProducer


async def main():
    topic = 'ya_kafka_project2'
    partitions = 3
    replicas = 2
    bootstrap_servers = 'kafka-0:9092'

    adm = KafkaAdm(
        title='KafkaAdm',
        bootstrap_servers=bootstrap_servers,
        timeouts=5.0,
    )
    adm.check_topic(
        topic=topic,
        partitions=partitions,
        replicas=replicas,
    )
    print(f'[{__name__}] Topic is checked ({topic}).')

    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        timeouts=5.0,
        topic=topic,
        title='MyStdin2TopicProducer',
    )
    single_consumer = SingleMessageConsumer(
        bootstrap_servers=bootstrap_servers,
        # или надо вообще уникальный? вопрос логики replicas: 2 в ТЗ
        group='SingleConsumerGroup',
        topic=topic,
        title='MySingleConsumer',
    )
    batch_consumer = BatchMessageConsumer(
        bootstrap_servers=bootstrap_servers,
        # или надо вообще уникальный? вопрос логики replicas: 2 в ТЗ
        group='BatchConsumerGroup',
        topic=topic,
        title='MyBatchConsumer',
    )

    # Запускаем все три корутины параллельно
    tasks = [
        asyncio.create_task(producer.run()),
        asyncio.create_task(single_consumer.run()),
        asyncio.create_task(batch_consumer.run()),
    ]

    # Ждём завершения всех
    await asyncio.gather(*tasks)

    print(f'[{__name__}] Все корутины завершены.')


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f'\n[{__name__}] Прервано пользователем.')
