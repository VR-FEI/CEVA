import os
from interface import App

if __name__ == "__main__":
    app = App()
    #app.wm_attributes('-fullscreen', True)
    #app.after(0, lambda: app.state('zoomed'))
    
    image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "InterfaceFigures")
    app.iconbitmap(os.path.join(image_path, "ceva_icon.ico"))
    
    app.mainloop()