import asyncio
import sys


class Reader:
    def __init__(self, queues):
        self.queues = queues  # список очередей, в которые будем писать

    async def run(self):
        print("[Reader] Готов к чтению из stdin...", file=sys.stderr)
        loop = asyncio.get_event_loop()

        while True:
            # Асинхронное чтение из stdin
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:  # EOF (например, Ctrl+D)
                break
            line = line.rstrip('\n')
            print(f"[Reader] Прочитано: {line!r}", file=sys.stderr)

            # Отправляем строку во все очереди
            for q in self.queues:
                await q.put(line)

        # Отправляем сигнал завершения во все очереди
        for q in self.queues:
            await q.put(None)
        print("[Reader] Завершён.", file=sys.stderr)


class Writer:
    def __init__(self, queue, name="[Writer]", transform_func=None, delay=0.5):
        self.queue = queue
        self.name = name
        self.transform_func = transform_func or (lambda x: x)
        self.delay = delay

    async def run(self):
        print(f"{self.name} Запущен.", file=sys.stderr)
        while True:
            item = await self.queue.get()
            if item is None:
                self.queue.task_done()
                break

            await asyncio.sleep(self.delay)  # имитация обработки
            result = self.transform_func(item)
            print(f"{self.name} Обработал: {result}")

            self.queue.task_done()

        print(f"{self.name} Завершён.", file=sys.stderr)


# Конкретные реализации writer'ов (можно и без них — через параметры выше)
class Writer1(Writer):
    def __init__(self, queue):
        super().__init__(
            queue,
            name="[Writer1]",
            transform_func=str.upper,
            delay=0.5
        )


class Writer2(Writer):
    def __init__(self, queue):
        super().__init__(
            queue,
            name="[Writer2]",
            transform_func=lambda s: s[::-1],  # переворот строки
            delay=0.3
        )


async def main():
    # Создаём отдельные очереди для каждого writer'а
    q1 = asyncio.Queue()
    q2 = asyncio.Queue()

    # Создаём объекты
    reader = Reader([q1, q2])
    writer1 = Writer1(q1)
    writer2 = Writer2(q2)

    # Запускаем все три корутины параллельно
    tasks = [
        asyncio.create_task(reader.run()),
        asyncio.create_task(writer1.run()),
        asyncio.create_task(writer2.run()),
    ]

    # Ждём завершения всех
    await asyncio.gather(*tasks)

    print("[Main 2] Все корутины завершены.", file=sys.stderr)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Main 2] Прервано пользователем.", file=sys.stderr)
