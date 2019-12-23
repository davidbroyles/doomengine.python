import sys, engine_diy, pygame, random, math
from engine_diy.wad import WAD
from engine_diy.game2d import Game2D
from engine_diy.map import *
from engine_diy.player import Player
from engine_diy.angle import Angle
from engine_diy.segment_range import *
from engine_diy.fps_renderer import FpsRenderer


#############
## HELPERS ##
#############
#############

class Plot(object):
    def __init__(self, map, surfWidth, surfHeight):
        # calculate map scale to fit screen minus padding
        self.pad = pad = 10
        gw = (surfWidth - self.pad*2)
        gh = (surfHeight - self.pad*2)
        self.scale = scale = min(gw/map.width, gh/map.height)

        # center the map on the screen
        self.xoff = (surfWidth - (map.width * scale))/2 - (map.minx * scale)
        self.yoff = (surfHeight - (map.height *scale))/2 + (map.maxy * scale)
    def ot(self, x, y):
        # flip cartesian, scale and translate
        x = x * self.scale + self.xoff
        y = -y * self.scale + self.yoff
        return x, y


# helper method to draw map nodes
def drawNode(game, node):
    ## draw front box
    rgba = (0, 1, 0, .5)
    fl, ft = pl.ot(node.frontBoxLeft, node.frontBoxTop)
    fr, fb = pl.ot(node.frontBoxRight, node.frontBoxBottom)
    game.drawBox([fl, ft], [fr, ft], [fr, fb], [fl, fb], rgba, 2)

    ## draw back box
    rgba = (1, 0, 0, .5)
    bl, bt = pl.ot(node.backBoxLeft, node.backBoxTop)
    br, bb = pl.ot(node.backBoxRight, node.backBoxBottom)
    game.drawBox([bl, bt], [br, bt], [br, bb], [bl, bb], rgba, 2)

    ## draw the node seg splitterd
    rgba = (1, 1, 0, 1)
    xp, yp = pl.ot(node.xPartition, node.yPartition)
    xc, yc = pl.ot(node.xPartition + node.xChangePartition, node.yPartition + node.yChangePartition)
    game.drawLine([xp, yp], [xc, yc], (0,0,1,1), 3)

# helper method to highlight a single subsector
def drawSubsector(subsectorId, rgba=None):
    global game, map, pl
    subsector = map.subsectors[subsectorId]
    if rgba is None:
        rgba = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1), 1)
    for i in range(0, subsector.segCount):
        seg = map.segs[subsector.firstSegID + i]
        startVertex = map.vertices[seg.startVertexID]
        endVertex = map.vertices[seg.endVertexID]
        sx, sy = pl.ot(startVertex.x, startVertex.y)
        ex, ey = pl.ot(endVertex.x, endVertex.y)
        game.drawLine([sx,sy], [ex,ey], rgba, 2)



#############
##  START  ##
#############
#############

# path to wad
if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    path = "wads/DOOM.WAD"
# map name
if len(sys.argv) > 2:
    mapname = sys.argv[2]
else:
    mapname = "E1M1"

# load WAD
wad = WAD(path)

# choose a map
map = wad.loadMap(mapname)
if map == None:
    print("ERROR: invalid map {}".format(mapname))
    quit()

# build player
player = Player()
player.id = 1
player.setPosition(map.playerThing.x, map.playerThing.y)
player.setAngle(map.playerThing.angle)


# setup game
game = Game2D()
game.setupWindow(1600, 1200)

# main screen plot
pl = Plot(map, game.width, game.height)

# fps window
fov = 90
fpsWinWidth = 320
fpsWinHeight = 200
fpsWinOffX = 20
fpsWinOffY = 20
fpsRenderer = FpsRenderer(map, player, game, fov, fpsWinWidth, fpsWinHeight, fpsWinOffX, fpsWinOffY)

# render helpers
mode = 0
max_modes = 10
def mode_up():
    global mode
    mode = (mode + 1) % max_modes
game.onKeyUp(pygame.K_UP, mode_up)
def mode_down():
    global mode
    mode = (mode - 1) % max_modes
game.onKeyUp(pygame.K_DOWN, mode_down)
def on_left():
    global player
    player.angle.iaddF(2) # rotate left
game.onKeyHold(pygame.K_LEFT, on_left)
def on_right():
    global player
    player.angle.isubF(2) # rotate right
game.onKeyHold(pygame.K_RIGHT, on_right)
def on_w():
    global player
    player.y += 5 # move "up"/"forward" (positive y in game world)
game.onKeyHold(pygame.K_w, on_w)
def on_s():
    global player
    player.y -= 5 # move "down"/"backward" (negative y in game world)
game.onKeyHold(pygame.K_s, on_s)
def on_a():
    global player
    player.x -= 5 # move "left"
game.onKeyHold(pygame.K_a, on_a)
def on_d():
    global player
    player.x += 5 # move "left"
game.onKeyHold(pygame.K_d, on_d)



###############
## GAME LOOP ##
###############
###############

modeSSrenderIndex = 0
modeAngleIndex = 0
while True:

    game.events()
    if game.over:
        break;

    # update

    # draw
    game.drawStart()

    # loop over linedefs
    for i, ld in enumerate(map.linedefs):
        start = map.vertices[ld.startVertexID]
        end = map.vertices[ld.endVertexID]
        # map is in cartesian, flip to screen y
        sx, sy = pl.ot(start.x, start.y)
        ex, ey = pl.ot(end.x, end.y)
        # draw the line
        game.drawLine([sx, sy], [ex, ey], (1,1,1,1), 1)

    # MODE LOOPS
    game.setFPS(60)

    # RENDER THINGS AS DOTS
    if mode == 1:
        for i, thing in enumerate(map.things):
            x, y = pl.ot(thing.x, thing.y)
            game.drawRectangle([x-2,y-2], 4, 4, (1,0,0,1))

        ## render player
        px, py = pl.ot(player.x, player.y)
        game.drawRectangle([px-2,py-2], 4, 4, (0,1,0,1))

    # RENDER ROOT NODE BSP BOXES
    if mode == 2:
        drawNode(game, map.getRootNode())

    # RENDER ALL NODE BSP BOXES
    if mode == 3:
        for i, n in enumerate(map.nodes):
            drawNode(game, n)

    # RENDER SUBSECTORS VIA BSP TRAVERSAL
    if mode == 4:
        game.setFPS(10)
        modeSSrenderIndex = ( modeSSrenderIndex + 1 ) % len(map.subsectors)
        drawSubsector(modeSSrenderIndex, (1, 0, 0, 1))

    # RENDER SUBSECTOR OF PLAYER
    if mode == 5:
        # render player
        px, py = pl.ot(player.x, player.y)
        game.drawRectangle([px-2,py-2], 4, 4, (0,1,0,1))
        # render player subsector
        ssId = map.getSubsector(player.x, player.y)
        drawSubsector(ssId)

    # RENDER ANGLE FROM PLAYER TO EACH VERTEX
    if mode == 6:
        game.setFPS(10)
        modeAngleIndex = (modeAngleIndex + 1) % len(map.vertices)
        # render player
        px, py = pl.ot(player.x, player.y)
        game.drawRectangle([px-2,py-2], 4, 4, (0,1,0,1))
        # render target vertex
        vertex = map.vertices[modeAngleIndex]
        vx, vy = pl.ot(vertex.x, vertex.y)
        game.drawRectangle([vx-3,vy-3], 6, 6, (1,0,0,1))
        # test angle
        a = player.angleToVertex(vertex)
        dirx, diry = a.toVector()
        # render angle
        endx, endy = pl.ot(player.x + dirx*50, player.y + diry*50)
        game.drawLine([px, py], [endx, endy], (0,1,1,1), 2)

    # RENDER FPS FOR WALL EDGES ONLY
    if mode == 7 or mode == 8:
        # render player
        px, py = pl.ot(player.x, player.y)
        game.drawRectangle([px-2,py-2], 4, 4, (0,1,0,1))

        # render only the wall edges
        def onSegInspect(seg, v1, v2):
            # render the seg (helper)
            v1x, v1y = pl.ot(v1.x, v1.y)
            v2x, v2y = pl.ot(v2.x, v2.y)
            game.drawLine([v1x,v1y], [v2x,v2y], (1,0,0,1), 2)

        fpsRenderer.renderEdgesOnly(mode == 8, onSegInspect)

    # RENDER FPS WITH WALL CULLING ONLY
    if mode == 9:
        # render player
        px, py = pl.ot(player.x, player.y)
        game.drawRectangle([px-2,py-2], 4, 4, (0,1,0,1))

        # test rendering segs with wall culling
        def onSegInspect(seg, v1, v2):
            # render the seg (helper)
            v1x, v1y = pl.ot(v1.x, v1.y)
            v2x, v2y = pl.ot(v2.x, v2.y)
            game.drawLine([v1x,v1y], [v2x,v2y], (1,0,0,1), 2)

        fpsRenderer.renderWallCullingOnly(onSegInspect)

    game.drawEnd()


    # dinky gameloop
    game.sleep()

