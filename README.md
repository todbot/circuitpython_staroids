# CircuitPython Staroids

Something like **Asteroids**, done in CircuitPython.
Works with [FunHouse](https://www.adafruit.com/product/4985),
[MacroPad](https://www.adafruit.com/product/5128),
[Pybadge](https://www.adafruit.com/product/4200),
[CLUE](https://www.adafruit.com/product/4500),
and [Pygamer](https://www.adafruit.com/product/4242).

<img src="./docs/staroids_family1.jpg" />

https://user-images.githubusercontent.com/274093/129097480-3be3b302-d7ba-4690-951a-0822a2933bb3.mp4

(And [@jedgarpark](https://github.com/jedgarpark) modified the [Pybadge version to have sound as seen in this video](https://www.youtube.com/watch?v=sC_fLp5CfTg)!)

## Game rules:

- You control a spaceship in an asteroid field
- Your ship has three controls: Turn Left, Turn Right, and Thrust/Fire
- You get +1 point for every asteroid shot
- You get -3 point every time an asteroid hits your ship
- Game ends when you get bored or the boss comes walking by
- If you hit an asteroid, LEDs flash orange. If your ship is hit, LEDs flash purply.
- No sound by default (as many boards do not support WAV playback)

## Installation

- Install CircuitPython onto your board (requires CircuitPython 7.0.0-alpha.5 or better)
- Install needed CircuitPython libraries
- Copy entire `imgs` directory to CIRCUITPY drive
- Copy `staroids_code.py` to your CIRCUITPY drive as `code.py`

If you have [`circup`](https://github.com/adafruit/circup) installed,
installation can be done entirely via the command-line
using the included `requirements.txt` and a few copy commands. MacOS example below:

```
$ circup install -r ./requirements.txt
$ cp -aX imgs /Volumes/CIRCUITPY
$ cp -X staroids_code.py /Volumes/CIRCUITPY/code.py
```

## Code techniques demonstrated

If you're interested in how to do stuff in CircuitPython, this code does things
that might be useful. Those include:
- Detecting which board is being used and adjusting I/O & game params accordingly
- Dealing with almost all possible LED & button input techniques in CircuitPython
- Timing without using `time.sleep()`
- Sprite sheet animation with `displayio`
- Smooth rotation animation with sprite sheets
- Simple 2D physics engine (velocity & acceleration, okay enough for this game)


## Sound effects

- In general, sound effects are not part of this game. CircuitPython doesn't do sound
as well as it does graphics, so I find the experience a little grating.

- But if you have a Pygamer and want sounds, you can set `enable_sound=True` at the top
of the `code.py` and copy over the `snds` directory to the CIRCUITPY drive to enable sounds.

- The sounds were created by me from audio of [John Park's 8/12/21 livestream](https://www.youtube.com/watch?v=EYGYTlM6usc).
Specifically, the "pew" sound comes from the 6:56 mark of him saying "pew pew"
and the "exp" sound comes from the "x" sound in "AdaBox" at 7:15.


## Implementation notes

(Notes for myself mostly)

- Sprite rotation is accomplished using sprite "sheets" containing all possible
rotations of the sprite. For the ship that is 36 rotation images tiles 
at 10-degrees apart. For the asteroids, that's 120 rotation image tiles
at 3 degrees apart. The rotated images were created using ImageMagick
on a single sprite.

- A simpler version of [this sprite rotation code can be found in this gist](https://gist.github.com/todbot/92373f93db9da0fca5ca4adee8d7d75b) and [this video demo](https://twitter.com/todbot/status/1423331295384399883).

- Another way to do this is via `bitmaptools.rotozoom()`. This technique worked but
seemed like it would not perform well on boards with chips with no floating-point
hardware (RP2040, ESP32-S2). You can find that [demo rotozoom code in this gist](https://gist.github.com/todbot/8b524daba51bd84c92799a2401324521)
and [this video demo](https://twitter.com/todbot/status/1423078302391037953).

- Ship, Asteroids, Shots (`Thing` objects) are in a floating-point (x,y) space,
while its corresponding `displayio.TileGrid` is integer (x,y) space. This allows
a `Thing` to accumulate its (x,y) velocity & acceleration without weird
int->float truncations.

- Similarly, `Thing` rotation angle is floatping point but gets quantized to the
sprite sheet's tile number.

- Per-board settings is useful not just for technical differences (sprite sizes),
but also for gameplay params (accel_max, vmax)

- Hitbox calculations are done on floating-point (x,y) of the `Thing` objects,
but converted to int before hitbox calculation to hopefully speed things up.

- Sprite sizes (e.g. 30x30 pixels), sprite bit-depth (1-bit for these sprits),
and quantity on screen (5 asteroids, 4 shots) greatly influences framerate.
For a game like Asteroids where FPS needs to be high, you have to balance this
carefully. To see this, try converting the ship spritesheet to a 4-bit
(16-color) BMP and watch the framerate drop. Or you might run out of memory.


## How the sprite sheets were made

(Notes for myself mostly)

Given a set of square images named:
- ship0.png - our spaceship coasting
- ship1.png - our spaceship thrusting
- roid0.png - one asteroid shape
- roid1.png - another asteroid shape
- roidexp.png - an exploding asteroid

and you want to create the sprite sheets:
- ship_sheet.bmp  -- two sets (coast + thrust) of 36 10-degree rotations in one palette BMP
- roid0_sheet.bmp -- 120 3-degree rotations in one palette BMP
- staroid1_sheet.bmp -- 120 3-degree rotations in one palette BMP
- roidexp_sheet.bmp -- 8 45-degree rotations in one palette BMP

The entire set of ImageMagick commands to create the sprite sheet of rotations,
as a single shell script is below.

Sprites were hand-drawn in Pixelmator using vague recollection of Asteroids.
For MacroPad, sprites were re-drawn as 12px square tile instead of 30px.
The were drawn with https://www.pixilart.com/art/staroids-sprites-12px-58e5853d4c2b0ef.
For Pybadge, 30px sprites were rescaled to 20px using ImageMagick.

```shell
# ship0 (coasting)
for i in $(seq -w 0 10 359) ; do
echo $i
convert ship0.png -distort SRT $i ship0-r$i.png
done
montage -mode concatenate -tile x1 ship0-r*png  ship0_sheet.png
convert ship0_sheet.png -colors 2 -type palette BMP3:ship0_sheet.bmp

# ship1 (thrusting)
for i in $(seq -w 0 10 359) ; do
echo $i
convert ship1.png -distort SRT $i ship1-r$i.png
done
montage -mode concatenate -tile x1 ship1-r*png  ship1_sheet.png
convert ship1_sheet.png -colors 2 -type palette BMP3:ship1_sheet.bmp

# combine ship0 & ship1 into one sprite sheet
montage -mode concatenate -tile x2 ship0_sheet.bmp ship1_sheet.bmp ship_sheet.png
convert ship_sheet.png -colors 2 -type palette BMP3:ship_sheet.bmp

# roid0
for i in $(seq -w 0 3 359) ; do  
echo $i
convert roid0.png -distort SRT $i roid0-r$i.png 
done
montage -mode concatenate -tile x1 roid0-r*png  roid0_sheet.png
convert roid0_sheet.png -colors 2 -type palette BMP3:roid0_sheet.bmp 

# roid1
for i in $(seq -w 0 3 359) ; do  
echo $i
convert roid1.png -distort SRT $i roid1-r$i.png 
done
montage -mode concatenate -tile x1 roid1-r*png  roid1_sheet.png
convert roid1_sheet.png -colors 2 -type palette BMP3:roid1_sheet.bmp 

# exploding asteroid
for i in $(seq -w 0 45 359) ; do 
echo $i
convert roidexp.png -distort SRT $i roidexp-r$i.png
done
montage -mode concatenate -tile x1 roidexp-r*png  roidexp_sheet.png
convert roidexp_sheet.png -colors 2 -type palette BMP3:roidexp_sheet.bmp

```

