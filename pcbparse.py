import sys, io, os

from parser_base import ParserBase

# from .arc import Arc
# from .circle import Circle
# from .curve import Curve
# from .layers import Layers
# from .line import Line
# from .metadata import Metadata
from module import Module
# from .pad import Pad
# from .poly import Poly
# from .segment import Segment
# from .text import Text
# from .via import Via
# from .zone import Zone

#https://github.com/KiCad/kicad-source-mirror/blob/93466fa1653191104c5e13231dfdc1640b272777/pcbnew/plugins/kicad/pcb_parser.cpp#L533

# kicad_pcb
# version
# host
# general
# page
# title_block
# layers
# setup
# net
# net_class
# module
# dimension
# gr_line
# gr_arc
# gr_text
# segment
# via
# zone


class Board(object):

    def __init__(self):
        self.Clear()
        currentdir = os.path.dirname(os.path.realpath(__file__))
        self.filename_default = os.path.join(currentdir, 'tests', 'complicated.kicad_pcb')
        
    def Load(self, filename = None):
        
        if filename is None:
            filename = self.filename_default

        with io.open(filename, 'r', encoding='utf-8') as f:
            self.pcb = ParserBase().parse_sexpression(f.read())
        
        self.Parse()

    def Clear(self):
        self.general = ''
        self.paper = ''
        self.title_block = ''


        # self.layers = Layers()
        # self.layers = ''
        self.setup = ''
        self.property = ''
        self.net = []
        self.net_class = ''
        self.gr_arc = []
        self.gr_curve = []
        self.gr_line = []
        self.gr_poly = []
        self.gr_circle = []
        self.gr_rect = []
        self.gr_text = []
        self.gr_dimension = []
        self.module = []
        self.footprint = []
        self.segment = []
        self.arc = []
        self.group = ''
        self.via = []
        self.zone = []
        self.target = ''
        self.metadata = []
        
        
    def Parse(self):
    
        for item in self.pcb:
            if type(item) is str:
                # print(item)
                continue
            else:
            
                if item[0] == 'layers':
                    continue
                    self.layers = Layers()
                    self.layers.From_PCB(item)
                    
                elif item[0] == 'footprint':
                    # This is the new name of modules
                    # KiCad 6 supports "module" as a legacy option
                    # So that's what we will use.
                    module = Module()
                    module.From_PCB(item)
                    self.module.append(module)

                elif item[0] == 'segment':
                    continue
                    segment = Segment()
                    segment.From_PCB(item)
                    self.segment.append(segment)
                    
                elif item[0] == 'arc':
                    continue
                    arc = Arc()
                    arc.From_PCB(item)
                    self.arc.append(arc)
                    
                elif item[0] == 'gr_arc':
                    continue
                    arc = Arc()
                    arc.From_PCB(item)
                    self.gr_arc.append(arc)
                    
                elif item[0] == 'gr_line':
                    continue
                    line = Line()
                    line.From_PCB(item)
                    self.gr_line.append(line)
                    
                elif item[0] == 'gr_circle':
                    continue
                    circle = Circle()
                    circle.From_PCB(item)
                    self.gr_circle.append(circle)
                    
                elif item[0] == 'gr_poly':
                    continue
                    poly = Poly()
                    poly.From_PCB(item)
                    self.gr_poly.append(poly)
                    
                elif item[0] == 'gr_curve':
                    continue
                    curve = Curve()
                    curve.From_PCB(item)
                    self.gr_curve.append(curve)
                    
                elif item[0] == 'gr_text':
                    continue
                    text = Text()
                    text.From_PCB(item)
                    self.gr_text.append(text)
                    # tag = BeautifulSoup(self.Convert_Gr_Text_To_SVG(item, i), 'html.parser')
                    # layer = tag.find('text')['layer']
                    # base.svg.find('g', {'inkscape:label': layer}, recursive=False).append(tag)

                elif item[0] == 'zone':
                    continue
                    zone = Zone()
                    zone.From_PCB(item)
                    self.zone.append(zone)

                elif item[0] == 'via':
                    continue
                    via = Via()
                    via.From_PCB(item)
                    self.via.append(via)

                elif item[0] == 'net':
                    #net #, name, count
                    self.net.append([int(item[1]), item[2], 0])
                    
                else:
                    self.metadata.append(item)

        for i_m, m in enumerate(self.module):
            for i_p, p in enumerate(m.pad):
                if len(p.net) > 0:
                    net_num = int(p.net[0])
                    self.net[net_num][2] += 1