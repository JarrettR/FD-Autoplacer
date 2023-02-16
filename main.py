import tkinter as tk

from pcbparse import Board

def move():
    c.move(circle, 5, 5)
    coordinates = c.coords(circle)
    
    window.after(33, move)

def reset():
    print("Reset")
    
class Footprint:
    def __init__(self, w, c):
        self.w = w
        self.c = c
        self.coord_initial = [0,0]
        self.coord = [0,0]
        self.shapes = []
        self.anchors = []
        self.zoom = 2
        
    def Load(self, mod):
        self.coord_initial = mod.at
        
        points = {}
        polypoints = []
        for line in mod.fp_line:
            if line.layer == 'F.CrtYd':
                if len(polypoints) == 0:
                    polypoints.append(line.start)
                    
                key = "{},{}".format(line.start[0],line.start[1])
                if "{},{}".format(line.start[0],line.start[1]) in points.keys():
                    key = "{},{}".format(line.end[0],line.end[1])
                    line.end = line.start
                points[key] = line.end
            
        for i in range(len(points)):
            key = "{},{}".format(polypoints[i][0],polypoints[i][1])
            polypoints.append(points[key])
            
        for i in range(len(polypoints)):
            polypoints[i] = [(polypoints[i][0] + self.coord_initial[0]) * self.zoom,(polypoints[i][1] + self.coord_initial[1]) * self.zoom]

        self.shapes.append(self.c.create_polygon(*polypoints, fill='red'))
        # self.Move(self.coord_initial)
        
    def Create(self):
        z = self.zoom
        centre = [self.coord_initial[0] * z, self.coord_initial[0] * z]
        
        body = c.create_rectangle(50 * z,50 * z,10 * z,10.3 * z)
        pad1 = c.create_rectangle(55 * z,54.5 * z,0.38 * z,1.7 * z)
        # circle = c.create_oval(60,60,210,210)
        
    def Move(self, coord):
        for shape in self.shapes:
            self.c.move(shape, coord[0], [1])
        # self.coord = c.coords(circle)


if __name__ == '__main__':
    window = tk.Tk()

    # window.geometry("600x400")


    optFrame = tk.Frame(master=window, height=50,relief=tk.RAISED,borderwidth=1)
    optFrame.pack(fill=tk.X, side=tk.BOTTOM)
    netFrame = tk.Frame(master=window, width=250,relief=tk.SUNKEN,borderwidth=1)
    netFrame.pack(fill=tk.Y, side=tk.RIGHT)
    c = tk.Canvas(window, height=600,width=600)
    c.pack(fill=tk.Y, side=tk.LEFT)


    optFrame.rowconfigure(0, minsize=50, weight=1)

    optFrame.columnconfigure([0, 1, 2], minsize=50, weight=1)

    label = tk.Label(text="Name", master=optFrame)
    label.grid(row=0, column=0, sticky="nsew")
    entry = tk.Entry(master=optFrame)
    entry.grid(row=0, column=1)

    button = tk.Button(text="Reset", master=optFrame, command=reset)
    button.grid(row=0, column=2, sticky="nsew")

    circle = c.create_oval(60,60,210,210)
    pcb = Board()
    pcb.Load()

    #net #, name, count, checked
    for i, net in enumerate(pcb.net):
        if net[2] > 1:
            pcb.net[i].append(tk.IntVar(value=1))
            netlabel = tk.Checkbutton(text=net[1], master=netFrame, justify=tk.LEFT, variable=pcb.net[i][3])
            netlabel.pack(fill=tk.X, side=tk.TOP)
    
    footprints = []
    
    for i, mod in enumerate(pcb.module):
        fp = Footprint(window,c)
        fp.Load(mod)
        footprints.append(fp)
    
    for fp in footprints:
        fp.Create()
    move()

    window.mainloop()