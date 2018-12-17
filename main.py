import pygame, engine, math
from engine.display import Display
from engine.eventlistener import EventListener
from engine.linedef import LineDef
from engine.solidbspnode import SolidBSPNode

print("\n")

# Lines, each vertex connects to the next one in CW fashion
# third element is direction its facing, when CW facing 1 = left
polygons = [
    # open room
    [
        # x, y, facing
        [30,  30, 0],
        [300, 20, 0],
        [400, 300, 0],
        [30, 200, 0]
    ],
    # inner col
    [
        # x, y, facing
        [50,  50, 1],
        [100, 50, 1],
        [75,  75, 1],
        [100, 100, 1],
        [50,  100, 1]
    ],
    # inner room
    [
        [55, 55, 0],
        [70, 55, 0],
        [70, 95, 0],
        [55, 95, 0],
    ]
]

# Line Defs built Clockwise
allLineDefs = []
for i, v in enumerate(polygons):
    polygon = polygons[i]
    lineDefs = []
    for idx, val in enumerate(polygon):
        lineDef = LineDef()

        # first point, connect to second point
        if idx == 0:
            lineDef.asRoot(polygon[idx][0], polygon[idx][1], polygon[idx + 1][0], polygon[idx + 1][1], polygon[idx + 1][2])
            lineDefs.append(lineDef)
            allLineDefs.append(lineDef)

        # some point in the middle
        elif idx < len(polygon) - 1:
            lineDef.asChild(lineDefs[-1], polygon[idx + 1][0], polygon[idx + 1][1], polygon[idx + 1][2])
            lineDefs.append(lineDef)
            allLineDefs.append(lineDef)
        
        # final point, final line, connects back to first point
        elif idx == len(polygon) - 1:
            lineDef.asLeaf(lineDefs[-1], lineDefs[0], polygon[idx][2])
            lineDefs.append(lineDef)
            allLineDefs.append(lineDef)

solidBsp = SolidBSPNode(allLineDefs)
# print(solidBsp.toText())


# TESTING WALL DRAWING
wallTest = allLineDefs[0]
camPoint = [90, 150]
camDir = [0, -1]


# testPoint = [60, 20]
# for lineDef in allLineDefs:
#     isBehind = lineDef.isPointBehind(testPoint[0], testPoint[1])
#     print(lineDef.start, lineDef.end, lineDef.facing, isBehind)
# print(solidBsp.inEmpty(testPoint))

display = Display(1280, 720)
listener = EventListener()
pygame.mouse.set_visible(False)
font = pygame.font.Font(None, 36)
    
# render mode ops
mode = 0
max_modes = 3
def mode_up():
    global mode
    mode = (mode + 1) % max_modes
listener.onKeyUp(pygame.K_UP, mode_up)
def mode_down():
    global mode
    mode = (mode - 1) % max_modes
listener.onKeyUp(pygame.K_DOWN, mode_down)
def on_left():
    global camDir
    camDir = engine.mathdef.rotate2d(camDir[0], camDir[1], -math.pi / 4 / 800)
listener.onKeyHold(pygame.K_LEFT, on_left)
def on_right():
    global camDir
    camDir = engine.mathdef.rotate2d(camDir[0], camDir[1], math.pi / 4 / 800)
listener.onKeyHold(pygame.K_RIGHT, on_right)
def on_a():
    global camDir
    camPoint[0] -= .05
listener.onKeyHold(pygame.K_a, on_a)
def on_d():
    global camDir
    camPoint[0] += .05
listener.onKeyHold(pygame.K_d, on_d)
def on_w():
    global camDir
    camPoint[1] -= .05
listener.onKeyHold(pygame.K_w, on_w)
def on_s():
    global camDir
    camPoint[1] += .05
listener.onKeyHold(pygame.K_s, on_s)

fpvpX = 500
fpvpY = 100
fpvpW = 500
fpvpH = 300
fpvp = [
        [fpvpX, fpvpY],
        [fpvpX + fpvpW, fpvpY],
        [fpvpX + fpvpW, fpvpY + fpvpH],
        [fpvpX, fpvpY + fpvpH],
]

while True:
    listener.update()

    display.start()

    # render the polygons directly
    if mode == 0:
        for lineDef in allLineDefs:
            display.drawLine([lineDef.start, lineDef.end], (0, 0, 255), 1)
            ln = 7
            mx = lineDef.mid[0]
            my = lineDef.mid[1]
            nx = lineDef.normals[lineDef.facing][0] * ln
            ny = lineDef.normals[lineDef.facing][1] * ln
            if lineDef.facing == 1:
                display.drawLine([ [mx, my] , [mx + nx, my + ny] ], (0, 255, 255), 1)
            else:
                display.drawLine([ [mx, my] , [mx + nx, my + ny] ], (255, 0, 255), 1)

    mx, my = pygame.mouse.get_pos()

    # render the tree
    if mode == 1:
        solidBsp.drawSegs(display)
    if mode == 2:
        solidBsp.drawFaces(display, mx, my)

    # render our viewport for 2D
    display.drawLines(fpvp, (100, 100, 100), 1, True)


    camDir = engine.mathdef.normalize(camDir[0], camDir[1])
    camR = engine.mathdef.rotate2d(camDir[0], camDir[1], math.pi / 4)
    camL = engine.mathdef.rotate2d(camDir[0], camDir[1], - (math.pi / 4))

    # compare the wall's left edge to the cameras left edge, repeat for right
    leftSide = [wallTest.start[0], wallTest.start[1]]
    leftSideDistance = engine.mathdef.distance2d(camPoint[0], camPoint[1], leftSide[0], leftSide[1])
    leftSideDirection = [wallTest.start[0] - camPoint[0], wallTest.start[1] - camPoint[1]]
    leftSideRadians = engine.mathdef.toRadians(leftSideDirection[0], leftSideDirection[1])
    leftCameraRadians = engine.mathdef.toRadians(camL[0], camL[1])

    rightSide = [wallTest.end[0], wallTest.end[1]]
    rightSideDistance = engine.mathdef.distance2d(camPoint[0], camPoint[1], rightSide[0], rightSide[1])
    rightSideDirection = [wallTest.end[0] - camPoint[0], wallTest.end[1] - camPoint[1]]
    rightSideRadians = engine.mathdef.toRadians(rightSideDirection[0], rightSideDirection[1])
    rightCameraRadians = engine.mathdef.toRadians(camR[0], camR[1])

    leftIntersection = engine.mathdef.intersection2d(camPoint, [camPoint[0] + camL[0], camPoint[1] + camL[1]], wallTest.start, wallTest.end)
    rightIntersection = engine.mathdef.intersection2d(camPoint, [camPoint[0] + camR[0], camPoint[1] + camR[1]], wallTest.start, wallTest.end)
    leftIntersectionDistance = engine.mathdef.distance2d(camPoint[0], camPoint[1], leftIntersection[0], leftIntersection[1])
    rightIntersectionDistance = engine.mathdef.distance2d(camPoint[0], camPoint[1], rightIntersection[0], rightIntersection[1])

    # Two things we need to determine:
    # 1. Is the wall visible in the camera?
    # 2. At what distance do we draw
    leftInX = (leftSide[0] <= leftIntersection[0] and leftIntersection[0] <= rightSide[0])
    leftInY = (leftSide[1] <= leftIntersection[1] and leftIntersection[1] <= rightSide[1])
    print(leftSide, rightSide, leftInX, leftInY, leftIntersection)




    # p' = P * V * M * p
    # p' is output (screen coords)
    # p = world coords
    # M = identity matrix (world offset?)
    # so p' = P * V * p
    # V = view matrix (translation and rotation of camera)
    #   R = view rotation
    #   T = view translation
    #   p' = P * R * T * p
    # P = projection matrix, can be computed offline, dependent on FoV and near/far clipping planes which are hard coded (90deg)
    '''
    function S3Proj(x,y,z)
     local c, s, a, b = S3.cosMy, S3.sinMy, S3.termA, S3.termB
     local px = 0.9815 * c * x+0.9815 * s *z+0.9815 * a
     local py = 1.7321 * y - 1.7321 * S3.ey
     local pz = s * x - z * c - b - 0.2
     local pw = x * s - z * c - b
     local ndcx, ndcy = px / abs(pw), py / abs(pw)
     return 120 + ndcx * 120, 68 - ndcy * 68, pz
    end
    '''
    '''
    FOR SX=0,127 DO
     ...
     LOCAL T=SX/127
     VX = V.X0 * (1-T) + V.X1 * T
     VY = V.Y0 * (1-T) + V.Y1 * T
    '''
    # Once a ray hits a wall, we want to find the position of the foot of the wall
    # on the screen. We can do this with SH/2 + K/TDIST, where SH is the screen
    # height, and K is some constant. Intuitively, as TDIST gets bigger (further
    # away), the foot of the wall shrinks toward the horizon. Similarly the
    # position of the top of the wall is SH/2 - K/TDIST.

    lensWidth = fpvpW
    leftHeight = 1 / leftIntersectionDistance
    rightHeight = 1 / rightIntersectionDistance

    wall = [
        [fpvpX, fpvpY + (fpvpH / 2) - 5000 * leftHeight],
        [fpvpX, fpvpY + (fpvpH / 2) + 5000 * leftHeight],
        [fpvpX + fpvpW, fpvpY + (fpvpH / 2) + 5000 * rightHeight],
        [fpvpX + fpvpW, fpvpY + (fpvpH / 2) - 5000 * rightHeight],
    ]
    display.drawLines(wall, (255, 255, 0), 1, True)



    # we can create intersection points on the screen with our fov to clip the frame
    # dist1 = engine.mathdef.distance2d(camPoint[0], camPoint[1], wallTest.start[0], wallTest.start[1])
    # dist2 = engine.mathdef.distance2d(camPoint[0], camPoint[1], wallTest.end[0], wallTest.end[1])

    # h = 1 # height of "wall"
    # perpWallDist1 = dist1 / 2 # / rayDirX
    # lineHeight1 = h / perpWallDist1
    # perpWallDist2 = dist2 / 2 # / rayDirX
    # lineHeight2 = h / perpWallDist2
    # # print (dist1, dist2, lineHeight1, lineHeight2)

    ll = 40
    display.drawLine([ camPoint, [camPoint[0] + camDir[0] * ll, camPoint[1] + camDir[1] * ll] ], (175, 175, 175), 1)
    display.drawLine([ camPoint, [camPoint[0] + camR[0] * ll, camPoint[1] + camR[1] * ll] ], (255, 0, 0), 1)
    display.drawLine([ camPoint, [camPoint[0] + camL[0] * ll, camPoint[1] + camL[1] * ll] ], (255, 0, 0), 1)
    display.drawPoint(camPoint, (255, 255, 255), 2)

    # wallOffsetX = 500
    # wallOffsetY = 500

    # # build lines
    # wall = [
    #     [wallOffsetX,           wallOffsetY - 5000 * lineHeight1],
    #     [wallOffsetX,           wallOffsetY + 5000 * lineHeight1],
    #     [wallOffsetX + 400,     wallOffsetY + 5000 * lineHeight2],
    #     [wallOffsetX + 400,     wallOffsetY - 5000 * lineHeight2],
    # ]
    # display.drawLines(wall, (255, 255, 0), 1, True)

    # draw our position information
    text = font.render("{}, {}".format(mx, my), 1, (50, 50, 50))
    textpos = text.get_rect(centerx = display.width / 2, centery = display.height/2)
    display.drawText(text, textpos)

    # test our BSP tree
    inEmpty = solidBsp.inEmpty([mx, my])
    display.drawPoint([mx, my], (0,255,255) if inEmpty else (255, 0, 0), 4)

    display.end()