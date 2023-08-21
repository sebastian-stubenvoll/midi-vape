Uses [CircuitPython](https://docs.circuitpython.org/en/latest/docs/index.html) for the respective RP2040 board.
The code is written for the `tiny2040` and may need to be adjusted slightly for other boards.
Intended for the glorious MIDI Vape and thrown together rather hastily :)

![vape picture](https://github.com/sebastian-stubenvoll/midi-vape/blob/main/midi-vape.jpeg)

Most disposable vapes have a pressure sensor controlling the heating mechanism.
That sensor is triggered by creating a high pressure bottleneck at the bottom of
the vape when sucking air into it and sends an electrical signal that can be captured by a micro-controller board.

This code incoming midi-clock signals to create one 4/4 bar sequencer lanes from the input.
Sucking on the vape creates midi events that are looped.
Each lane has its own midi channel; lanes can be cycled with the boot button.

MIDI communication is done using the [`usb_midi` module](https://docs.circuitpython.org/en/latest/shared-bindings/usb_midi/index.html) as well as the [`adafruit-circuitpython-midi` package](https://docs.circuitpython.org/projects/midi/en/latest/index.html).

## Dependencies

+ Adafruit CircuitPython
+ adafruit-circuitpython-midi
+ asyncio

Dependencies are easily installed using [circup](https://github.com/adafruit/circup#installation) (see Pipfile).
```bash
circup install adafruit-circuitpython-midi asyncio
```


## TODO

+ Find a sensible design for clearing the current lane and implement it.
