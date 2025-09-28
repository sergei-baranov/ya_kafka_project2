# Учебный проект "Практическая работа 2" курса "Apache Kafka для разработки и архитектуры" Я.Практикума

Разворачиваем контейнеры, заходим в любой или оба из python-app-из-них,
там запускаем консольное приложение через `python main.py`.

Запускается один продъюсер и два консьюмера согласно ТЗ.

Отправить сообщение в топик - написать в консоли текст и нажать [Enter].

Консьюмеры всё, что читают, тоже отправляют на консоль согласно бизнес-логике из ТЗ
(один каждое прочитанное сообщение, второй каждые 10, относятся к разным группам,
соотв. читают те же сообщения из топика).

При запуске приложения в двух контейнерах - сработает параллельное чтение
топика консьюмерами из разных партиций, так как каждому из двух консьюмеров
задана своя группа, но одна и то же в двух контейнерах.

**NB:** порт для http-ui - **8070**

- [Как запустить ансамбль контейнеров](#compose_up)
- [Как погасить ансамбль](#compose_down)
- [Тестирование](#test_1)
- [Тестирование двух приложений в параллели (у нас `deploy/replicas: 2`)](#test_2)
- [Тестирование: смотрим web-ui](#test_3)
- [Реализуйте сериализацию и десериализацию. Формат данных выберите по желанию.](#serialization)
- [Обеспечьте гарантии доставки сообщений.](#acks)

## <a name="compose_up">Как запустить ансамбль контейнеров</a>

```bash
sudo docker compose --env-file .env.39 up -d
```

если что-то правили в приложении и надо пересобрать его:

```bash
sudo docker compose --env-file .env.39 up -d --build
```

если игрались с кодом в вольюме, и надо восстановить исходники,
перед этим сделать что-то типа:

```bash
sudo docker volume remove ya_kafka_project2_python_app
```

## <a name="compose_down">Как погасить ансамбль</a>

```bash
sudo docker compose --env-file .env.39 down
```

## <a name="test_1">Тестирование</a>

Заходим в один из контейнеров приложения

```bash
tesla@tesla:~/VCS/ya_kafka_project2$ sudo docker exec -it ya_kafka_project2-python-app-1 bash
root@d88df46480a1:/app#
```

запускаем программу

```bash
root@d88df46480a1:/app# python main.py
[__main__] Topic is checked (ya_kafka_project2).
[MySingleConsumer] Инстанциирован.
[MyBatchConsumer] Инстанциирован.
[MySingleConsumer] Подписан.
[MyBatchConsumer] Подписан.
[MyStdin2TopicProducer] Готов к чтению из stdin. Печатайте сообщения, жмите Enter.
[MySingleConsumer] Запущен.
[MyBatchConsumer] Запущен.
```

печатаем сообщения в консоль,
смотрим сообщения и ошибки в той же консоли

```bash
...
фыва олдж
[MyStdin2TopicProducer] Прочитано из stdin: 'фыва олдж'
[MyStdin2TopicProducer] Отправлено в топик: 'фыва олдж'


[MySingleConsumer] Получен пакет сообщений: 1 шт.
ya_kafka_project2:0:28: key=MyStdin2TopicProducer: rand: 3 timestamp_ms=1759060316600
payload.message: фыва олдж
payload.dummy: a5d0998c-5e9c-4538-8e56-9ed7ce02f872

...

10
[MyStdin2TopicProducer] Прочитано из stdin: '10'
[MyStdin2TopicProducer] Отправлено в топик: '10'


[MyBatchConsumer] Получен пакет сообщений: 10 шт.
ya_kafka_project2:0:28: key=MyStdin2TopicProducer: rand: 3 timestamp_ms=1759060316600
payload.message: фыва олдж
payload.dummy: a5d0998c-5e9c-4538-8e56-9ed7ce02f872
ya_kafka_project2:1:20: key=MyStdin2TopicProducer: rand: 4 timestamp_ms=1759060330461
payload.message: asdf 123
payload.dummy: d1143fd7-e86d-4d8e-a7a6-8ce00b4afc96
ya_kafka_project2:0:29: key=MyStdin2TopicProducer: rand: 2 timestamp_ms=1759060338424
...
payload.message: 10
payload.dummy: 840fcb12-a901-49dd-865d-a640f8e870e4
```

Остановить приложение: `Ctrl+C` несколько раз :)

(Остановить продъюсера можно через `Ctrl+D`,
но корутины консьюмеров продолжат работать.)

## <a name="test_2">Тестирование двух приложений в параллели (у нас `deploy/replicas: 2`)</a>

В данной реализации имена групп зашиты в коде,
поэтому когда мы запускаем приложение из второго контейнера,
консьюмеры читают не все отправленные продъюсером сообщения,
а только из тех партиций топика, что им набалансировала Кафка.

Открываем терминалы в два контейнера с приложением, в одном например пишем,
в обоих читаем:

`ya_kafka_project2-python-app-1`:

```bash
$ sudo docker exec -it ya_kafka_project2-python-app-1 bash
root@d88df46480a1:/app# python main.py
[__main__] Topic is checked (ya_kafka_project2).
...
[MyStdin2TopicProducer] Готов к чтению из stdin. Печатайте сообщения, жмите Enter.

[MyStdin2TopicProducer] Прочитано из stdin: ''
[MyStdin2TopicProducer] Отправлено в топик: ''

[MySingleConsumer] Получен пакет сообщений: 1 шт.
ya_kafka_project2:0:34: key=MyStdin2TopicProducer: rand: 1 timestamp_ms=1759060543469
payload.message: 
payload.dummy: 60219f7f-21ed-4c87-93a4-d0b9b9019f13


Heartbeat failed for group BatchConsumerGroup because it is rebalancing
Heartbeat failed for group SingleConsumerGroup because it is rebalancing
qwerty
[MyStdin2TopicProducer] Прочитано из stdin: 'qwerty'
[MyStdin2TopicProducer] Отправлено в топик: 'qwerty'
asdfg
[MyStdin2TopicProducer] Прочитано из stdin: 'asdfg'
[MyStdin2TopicProducer] Отправлено в топик: 'asdfg'


[MySingleConsumer] Получен пакет сообщений: 1 шт.
ya_kafka_project2:1:23: key=MyStdin2TopicProducer: rand: 4 timestamp_ms=1759060587614
payload.message: asdfg
payload.dummy: 882c23f4-be8b-4ec5-8e8a-5f031caed15c
```

`ya_kafka_project2-python-app-2`:

```bash
$ sudo docker exec -it ya_kafka_project2-python-app-2 bash
root@ed08d925c797:/app# python main.py
[__main__] Topic is checked (ya_kafka_project2).
[MySingleConsumer] Инстанциирован.
[MyBatchConsumer] Инстанциирован.
[MySingleConsumer] Подписан.
[MyBatchConsumer] Подписан.
[MyStdin2TopicProducer] Готов к чтению из stdin. Печатайте сообщения, жмите Enter.
[MyBatchConsumer] Запущен.
[MySingleConsumer] Запущен.


[MySingleConsumer] Получен пакет сообщений: 1 шт.
ya_kafka_project2:0:35: key=MyStdin2TopicProducer: rand: 2 timestamp_ms=1759060581111
payload.message: qwerty
payload.dummy: ee3a1e0f-1719-4b9e-9ffd-12e0106a888f

```

В этом смысле (чтение разных партиций в одной группе) всё нормально.

Видим так же ребалансировку при подключении консьюмеров в группу - радуемся.

## <a name="test_3">Тестирование: смотрим web-ui</a>

**NB:** порт для http-ui - **8070**

Идём в браузере на порт 8070 хоста, на котором развернули контейнеры,
допустим это localhost, и там смотрим всякое

`http://localhost:8070/ui/clusters/kraft/all-topics/ya_kafka_project2/messages` - там можно и отправлять сообщения,
но надо сериализовать руками. Ну можно потестить, отправив несериализованное (приложение упадёт некрасиво (TODO)).

## <a name="serialization">Реализуйте сериализацию и десериализацию. Формат данных выберите по желанию.</a>

см. `ya_kafka_project2/app/Workers/PayloadStructure.py`

и работу с ним продъюсером и консьюмером

TODO: обработка ошибок при невозможности десериализации

## <a name="acks">Обеспечьте гарантии доставки сообщений.</a>

Использовал библиотеку `aiokafka==0.12.0`, её соотв. настройки продъюсера
см. в `ya_kafka_project2/app/Workers/KafkaProducer.py`

понавставлял в код комментов из доки либы
