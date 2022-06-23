# =============================================================================
# >> IMPORTS
# =============================================================================
# EventScripts
from vecmath import vector

# SPE Effects
from spe_effects import *


# =============================================================================
# >> FUNCTIONS
# =============================================================================
def polygon(points,
        users='#all',
        delay=0,
        model='sprites/laser.vmt',
        halo=0,
        startframe=0,
        framerate=255,
        life=3,
        width=3,
        endwidth=3,
        fadelength=3,
        amplitude=0,
        r=255,
        g=255,
        b=255,
        a=255,
        speed=1,
        parent=False,
        queue=True):
    '''
    Creates a polygon by entity indexes and/or coordinates. If you set
    "parent" to True, all beams are parented to all given indexes.
    '''

    count = len(points)
    if count < 3:
        raise SPEEffectError('"points" requires at least 3 coordinates an' + \
            'd/or entity indexes, but %i were given'% count)

    points = dict(enumerate(points))
    for index in points.iterkeys():
        beam(users, delay, points[index], points.get(index+1, points[0]),
            model, halo, startframe, framerate, life, width, endwidth,
            fadelength, amplitude, r, g, b, a, speed, parent, queue)

def square(start, end,
        frame=True,
        fill=False,
        steps=15,
        users='#all',
        delay=0,
        model='sprites/laser.vmt',
        halo=0,
        startframe=0,
        framerate=255,
        life=3,
        width=3,
        endwidth=3,
        fadelength=3,
        amplitude=0,
        r=255,
        g=255,
        b=255,
        a=255,
        speed=1,
        queue=True):
    '''
    Creates a simple, rectangular square by entity indexes and/or coordinates.
    You can fill it by setting "fill" to True. If you decided to fill the
    square, you need to set "steps" to the number of lines should be used to
    fill it. You can also disable the frame by setting "frame" to False.
    '''

    start = vector(getLocation(start))
    end = vector(getLocation(end))

    if frame:
        p1 = vector(start)
        p2 = vector(end)
        p1.z = end.z
        p2.z = start.z
        polygon((start, p1, end, p2), users, delay, model, halo, startframe,
            framerate, life, width, endwidth, fadelength, amplitude, r, g, b,
            a, speed, queue=queue)

    if not fill:
        return

    minz = min(start.z, end.z)
    step = (max(start.z, end.z) - minz) / (steps + 1)
    end.z = minz
    start.z = minz
    for x in xrange(steps):
        start.z += step
        end.z += step
        beamPoints(users, delay, start, end, model, halo, startframe,
            framerate, life, width, endwidth, fadelength, amplitude, r, g, b,
            a, speed, queue=queue)

def box(start, end,
        frame=True,
        fill=False,
        steps=15,
        users='#all',
        delay=0,
        model='sprites/laser.vmt',
        halo=0,
        startframe=0,
        framerate=255,
        life=3,
        width=3,
        endwidth=3,
        fadelength=3,
        amplitude=0,
        r=255,
        g=255,
        b=255,
        a=255,
        speed=1,
        queue=True):
    '''
    Creates a simple rectangular box by entity indexes and/or coordinates.
    You can fill the walls by setting "fill" to True. If you decided to fill
    the box, you need to set "steps" to the number of lines should be used to
    fill it. You can also disable the frame by setting "frame" to False.
    '''

    start = vector(getLocation(start))
    end   = vector(getLocation(end))

    p1 = vector(start)
    p2 = vector(start)
    p3 = vector(start)
    p4 = vector(end)
    p5 = vector(end)
    p6 = vector(end)

    p1.x = end.x
    p2.y = end.y
    p3.z = end.z
    p4.x = start.x
    p5.y = start.y
    p6.z = start.z

    args = (model, halo, startframe, framerate, life, width, endwidth,
        fadelength, amplitude, r, g, b, a, speed)

    args2 = (False, fill, steps, users, delay)

    square(start, p4, queue=queue, *args2+args)
    square(start, p5, queue=queue, *args2+args)
    square(p1, end, queue=queue, *args2+args)
    square(p2, end, queue=queue, *args2+args)

    if not frame:
        return

    polygon((start, p1, p5, p3), users, delay, *args)
    polygon((end, p4, p2, p6), users, delay, *args)

    beamPoints(users, delay, start, p2, queue=queue, *args)
    beamPoints(users, delay, p1, p6, queue=queue, *args)
    beamPoints(users, delay, p5, end, queue=queue, *args)
    beamPoints(users, delay, p3, p4, queue=queue, *args)

def ball(origin, radius,
        steps=15,
        users='#all',
        delay=0,
        model='sprites/laser.vmt',
        halo=0,
        startframe=0,
        framerate=255,
        life=3,
        width=3,
        spread=0,
        amplitude=0,
        r=255,
        g=255,
        b=255,
        a=255,
        speed=1,
        flags=0,
        upper=True,
        lower=True,
        queue=True):
    '''
    Creates a ball by an entity index or coordinate and a radius.

    NOTE:
    The number of steps is used for the lower and upper half.
    '''

    step = float(radius) / steps
    for x in xrange(steps):
        dist = step * x
        org = vector(origin)
        org.z += dist
        rad = 2 * radius * (1 - (float(x) / steps) ** 2) ** 0.5

        args = (users, delay, org, rad, rad-0.1, model, halo, startframe,
            framerate, life, width, spread, amplitude, r, g, b, a, speed,
            flags)

        if upper:
            beamRingPoint(queue=queue, *args)

        if not x or not lower:
            continue

        org.z -= 2 * dist
        beamRingPoint(queue=queue, *args)