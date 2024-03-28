
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

pymunk.pygame_util.positive_y_is_up = True

def kicad_to_mm(vec):
    #Todo: handle single variables as well
    points = []
    if type(vec) == pcbnew.VECTOR2I:
        points = [vec.x / 1000000, vec.y / 1000000]
        return points
    for k in vec:
        points.append((k[0] / 1000000, k[1] / 1000000))
        
    return points

def draw_collision(arbiter, space, data):
    for c in arbiter.contact_point_set.points:
        r = max(3, abs(c.distance * 5))
        r = int(r)

        p = pymunk.pygame_util.to_pygame(c.point_a, data["surface"])
        pygame.draw.circle(data["surface"], pygame.Color("orange"), p, r, 1)

gravityStrength = 5.0e6


def planetGravity(body, gravity, damping, dt):
    # Gravitational acceleration is proportional to the inverse square of
    # distance, and directed toward the origin. The central planet is assumed
    # to be massive enough that it affects the satellites but not vice versa.
    sq_dist = body.position.get_dist_sqrd((300, 300))
    g = (
        (body.position - pymunk.Vec2d(300, 300))
        * -gravityStrength
        / (sq_dist * math.sqrt(sq_dist))
    )
    pymunk.Body.update_velocity(body, g, damping, dt)
    
class Footprint:
    def __init__(self, pcb, fp):
        self.shapes = []
        self.fp = fp
        
        gi = fp.GraphicalItems()

        # drawings = fppcb.GetDrawings()
        points = {}
        polypoints = []
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
            
            a = pymunk.Poly(space.static_body, points)
            a.friction = 0.5
            shapes.append(a)
            
    return shapes
        
def add_footprints(space, pcb):
    primitives = []
    shapes = []
    footprints = pcb.GetFootprints()
    for fp in footprints:
        footprint = Footprint(pcb, fp)
        # print(footprint.points)
        if len(footprint.shapes) > 0:

            a = pymunk.Poly(space.static_body, footprint.shapes)
            a.friction = 0.5
            shapes.append(a)
                
    return shapes
            
    
def main(pcb):

    bb = pcb.GetBoardEdgesBoundingBox().GetSize()
    pygame.init()
    # screen = pygame.display.set_mode((bb[0] / 1000000, bb[1] / 1000000))
    screen = pygame.display.set_mode((800,800))
    clock = pygame.time.Clock()
    running = True

    space = pymunk.Space()
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    # disable the build in debug draw of collision point since we use our own code.
    draw_options.flags = (
        draw_options.flags ^ pymunk.pygame_util.DrawOptions.DRAW_COLLISION_POINTS
    )

    static_lines = build_edge_cuts(space, pcb)
    space.add(*static_lines)


    ch = space.add_collision_handler(0, 0)
    ch.data["surface"] = screen
    ch.post_solve = draw_collision
    
    fp = add_footprints(space, pcb)
    space.add(*fp)
    # return

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                pygame.image.save(screen, "contact_with_friction.png")

        # ticks_to_next_ball -= 1
        # if ticks_to_next_ball <= 0:
            # ticks_to_next_ball = 100
            # mass = 0.1
            # radius = 25
            # inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
            # body = pymunk.Body(mass, inertia)
            # x = random.randint(115, 350)
            # body.position = x, 400
            # # body.velocity_func = planetGravity
            # shape = pymunk.Circle(body, radius, (0, 0))
            # shape.friction = 0.5
            # space.add(body, shape)
            # balls.append(shape)

        ### Clear screen
        screen.fill(pygame.Color("white"))

        ### Draw stuff
        space.debug_draw(draw_options)

        # balls_to_remove = []
        # for ball in balls:
            # if ball.body.position.y < 200:
                # balls_to_remove.append(ball)
        # for ball in balls_to_remove:
            # space.remove(ball, ball.body)
            # balls.remove(ball)

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