# =============================================================================
# >> IMPORTS
# =============================================================================
# EventScripts
import es
import gamethread

# SPE Effects
from spe_effects import beamRingPoint


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
__self__ = __import__(__name__)
Beacons  = {}


# =============================================================================
# >> FUNCTIONS
# =============================================================================
def create(userid, override=False, **kw):
    '''
    Creates a new beacon for the given player. If you set "override" to True,
    the old beacon is deleted (if it exists) and a new one is created.
    Otherwise no new beacon is created. You can also change the default values
    for the beacon by passing them as keywords or change the attributes of the
    new created instance:

    Values:
    - Effect:
        users       = '#all'
        startradius = 0
        endradius   = 400
        model       = 'sprites/laser.vmt'
        halo        = 0
        startframe  = 0
        framerate   = 255
        width       = 2
        spread      = 0
        amplitude   = 0
        r           = 255
        g           = 255
        b           = 255
        a           = 255
        speed       = 1
        flags       = 0
        offset      = {'x':0, 'y': 0, 'z': 5}

    - Sound:
        sound       = 'buttons/blip1.wav'
        soundtype   = 'emitsound'
        volume      = 1
        attenuation = 0.75

    - Miscellaneous:
        duration     = 'indefinitely'
        interval     = 1.5
        precallback  = lambda userid, instance: None
        postcallback = lambda userid, instance: None
        destcallback = lambda userid, instance: None
    '''

    if not es.exists('userid', userid):
        return None

    userid = int(userid)
    if override or not exists(userid):
        if es.getplayerprop(userid, 'CBasePlayer.pl.deadflag'):
            return None

        pause(userid)
        beacon = Beacons[userid] = _Beacon(userid, **kw)

    else:
        beacon = Beacon[userid]

    return beacon

def start(userid):
    '''
    Starts the beacon for the given player, if it exists.
    '''

    beacon = find(userid)
    if beacon:
        beacon.start()

def find(userid):
    '''
    Returns the instance of the beacon for the given player, if it exists.
    Otherwise None is returned.
    '''

    return Beacons[int(userid)] if exists(userid) else None

def exists(userid):
    '''
    Returns True if a beacon exists for the given player, False if it doesn't.
    '''

    return int(userid) in Beacons

def pause(userid):
    '''
    Pauses the beacon for the given player, if it exists and is running.
    '''

    beacon = find(userid)
    if beacon:
        beacon.pause()

def resume(userid):
    '''
    Resumes the beacon for the given player, if it exists and was stopped.
    '''

    beacon = find(userid)
    if beacon:
        beacon.resume()

def stop(userid):
    '''
    Stops and deletes the beacon for the given player, if it exists.
    '''

    beacon = find(userid)
    if beacon:
        beacon.stop()


# =============================================================================
# >> CLASSES
# =============================================================================
class _Beacon(object):
    '''
    This class is used to create a beacon for a player.

    NOTE:
    Don't use the init() function, but the create() function, if you don't
    want multiple beacons at the same time and an error when stopping it!
    '''

    def __init__(self, userid, **kw):
        '''
        Initializes the beacon for the given player.
        '''

        self.__userid  = int(userid)
        self.__name    = 'Beacon: %s'% userid
        self.__stopped = True

        self.users       = '#all'
        self.startradius = 0
        self.endradius   = 350
        self.model       = 'sprites/laserbeam.vmt'
        self.halo        = 0
        self.startframe  = 0
        self.framerate   = 255
        self.width       = 2
        self.spread      = 0
        self.amplitude   = 0
        self.r           = 255
        self.g           = 255
        self.b           = 255
        self.a           = 255
        self.speed       = 1
        self.flags       = 0
        self.offset      = {'x':0, 'y': 0, 'z': 5}

        self.sound       = 'buttons/blip1.wav'
        self.soundtype   = 'emitsound'
        self.volume      = 1
        self.attenuation = 0.75

        self.duration     = 'indefinitely'
        self.interval     = 1.5
        self.precallback  = lambda userid, instance: None
        self.postcallback = lambda userid, instance: None
        self.destcallback = lambda userid, instance: None

        for key, value in kw.iteritems():
            setattr(self, key, value)

    def __del__(self):
        '''
        Calls the end callback.
        '''

        self.destcallback(self.__userid, self)

    def __mainloop(self):
        '''
        Creates the beacon, plays the sound and calls the callbacks.
        '''

        if self.duration != 'indefinitely':
            self.duration -= self.interval

        if self.duration <= 0:
            return stop(self.__userid)

        self.precallback(self.__userid, self)
        origin = es.getplayerlocation(self.__userid)
        origin = tuple(origin[x]+self.offset[y] for x, y in enumerate('xyz'))
        beamRingPoint(self.users, 0, origin, self.startradius, self.endradius,
            self.model, self.halo, self.startframe, self.framerate,
            self.interval, self.width, self.spread, self.amplitude, self.r,
            self.g, self.b, self.a, self.speed, self.flags)

        if self.soundtype == 'emitsound':
            es.emitsound('player', self.__userid, self.sound, self.volume,
                self.attenuation)

        elif self.soundtype == 'playsound':
            es.playsound(self.__userid, self.sound, self.volume)

        self.postcallback(self.__userid, self)
        gamethread.delayedname(self.interval, self.__name, self.__mainloop)

    def start(self):
        '''
        Starts the beacon. It's the same like resume().
        '''

        self.resume()

    def pause(self):
        '''
        Pauses the beacon.
        '''

        gamethread.cancelDelayed(self.__name)
        self.__stopped = True

    def resume(self):
        '''
        Resumes the beacon, if it was stopped.
        '''

        if not self.__stopped:
            return

        self.__stopped = False
        self.__mainloop()

    def stop(self):
        '''
        Stops and deletes the beacon.
        '''

        self.pause()
        del Beacons[self.__userid]


# =============================================================================
# >> GAME EVENTS
# =============================================================================
def player_death(ev):
    '''
    Tries to stop and delete the beacon for the dying player.
    '''

    stop(ev['userid'])

es.addons.registerForEvent(__self__, 'player_death', player_death)

def player_disconnect(ev):
    '''
    Tries to stop and delete the beacon for the leaving player.
    '''

    stop(ev['userid'])

es.addons.registerForEvent(__self__, 'player_disconnect', player_disconnect)

def round_end(ev):
    '''
    Stops and deletes all running beacons.
    '''

    for beacon in Beacons.values():
        beacon.stop()

es.addons.registerForEvent(__self__, 'round_end', round_end)