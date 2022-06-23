# A really huge thank to L'In20Cible for showing how to use TE_Effects!!

# =============================================================================
# >> IMPORTS
# =============================================================================
# Python
from binascii  import unhexlify
from configobj import ConfigObj
from path      import path

# EventScripts
import es
import playerlib

# Source-Python-Extensions
import spe


# =============================================================================
# >> ADDON INFORMATION
# =============================================================================
info = es.AddonInfo()
info.name        = 'SPE Effects'
info.version     = '1.0.12'
info.author      = 'Ayuto'
info.url         = 'http://addons.eventscripts.com/addons/user/53757'
info.basename    = 'spe_effects'
info.description = 'Provides many new effects by using SPE'

es.set('spe_effects_version', info.version)
es.makepublic('spe_effects_version')


# =============================================================================
# >> GLOBAL VARIABLES & INITIALIZATION
# =============================================================================
MAX_ENTITIES = 32
DATAPATH = path(__file__).parent.joinpath('data')
EFFECTS  = ConfigObj(DATAPATH.joinpath('effects.ini'))
POINTERS = ConfigObj(DATAPATH.joinpath('pointers.ini'))

if spe.platform == 'nt':
    sig, pos = POINTERS['g_TESystem']['nt']
    g_TESystem = spe.getPointer(sig, int(pos))

else:
    sym = POINTERS['g_TESystem']['linux']
    g_TESystem = spe.getLocVal('i', spe.findSymbol(sym))

spe.parseINI('_libs/python/spe_effects/data/signatures.ini')


# =============================================================================
# >> STATIC EFFECTS
# =============================================================================
def beam(users, delay, start, end, model, halo, startframe, framerate, life,
        width, endwidth, fadelength, amplitude, r, g, b, a, speed,
        parent=True, queue=True):
    '''
    This is a wrapper for beamEnts(), beamPoints() and beamEntPoint(). You can
    pass two entity indexes or an entity index and a cooardinate or even two
    coordinates.
    If you set "parent" to True, the beam is parented to the given entity
    index(es).
    '''

    startindex = 0
    startorigin = 0
    endindex = 0
    endorigin = 0

    if isIndex(start) and parent:
        startindex = start

    else:
        startorigin = getLocation(start)

    if isIndex(end) and parent:
        endindex = end

    else:
        endorigin = getLocation(end)

    beamEntPoint(users, delay, startindex, startorigin, endindex, endorigin,
        model, halo, startframe, framerate, life, width, endwidth, fadelength,
        amplitude, r, g, b, a, speed, queue=queue)

def radioIcon(users, fDelay, userid, queue=True):
    '''
    Creates an exclamation mark above the player's head.
    '''

    if not es.exists('userid', userid):
        return

    player = spe.getPlayer(int(userid))
    QueueSystem.add(spe.call, ('RadioIcon', IRecipientFilter(users), fDelay,
        player), queue)


# =============================================================================
# >> FUNCTIONS
# =============================================================================
def createEffect(effect, users, *args, **kw):
    '''
    Creates an effect by name. You better use the wrappers for your scripts.

    NOTE:
    This function can just create an effect, if it is a part of the class
    CTempEntsSystem.
    '''

    if effect not in EFFECTS:
        raise SPEEffectError('Effect "%s" does not exist'% effect)

    args = (IRecipientFilter(users),) + tuple(map(formatter, args))
    mapping = EFFECTS[effect]['mapping']
    if len(mapping) != len(args):
        raise SPEEffectError('Invalid number of arguments for "' + effect + \
            '". Given: %i, Required: %i'% (len(args), len(mapping)))

    def callEffect():
        func = findVirtualFunc(g_TESystem, int(EFFECTS[effect]['offset']))
        spe.setCallingConvention('thiscall')
        spe.callFunction(func, 'p'+mapping+')v', ((g_TESystem,) + args))

    queue = True if 'queue' not in kw else kw['queue']
    QueueSystem.add(callEffect, (), queue)

def findVirtualFunc(pointer, offset):
    '''
    Finds the virtual function by a pointer and an offset.
    '''

    if spe.platform != 'nt':
        offset += 1

    return spe.getLocVal('i', spe.getLocVal('i', pointer) + (offset * 4))

def formatter(value):
    '''
    Returns:
    1. A pointer, if the given value is iterable.
    2. An index, if the given value ends with ".vmt" or ".mdl".
    3. The given value, if 1 and 2 is false.
    '''

    if hasattr(value, '__iter__'):
        if len(value) > 3:
            raise SPEEffectError('"%s" is not a valid vector'% str(value))

        return Vector(*value)

    if str(value).endswith('.vmt') or str(value).endswith('.mdl'):
        return es.precachemodel(value)

    return value

def getUsers(users):
    '''
    Returns a list of existing user IDs as integers. You can pass an iterable
    containing user IDs, playerlib filter, single user ID, handle or name.
    '''

    if hasattr(users, '__iter__'):
        return map(int, filter(lambda x: es.exists('userid', x), users))

    return playerlib.getUseridList(str(users))

def isIndex(value):
    '''
    Returns False, if the given value is iterable. Otherwise, it returns True.
    '''

    if hasattr(value, '__iter__'):
        return False

    return True

def getLocation(value):
    '''
    Returns the given value, if it is an iterable. Otherwise, it tries to get
    a location by using the given value as an index. If no location was found,
    a tuple of 3 null floats is returned.
    '''

    if hasattr(value, '__iter__'):
        return value

    origin = es.entitygetvalue(value, 'origin')
    if not origin:
        return (0.0, 0.0, 0.0)

    return map(float, origin.split(' '))

def _setupEffectFunction(effect):
    '''
    Interally use only! Setups all effects of CTempEntsSystem as functions!
    '''

    function = lambda *args, **kw: createEffect(effect, *args, **kw)
    function.__doc__ = effect + '(' + EFFECTS[effect]['doc'] + ', queue=True)'
    function.__name__ = effect
    globals()[effect] = function

# Setups all effects as functions
for effect in EFFECTS:
    _setupEffectFunction(effect)


# =============================================================================
# >> CALLBACKS
# =============================================================================
def tick_listener():
    '''
    Used to reset the number of created entities per server tick. This
    increases the number of shown effects in most cases. Take a look at this:
    https://developer.valvesoftware.com/wiki/Temporary_Entity

    It seems that an update is not the server tick, but a client tick?!
    '''

    QueueSystem.entities = 0
    QueueSystem.callNext()

es.addons.registerTickListener(tick_listener)


# =============================================================================
# >> CLASSES
# =============================================================================
class SPEEffectError(Exception): pass


class _QueueSystem(list):
    '''
    This is a really cheap queue system for the temporary effects. For more
    information look at the documentation of tick_listener().
    '''

    def __init__(self):
        '''
        Initializes the queue system by setting the number of created
        temporary effects to 0.
        '''

        self.entities = 0

    def add(self, function, args, queue):
        '''
        If queue is False, the effect is created instantly. It could happen
        that the effect is not shown due to the maximum number of temporary
        entities per update.
        If queue is True, this function tries to create the effect. If it
        fails, the creation is added to the end of this list.
        '''

        if not queue:
            function(*args)

        elif self.entities <= MAX_ENTITIES:
            function(*args)
            self.entities += 1

        else:
            self.append((function, args))

    def callNext(self):
        '''
        Calls the next creations and removes them from the queue.
        '''

        for function, args in self:
            if self.entities > MAX_ENTITIES:
                break

            function(*args)
            self.entities += 1
            self.remove((function, args))

QueueSystem = _QueueSystem()


class IRecipientFilter(int):
    '''
    This class is used to reconstruct the source engine's IRecipientFilter.
    '''

    def __new__(cls, users):
        '''
        Adds all given users to the new created pointer.
        '''

        pointer = spe.alloc(40)
        spe.call('RecipientFilterConst', pointer)
        for userid in getUsers(users):
            player = spe.getPlayer(userid)
            spe.call('AddRecipient', pointer, player)

        return super(cls, cls).__new__(cls, pointer)

    def __init__(self, users):
        pass

    def __del__(self):
        '''
        Calls the destructor and frees the memory.
        '''

        spe.call('RecipientFilterDest', self)
        spe.dealloc(self)


class Vector(int):
    '''
    This class is used to reconstruct the source engine's Vector.
    '''

    def __new__(cls, x=0, y=0, z=0):
        '''
        Creates a pointer and sets the coordinates.
        '''

        pointer = spe.alloc(12)
        spe.setLocVal('f', pointer,     float(x))
        spe.setLocVal('f', pointer + 4, float(y))
        spe.setLocVal('f', pointer + 8, float(z))
        return super(cls, cls).__new__(cls, pointer)

    def __init__(self, x=0, y=0, z=0):
        pass

    def __del__(self):
        '''
        Frees the memory.
        '''

        spe.dealloc(self)