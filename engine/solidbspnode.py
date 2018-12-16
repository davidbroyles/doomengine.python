import random
from engine import linedef
from engine import display

class SolidBSPNode(object):
    def __init__(self, lineDefs):
        self.splitter = None # LineDef
        self.splitterIndex = None
        self.front = None # Self
        self.back =  None # Self
        self.isLeaf = False
        self.isSolid = False

        if len(lineDefs) == 0: # leaf
            return

        # get splitter line
        self.splitterIndex = self.selectBestSplitter(lineDefs)
        self.splitter = lineDefs[self.splitterIndex]

        # iterate the lineDefs and figure out which side of the splitter they are on
        frontList = []
        backList = []
        for lineDef in lineDefs:
            # skip splitter self check
            if lineDef != self.splitter:
                d = self.classifyLine(self.splitter, lineDef)
                
                if d == 1:
                    # Behind
                    backList.append(lineDef)
                elif d == 2:
                    # Front
                    frontList.append(lineDef)
                elif d == 3:
                    # Spanning
                    # first element is behind, second is in front
                    splits = self.splitLine(self.splitter, lineDef)
                    backList.append(splits[0])
                    frontList.append(splits[1])
                else:
                    # co planar
                    backList.append(lineDef)
        
        # all lines have been split and put into front or back list
        if len(frontList) == 0:
            # create an empty leaf node
            self.front = SolidBSPNode([])
            self.front.isLeaf = True
            self.front.isSolid = False
        else:
            # create our recursive front
            self.front = SolidBSPNode(frontList)
        
        if len(backList) == 0:
            # create a solid back node
            self.back = SolidBSPNode([])
            self.back.isLeaf = True
            self.back.isSolid = True
        else:
            # create our recursive back
            self.back = SolidBSPNode(backList)



    def splitLine(self, splitterLineDef, lineDef):
        # first element is behind, second is in front, use facing from parent
        splits = splitterLineDef.split(lineDef)

        splitBehind = splits[0]
        splitBehindDef = linedef.LineDef()
        splitBehindDef.asRoot(splitBehind[0][0], splitBehind[0][1], splitBehind[1][0], splitBehind[1][1], lineDef.facing)

        splitFront = splits[1]
        splitFrontDef = linedef.LineDef()
        splitFrontDef.asRoot(splitFront[0][0], splitFront[0][1], splitFront[1][0], splitFront[1][1], lineDef.facing)
        return [splitBehindDef, splitFrontDef]

    # if all points behind, we would put whole poly in back list
    # if all points ahead, we would put whole poly in front list
    # if overlap, split and put into both
    def classifyLine(self, splitterLineDef, lineDef):
        return splitterLineDef.classifyLine(lineDef)

    def selectBestSplitter(self, lineDefs):
        # TODO, make this smarter
        return 0

    def draw(self, display, depth = 0):
        # draw self
        if self.isLeaf == False:
            display.drawLine([self.splitter.start, self.splitter.end], self.splitter.drawColor, 1)
        if self.back:
            self.back.draw(display, depth + 1)
        if self.front:
            self.front.draw(display, depth + 1)

    def toText(self, depth = 0):
        s = "{}{}".format(" " * depth, self)
        if self.back:
            s += "{}BACK {}: {}".format(" " * depth, depth, self.back.toText(depth+1))
        if self.front:
            s += "{}FRNT {}: {}".format(" " * depth, depth, self.front.toText(depth+1))
        return s

    def __str__(self):
        if self.splitter:
            return "isLeaf: {} - isSolid: {} - splitter: {}, {}\n".format(
                self.isLeaf, self.isSolid, self.splitter.start, self.splitter.end
            )
        else:
            return "isLeaf: {} - isSolid: {}\n".format(
                self.isLeaf, self.isSolid
            )


