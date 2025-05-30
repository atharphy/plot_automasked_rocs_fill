import ROOT
import sys
import getopt
from copy import deepcopy
import os

ROOT.gROOT.SetBatch()

rocsInCol = 2
rocsInRow = 8
rocXLen = 1.0 / rocsInRow
maxRocIdx = rocsInCol * rocsInRow - 1
onlineMaxLadder = [6, 14, 22, 32]
onlineMaxBlade = [11, 17]
maxOnlineModule = 4
maxOnlineDisk = 3
useNumberAsPartName = False
output_dir = "."
inputFileName = "input.dat"
hRes, vRes = 1920, 1080
useFileSuffix = False
colorCoded = False
pixelAlive = False


class HistogramManager:
    def __init__(self):
        self.barrelHists = []
        self.forwardHists = []

        for i, maxLadder in enumerate(onlineMaxLadder, start=1):
            nBinsX = (maxOnlineModule * 2 + 1) * rocsInRow
            nBinsY = (maxLadder * 2 + 1) * rocsInCol
            name = "PXBarrel_Layer{}".format(i)
            hist = ROOT.TH2F(name, name, nBinsX, -(maxOnlineModule + 0.5), maxOnlineModule + 0.5,
                             nBinsY, -(maxLadder + 0.5), maxLadder + 0.5)
            hist.GetXaxis().SetTitle("OnlineSignedModule")
            hist.GetYaxis().SetTitle("OnlineSignedLadder")
            hist.SetOption("COLZ")
            hist.SetStats(0)
            self.barrelHists.append(deepcopy(hist))

        for i, maxBlade in enumerate(onlineMaxBlade, start=1):
            nBinsX = (maxOnlineDisk * 2 + 1) * rocsInRow
            nBinsY = (maxBlade * 2 + 1) * 2 * rocsInCol
            name = "PXForward_Ring{}".format(i)
            hist = ROOT.TH2F(name, name, nBinsX, -(maxOnlineDisk + 0.5), maxOnlineDisk + 0.5,
                             nBinsY, -(maxBlade + 0.5), maxBlade + 0.5)
            hist.GetXaxis().SetTitle("OnlineSignedDisk")
            hist.GetYaxis().SetTitle("OnlineSignedBladePanel")
            hist.SetOption("COLZ")
            hist.SetStats(0)
            self.forwardHists.append(deepcopy(hist))

    def fillHistograms(self, barrelObjs, forwardObjs):
        for b in barrelObjs:
            x, y = b.GetXYCoords()
            hist = self.barrelHists[b.layer - 1]
            binNum = hist.FindBin(x, y)
            hist.SetBinContent(binNum, b.reason)

        for f in forwardObjs:
            x, y = f.GetXYCoords()
            hist = self.forwardHists[f.ring - 1]
            binNum = hist.FindBin(x, y)
            hist.SetBinContent(binNum, f.reason)

    def drawLine(self, lineObj, x1, x2, y1, y2, width=2, style=1, color=1):
        lineObj.SetLineWidth(width)
        lineObj.SetLineStyle(style)
        lineObj.SetLineColor(color)
        lineObj.DrawLine(x1, y1, x2, y2)

    def drawRectangle(self, lineObj, x1, x2, y1, y2, width=2, style=1, color=1):
        self.drawLine(lineObj, x1, x2, y2, y2, width, style, color)
        self.drawLine(lineObj, x2, x2, y2, y1, width, style, color)
        self.drawLine(lineObj, x2, x1, y1, y1, width, style, color)
        self.drawLine(lineObj, x1, x1, y1, y2, width, style, color)

    def prettifyCanvas(self, hist):
        nBinsX = hist.GetXaxis().GetNbins()
        xMin = hist.GetXaxis().GetXmin()
        xMax = hist.GetXaxis().GetXmax()
        nBinsY = hist.GetYaxis().GetNbins()
        yMin = hist.GetYaxis().GetXmin()
        yMax = hist.GetYaxis().GetXmax()

        xLen = int(xMax)
        yLen = int(yMax)

        name = hist.GetName()[0:3]
        isBarrel = True if name != "PXF" else False

        xBaseStep = 1
        xRange = (nBinsX - 1) // (rocsInRow * 2) + 1
        yBaseStep = (yMax - yMin) / nBinsY
        yRange = (nBinsY - 1) // 2 + 1
        if not isBarrel:
            yBaseStep *= 2
            yRange //= 2

        x1 = xMin
        x2 = xMin + xLen
        y1 = yMin
        y2 = yMin

        lineObj = ROOT.TLine()
        lineObj.SetBit(ROOT.kCanDelete)

        for i in range(yRange):
            w = 1 if i % 2 else 2
            self.drawLine(lineObj, x1, x2, y1, y2, w)
            self.drawLine(lineObj, x1, x2, -y1, -y2, w)
            self.drawLine(lineObj, -x1, -x2, -y1, -y2, w)
            self.drawLine(lineObj, -x1, -x2, y1, y2, w)
            y1 += yBaseStep
            y2 += yBaseStep

        x1 = xMin
        x2 = xMin
        y1 = yMin
        y2 = yMin + yLen

        for i in range(xRange):
            self.drawLine(lineObj, x1, x2, y1, y2, style=9)
            self.drawLine(lineObj, x1, x2, -y1, -y2, style=9)
            self.drawLine(lineObj, -x1, -x2, -y1, -y2, style=9)
            self.drawLine(lineObj, -x1, -x2, y1, y2, style=9)
            x1 += xBaseStep
            x2 += xBaseStep

        zeroModuleHeight = yBaseStep if isBarrel else yBaseStep * 0.5
        yRange = int(yMax) if isBarrel else int(yMax) * 2

        x1_base = 0 + xMin
        x2_base = xBaseStep / float(rocsInRow) + xMin
        y1_base = zeroModuleHeight + yMin
        y2_base = 2 * zeroModuleHeight + yMin

        for i in range(yRange):
            y1 = y1_base + i * (zeroModuleHeight * 2) - (zeroModuleHeight if i % 2 else 0)
            y2 = y2_base + i * (zeroModuleHeight * 2) - (zeroModuleHeight if i % 2 else 0)

            for j in range(int(xMax)):
                x1 = x1_base + j * xBaseStep
                x2 = x2_base + j * xBaseStep

                self.drawRectangle(lineObj, x1, x2, y1, y2, color=8)

                x1, x2 = -x1, -x2
                yPosChange = -zeroModuleHeight if i % 2 else zeroModuleHeight
                self.drawRectangle(lineObj, x1, x2, y1 - yPosChange, y2 - yPosChange, color=8)

            y1 = y1 - yMin + yBaseStep
            y2 = y2 - yMin + yBaseStep

            for j in range(int(xMax)):
                x1 = x1_base + j * xBaseStep
                x2 = x2_base + j * xBaseStep

                self.drawRectangle(lineObj, x1, x2, y1, y2, color=8)

                x1, x2 = -x1, -x2
                self.drawRectangle(lineObj, x1, x2, y1 - yPosChange, y2 - yPosChange, color=8)

    def saveHistograms(self):
        for hists in [self.barrelHists, self.forwardHists]:
            for hist in hists:
                if hist.GetEntries():
                    c1 = ROOT.TCanvas(hist.GetName(), hist.GetName(), hRes, vRes)
                    hist.Draw("COLZ")
                    self.prettifyCanvas(hist)
                    suffix = "_{}".format(inputFileName[:-4]) if useFileSuffix else ""
                    out_path = os.path.join(output_dir, "{}{}.png".format(hist.GetName(), suffix))
                    print("Saving histogram to:", out_path)
                    c1.Print(out_path)


class Barrel:
    def __init__(self, part, sector, layer, ladder, module, roc, reason=1):
        self.part = part
        self.sector = sector
        self.layer = layer
        self.ladder = ladder
        self.module = module
        self.roc = roc
        self.reason = reason
        self.isConverted = False

    def convertParts(self):
        if not self.isConverted:
            self.ladder = -self.ladder if self.part % 2 else self.ladder
            self.module = -self.module if self.part <= 2 else self.module
            self.isConverted = True

    def GetXYCoords(self):
        xBase = -0.625 + ((maxRocIdx - self.roc if self.roc >= rocsInRow else self.roc) + 1) * rocXLen
        flipY = (self.module < 0 and self.ladder < 0 and abs(self.ladder) % 2 == 1) or \
                (self.module < 0 and self.ladder >= 0 and self.ladder % 2 == 0) or \
                (self.module >= 0 and self.ladder < 0 and abs(self.ladder) % 2 == 0) or \
                (self.module >= 0 and self.ladder >= 0 and self.ladder % 2 == 1)
        tmpRoc = maxRocIdx - self.roc if flipY else self.roc
        yBase = -0.5 * (tmpRoc // rocsInRow)
        x = self.module + (xBase if self.module < 0 else -xBase - rocXLen)
        y = self.ladder + yBase
        return x, y


class Forward:
    def __init__(self, part, disk, blade, panel, ring, roc, reason=1):
        self.part = part
        self.disk = disk
        self.blade = blade
        self.panel = panel
        self.ring = ring
        self.roc = roc
        self.reason = reason
        self.isConverted = False

    def convertParts(self):
        if not self.isConverted:
            self.blade = -self.blade if self.part % 2 else self.blade
            self.disk = -self.disk if self.part <= 2 else self.disk
            self.isConverted = True

    def GetXYCoords(self):
        xBase = -0.625 + ((maxRocIdx - self.roc if self.roc >= rocsInRow else self.roc) + 1) * rocXLen
        x = self.disk + (xBase if self.disk < 0 else -xBase - rocXLen)
        flipY = (self.panel == 2 if self.disk < 0 else self.panel == 1)
        tmpRoc = maxRocIdx - self.roc if flipY else self.roc
        yBase = -0.25 - 0.25 * (tmpRoc // rocsInRow) + 0.5 * (self.panel - 1)
        y = self.blade + yBase
        return x, y


def TranslatePartString(thePartStr):
    return {"mO": 1, "mI": 2, "pO": 3, "pI": 4}.get(thePartStr, 0)


def GetOnlineBarrelCharacteristics(detElements, roc, freq):
    part = int(detElements[1][1:]) if useNumberAsPartName else TranslatePartString(detElements[1][1:])
    sector = int(detElements[2][3:])
    layer = int(detElements[3][3:])
    ladder = int(detElements[4][3:].rstrip("HF"))
    module = int(detElements[5][3:])
    return Barrel(part, sector, layer, ladder, module, roc, freq)


def GetOnlineForwardCharacteristics(detElements, roc, freq):
    part = int(detElements[1][1:]) if useNumberAsPartName else TranslatePartString(detElements[1][1:])
    disk = int(detElements[2][1:])
    blade = int(detElements[3][3:])
    panel = int(detElements[4][3:])
    ring = int(detElements[5][3:])
    return Forward(part, disk, blade, panel, ring, roc, freq)


histMan = HistogramManager()
barrelObjs = []
forwardObjs = []

if len(sys.argv) > 1:
    inputFileName = sys.argv[1]
    if len(sys.argv) > 2:
        opts, args = getopt.getopt(sys.argv[2:], "bscp", ["help", "output=", "output-dir="])
        for o, a in opts:
            if o == "-b":
                useNumberAsPartName = False
            if o == "-s":
                useFileSuffix = True
            if o == "-c":
                colorCoded = True
            if o == "-p":
                pixelAlive = True
            if o == "--output-dir":
                output_dir = a

with open(inputFileName, "r") as inputFile:
    for item in inputFile:
        if item.startswith("Bad"):
            inputs = item.strip().split()
            if len(inputs) >= 3:
                detElements = inputs[1].split("_")
                roc = int(detElements[6][3:])
                freq = int(inputs[2])
                if detElements[0][0] == "B":
                    obj = GetOnlineBarrelCharacteristics(detElements, roc, freq)
                    obj.convertParts()
                    barrelObjs.append(obj)
                elif detElements[0][0] == "F":
                    obj = GetOnlineForwardCharacteristics(detElements, roc, freq)
                    obj.convertParts()
                    forwardObjs.append(obj)

histMan.fillHistograms(barrelObjs, forwardObjs)
histMan.saveHistograms()