import tkinter as tk

def move():
    c.move(circle, 5, 5)
    coordinates = c.coords(circle)
    
    window.after(33, move)

window = tk.Tk()

# window.geometry("600x400")

c = tk.Canvas(window, height=400,width=600)
c.pack(fill=tk.Y, side=tk.TOP)

frame3 = tk.Frame(master=window, height=50, bg="blue")
frame3.pack(fill=tk.X, side=tk.BOTTOM)

circle = c.create_oval(60,60,210,210)

move()

window.mainloop()