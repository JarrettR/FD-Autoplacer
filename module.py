import sys


import base64
import math

# from .arc import Arc
# from .circle import Circle
# from .curve import Curve
from layers import Layers
from line import Line
from metadata import Metadata
from pad import Pad
# from .poly import Poly
# from .segment import Segment
# from .text import Text
# from .via import Via
from zone import Zone


# https://github.com/KiCad/kicad-source-mirror/blob/93466fa1653191104c5e13231dfdc1640b272777/pcbnew/plugins/kicad/pcb_parser.cpp#L2839

# 0 module
# 1 Diode_SMD:D_SMD_SOD123
# 2
#   0 layer
#   1 B.Cu
# 3
#   0 tstamp
#   1 0DF
# 4
#   0 at
#   1 66.66
#   2 99.99
# 3
#   0 descr
#   1 0.25
# 4
#   0 tags
#   1 B.Cu
# 5
#   0 path
#   1 1
# 5
#   0 attr
#   1 1
# 5
#   0 fp_text / fp_line / fp_text / pad
#   1 1
#....
#....
# 5
#   0 model
#   1 ${KISYS3DMOD}/Package_TO_SOT_SMD.3dshapes/SOT-23-6.wrl
#   2 offset
#     0 xyz
#     1 0
#     2 0
#     3 0
#   3 scale
#     0 xyz
#     1 1
#     2 1
#     3 1
#   4 rotate
#     0 xyz
#     1 0
#     2 0
#     3 0


pxToMM = 96 / 25.4

class Module(object):

    def __init__(self):
        self.symbol = ''
        self.version = ''
        self.generator = ''
        self.locked = False
        self.placed = False
        self.layer = ''
        self.tedit = ''
        self.tstamp = ''
        self.at = []
        self.descr = ''
        self.tags = ''
        self.property = []
        self.path = ''
        self.autoplace_cost90 = ''
        self.autoplace_cost180 = ''
        self.solder_mask_margin = ''
        self.solder_paste_margin = ''
        self.solder_paste_ratio = ''
        self.clearance = ''
        self.zone_connect = ''
        self.thermal_width = ''
        self.thermal_gap = ''
        self.attr = ''
        self.fp_text = []
        self.fp_arc = []
        self.fp_circle = []
        self.fp_curve = []
        self.fp_rect = []
        self.fp_line = []
        self.fp_poly = []
        self.pad = []
        self.model = ''
        self.zone = []
        self.group = ''
        
        
    def From_PCB(self, pcblist):

        # Why is this necessary?
        if sys.version_info[0] != 3:
            if type(pcblist[1]) == unicode:
                pcblist[1] = str(pcblist[1])
            
        if type(pcblist[1]) != str:
            assert False,"Module: Unexpected symbol type {}: {}".format(type(pcblist[1]), pcblist[1])
            return None

        self.symbol = pcblist[1]

        for item in pcblist[2:]:


            if item[0] == 'version':
                self.version = item[1]
                
            if item[0] == 'generator':
                self.generator = item[1]
                
            if item[0] == 'locked':
                self.locked = True
                
            if item[0] == 'placed':
                self.placed = True
                
            if item[0] == 'layer':
                self.layer = item[1]
                
            if item[0] == 'tedit':
                self.tedit = item[1]
                
            if item[0] == 'tstamp':
                self.tstamp = item[1]
            
            if item[0] == 'at':
                self.at += [float(item[1]),float(item[2])]
                
            if item[0] == 'descr':
                self.descr = item[1]
                
            if item[0] == 'tags':
                self.tags = item[1]
                
            if item[0] == 'property':
                self.property.append(item[1:])
                
            if item[0] == 'path':
                self.path = item[1]
                
            if item[0] == 'autoplace_cost90':
                self.autoplace_cost90 = item[1]
                
            if item[0] == 'autoplace_cost180':
                self.autoplace_cost180 = item[1]
                
            if item[0] == 'solder_mask_margin':
                self.solder_mask_margin = item[1]
                
            if item[0] == 'solder_paste_margin':
                self.solder_paste_margin = item[1]
                
            if item[0] == 'solder_paste_ratio':
                self.solder_paste_ratio = item[1]
                
            if item[0] == 'clearance':
                self.clearance = item[1]
                
            if item[0] == 'zone_connect':
                self.zone_connect = item[1]
                
            if item[0] == 'thermal_width':
                self.thermal_width = item[1]
                
            if item[0] == 'thermal_gap':
                self.thermal_gap = item[1]
                
            if item[0] == 'attr':
                self.attr = ','.join(item[1:])
                
            if item[0] == 'fp_text':
                continue
                text = Text()
                text.From_PCB(item)
                self.fp_text.append(text)
                
            if item[0] == 'fp_arc':
                continue
                arc = Arc()
                arc.From_PCB(item)
                self.fp_arc.append(arc)
                
            if item[0] == 'fp_circle':
                continue
                circle = Circle()
                circle.From_PCB(item)
                self.fp_circle.append(circle)
                
            # if item[0] == 'fp_circle':
            # if item[0] == 'fp_curve':
            # if item[0] == 'fp_rect':
                
            if item[0] == 'fp_line':
                line = Line()
                line.From_PCB(item)
                self.fp_line.append(line)
                
            if item[0] == 'fp_poly':
                continue
                poly = Poly()
                poly.From_PCB(item)
                self.fp_poly.append(poly)
            
            if item[0] == 'pad':
                pad = Pad()
                pad.From_PCB(item)
                self.pad.append(pad)

            if item[0] == 'model':
                model = item[1] + ';'
                #offset
                model += item[2][1][1] + ',' + item[2][1][2] + ',' + item[2][1][3] + ';'
                #scale
                model += item[3][1][1] + ',' + item[3][1][2] + ',' + item[3][1][3] + ';'
                #rotate
                model += item[4][1][1] + ',' + item[4][1][2] + ',' + item[4][1][3] + ';'
                self.model = model

            # if item[0] == 'zone':
            # if item[0] == 'group':
