
import math
import random
import sys

import pcbnew
import pygame

import pymunk
import pymunk.pygame_util
from pymunk import Vec2d

from pcbparse import Board

random.seed(5)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
SCREEN_ZOOM = 4
ELECTRON_CONSTANT = 20
SPRING_CONSTANT = 2000
SPRING_DAMPING = 0.1
BODY_ELASTICITY = 0.1
BODY_FRICTION = 0.2
BODY_MASS_COEFFICIENT = 1


FOOTPRINT_COLOUR = (255.0, 0.0, 0.0, 255.0)

space = pymunk.Space()

def kicad_to_mm(vec):
    #Todo: handle single variables as well
    points = []
    if type(vec) == pcbnew.VECTOR2I:
        points = [vec.x / 1000000, vec.y / 1000000]
        return points
    if isinstance(vec, int):
        return vec / 1000000
    for k in vec:
        points.append((k[0] / 1000000, k[1] / 1000000))
        
    return points



def calc_physics(body, gravity, damping, dt):
    bodies = space.bodies
    # print(body.name)
    # distance = b.position
    d = [0, 0]
    for b in bodies:
        diff = b.position - body.position
        # print(diff)
        d += diff
    distance =  math.sqrt(d[0] ** 2 + d[1] ** 2)
    if distance != 0:
        force = ELECTRON_CONSTANT * -1.0
        g = [force * d[0] / (distance ** 2), force * d[1] / (distance ** 2)]
    else:
        g = 0
    # sq_dist = body.position.get_dist_sqrd(distance)
    # g = (force / sq_dist, force / sq_dist)
    # print(distance, sq_dist, g)
    
    pymunk.Body.update_velocity(body, g, damping, dt)
    
class Footprint:
    def __init__(self, fp, nets):
        self.shapes = []
        self.fp = fp
        self.name = fp.GetReference()
        # print(self.name)
        self.nets = nets
        self.centre = [0,0]
        self.pads = []
        # self.bb = kicad_to_mm(fp.GetBoundingBox())
        self.mass = kicad_to_mm(fp.GetBoundingBox().GetArea()) * BODY_MASS_COEFFICIENT
        self.gen_footprints()
        self.get_pads()

    def gen_footprints(self):
        gi = self.fp.GraphicalItems()
        # drawings = fppcb.GetDrawings()
        points = {}
        polypoints = []
        self.centre = kicad_to_mm(self.fp.GetCenter())
        # print(gi)
        for obj in gi:
            if obj.GetLayerName() == "F.Courtyard":
                line = obj.GetConnectionPoints()
                if len(line) == 0: 
                    continue
                line_start = kicad_to_mm(line[0])
                line_end = kicad_to_mm(line[1])
                # print(obj.GetParentAsString(), line_start, line_end)
                if len(polypoints) == 0:
                    polypoints.append(line_start)
                    
                #Conversion of mixed up start/end points to a polygon, by way of dictionary entries
                key = "{},{}".format(line_start[0],line_start[1])
                # print(key)
                if key in points.keys():
                    key = "{},{}".format(line_end[0],line_end[1])
                    # print("Alt: ", key)
                    if key in points.keys():
                        # print("Extra alt")
                        # print(points)
                        temp = points[key]
                        points[key] = line_start
                        key = "{},{}".format(temp[0],temp[1])
                        # print(key)
                        if key in points.keys(): # With enough nesting, you have recursion*
                            temp = points[key]
                            points[key] = line_start
                            key = "{},{}".format(temp[0],temp[1])
                        points[key] = line_end
                        # print(points)
                    else:
                        line_end = line_start
                points[key] = line_end
            
        # print(points)
        for i in range(len(points)):
            key = "{},{}".format(polypoints[i][0],polypoints[i][1])
            polypoints.append(points[key])
            
        self.shapes = polypoints
       
    def get_pads(self):
        pads = self.fp.Pads()
        
        i = 0
        for pad in pads:
            net = pad.GetNetname()
            shape = pad.GetShape()
            centre = kicad_to_mm(pad.GetCenter())
            centre[0] = self.centre[0] - centre[0]
            centre[1] = self.centre[1] - centre[1]
            xy = [0,0]
            if shape == pcbnew.SHAPE_T_RECT:
                # print("rect")
                xy = kicad_to_mm(pad.GetBoundingBox().GetSize())
                # print(centre, xy)
            elif shape == pcbnew.SHAPE_T_POLY:
                # print("poly")
                xy = kicad_to_mm(pad.GetBoundingBox().GetSize())
            elif shape == pcbnew.SHAPE_T_CIRCLE:
                # print("circ")
                xy = kicad_to_mm(pad.GetBoundingBox().GetSize())
            elif shape == pcbnew.SHAPE_T_ARC:
                # print("arc")
                xy = kicad_to_mm(pad.GetBoundingBox().GetSize())
            elif shape == pcbnew.SHAPE_T_SEGMENT:
                # print("segment")
                xy = kicad_to_mm(pad.GetBoundingBox().GetSize())
            elif shape == pcbnew.SHAPE_T_BEZIER:
                print("unhandled bezier pad")
            else:
                print("unknown shape ", shape)
            self.pads.append([i, net, centre, xy])
            if net in self.nets.keys():
                self.nets[net].append([self.name, i])
            else:
                self.nets[net] = [[self.name, i]]
            i += 1
            
       
    def get_net_connections(self, target):
        # print(self.nets)
        # print(footprints.keys())
        targetNets = []
        for net in self.nets:
            # print(net, self.nets[net])
            for c in self.nets[net]:
                # print(c)
                if c[0] == self.name:
                    # print(target, c[0])
                    for e in self.nets[net]:
                        if e[0] == target:
                            targetNets.append([c[1], e])
                            # print("target", e[0])
        return targetNets
       
def build_edge_cuts(space, pcb):
    primitives = []
    shapes = []
    drawings = pcb.GetDrawings()
    for drawing in drawings:
        if drawing.GetLayerName() == "Edge.Cuts":
            primitives.append(drawing)
            
    for primitive in primitives:
        if primitive.GetShapeStr() == "Rect": #Todo: add more types
            points = kicad_to_mm(primitive.GetCorners())
            centre = kicad_to_mm(pcb.GetBoardEdgesBoundingBox().Centre())
            
            # a = pymunk.Poly(space.static_body, points)
            i = 0
            while i < 4:
                a = pymunk.Segment(space.static_body, points[i], points[(i + 1) % 4], 0.2)
                a.friction = 0.5
                shapes.append(a)
                i += 1
            
    return shapes, centre
        
def connect(space, footprints, sourceFp, targets):
    for conn in targets:
        sourcePin = conn[0]
        destFp = conn[1][0]
        destPin = conn[1][1]
        # print(sourcePin, destFp, destPin)
        body1 = footprints[sourceFp].body
        body2 = footprints[destFp].body
        xy1 = footprints[sourceFp].pads[sourcePin][2]
        xy2 = footprints[destFp].pads[destPin][2]
        # print(sourceFp, xy1, destFp, xy2)
        c = pymunk.DampedSpring(body1, body2, xy1, xy2, 0, SPRING_CONSTANT, SPRING_DAMPING)
        space.add(c)
    

def add_footprints(space, pcb):
    primitives = []
    bodies = []
    shapes = []
    nets = {}
    footprints = {}
    pcbFootprints = pcb.GetFootprints()
    for fp in pcbFootprints:
        footprint = Footprint(fp, nets)
        # print(footprint.points)
        if len(footprint.shapes) > 0:
            footprints[footprint.name] = footprint

            inertia = pymunk.moment_for_poly(footprint.mass, footprint.shapes, (footprint.centre[0], footprint.centre[1]))
            body = pymunk.Body(footprint.mass, inertia / 1000000)
            body.name = footprint.name
            body.velocity_func = calc_physics

            a = pymunk.Poly(body, footprint.shapes, radius=0.01)
            
            body.position = a.center_of_gravity[0], a.center_of_gravity[1]
            t = pymunk.Transform(tx=a.center_of_gravity[0] / -1, ty=a.center_of_gravity[1] / -1)
            a = pymunk.Poly(body, footprint.shapes, transform=t, radius=0.01)
            a.friction = BODY_FRICTION
            a.elasticty = BODY_ELASTICITY
            a.color = FOOTPRINT_COLOUR
            # a2 = pymunk.Circle(body, 1.0, (1, 1))
            # a2.color = (0, 255, 0, 255)
            
            bodies.append(body)
            shapes.append(a)
            # shapes.append(a2)
            footprint.body = body
            footprint.shape = a
            
            
    space.add(*bodies, *shapes)
    
    completedF1 = []
    for f1 in footprints:
        completedF1.append(f1)
        for f2 in footprints:
            if f2 not in completedF1:
                targets = footprints[f1].get_net_connections(f2)
                if len(targets) > 0:
                    # print(f1, targets)
                    connect(space, footprints, f1, targets)
        
    return shapes, bodies
            
    
def main(pcb):

    # bb = pcb.GetBoardEdgesBoundingBox().GetSize()
    pygame.init()
    # screen = pygame.display.set_mode((bb[0] / 1000000, bb[1] / 1000000))
    screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    running = True

    # space.gravity = (0.0, 900.0)
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    # Don't draw the spring constraint
    draw_options.flags = (
        draw_options.flags ^ pymunk.pygame_util.DrawOptions.DRAW_CONSTRAINTS
    )
    draw_options.transform = pymunk.Transform.scaling(5) @ pymunk.Transform.translation(-50,-20)
    static_lines, pcb_rect = build_edge_cuts(space, pcb)
    space.add(*static_lines)
    
    
    fp, bodies = add_footprints(space, pcb)
    
    # pygame.draw.circle(screen, (0,0,255,255), (20,300), 20)
    

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        

        ### Clear screen
        screen.fill(pygame.Color("white"))

        ### Draw stuff
        space.debug_draw(draw_options)
        
        
  

        ### Update physics
        dt = 1.0 / 60.0
        for x in range(1):
            space.step(dt)

        ### Flip screen
        pygame.display.flip()
        clock.tick(50)
        pygame.display.set_caption("fps: " + str(clock.get_fps()))


if __name__ == "__main__":
    pcb = pcbnew.LoadBoard("tests\\v3.kicad_pcb")
    # print(pcb.GetFootprints())
    
    sys.exit(main(pcb))