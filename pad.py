from colour import Colour

# https://github.com/KiCad/kicad-source-mirror/blob/93466fa1653191104c5e13231dfdc1640b272777/pcbnew/plugins/kicad/pcb_parser.cpp#L3530
# 0 pad
# 1 1/2/3
# 2 smd
# 3 rect
# 4
#   0 at
#   1 66.66
#   2 99.99
#   2 180
# 5
#   0 size
#   1 0.9
#   2 1.2
# 6
#   0 layers
#   1 F.Cu
#   2 F.Paste
#   3 F.Mask
# 7
#   0 net
#   1 16
#   2 Net-(D4-Pad1)
# 8
#   0 pinfunction
#   1 "A"
# 9
#   0 pintype
#   1 "passive"
       

pxToMM = 96 / 25.4 
        
class Pad(object):

    def __init__(self):
        self.name = ''
        #thru_hole, smd, connect, or np_thru_hole
        self.attribute = ''
        self.shape = ''
        self.size = []
        self.at = []
        self.rect_delta = []
        self.drill = []
        self.layers = []
        self.net = []
        self.pinfunction = ''
        self.pintype = ''
        self.die_length = ''
        self.solder_mask_margin = ''
        self.solder_paste_margin = ''
        self.solder_paste_margin_ratio = ''
        self.clearance = ''
        self.zone_connect = ''
        self.thermal_width = ''
        self.thermal_gap = ''
        self.roundrect_rratio = ''
        self.chamfer_ratio = ''
        self.chamfer = ''
        self.property = ''
        self.options = ''
        self.primitives = ''
        self.remove_unused_layers = ''
        self.keep_end_layers = ''
        self.tstamp = ''
        
    def From_PCB(self, input):

        at = []
        size = []
        layers = []
        roundrect_rratio = ''
        net = ''
        rotate = ''

        if input[0] != 'pad':
            assert False,"Pad: Not a pad"
            return None

        self.name = input[1]

        self.attribute = input[2]

        self.shape = input[3]

        for item in input[4:]:
            if item[0] == 'size':
                self.size = item[1:]
                
            if item[0] == 'at':
                for at in item[1:]:
                    self.at.append(float(at))
                    
            #Todo: proper handling for many of these
            if item[0] == 'rect_delta':
                self.rect_delta = item[1]
            if item[0] == 'drill':
                self.drill = item[1] 
            if item[0] == 'layers':
                for layer in item[1:]:
                    self.layers.append(layer)
            if item[0] == 'net':
                self.net = item[1:] 
            if item[0] == 'pinfunction':
                self.pinfunction = item[1] 
            if item[0] == 'pintype':
                self.pintype = item[1] 
            if item[0] == 'die_length':
                self.die_length = item[1] 
            if item[0] == 'solder_mask_margin':
                self.solder_mask_margin = item[1] 
            if item[0] == 'solder_paste_margin':
                self.solder_paste_margin = item[1] 
            if item[0] == 'solder_paste_margin_ratio':
                self.solder_paste_margin_ratio = item[1] 
            if item[0] == 'clearance':
                self.clearance = item[1] 
            if item[0] == 'zone_connect':
                self.zone_connect = item[1] 
            if item[0] == 'thermal_width':
                self.thermal_width = item[1] 
            if item[0] == 'thermal_gap':
                self.thermal_gap = item[1] 
            if item[0] == 'roundrect_rratio':
                self.roundrect_rratio = item[1] 
            if item[0] == 'chamfer_ratio':
                self.chamfer_ratio = item[1] 
            if item[0] == 'chamfer':
                self.chamfer = item[1] 
            if item[0] == 'property':
                self.property = item[1] 
            if item[0] == 'options':
                self.options = item[1] 
            if item[0] == 'primitives':
                self.primitives = item[1] 
            if item[0] == 'remove_unused_layers':
                self.remove_unused_layers = item[1] 
            if item[0] == 'keep_end_layers':
                self.keep_end_layers = item[1] 
            if item[0] == 'tstamp':
                self.tstamp = item[1] 
