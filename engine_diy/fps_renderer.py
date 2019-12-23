import random, math
from engine_diy.player import Player
from engine_diy.angle import Angle
from engine_diy.segment_range import SolidSegmentRange
from engine_diy.map import *

class FpsRenderer(object):
    def __init__(self, map, player, game, fov, width, height, xOffset, yOffset):
        self.map = map
        self.player = player
        self.game = game
        self.fov = fov
        self.width = width
        self.height = height
        self.xOffset = xOffset
        self.yOffset = yOffset

        self.wallColors = {} # helper to map a texture to a single color (until textures are added)
        self.onSegInspect = None # function pointer for helping to visualize segs in fps viewport

    def renderEdgesOnly(self, solidOnly = False, onSegInspect = None):
        # loop over all segs
        for i, seg in enumerate(self.map.segs):
            linedef = self.map.linedefs[seg.linedefID]
            # if in mode 8 only render solid walls
            if solidOnly and linedef.isSolid() is False:
                continue

            v1 = self.map.vertices[seg.startVertexID]
            v2 = self.map.vertices[seg.endVertexID]
            angles = self.clipVerticesToFov(v1, v2)
            if angles is not None:
                if onSegInspect is not None:
                    onSegInspect(seg, v1, v2)

                # render fps window for all walls
                v1xScreen = self.angleToScreen(angles[0])
                v2xScreen = self.angleToScreen(angles[1])

                # wall edge1
                fpsStart = [v1xScreen + self.xOffset, self.yOffset]
                fpsEnd = [v1xScreen + self.xOffset, self.height + self.yOffset]
                self.game.drawLine(fpsStart, fpsEnd, (1,1,0,1), 1)

                # wall edge 2
                fpsStart = [v2xScreen + self.xOffset, self.yOffset]
                fpsEnd = [v2xScreen + self.xOffset, self.height + self.yOffset]
                self.game.drawLine(fpsStart, fpsEnd, (1,0,1,1), 1)

    def render(self, onSegInspect = None):

        # optional function pointer when we inspect a visible seg
        self.onSegInspect = onSegInspect

        # clear our clipping list of walls
        self.segList = [SolidSegmentRange(-100000, -1)]
        self.segList.append(SolidSegmentRange(self.width, 100000))
        self.clippings = {} # dict of segIds to screenXs

        # render 3d viewport
        self.map.renderBspNodes(self.player.x, self.player.y, self.renderSubsector)

    def renderSubsector(self, subsectorId):
        # iterate segs in subsector
        subsector = self.map.subsectors[subsectorId]
        for i in range(subsector.segCount):
            segId = subsector.firstSegID + i
            seg = self.map.segs[segId]
            linedef = self.map.linedefs[seg.linedefID]
            if linedef.isSolid() is False: # skip non-solid walls for now
                continue

            v1 = self.map.vertices[seg.startVertexID]
            v2 = self.map.vertices[seg.endVertexID]
            angles = self.clipVerticesToFov(v1, v2)

            if angles is not None:
                if self.onSegInspect is not None:
                    self.onSegInspect(seg, v1, v2)
                # get screen projection Xs
                v1xScreen = self.angleToScreen(angles[0])
                v2xScreen = self.angleToScreen(angles[1])

                # build wall clippings
                self.clipWall(segId, self.segList, v1xScreen, v2xScreen, self.clippings, self.renderRange)

    def renderRange(self, segId, segPair):
        # get unique color for this line
        linedef = self.map.linedefs[self.map.segs[segId].linedefID]
        sidedef = self.map.sidedefs[linedef.frontSideDef]
        rgba = self.getWallColor(sidedef.middleTexture)
        # hardcoded helper to render the range
        fpsStart = [segPair[0] + self.xOffset, self.yOffset]
        # ranges are exclusive of eachothers start and end
        # so add +1 to width (not for now because I like the line)
        width = segPair[1] - segPair[0] # + 1
        self.game.drawRectangle(fpsStart, width, self.height, rgba)

    def angleToScreen(self, angle):
        ix = 0
        halfWidth = (int)(self.width / 2)
        if angle.gtF(self.fov):
            # left side
            angle.isubF(self.fov)
            ix = halfWidth - (int)(math.tan(angle.toRadians()) * halfWidth)
        else:
            # right side
            angle = Angle(self.fov - angle.deg)
            ix = (int)(math.tan(angle.toRadians()) * halfWidth)
            ix += halfWidth
        return ix

    def angleToVertex(self, vertex):
        vdx = vertex.x - self.player.x
        vdy = vertex.y - self.player.y

        radians = math.atan2(vdy, vdx)
        return Angle.fromRadians(radians)

    def isSegFacingUs(self, seg):
        # if angle to vertex1 > vertex2
        # then the seg is facing us
        # this is because the placement of a seg
        # vertices indicate which way it faces
        v1 = self.map.vertices[seg.startVertexID]
        v2 = self.map.vertices[seg.endVertexID]
        v1Angle = self.angleToVertex(v1)
        v2Angle = self.angleToVertex(v2)
        spanAngle = v1Angle.subA(v2Angle)
        if spanAngle.gteF(self.fov * 2):
            return None

    def clipSegToFov(self, seg):
        fov = Angle(self.fov)
        v1 = self.map.vertices[seg.startVertexID]
        v2 = self.map.vertices[seg.endVertexID]
        return self.clipVerticesToFov(v1, v2, fov)

    def clipVerticesToFov(self, v1, v2):
        fov = Angle(self.fov)
        v1Angle = self.angleToVertex(v1)
        v2Angle = self.angleToVertex(v2)
        spanAngle = v1Angle.subA(v2Angle)
        if spanAngle.gteF(self.fov * 2):
            return None
        # Cases
        #  ~: Seg left and right are in fov and fully visible
        #  A: Seg is all the way to the left and not visible
        #  B: Seg is to the right and not visible
        #  C: Right part of seg is visible and left is clipped
        #  D: Left part of seg is visible and right is clipped
        #  E: Left and right are clipped but middle is visible
        # segs must be facing us
        # segs are made of two vertices
        # rotate the seg minus the player angle
        v1Angle = v1Angle.subA(self.player.angle)
        v2Angle = v2Angle.subA(self.player.angle)
        # this puts their vertices around the 0 degree
        # left side of FOV is 45
        # right side of FOV = -45 (315)
        # if we rotate player to 45 then
        # left side is at 90
        # right side is at 0 (no negative comparisons)
        # if V1 is > 90 its outside
        # if V2 is < 0 its outside
        # v1 test:
        halfFov = fov.divF(2)
        v1Moved = v1Angle.addA(halfFov)
        if v1Moved.gtA(fov):
            # v1 is outside the fov
            # check if angle of v1 to v2 is also outside fov
            # by comparing how far v1 is away from fov
            # if more than dist v1 to v2 then the angle outside fov
            v1MovedAngle = v1Moved.subA(fov)
            if v1MovedAngle.gteA(spanAngle):
                return None

            # v2 is valid, clip v1
            v1Angle = halfFov
        # v2 test: (we cant have angle < 0 so subtract angle from halffov)
        v2Moved = halfFov.subA(v2Angle)
        if v2Moved.gtA(fov):
            v2Angle = halfFov.neg()

        # rerotate angles
        v1Angle.iaddA(fov)
        v2Angle.iaddA(fov)

        return v1Angle, v2Angle

    def getWallColor(self, textureId):
        if textureId in self.wallColors:
            return self.wallColors[textureId]
        rgba = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1), 1)
        self.wallColors[textureId] = rgba
        return rgba

    # python DIY linked lists are a nightmare
    # because of the pass-object-by-reference
    # nature of variables
    # when I change next and prev values on a
    # node it changes it for that copy of the
    # variable, and not for the underlying reference
    # TODO take a seg and implement StoreWallRange
    # so that we can update the segs display range
    def clipWall(self, segId, segList, wallStart, wallEnd, clippings, renderRange):
        segRange = None
        segIndex = None
        # skip all segments that end before this wall starts
        i=0
        while (i < len(segList) and segList[i].xEnd < wallStart - 1):
            i += 1
        segIndex = i
        segRange = segList[segIndex]
        # should always have a node since we cap our ends with
        # "infinity"
        # START to OVERLAP
        if wallStart < segRange.xStart:
            # found a position in the node list
            # are they overlapping?
            if wallEnd < segRange.xStart - 1:
                # all of the wall is visible to insert it
                # STOREWALL
                # StoreWallRange(seg, CurrentWall.XStart, CurrentWall.XEnd);
                clippings[segId] = (wallStart, wallEnd)
                renderRange(segId, clippings[segId])
                segList.insert(segIndex, SolidSegmentRange(wallStart, wallEnd))
                # go to next wall
                return
            # if not overlapping, end is already included
            # so just update the start
            # STOREWALL
            # StoreWallRange(seg, CurrentWall.XStart, FoundClipWall->XStart - 1);
            clippings[segId] = (wallStart,  segRange.xStart - 1)
            renderRange(segId, clippings[segId])
            segRange.xStart = wallStart
        # FULL OVERLAPPED
        # this part is already occupied
        if wallEnd <= segRange.xEnd:
            return # go to next wall

        # CHOP AND MERGE
        # start by looking at the next entry in the list
        # is the next entry within the current wall range?
        nextSegIndex = segIndex
        nextSegRange = segRange
        while wallEnd >= segList[nextSegIndex + 1].xStart - 1:
            # STOREWALL
            # StoreWallRange(seg, NextWall->XEnd + 1, next(NextWall, 1)->XStart - 1);
            clippings[segId] = (nextSegRange.xEnd + 1,  segList[nextSegIndex + 1].xStart - 1)
            renderRange(segId, clippings[segId])
            nextSegIndex += 1
            nextSegRange = segList[nextSegIndex]
            # partially clipped by other walls, store each fragment
            if wallEnd <= nextSegRange.xEnd:
                segRange.xEnd = nextSegRange.xEnd
                if nextSegIndex != segIndex:
                    segIndex += 1
                    nextSegIndex += 1
                    del segList[segIndex:nextSegIndex]
                return

        # wall precedes all known segments
        # STOREWALL
        # StoreWallRange(seg, NextWall->XEnd + 1, CurrentWall.XEnd);
        clippings[segId] = (nextSegRange.xEnd + 1,  wallEnd)
        renderRange(segId, clippings[segId])
        segRange.xEnd = wallEnd
        if (nextSegIndex != segIndex):
            segIndex += 1
            nextSegIndex += 1
            del segList[segIndex:nextSegIndex]
        return

    def printSegList(self, segList):
        for i,r in enumerate(segList):
            if i+1 < len(segList):
                print("{} > ".format(r), end='')
            else:
                print(r, end='')
        print('')

