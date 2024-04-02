
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
SPRING_CONSTANT = 20000
SPRING_DAMPING = 0.3
BODY_ELASTICITY = 0.1
BODY_FRICTION = 0.2
BODY_MASS_COEFFICIENT = 1


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
    def __init__(self, fp):
        self.shapes = []
        self.fp = fp
        self.name = fp.GetReference()
        print(self.name)
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
        # print(gi)
        for obj in gi:
            if obj.GetLayerName() == "F.Courtyard":
                line = obj.GetConnectionPoints()
                self.centre = kicad_to_mm(obj.GetCenter())
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
                print("rect")
                xy = kicad_to_mm(pad.GetBoundingBox().GetSize())
                print(centre, xy)
            elif shape == pcbnew.SHAPE_T_POLY:
                print("poly")
            elif shape == pcbnew.SHAPE_T_CIRCLE:
                print("circ")
            elif shape == pcbnew.SHAPE_T_ARC:
                print("arc")
            elif shape == pcbnew.SHAPE_T_SEGMENT:
                print("segment")
            elif shape == pcbnew.SHAPE_T_BEZIER:
                print("unhandled bezier pad")
            else:
                print("unknown shape ", shape)
            self.pads.append([i, net, centre, xy])
       
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
        
def add_footprints(space, pcb):
    primitives = []
    bodies = []
    shapes = []
    footprints = pcb.GetFootprints()
    for fp in footprints:
        footprint = Footprint(fp)
        # print(footprint.points)
        if len(footprint.shapes) > 0:

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
            
            bodies.append(body)
            shapes.append(a)
                
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
    # draw_options.flags = (
        # draw_options.flags ^ pymunk.pygame_util.DrawOptions.DRAW_CONSTRAINTS
    # )
    draw_options.transform = pymunk.Transform.scaling(5) @ pymunk.Transform.translation(-50,-20)
    static_lines, pcb_rect = build_edge_cuts(space, pcb)
    space.add(*static_lines)
    
    
    fp, bodies = add_footprints(space, pcb)
    space.add(*bodies, *fp)
    
    
    c = pymunk.DampedSpring(bodies[0], bodies[15], (1, 0), (-1, 0), 0, SPRING_CONSTANT, SPRING_DAMPING)
    space.add(c)

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