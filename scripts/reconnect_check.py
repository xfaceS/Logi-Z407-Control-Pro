"""Real-device reconnect check. Requests USB; does not change volume or bass."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.bluetooth.controller import Controller
from app.bluetooth.protocol import Command

async def run():
    controller = Controller(lambda kind, value: print(kind, 'redacted' if kind == 'devices' else value))
    devices = await controller.scan()
    if len(devices) != 1:
        raise RuntimeError('Expected one candidate')
    try:
        for index in range(3):
            print('Connection cycle', index + 1)
            await controller.connect(devices[0])
            await controller.send(Command.USB)
            await controller.disconnect()
    finally:
        await controller.close()

if __name__ == '__main__':
    asyncio.run(run())
