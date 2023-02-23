import tkinter as tk
import math

from pcbparse import Board


ELECTRON_CONSTANT = 0.002
SPRING_CONSTANT = 0.0005
TORQUE_CONSTANT = 1.0
DAMPING = 0.9
    
class Viewport:
    def __init__(self):
        self.zoom = 5
        self.pan = [0,0]
        self.tk_shapes = []
        self.tk_nets = []
        self.tk_lines = []
        
        window = tk.Tk()

        optFrame = tk.Frame(master=window, height=50,relief=tk.RAISED,borderwidth=1)
        optFrame.pack(fill=tk.X, side=tk.BOTTOM)
        self.netFrame = tk.Frame(master=window, width=250,relief=tk.SUNKEN,borderwidth=1)
        self.netFrame.pack(fill=tk.Y, side=tk.RIGHT)
        c = tk.Canvas(window, height=600,width=600)
        c.pack(fill=tk.Y, side=tk.LEFT)


        optFrame.rowconfigure([0, 1], minsize=25, weight=1)

        optFrame.columnconfigure([0, 1, 2, 3, 4, 5], minsize=50, weight=1)

        speed = tk.IntVar(value=1)
        label = tk.Label(text="Speed (FPS)", master=optFrame)
        label.grid(row=0, column=0, sticky="nsew")
        entry = tk.Entry(master=optFrame, text=speed)
        entry.grid(row=0, column=1)
            
        button = tk.Button(text="Reset", master=optFrame, command=self.Reset)
        button.grid(row=1, column=5, sticky="nsew")
        
        self.w = window
        self.c = c
        
    def Load(self, nets):
        #net #, name, count, checked
        activenets = 0
        for net in enumerate(nets.netnames):
            self.tk_nets.append([net,tk.IntVar(value=1)])
            netlabel = tk.Checkbutton(text=net, master=self.netFrame, justify=tk.LEFT, variable=self.tk_nets[activenets][1])
            netlabel.pack(fill=tk.X, side=tk.TOP)
            activenets += 1
        
    def Draw(self, footprints, nets):
        self.footprints = footprints
        self.nets = nets
        z = self.zoom
        #Footprints
        for shape in self.tk_shapes:
            self.c.delete(shape)
        for fp in footprints:
            move = fp.coord_current
            i = 0
            while i < len(fp.shapes):
                poly = []
                for pts in fp.shapes[i]:
                    poly.append([(pts[0] + move[0]) * z, (pts[1] + move[1]) * z])
                self.tk_shapes.append(self.c.create_polygon(*poly, fill=fp.shape_fills[i]))
                i += 1
        
        #Nets
        for line in self.tk_lines:
            self.c.delete(line)
        for net in nets.netnames:
            # print(net)
            for i, conn in enumerate(nets.netnames[net]):
                for e in range(i):
                    pos1 = nets.netnames[net][i]
                    xy1 = footprints[pos1[0]].anchors[pos1[1]].copy()
                    xy1[0] += footprints[pos1[0]].coord_current[0]
                    xy1[1] += footprints[pos1[0]].coord_current[1]
                    pos2 = nets.netnames[net][e]
                    xy2 = footprints[pos2[0]].anchors[pos2[1]].copy()
                    xy2[0] += footprints[pos2[0]].coord_current[0]
                    xy2[1] += footprints[pos2[0]].coord_current[1]
                    self.tk_lines.append(self.c.create_line(xy1[0] * z,xy1[1] * z,xy2[0] * z,xy2[1] * z))
        
    def Animate(self):
        for fp in self.footprints:
            fp.Move()
            # nets.Draw(footprints)
            
        nets.Calc(footprints)
        
        self.Draw(self.footprints, self.nets)
        
        self.w.after(33, self.Animate)
        
    def Reset(self):
        for fp in self.footprints:
            fp.Reset()
        
    def Start(self):
        self.Animate()
        self.w.mainloop()
        
class Nets:
    def __init__(self):
        self.nets = []
        self.netnames = {}
    
    def Load(self, nets):
        #net format: net number, name, count, checked
        activenets = 0
        for i, net in enumerate(nets):
            if net[2] > 1:
                self.netnames[nets[i][1]] = []
    
    def calc_electron(self, pos1, pos2):
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance == 0:
            return [0, 0]
        force = ELECTRON_CONSTANT * distance
        return [force * dx / distance, force * dy / distance]
    
    def calc_spring(self, pos1, pos2):
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance == 0:
            return [0, 0]
        force = SPRING_CONSTANT * distance
        return [force * dx / distance, force * dy / distance]
    
    def calc_torque(self, force, xy):
        distance = math.sqrt(xy[0] ** 2 + xy[1] ** 2)
        
        torque = xy[0]*force[1] - xy[1]*force[0]
        return torque * TORQUE_CONSTANT
    
    def Calc(self, footprints):
        for i1, fp1 in enumerate(footprints):
            for i2, fp2 in enumerate(footprints):
                if i1 != i2:
                    force = self.calc_electron(fp1.coord_current, fp2.coord_current) 
                    footprints[i1].momentum[0] -= force[0]
                    footprints[i1].momentum[1] -= force[1]
                    
        for net in self.netnames:
            # print(net)
            for i, conn in enumerate(self.netnames[net]):
                for e, conn in enumerate(self.netnames[net]):
                    if i != e:
                        pos1 = self.netnames[net][i]
                        pos2 = self.netnames[net][e]
                        if pos1[0] != pos2[0]:
                            # xy1 = footprints[pos1[0]].anchors[pos1[1]] + footprints[pos1[0]].coor
                            xy1 = [sum(x) for x in zip(footprints[pos1[0]].anchors[pos1[1]], footprints[pos1[0]].coord_current)]
                            xy2 = [sum(x) for x in zip(footprints[pos2[0]].anchors[pos2[1]], footprints[pos2[0]].coord_current)]
                            # xy2 = footprints[pos2[0]].anchors[pos2[1]]
                            
                            force = self.calc_spring(xy1, xy2)
                            torque = self.calc_torque(force, footprints[pos1[0]].anchors[pos1[1]])
                            footprints[pos1[0]].momentum[0] += force[0]
                            footprints[pos1[0]].momentum[1] += force[1]
                            footprints[pos1[0]].momentum[2] += torque
                        
        for i, fp in enumerate(footprints): 
            footprints[i].momentum[0] *= DAMPING
            footprints[i].momentum[1] *= DAMPING
            footprints[i].momentum[2] *= DAMPING
            
    def Associate(self, footprints):
        for i_f, fp in enumerate(footprints):
            for i_p, pad in enumerate(fp.nets):
                if pad[1] in self.netnames:
                    self.netnames[pad[1]].append([i_f, i_p])
                    # print(pad, i_f, i_p)
        # print(self.netnames)
        # self.Draw(footprints)
        
class Footprint:
    def __init__(self, mod = False):
        self.coord_initial = [0,0,0]
        self.coord_current = [0,0,0]
        self.shapes_initial = []
        self.shapes = []
        self.shape_fills = []
        self.anchors_initial = []
        self.anchors = []
        self.nets = []
        self.force = 1
        self.momentum = [0,0,0]
        
        if mod != False:
            self.Load(mod)
        
    def Load(self, mod):
        self.coord_initial = mod.at
        if len(self.coord_initial) == 2:
            self.coord_initial.append(0)
        
        self.coord_current = self.coord_initial
        #courtyard
        points = {}
        polypoints = []
        for line in mod.fp_line:
            if line.layer == 'F.CrtYd':
                if len(polypoints) == 0:
                    polypoints.append(line.start)
                    
                #Conversion of mixed up start/end points to a polygon, by way of dictionary entries
                key = "{},{}".format(line.start[0],line.start[1])
                if "{},{}".format(line.start[0],line.start[1]) in points.keys():
                    key = "{},{}".format(line.end[0],line.end[1])
                    line.end = line.start
                points[key] = line.end
            
        for i in range(len(points)):
            key = "{},{}".format(polypoints[i][0],polypoints[i][1])
            polypoints.append(points[key])
            
        self.shapes_initial.append(polypoints)
        self.shapes.append(polypoints)
        self.shape_fills.append('red')
        
        #pads
        for pad in mod.pad:
            polypoints = []
            polypoints.append([(pad.at[0] - (pad.size[0] / 2.0)), (pad.at[1] - (pad.size[1] / 2.0))])
            polypoints.append([(pad.at[0] + (pad.size[0] / 2.0)), (pad.at[1] - (pad.size[1] / 2.0))])
            polypoints.append([(pad.at[0] + (pad.size[0] / 2.0)), (pad.at[1] + (pad.size[1] / 2.0))])
            polypoints.append([(pad.at[0] - (pad.size[0] / 2.0)), (pad.at[1] + (pad.size[1] / 2.0))])
            self.shapes.append(polypoints)
            self.shapes_initial.append(polypoints)
            self.shape_fills.append('grey')
            self.nets.append(pad.net)
            # self.anchors.append([(pad.at[0] + self.coord_initial[0]) * 1, (pad.at[1] + self.coord_initial[1]) * 1])
            self.anchors.append([pad.at[0], pad.at[1]])
            self.anchors_initial.append([pad.at[0], pad.at[1]])
            
        # self.Move(self.coord_initial)
        
    def rotate(self, points, angle, center):
        angle = math.radians(angle)
        cos_val = math.cos(angle)
        sin_val = math.sin(angle)
        cx, cy = center
        new_points = []
        for x_old, y_old in points:
            x_old -= cx
            y_old -= cy
            x_new = x_old * cos_val - y_old * sin_val
            y_new = x_old * sin_val + y_old * cos_val
            new_points.append([x_new + cx, y_new + cy])
        return new_points
        
    def Move(self, move = False):
        if move is False:
            move = self.momentum
        new_shapes = []
        for shape in self.shapes:
            pts = self.rotate(shape, self.momentum[2], [0,0]) # self.coord_current[0:2])
            new_shapes.append(pts)
        self.shapes = new_shapes
        self.coord_current[0] += move[0]
        self.coord_current[1] += move[1]
        self.coord_current[2] += move[2]
        self.anchors = self.rotate(self.anchors, self.momentum[2], [0,0])
            
    def Reset(self):
        # diff = [0,0]
        # # print(self.coord)
        # diff[0] = -1 * (self.coord[0] - self.coord_initial[0])
        # diff[1] = -1 * (self.coord[1] - self.coord_initial[1])
        # for shape in self.shapes:
            # self.c.move(shape, diff[0] * self.zoom, diff[1] * self.zoom)
        # anchors = []
        # for anchor in self.anchors:
            # anchor[0] += diff[0]
            # anchor[1] += diff[1]
            # anchors.append(anchor)
        self.anchors = self.anchors_initial
        self.coord_current = self.coord_initial
        self.shapes = self.shapes_initial
        self.momentum = [0,0,0]


if __name__ == '__main__':

    vp = Viewport()

    pcb = Board()
    pcb.Load()

    nets = Nets()
    nets.Load(pcb.net)
    
    footprints = []
    
    for i, mod in enumerate(pcb.module):
        fp = Footprint(mod)
        footprints.append(fp)
    
    nets.Associate(footprints)
    
    vp.Load(nets)
    vp.Draw(footprints, nets)


    vp.Start()