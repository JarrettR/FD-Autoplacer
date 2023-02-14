import tkinter as tk

def move():
    c.move(circle, 5, 5)
    coordinates = c.coords(circle)
    
    window.after(33, move)

def reset():
    print("Reset")
    
class Module:
    def __init__(self, w, c):
        self.w = w
        self.c = c
        self.coord = [0,0]
        self.shapes = []
        self.zoom = 5
        self.create()
        
    def create(self):
        z = self.zoom
        body = c.create_rectangle(50 * z,50 * z,10 * z,10.3 * z)
        pad1 = c.create_rectangle(55 * z,54.5 * z,0.38 * z,1.7 * z)
        # circle = c.create_oval(60,60,210,210)
        
    def move(self, c, circle):
        c.move(circle, 5, 5)
        self.coord = c.coords(circle)

if __name__ == '__main__':
    window = tk.Tk()

    # window.geometry("600x400")

    c = tk.Canvas(window, height=400,width=600)
    c.pack(fill=tk.Y, side=tk.TOP)

    frame = tk.Frame(master=window, height=50,relief=tk.RAISED,borderwidth=1)
    frame.pack(fill=tk.X, side=tk.BOTTOM)

    frame.rowconfigure(0, minsize=50, weight=1)

    frame.columnconfigure([0, 1, 2], minsize=50, weight=1)

    label = tk.Label(text="Name", master=frame)
    label.grid(row=0, column=0, sticky="nsew")
    entry = tk.Entry(master=frame)
    entry.grid(row=0, column=1)

    button = tk.Button(text="Reset", master=frame, command=reset)
    button.grid(row=0, column=2, sticky="nsew")

    circle = c.create_oval(60,60,210,210)
    what = Module(window,c)
    move()

    window.mainloop()