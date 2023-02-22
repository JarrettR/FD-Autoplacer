import tkinter as tk
import math

from pcbparse import Board


SPRING_CONSTANT = 0.0005
DAMPING = 0.9
    
class Nets:
    def __init__(self, w, c):
        self.w = w
        self.c = c
        self.nets = []
        self.netnames = {}
        self.lines = []
    
    def Load(self, nets):
        #net #, name, count, checked
        activenets = 0
        for i, net in enumerate(nets):
            if net[2] > 1:
                nets[i].append(tk.IntVar(value=1))
                self.nets.append(nets[i])
                self.netnames[nets[i][1]] = []
                netlabel = tk.Checkbutton(text=net[1], master=netFrame, justify=tk.LEFT, variable=self.nets[activenets][3])
                netlabel.pack(fill=tk.X, side=tk.TOP)
                activenets += 1
    
    def calc_electron(self, pos1, pos2):
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance == 0:
            return [0, 0]
        force = SPRING_CONSTANT * distance
        return [force * dx / distance, force * dy / distance]
    
    def calc_spring(self, pos1, pos2):
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance == 0:
            return [0, 0]
        force = SPRING_CONSTANT * distance
        return [force * dx / distance, force * dy / distance]
    
    def Calc(self, footprints):
        for i1, fp1 in enumerate(footprints):
            for i2, fp2 in enumerate(footprints):
                if i1 != i2:
                    force = self.calc_electron(fp1.coord, fp2.coord) 
                    footprints[i1].momentum[0] -= force[0]
                    footprints[i1].momentum[1] -= force[1]
                    
        for net in self.netnames:
            # print(net)
            for i, conn in enumerate(self.netnames[net]):
                for e, conn in enumerate(self.netnames[net]):
                    if i != e:
                        pos1 = self.netnames[net][i]
                        xy1 = footprints[pos1[0]].anchors[pos1[1]]
                        pos2 = self.netnames[net][e]
                        xy2 = footprints[pos2[0]].anchors[pos2[1]]
                        
                        force = self.calc_spring(xy1, xy2) 
                        footprints[pos1[0]].momentum[0] += force[0]
                        footprints[pos1[0]].momentum[1] += force[1]
                        
        for i, fp in enumerate(footprints): 
            footprints[i].momentum[0] *= DAMPING
            footprints[i].momentum[1] *= DAMPING
            footprints[i].momentum[2] *= DAMPING
            
    
    def Draw(self, footprints):
        for line in self.lines:
            self.c.delete(line)
        for net in self.netnames:
            # print(net)
            for i, conn in enumerate(self.netnames[net]):
                for e in range(i):
                    pos1 = self.netnames[net][i]
                    xy1 = footprints[pos1[0]].anchors[pos1[1]]
                    z1 = footprints[pos1[0]].zoom
                    pos2 = self.netnames[net][e]
                    xy2 = footprints[pos2[0]].anchors[pos2[1]]
                    z2 = footprints[pos2[0]].zoom
                    self.lines.append(self.c.create_line(xy1[0] * z1,xy1[1] * z1,xy2[0] * z2,xy2[1] * z2))
                
        
    def Associate(self, footprints):
        for i_f, fp in enumerate(footprints):
            for i_p, pad in enumerate(fp.nets):
                if pad[1] in self.netnames:
                    self.netnames[pad[1]].append([i_f, i_p])
                    # print(pad, i_f, i_p)
        # print(self.netnames)
        self.Draw(footprints)
        
class Footprint:
    def __init__(self, w, c):
        self.w = w
        self.c = c
        self.coord_initial = [0,0,0]
        self.coord = [0,0,0]
        self.shapes = []
        self.shape_coords = []
        self.shape_fills = []
        self.anchors = []
        self.nets = []
        self.zoom = 5
        self.force = 1
        self.momentum = [0,0,1]
        
    def Load(self, mod):
        self.coord_initial = mod.at
        if len(self.coord_initial) == 2:
            self.coord_initial.append(0)
        
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
            
        for i in range(len(polypoints)):
            # polypoints[i] = [(polypoints[i][0] + self.coord_initial[0]) * self.zoom,(polypoints[i][1] + self.coord_initial[1]) * self.zoom]
            polypoints[i] = [polypoints[i][0] * self.zoom,polypoints[i][1] * self.zoom]

        self.shapes.append(self.c.create_polygon(*polypoints, fill='red'))
        self.shape_coords.append(polypoints)
        self.shape_fills.append('red')
        
        #pads
        for pad in mod.pad:
            polypoints = []
            polypoints.append([(pad.at[0] - (pad.size[0] / 2.0)) * self.zoom, (pad.at[1] - (pad.size[1] / 2.0)) * self.zoom])
            polypoints.append([(pad.at[0] + (pad.size[0] / 2.0)) * self.zoom, (pad.at[1] - (pad.size[1] / 2.0)) * self.zoom])
            polypoints.append([(pad.at[0] + (pad.size[0] / 2.0)) * self.zoom, (pad.at[1] + (pad.size[1] / 2.0)) * self.zoom])
            polypoints.append([(pad.at[0] - (pad.size[0] / 2.0)) * self.zoom, (pad.at[1] + (pad.size[1] / 2.0)) * self.zoom])
            # Flatten for internal representation
            # flat_list = [item for sublist in polypoints for item in sublist]
            # self.shape_coords.append(flat_list)
            self.shape_coords.append(polypoints)
            self.shapes.append(self.c.create_polygon(*polypoints, fill='grey'))
            self.shape_fills.append('grey')
            self.nets.append(pad.net)
            # self.anchors.append([(pad.at[0] + self.coord_initial[0]) * 1, (pad.at[1] + self.coord_initial[1]) * 1])
            self.anchors.append([pad.at[0], pad.at[1]])
            
        self.Move(self.coord_initial)
        
    def Create(self):
        z = self.zoom
        centre = [self.coord_initial[0] * z, self.coord_initial[0] * z]
        
        body = c.create_rectangle(50 * z,50 * z,10 * z,10.3 * z)
        pad1 = c.create_rectangle(55 * z,54.5 * z,0.38 * z,1.7 * z)
        # circle = c.create_oval(60,60,210,210)
        
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
            new_points.append(x_new + cx)
            new_points.append(y_new + cy)
        return new_points
        
    def Move(self, coord = False):
        if coord is False:
            coord = self.momentum
        new_shapes = []
        new_fills = []
        for shape in self.shape_coords:
            # coords = self.c.coords(shape)
            flat_shape = shape
            pts = []
            #Flatten for internal representation
            if isinstance(shape[0], list):
                flat_shape = [item for sublist in shape for item in sublist]
                
            i = 0
            while i < len(flat_shape):
                pts.append([flat_shape[i] + (coord[0] * self.zoom), flat_shape[i+1] + (coord[1] * self.zoom)])
                i += 2
            # print(pts)
            pts = self.rotate(pts, self.momentum[2], self.coord[0:2])
            new_fills.append(self.c.itemcget(shape, "fill"))
            self.c.delete(shape)
            new_shapes.append(pts)
            # self.c.move(shape, coord[0] * self.zoom, coord[1] * self.zoom)
        # self.coord = self.c.coords(self.shapes[0])
        self.shapes = []
        self.shape_coords = new_shapes
        for i in range(len(new_shapes)):
            self.shapes.append(self.c.create_polygon(*new_shapes[i], fill=self.shape_fills[i]))
        self.coord[0] += coord[0]
        self.coord[1] += coord[1]
        self.coord[2] += coord[2]
        # self.coord[0] = self.coord[0] / self.zoom
        # self.coord[1] = self.coord[1] / self.zoom
        for i, a in enumerate(self.anchors): #Todo calc rotation
            self.anchors[i][0] += coord[0]
            self.anchors[i][1] += coord[1]
            
    def Reset(self):
        diff = [0,0]
        # print(self.coord)
        diff[0] = -1 * (self.coord[0] - self.coord_initial[0])
        diff[1] = -1 * (self.coord[1] - self.coord_initial[1])
        for shape in self.shapes:
            self.c.move(shape, diff[0] * self.zoom, diff[1] * self.zoom)
        anchors = []
        for anchor in self.anchors:
            anchor[0] += diff[0]
            anchor[1] += diff[1]
            anchors.append(anchor)
        self.anchors = anchors
        self.coord = self.coord_initial
        self.momentum = [0,0,0]


if __name__ == '__main__':
    window = tk.Tk()

    # window.geometry("600x400")


    optFrame = tk.Frame(master=window, height=50,relief=tk.RAISED,borderwidth=1)
    optFrame.pack(fill=tk.X, side=tk.BOTTOM)
    netFrame = tk.Frame(master=window, width=250,relief=tk.SUNKEN,borderwidth=1)
    netFrame.pack(fill=tk.Y, side=tk.RIGHT)
    c = tk.Canvas(window, height=600,width=600)
    c.pack(fill=tk.Y, side=tk.LEFT)


    optFrame.rowconfigure([0, 1], minsize=25, weight=1)

    optFrame.columnconfigure([0, 1, 2, 3, 4, 5], minsize=50, weight=1)

    speed = tk.IntVar(value=1)
    label = tk.Label(text="Speed (FPS)", master=optFrame)
    label.grid(row=0, column=0, sticky="nsew")
    entry = tk.Entry(master=optFrame, text=speed)
    entry.grid(row=0, column=1)


    # circle = c.create_oval(60,60,210,210)
    pcb = Board()
    pcb.Load()

    
    net = Nets(window,c)
    net.Load(pcb.net)
    
    footprints = []
    
    for i, mod in enumerate(pcb.module):
        fp = Footprint(window,c)
        fp.Load(mod)
        footprints.append(fp)
    
    net.Associate(footprints)
    
    
    def move():
        for fp in footprints:
            fp.Move()
            net.Draw(footprints)
            
        net.Calc(footprints)
        
        window.after(330, move)
    def reset():
        for fp in footprints:
            fp.Reset()
    button = tk.Button(text="Reset", master=optFrame, command=reset)
    button.grid(row=1, column=5, sticky="nsew")
    move()

    window.mainloop()