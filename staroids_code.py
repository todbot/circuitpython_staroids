# staroids_code.py -- fakey Almost Asteroids
# 4 Aug 2021 - @todbot
import board, time, math, random
import displayio, terminalio, bitmaptools
import adafruit_imageload
from adafruit_display_text import bitmap_label as label
import os

enable_sound = False  # set to True to enable experimental sound support (Pygamer)

num_ship_tiles = 36   # how many rotations of the ship sprite
num_roid_tiles = 120  # how many rotations of the asteroid sprites

point_roid = 1        # points for shooting an asteroid
point_ship = -3       # points for getting hit by an asteroid

score = 0

# sprite filename templates, '%d' is filled in with tile size (30, 20, 12)
ship_fname = '/imgs/ship_%d_sheet.bmp'
roidexp_fname = '/imgs/roidexp_%d_sheet.bmp'
roid_fnames = ['/imgs/roid0_%d_sheet.bmp', '/imgs/roid1_%d_sheet.bmp']
shot_fname = '/imgs/shotsm3.bmp' # shot fname has smaller 3x3 tile
bg_fname = '/imgs/bg_starfield.bmp' # hubble star field by default (funhouse/pygamer)

# sound wav files, if 'enable_sound=True' (only for Pygamer currently)
pew_wav_fname = "/snds/pew1_11k.wav"
exp_wav_fname = "/snds/exp1_11k.wav"

# default effect handling (sound/light)
# fx_type = 0 pew, fx_type = 1 explosion
def play_effect(fx_type,fx_color=0):
    if fx_type==1: leds.fill(fx_color)

# --- board params -----------------------------------------------------

board_type = os.uname().machine

# Macropad 128x64 monochrome display, uses 4/5/6 keys for L/T/R
if 'macropad' in board_type.lower():
    import keypad
    import neopixel
    num_roids = 3
    num_shots = 3
    shot_life = 0.4
    accel_max_shot = 4
    accel_max_ship = 0.08
    vmax = 3
    tile_w = 12
    bg_fname = '/imgs/bg_stars_mono.bmp'  # special monochrome starfield for macropad
    display = board.DISPLAY
    display.rotation = 0
    leds = neopixel.NeoPixel(board.NEOPIXEL, 12, brightness=0.1)
    # stolen from adafruit_macropad, thx kattni!
    keypins = [getattr(board, "KEY%d" % (num + 1)) for num in (list(range(12)))]
    keys = keypad.Keys(keypins, value_when_pressed=False, pull=True)
    # Macropad, key processing
    def get_user_input(turning,thrusting,firing):
        key = keys.events.get()
        if key:
            if key.key_number == 3:  # KEY4 rotate LEFT
                turning = -0.15 if key.pressed else 0
            if key.key_number == 5:  # KEY6 rotate RIGHT
                turning = 0.15 if key.pressed else 0
            if key.key_number == 4:  # KEY5 THRUST/FIRE!
                thrusting = key.pressed
        firing = thrusting  # only using 3 keys
        return turning, thrusting, firing

# FunHouse 240x240 color display, only 3 buttons so L/T/F (when rotated 90-deg)
elif 'funhouse' in board_type.lower():
    import digitalio
    import adafruit_dotstar
    num_roids = 4
    num_shots = 5
    shot_life = 1
    accel_max_shot = 5
    accel_max_ship = 0.2
    vmax = 5
    tile_w = 30
    display = board.DISPLAY
    display.rotation = 0
    button_L = digitalio.DigitalInOut(board.BUTTON_UP)     # turn left
    button_L.switch_to_input(pull=digitalio.Pull.DOWN)
    button_R = digitalio.DigitalInOut(board.BUTTON_DOWN)   # turn right
    button_R.switch_to_input(pull=digitalio.Pull.DOWN)
    button_F = digitalio.DigitalInOut(board.BUTTON_SELECT) # thrust!
    button_F.switch_to_input(pull=digitalio.Pull.DOWN)
    leds = adafruit_dotstar.DotStar(board.DOTSTAR_CLOCK,board.DOTSTAR_DATA,5,brightness=0.1)
    # Funhouse, key processing
    def get_user_input(turning,thrusting,firing):
        thrusting = button_F.value
        turning = 0
        # check on the user
        if button_L.value:  # rotate LEFT
            turning = -0.15
        if button_R.value:  # rotate RIGHT
            turning = 0.15
        if button_F.value:  # THRUST/FIRE!
            thrusting = True
        firing = thrusting  # only using 3 keys!
        return turning, thrusting, firing
    
# Pybadge 160x128 color display, D-pad L/R for L/R, A for Thrust/Fire
elif 'pybadge' in board_type.lower():
    import keypad
    import neopixel
    import rainbowio
    num_roids = 3
    num_shots = 3
    shot_life = 0.5
    accel_max_shot = 3
    accel_max_ship = 0.06
    vmax = 3
    tile_w = 20
    display = board.DISPLAY
    display.rotation = 0
    keys = keypad.ShiftRegisterKeys(clock=board.BUTTON_CLOCK,data=board.BUTTON_OUT,
                                    latch=board.BUTTON_LATCH, key_count=8,
                                    value_when_pressed=True)
    leds = neopixel.NeoPixel(board.NEOPIXEL, 5, brightness=0.1)
    rainbowing = False # secret rainbowing mode
    if enable_sound:
        import audiocore, audioio, digitalio
        speaker_enable = digitalio.DigitalInOut(board.SPEAKER_ENABLE)
        speaker_enable.switch_to_output(value=True)
        wav_pew = audiocore.WaveFile(open(pew_wav_fname,"rb"))
        wav_exp = audiocore.WaveFile(open(exp_wav_fname,"rb"))
        audio = audioio.AudioOut(board.SPEAKER)
    # Pybadge, key processing
    def get_user_input(turning,thrusting,firing):
        global rainbowing
        key = keys.events.get()
        if key:
            if key.key_number == 7:  # KEY4 rotate LEFT
                turning = -0.12 if key.pressed else 0
            if key.key_number == 4:  # KEY6 rotate RIGHT
                turning = 0.12 if key.pressed else 0
            if key.key_number == 1:  # KEY5 THRUST/FIRE!
                thrusting = key.pressed
            if key.key_number == 3:  # SELECT key
                rainbowing = key.pressed
        if rainbowing:
            c = rainbowio.colorwheel( time.monotonic()*100 % 255 )
            #bg_pal[1] = c # this slows things down a lot due to full screen redraw
            ship_sprites_pal[1] = c
            roidexp_sprites_pal[1] = c
            shot_sprites_pal[1] = c
            for (s,p) in roid_spr_pal: p[1] = c
            score_label.color = c
        firing = thrusting  # only using 3 keys
        return turning, thrusting, firing
    # Pybadge, sound/light handling, overrides default
    def play_effect(fx_type,fx_color=0): # fx_type=0 pew, fx_type = 1 explosion
        if fx_type==1: leds.fill(fx_color)
        if enable_sound:
            if fx_type==0: audio.play(wav_pew)
            if fx_type==1: audio.play(wav_exp)

# Pygamer 160x128 color display, analog pad L/R for L/R, A for Thrust/Fire
elif 'pygamer' in board_type.lower():
    import keypad
    import neopixel
    import analogio
    import rainbowio
    num_roids = 3
    num_shots = 3
    shot_life = 0.5
    accel_max_shot = 3
    accel_max_ship = 0.06
    vmax = 3
    tile_w = 20
    display = board.DISPLAY
    display.rotation = 0
    keys = keypad.ShiftRegisterKeys(clock=board.BUTTON_CLOCK,data=board.BUTTON_OUT,
                                    latch=board.BUTTON_LATCH, key_count=8,
                                    value_when_pressed=True)
    joystick_x = analogio.AnalogIn(board.JOYSTICK_X)
    leds = neopixel.NeoPixel(board.NEOPIXEL, 5, brightness=0.1)
    rainbowing = False # secret rainbowing mode
    if enable_sound:
        import audiocore, audioio, digitalio
        speaker_enable = digitalio.DigitalInOut(board.SPEAKER_ENABLE)
        speaker_enable.switch_to_output(value=True)
        wav_pew = audiocore.WaveFile(open(pew_wav_fname,"rb"))
        wav_exp = audiocore.WaveFile(open(exp_wav_fname,"rb"))
        audio = audioio.AudioOut(board.SPEAKER)
    # Pygamer, key processing
    def get_user_input(turning,thrusting,firing):
        global rainbowing
        key = keys.events.get()
        if key:
            if key.key_number == 1:  # KEY5 THRUST/FIRE!
                thrusting = key.pressed
            if key.key_number == 3:  # SELECT key
                rainbowing = key.pressed
        if rainbowing:  # rainbow mode!
            c = rainbowio.colorwheel( time.monotonic()*100 % 255 )
            #bg_pal[1] = c # this slows things down a lot due to full screen redraw
            ship_sprites_pal[1] = c
            roidexp_sprites_pal[1] = c
            shot_sprites_pal[1] = c
            for (s,p) in roid_spr_pal: p[1] = c
            score_label.color = c
        firing = thrusting  # only using 3 keys
        turning = 0
        if joystick_x.value > 55000: turning = 0.12
        if joystick_x.value < 1000: turning = -0.12
        return turning, thrusting, firing
    # Pygamer, sound/light handling, overrides default
    def play_effect(fx_type,fx_color=0): # fx_type=0 pew, fx_type = 1 explosion
        if fx_type==1: leds.fill(fx_color)
        if enable_sound:
            if fx_type==0: audio.play(wav_pew)
            if fx_type==1: audio.play(wav_exp)

# Clue 240x240 color display, A/B for L/R, touch pad 2 (D2) for Thrust/Fire
elif 'clue' in board_type.lower():
    import keypad
    import neopixel
    import touchio
    num_roids = 3
    num_shots = 3
    shot_life = 0.5
    accel_max_shot = 3
    accel_max_ship = 0.06
    vmax = 3
    tile_w = 20
    display = board.DISPLAY
    display.rotation = 0
    shooty = touchio.TouchIn(board.D2)
    keys = keypad.Keys([board.BUTTON_A, board.BUTTON_B], value_when_pressed=False, pull=True)
    leds = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1)
    # Clue, key processing
    def get_user_input(turning,thrusting,firing):
        key = keys.events.get()
        if key:
            if key.key_number == 0:  # A rotate LEFT
                turning = -0.15 if key.pressed else 0
            if key.key_number == 1:  # B rotate RIGHT
                turning = 0.15 if key.pressed else 0
        thrusting = shooty.value
        firing = thrusting  # only using 3 keys!
        return turning, thrusting, firing

else:
    raise OSError("unknown board")

# --- board params end -------------------------------------------------


# helper object for physics things
class Thing:
    hitbox = tile_w // 2  # how big our hitbox is, for all Things
    def __init__(self, x,y, w=0, vx=0,vy=0, angle=0, va=0, tilegrid=None, num_tiles=1):
        self.x, self.y, self.w = x, y, w  # x,y pos and width
        self.vx,self.vy = vx,vy # initial x,y velocity
        self.angle = angle # angle object is rotation
        self.va = va   # initial angular velocity
        self.vmax = vmax  # max velocity. 3 on pybadge, 4 on FunHouse 
        self.tg = tilegrid
        self.num_tiles = num_tiles
        self.time = 0
    def accelerate(self,angle, amount):
        self.vx = max(min(self.vx + (math.sin(angle) * amount), self.vmax),-self.vmax)
        self.vy = max(min(self.vy - (math.cos(angle) * amount), self.vmax),-self.vmax)
    def update_pos(self, alt_sprite_index=0):
        self.x = (self.x + self.vx) % display.width  # wrap around top-bottom
        self.y = (self.y + self.vy) % display.height # and left-right
        self.tg.x = int(self.x) - self.w//2 # we think in zero-centered things
        self.tg.y = int(self.y) - self.w//2 # but tilegrids are top-left zero'd
        self.angle += self.va   # if object is spinning
        # get a tilegrid index based on angle and number of tiles total
        i = round(math.degrees(self.angle) / (360 / self.num_tiles)) % self.num_tiles
        self.tg[0] = i + (alt_sprite_index * self.num_tiles)
    def set_pos(self,obj):
        self.x, self.y = obj.x, obj.y
        self.vx, self.vy, self.va = obj.vx, obj.vy, obj.va
    def is_hit(self, obj):
        # try doing all as int math for speed
        if (int(self.x) > int(obj.x) - self.hitbox and
            int(self.x) < int(obj.x) + self.hitbox and
            int(self.y) > int(obj.y) - self.hitbox and
            int(self.y) < int(obj.y) + self.hitbox):
                return True
        return False
    def hide(self,hide=True):
        self.tg.hidden=hide
    @property
    def hidden(self):
        return self.tg.hidden
    # ship angle is perceptually wrong for shots at times where displayed sprite tile
    # doesn't match internal Thing angle. So this computes a new angle based off the
    # coarse tile grid rotation. Seems to fix the weird "off-axis" shots I was seeing
    @property
    def angle_quantized(self): 
        return self.tg[0] * (2*math.pi / self.num_tiles)

display.auto_refresh=False  # only update display on display.refresh()

screen = displayio.Group()  # group that holds everything
display.show(screen) # add main group to display

# ship sprites
ship_sprites,ship_sprites_pal = adafruit_imageload.load(ship_fname % tile_w)
ship_sprites_pal.make_transparent(0)
shiptg = displayio.TileGrid(ship_sprites, pixel_shader=ship_sprites_pal,
                            width=1, height=1, tile_width=tile_w, tile_height=tile_w)
# asteroid sprites
roid_spr_pal = []
for f in roid_fnames: 
    spr,pal = adafruit_imageload.load(f % tile_w)
    pal.make_transparent(0)
    roid_spr_pal.append( (spr,pal) )

# roid exploding sprite
roidexp_sprites, roidexp_sprites_pal = adafruit_imageload.load(roidexp_fname % tile_w)
roidexp_sprites_pal.make_transparent(0)
roidexptg = displayio.TileGrid(roidexp_sprites, pixel_shader=roidexp_sprites_pal,
                               width=1, height=1, tile_width=tile_w, tile_height=tile_w)

# shot sprite
shot_sprites, shot_sprites_pal = adafruit_imageload.load(shot_fname)
shot_sprites_pal.make_transparent(0)

# get background image
bg_img, bg_pal = adafruit_imageload.load(bg_fname)
screen.append(displayio.TileGrid(bg_img, pixel_shader=bg_pal))

# create all the asteroids, add them to the screen
roids = []
for i in range(num_roids):
    vx,vy = random.uniform(-0.5,0.5), random.uniform(-0.2,0.2 ) # more x than y
    spr,pal = roid_spr_pal[ i % len(roid_spr_pal) ]
    roidtg = displayio.TileGrid(spr, pixel_shader=pal, width=1, height=1,
                                tile_width=tile_w, tile_height=tile_w)
    va = random.choice((-0.015,-0.01,0.01,0.015)) # either rotate a little one way or other
    roid = Thing(display.width/2, display.height/2, w=tile_w, vx=vx, vy=vy, va=va,
                 tilegrid=roidtg, num_tiles=num_roid_tiles)
    roids.append(roid)
    screen.append(roid.tg)

# create shot objects, add to screen, then hide them 
shots = []
for i in range(num_shots):
    shottg = displayio.TileGrid(shot_sprites, pixel_shader=shot_sprites_pal,
                                width=1, height=1, tile_width=3, tile_height=3)
    shot = Thing(display.width/2, display.height/2, tilegrid=shottg, num_tiles=1)
    shot.hide()
    shots.append(shot)
    screen.append(shottg)

# create ship object add it to the screen
ship = Thing( display.width/2, display.height/2, w=tile_w, vx=0.5, vy=0.2, angle=5.5, va=0,
              tilegrid=shiptg, num_tiles=num_ship_tiles)
screen.append(ship.tg)

# create explosion object, add to screen, but hide it
roidexp = Thing(display.width/2, display.height/2, w=tile_w, va=0.2,
                 tilegrid=roidexptg, num_tiles=8)
roidexp.hide() # initially don't show
screen.append(roidexp.tg)

# finally, add score display to screen
score_label = label.Label(font=terminalio.FONT, x=5, y=5, color=0x999999, text="000")
screen.append(score_label)

# see if asteroid was hit and by what
def roid_hit(roid,hit_ship=False):
    global score
    print("hit")
    if hit_ship:
        play_effect(1, 0x9900ff)
        leds.fill(0x9900ff)
        score = max(score + point_ship,0) # never go below score=0
    else:
        play_effect(1, 0xff3300)
        score = max(score + point_roid,0) # never go below score=0
    score_label.text = ("%03d" % score)
    roidexp.hide(False) # show explosion
    roidexp.set_pos(roid) # give it roid's position
    roidexp.va = 0.5  # gotta put back explosions spin
    roid.hide() # hide now exploded roid
    # and give it a new random location
    roid.x = random.randint(0,display.width)
    roid.y = random.randint(0,display.height)

# ----------------------------------------------------------------------
# main loop
last_led_time = 0   # when was LED age last checked
last_roid_time = 0  # when was asteroid age last checked  
shot_time = 0       # when did shooting start
shot_index = -1     # which shot are we on
turning = 0 # neg if currrently turning left, pos if turning right
thrusting = False   # true if thrusting 
firing = False      # true if firing
while True:
    now = time.monotonic()
    # get what user wants, (thrust & fire separate now, even tho normally don't use it)
    turning, thrusting, firing = get_user_input(turning,thrusting,firing)

    # update ship state
    ship.angle = ship.angle + turning
    if thrusting: 
        ship.accelerate( ship.angle, accel_max_ship)
    if firing:
        if now - shot_time > 0.2:  # Fire ze missiles 
            shot_time = now
            print("fire", ship.angle, ship.tg[0], ship.angle_quantized)
            play_effect(0)
            shot_index = (shot_index+1) % len(shots)
            shot = shots[shot_index]
            if shot.hidden:  # we can use this shot
                shot.x, shot.y = ship.x,ship.y # put shot at ship pos
                shot.vx,shot.vy = 0,0  # we accelerate it later
                shot.time = time.monotonic() # newborn!
                shot.accelerate(ship.angle_quantized, accel_max_shot) 
                shot.hide(False) # show it off

    # update ship position
    ship.update_pos( thrusting )
    
    # update asteroids state and positions
    for roid in roids:
        roid.update_pos()
        for shot in shots:
            if not shot.hidden and roid.is_hit(shot):
                roid_hit(roid) # FIXME magic value 0 and 1
                shot.hide()
        if roid.is_hit( ship ):
            roid_hit(roid,hit_ship=True)

    # update shot positions, age them out
    for shot in shots:
        shot.update_pos()
        if time.monotonic() - shot.time > shot_life: 
            shot.hide()
            
    # update position of our single explosion thing
    roidexp.update_pos()

    # age out the explosion, 1.5 = explosion lifetime
    if now - last_roid_time > 1.5:
        last_roid_time = now
        for roid in roids:
            if roid.hidden: # roid was shot
                roid.hide(False) # show it, its already in new location
        roidexp.hide() # don't need explosion any more

    display.refresh(target_frames_per_second=30)

    # LED aging and debug
    if time.monotonic() - last_led_time > 0.4:
        last_led_time = time.monotonic()
        leds.fill(0) # age out "you were hit" LEDs
        if 'Macropad' in board_type:  # FIXME figure out way to make per-board
            leds[3:6] = (0x111111,0x111111,0x111111) # return them to on
