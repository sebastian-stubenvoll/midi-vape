import board
import asyncio
import digitalio
import usb_midi
import adafruit_midi
import async_button
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.timing_clock import TimingClock
from adafruit_midi.start import Start
from adafruit_midi.stop import Stop


class Sequencer:

    def __init__(self, midi, ppqn=24, lanes=16, note=60):
        self.midi = midi
        self.ppqn = ppqn
        self.note = note
        self.lanes = [SequencerLane(c) for c in range(lanes)]
        self.activeLane = 0
        self.tick = 0
        self.recording = False
        self.armed = True

    def __enter__(self):
        self.STOP = False
        self._playing = asyncio.create_task(self._play())
        return self

    async def _play(self):
        while not self.STOP:
            if isinstance(( msg := self.midi.receive()), TimingClock):
                self.recording = True # should only receive TimingClock if playing
                self.tick = (self.tick + 1) % (self.ppqn * 4)
                self._send()
            elif isinstance(msg, Start):
                self.tick = 0
                self.recording = True # technically redundant
            elif isinstance(msg, Stop):
                self.tick = 0
                self.recording = False
                self._single_send(NoteOff(self.note))

            await asyncio.sleep(0)

    def _send(self):
        for l in self.lanes:
            if (event := l.events.get(self.tick)):
                self.midi.send(event, channel=event.channel)

    def _single_send(self, event):
        self.midi.send(event, channel=self.activeLane)

    def nextLane(self):
        self.activeLane = (self.activeLane + 1) % len(self.lanes)
        print(f'Active lane (channel): {self.activeLane+1}')

    def clearLane(self):
        self.lanes[self.activeLane].clear()
        self._single_send(NoteOff(self.note))
        print(f'Clearing lane (channel): {self.activeLane+1}')

    def toggleArmed(self):
        self.armed = not self.armed
        print(f'Armed for recording: {self.armed}')

    def addEvent(self, event):
        if self.recording and self.armed:
            self.lanes[self.activeLane].insert(self.tick, event)
        self._single_send(event)

    def stop(self):
        self.STOP = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()



class SequencerLane:

    def __init__(self, channel):
        self.events = dict()
        self.channel = channel

    def insert(self, tick, event):
        event.channel = self.channel
        self.events[tick] = event

    def clear(self):
        self.events = dict()


# the whacky timeout hack is needed so double clicks don't also fire as single clicks
# there's probably a more elegant way, feel free to submit a PR :)
async def mode_changes(pin, single_callback, double_callback, long_callback):
    button = async_button.Button(pin, False, pull=True, interval=0.01, long_click_min_duration=0.3, long_click_enable=True)

    while True:
        await button.wait(async_button.Button.PRESSED)
        try:
            await asyncio.wait_for(button.wait(async_button.Button.PRESSED), timeout=0.35)
            double_callback()
        except asyncio.TimeoutError:
            if button.last_click == 32:
                long_callback()
            else:
                single_callback()
        await asyncio.sleep(0)

# circuitpython edge detection doesn't support RISE_AND_FALL for the RP2040
# so unfortunately not all state changes can be detected on a single pin using interrupts
# therefore this function has to resort to polling the pin instead
async def poll_input(pin, callback, cbargs):
    state = False
    while True:
        if state != (v := pin.value):
            state = v
            if state:
                callback(NoteOn(*cbargs))
            else:
                callback(NoteOff(*cbargs))
        await asyncio.sleep(0)



async def main():
    #################
    #  BOARD SETUP  #
    #################
    if board.board_id == "pimoroni_tiny2040":
        raw_input_pin = board.GP0
        onboard_switch = board.USER_SW
        print("Successfully set up pin aliases for the pimoroni tiny2040!")
    if board.board_id == "seeeduino_xiao_rp2040":
        raw_input_pin = board.D0
        # requires an external button bridging D7 and D9
        # this is needed because the boot button cannot function as switch on this board
        onboard_switch = board.D7
        custom_ground = digitalio.DigitalInOut(board.D9)
        custom_ground.switch_to_output(value=False)
        print("Successfully set up pin aliases for the seeeduino xiao rp2040!")
    # add more branches for other boards/pin aliases

    try:
        raw_input_pin and onboard_switch
    except:
        raise RuntimeError("Unknown board; couldn't assign pins!\n\
        Please make sure you're using the correct CircuitPython version or set up your own aliases!")

    port_in, port_out = usb_midi.ports
    midi = adafruit_midi.MIDI(midi_in=port_in, midi_out=port_out)
    input_pin = digitalio.DigitalInOut(raw_input_pin)
    input_pin.pull = digitalio.Pull.DOWN


    #####################################
    #  SEQUENCER/COROUTINE TASKS SETUP  #
    #####################################
    with Sequencer(midi, lanes=8) as sequencer:
        sequencer_funcs = (sequencer.nextLane, sequencer.toggleArmed, sequencer.clearLane)
        mode_changes_coro = asyncio.create_task(mode_changes(onboard_switch, *sequencer_funcs))
        poll_input_coro = asyncio.create_task(poll_input(input_pin, sequencer.addEvent, (sequencer.note,)))
        print("\n\n")
        print("Ready to rip some fat beats")
        print("Don't do vapes though, kids.")
        print("\n\n")
        await asyncio.gather(mode_changes_coro, poll_input_coro)

asyncio.run(main())
