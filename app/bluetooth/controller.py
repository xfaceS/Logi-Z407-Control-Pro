"""Single-loop, serialized BLE transport. Never replay uncertain commands."""
import asyncio
import time
from .protocol import SERVICE, COMMAND, RESPONSE, Command, INPUT_STATUS

class Controller:
    def __init__(self, emit=lambda *args: None, client_factory=None, scanner=None):
        self.emit = emit
        self.factory = client_factory
        self.scanner = scanner
        self.client = None
        self.ready = False
        self.address = None
        self.auto_reconnect = True
        self.retry_task = None
        self.lock = asyncio.Lock()
        self.lifecycle = asyncio.Lock()
        self.events = {}
        self.pending = 0
        self.generation = 0
        self.last_write = 0
        self.closed = False
        self.timeout = 4
        self.input = None

    async def scan(self):
        if self.scanner is None:
            from bleak import BleakScanner
            self.scanner = BleakScanner.discover
        self.emit('state', 'Scanning · Bluetooth adapter check')
        try:
            devices = await self.scanner(timeout=8, service_uuids=[SERVICE])
            self.emit('devices', devices)
            self.emit('state', f'{len(devices)} Z407 device(s) discovered' if devices else
                      'Z407 not detected. Remove dial batteries or allow it to idle for five minutes, then scan again.')
            return devices
        except Exception as exc:
            self.emit('error', f'Bluetooth scan failed: {exc}. Check that an adapter is present and Bluetooth is enabled.')
            return []

    def notify(self, sender, data):
        data = bytes(data)
        event = self.events.get(data)
        if event:
            event.set()
        if data in INPUT_STATUS:
            self.input = INPUT_STATUS[data]
            self.emit('input', f'{self.input} · hardware reported')
        self.emit('notification', data.hex())

    async def write(self, payload):
        # Conservative 100 ms minimum interval; tune only after hardware testing.
        await asyncio.sleep(max(0, .1 - (time.monotonic() - self.last_write)))
        await asyncio.wait_for(self.client.write_gatt_char(COMMAND, payload, response=False), self.timeout)
        self.last_write = time.monotonic()

    async def exchange(self, payload, expected):
        event = self.events.setdefault(expected, asyncio.Event())
        event.clear()
        await self.write(payload)
        await asyncio.wait_for(event.wait(), self.timeout)

    async def connect(self, device):
        async with self.lifecycle, self.lock:
            if self.closed:
                return
            if self.client:
                await self._disconnect()
            self.address = getattr(device, 'address', device)
            self.emit('state', 'Connecting · discovering GATT services')
            if self.factory is None:
                from bleak import BleakClient
                self.factory = BleakClient
            self.client = self.factory(device, disconnected_callback=self._lost, timeout=15)
            try:
                await asyncio.wait_for(self.client.connect(), 20)
                services = self.client.services
                if not services.get_service(SERVICE) or not all(services.get_characteristic(x) for x in (COMMAND, RESPONSE)):
                    raise RuntimeError('Required Z407 GATT service or characteristic unavailable')
                self.emit('state', 'GATT verified · initializing protocol')
                client = self.client
                self.events.clear()
                await client.start_notify(RESPONSE, lambda sender, data: self.notify(sender, data) if client is self.client else None)
                await self.exchange(b'\x84\x05', b'\xd4\x05\x01')
                # Local hardware emits either d40001 or d40003 on different
                # connections. Both are documented positive handshake states.
                complete = asyncio.Event()
                self.events[b'\xd4\x00\x01'] = complete
                self.events[b'\xd4\x00\x03'] = complete
                await self.write(b'\x84\x00')
                await asyncio.wait_for(complete.wait(), self.timeout)
                self.ready = True
                self.emit('ready', True)
                self.emit('state', 'Connected · protocol handshake acknowledged')
            except TimeoutError as exc:
                await self._disconnect()
                raise RuntimeError('Connection or handshake timed out. Release other controllers, check speaker power, then reconnect.') from exc
            except BaseException:
                await self._disconnect()
                raise

    def _lost(self, client):
        if client is not self.client:
            return
        self.ready = False
        self.generation += 1
        self.input = None
        self.emit('ready', False)
        self.emit('input', 'Unknown · connection interrupted')
        self.emit('state', 'Device disconnected · session estimates invalidated')
        if not self.closed and self.auto_reconnect and (self.retry_task is None or self.retry_task.done()):
            self.retry_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self):
        for attempt in range(1, 6):
            self.emit('state', f'Reconnecting · attempt {attempt}/5')
            await asyncio.sleep(min(2 ** attempt, 30))
            try:
                await self.connect(self.address)
                return
            except Exception as exc:
                self.emit('error', f'Reconnect {attempt}/5: {exc}')
        self.emit('state', 'Reconnect limit reached. Check speaker power and dial ownership, then reconnect manually.')

    async def send(self, command):
        if not isinstance(command, Command):
            raise ValueError('Unsupported command')
        if not self.ready:
            raise RuntimeError('Speaker is not ready. Connect and complete the handshake first.')
        if self.pending >= 8:
            raise RuntimeError('Command queue full. Slow down and wait for pending adjustments.')
        generation = self.generation
        self.pending += 1
        try:
            async with self.lock:
                if not self.ready or generation != self.generation:
                    raise RuntimeError('Stale command discarded after connection change')
                try:
                    await self.exchange(command.value, command.acknowledgment)
                except Exception as exc:
                    # A timeout may mean the speaker acted without an ACK. Do not retry.
                    await self._disconnect()
                    raise RuntimeError('Command failed or acknowledgment timed out; state is uncertain. Reconnect before continuing.') from exc
                self.emit('command', command.name)
                source = {'BLUETOOTH': 'Bluetooth', 'USB': 'USB', 'AUX': 'AUX'}.get(command.name)
                if source and self.input != source:
                    self.emit('input', source + ' · last requested (acknowledged)')
        finally:
            self.pending -= 1

    async def _disconnect(self):
        self.ready = False
        self.generation += 1
        self.emit('ready', False)
        client, self.client = self.client, None
        self.input = None
        self.emit('input', 'Unknown')
        if client:
            try:
                await asyncio.wait_for(client.disconnect(), 5)
            except Exception:
                pass

    async def disconnect(self):
        if self.retry_task and self.retry_task is not asyncio.current_task():
            self.retry_task.cancel()
            await asyncio.gather(self.retry_task, return_exceptions=True)
        # Mark queued commands stale before waiting for an in-flight command.
        self.ready = False
        self.generation += 1
        async with self.lifecycle, self.lock:
            await self._disconnect()
        self.emit('state', 'Disconnected')

    async def close(self):
        self.closed = True
        await self.disconnect()
