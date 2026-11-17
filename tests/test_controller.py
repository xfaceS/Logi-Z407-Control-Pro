import asyncio
from types import SimpleNamespace
import pytest
from app.bluetooth.controller import Controller
from app.bluetooth.protocol import Command, SERVICE, COMMAND, RESPONSE

class Services:
    def get_service(self, uuid): return uuid == SERVICE
    def get_characteristic(self, uuid): return uuid in (COMMAND, RESPONSE)

class FakeClient:
    def __init__(self, device, disconnected_callback, **kwargs):
        self.services = Services()
        self.lost = disconnected_callback
        self.writes = []
        self.respond = True
        self.connected = False
    async def connect(self): self.connected = True
    async def disconnect(self): self.connected = False
    async def start_notify(self, uuid, callback): self.notify = callback
    async def write_gatt_char(self, uuid, data, response):
        self.writes.append(data)
        assert response is False
        if not self.respond: return
        if data == b'\x84\x05': self.notify(None, b'\xd4\x05\x01')
        elif data == b'\x84\x00':
            self.notify(None, b'\xd4\x00\x01')
            self.notify(None, b'\xd4\x00\x03')
        else: self.notify(None, bytes((data[0] + 0x40, data[1])))

@pytest.mark.asyncio
async def test_handshake_and_all_commands():
    events = []
    controller = Controller(lambda *event: events.append(event), FakeClient)
    await controller.connect('test-only')
    assert controller.ready
    assert controller.client.writes == [b'\x84\x05', b'\x84\x00']
    for command in Command:
        await controller.send(command)
    assert [event[1] for event in events if event[0] == 'command'] == [c.name for c in Command]
    await controller.close()
    assert not controller.ready

@pytest.mark.asyncio
async def test_missing_handshake_never_ready():
    class Silent(FakeClient):
        async def write_gatt_char(self, *args, **kwargs): pass
    controller = Controller(client_factory=Silent)
    controller.timeout = .02
    with pytest.raises(RuntimeError, match='handshake timed out'): await controller.connect('test-only')
    assert not controller.ready and controller.client is None

@pytest.mark.asyncio
async def test_observed_firmware_without_final_notification():
    class ObservedFirmware(FakeClient):
        async def write_gatt_char(self, uuid, data, response):
            if data == b'\x84\x00':
                self.notify(None, b'\xd4\x00\x01')
            else:
                await super().write_gatt_char(uuid, data, response)
    controller = Controller(client_factory=ObservedFirmware)
    await controller.connect('test-only')
    assert controller.ready
    await controller.send(Command.BASS_DOWN)
    await controller.close()

@pytest.mark.asyncio
async def test_observed_reconnect_with_only_connected_notification():
    class ReconnectedFirmware(FakeClient):
        async def write_gatt_char(self, uuid, data, response):
            if data == b'\x84\x00':
                self.notify(None, b'\xd4\x00\x03')
            else:
                await super().write_gatt_char(uuid, data, response)
    controller = Controller(client_factory=ReconnectedFirmware)
    await controller.connect('test-only')
    assert controller.ready
    await controller.send(Command.BASS_UP)
    await controller.close()

@pytest.mark.asyncio
async def test_timeout_does_not_retry_uncertain_adjustment():
    controller = Controller(client_factory=FakeClient)
    await controller.connect('test-only')
    client = controller.client
    client.respond = False
    controller.timeout = .02
    with pytest.raises(RuntimeError): await controller.send(Command.BASS_UP)
    assert client.writes.count(Command.BASS_UP.value) == 1
    assert not controller.ready

@pytest.mark.asyncio
async def test_queue_serialization_and_stale_drop():
    controller = Controller(client_factory=FakeClient)
    await controller.connect('test-only')
    await controller.lock.acquire()
    tasks = [asyncio.create_task(controller.send(Command.VOLUME_UP)) for _ in range(8)]
    await asyncio.sleep(0)
    with pytest.raises(RuntimeError, match='queue full'): await controller.send(Command.VOLUME_UP)
    controller.generation += 1
    controller.lock.release()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    assert all(isinstance(result, RuntimeError) for result in results)
    assert controller.pending == 0
    await controller.close()

@pytest.mark.asyncio
async def test_scan_and_input_notifications():
    async def scan(**kwargs):
        assert kwargs['service_uuids'] == [SERVICE]
        return [SimpleNamespace(address='test-only', name='Z407')]
    events = []
    controller = Controller(lambda *event: events.append(event), scanner=scan)
    assert len(await controller.scan()) == 1
    controller.notify(None, b'\xcf\x06')
    assert ('input', 'USB · hardware reported') in events

@pytest.mark.asyncio
async def test_reconnect_and_shutdown(monkeypatch):
    controller = Controller(client_factory=FakeClient)
    await controller.connect('test-only')
    real_sleep = asyncio.sleep
    async def quick_sleep(seconds): await real_sleep(0)
    monkeypatch.setattr('app.bluetooth.controller.asyncio.sleep', quick_sleep)
    controller._lost(controller.client)
    assert not controller.ready
    await controller.retry_task
    assert controller.ready
    await controller.close()
    assert controller.closed and not controller.ready

def test_encoding():
    assert Command.BASS_UP.value.hex() == '8000'
    assert Command.BASS_DOWN.value.hex() == '8001'
    assert Command.USB.value.hex() == '8103'
    assert Command.BASS_UP.acknowledgment.hex() == 'c000'
