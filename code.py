import board
import countio
import asyncio
import digitalio
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.timing_clock import TimingClock
from adafruit_midi.start import Start
from adafruit_midi.stop import Stop

        
class Sequencer:
    
    def __init__(self, midi, ppqn=24, lanes=16):
        self.midi = midi
        self.ppqn = ppqn
        self.lanes = [SequencerLane(c) for c in range(lanes)]
        self.activeLane = 0
        self.tick = 0

    def __enter__(self):
        self.STOP = False
        self._playing = asyncio.create_task(self._play())
        return self

    async def _play(self):
        while not self.STOP:
            if isinstance(( msg := self.midi.receive()), TimingClock):
                self.tick = (self.tick + 1) % 96 #clock pulses in a 4/4 bar
                self._send()
            elif isinstance(msg, Start) or isinstance(msg, Stop):
                self.tick = 0
            await asyncio.sleep(0)

    def _send(self):
        for l in self.lanes:
            if (event := l.events.get(self.tick)):
                self.midi.send(event, channel=event.channel)

    def _single_send(self, event):
        self.midi.send(event, channel=event.channel)

    def nextLane(self):
        self.activeLane = (self.activeLane + 1) % 16
        print(f'Active lane: {self.activeLane}')

    def addEvent(self, event):
        self.lanes[self.activeLane].insert(self.tick, event, self._single_send)

    def stop(self):
        self.STOP = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()



class SequencerLane:

    def __init__(self, channel):
        self.events = dict()
        self.channel = channel

    def insert(self, tick, event, send_func):
        event.channel = self.channel
        self.events[tick] = event
        send_func(event)
        

async def catch_cycle_interrupt(pin, callback):
    with countio.Counter(pin) as interrupt:
        while True:
            if interrupt.count > 0:
                interrupt.count = 0
                callback()
            await asyncio.sleep(0)


# circuitpython edge detection doesn't support RISE_AND_FALL for the RP2040
# so unfortunately not all state changes can be detected on a single pin using interrupts
# therefore this function has to resort to polling the pin instead
async def poll_input(pin, callback, cbargs):
    state = False
    while True:
        if state != pin.value:
            state = pin.value
            if state:
                callback(NoteOn(*cbargs))
            else:
                callback(NoteOff(*cbargs))
        await asyncio.sleep(0.005)



async def main():
    port_in, port_out = usb_midi.ports
    midi = adafruit_midi.MIDI(midi_in=port_in, midi_out=port_out)
    input_pin = digitalio.DigitalInOut(board.GP1)
    with Sequencer(midi) as sequencer:
        cycle_interrupt = asyncio.create_task(catch_cycle_interrupt(board.USER_SW, sequencer.nextLane))
        poll_input_coro = asyncio.create_task(poll_input(input_pin, sequencer.addEvent, (60,)))
        await asyncio.gather(cycle_interrupt, poll_input_coro)

asyncio.run(main())
