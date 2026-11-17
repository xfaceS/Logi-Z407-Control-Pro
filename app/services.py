import asyncio
import threading
from PySide6.QtCore import QObject, Signal
from .bluetooth.controller import Controller

class Worker(QObject):
    event = Signal(str, object)

    def __init__(self):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        self.controller = None
        self.started = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True, name='Z407 BLE')
        self.thread.start()
        self.started.wait(3)

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.controller = Controller(self.event.emit)
        self.started.set()
        self.loop.run_forever()
        self.loop.close()

    def submit(self, coroutine):
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        def done(result):
            try:
                result.result()
            except Exception as exc:
                self.event.emit('error', str(exc) or type(exc).__name__)
        future.add_done_callback(done)
        return future

    def shutdown(self):
        async def finish():
            self.controller.closed = True
            self.controller.auto_reconnect = False
            current = asyncio.current_task()
            tasks = [task for task in asyncio.all_tasks() if task is not current]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.controller.close()
        asyncio.run_coroutine_threadsafe(finish(), self.loop).result(timeout=10)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(3)
