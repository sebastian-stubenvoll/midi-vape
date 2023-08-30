Uses [CircuitPython](https://docs.circuitpython.org/en/latest/docs/index.html) for the respective RP2040 board.
The code is written for the `tiny2040` and may need to be adjusted slightly for other boards.
Intended for the glorious MIDI Vape and thrown together rather hastily :)

If abusing async APIs for bodging together pseudo-multithreading behaviour was a crime, this repository would be sentenced to life in prison.

![vape picture](https://github.com/sebastian-stubenvoll/midi-vape/blob/main/midi-vape.jpeg)

Most disposable vapes have a pressure sensor controlling the heating mechanism.
That sensor is triggered by creating a high pressure bottleneck at the bottom of
the vape when sucking air into it and sends an electrical signal that can be captured by a micro-controller board.

This code reads incoming midi-clock signals to create one 4/4 bar sequencer lanes from the input.
Sucking on the vape creates midi events that are looped.
Each lane has its own midi channel; lanes can be cycled with the boot button.

MIDI communication is done using the [`usb_midi` module](https://docs.circuitpython.org/en/latest/shared-bindings/usb_midi/index.html) as well as the [`adafruit-circuitpython-midi` package](https://docs.circuitpython.org/projects/midi/en/latest/index.html).

## Usage
The code will detect which board it is running on at runtime.
So far only the `tiny2040` and `seeeduino xiao 2040` are supported, though pin aliases for additional boards can be easily added.

For the `seeeduino` an additional button is needed. Unlike the `tiny2040` this board doesn't use the `BOOT` button as a regular button/pin when running.
In the supplied code, the button is attached to `D7` and `D9` (set to ground level).
The pins are chosen purely for ergonomics, any pair of digital input + pin that can act as ground can work!

More pin aliases may be added in the near future!

---

Connect the pressure sensor switch to the pin respective to your board and connect one of the ground pins to the vape battery ground.

Vape (or set the input pin to high/low by other means) to trigger a MIDI signal on the current channel.  
**To switch channels press the `BOOT` button.**

When receiving MIDI Clock signals, the MCU records those input MIDI signals and loops them over one bar (four quater notes).  
**To toggle if the device is armed for recording double press the `BOOT` button.**  
This is a global setting (not per channel).

Additional MIDI signals can be added in separate loops, overwriting any signals happening on the same clock pulse.  
**To clear all MIDI signals for the currently selected channel hold the  `BOOT` button.**  
Other MIDI channels will retain their recorded signals.


## Dependencies

+ Adafruit CircuitPython
+ adafruit-circuitpython-midi
+ asyncio
+ async-button

Dependencies are easily installed using [circup](https://github.com/adafruit/circup#installation) (see Pipfile).
```bash
circup install adafruit-circuitpython-midi asyncio async_button
```


## TODO

+ Add LED indication for current channel/recording arm
+ Add a showcase video
