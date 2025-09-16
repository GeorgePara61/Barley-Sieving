import cv2
import math
import tkinter as tk
from tkinter import Toplevel, Canvas, Frame, Button, Label, simpledialog
from PIL import Image, ImageTk

class ScaleCalibrator: #This gets the scale from the image, by drawing a line on the scale bar of the image
    def __init__(self, parent, img_path): #initialize the class
        self.parent = parent
        self.img_path = img_path
        self.img = cv2.imread(img_path) #load image
        
        if self.img is None:
            raise ValueError(f"Could not load image from {img_path}")
        
        self.setup_window()
        self.setup_variables()
        self.setup_ui()
        self.display_image()
        
    def setup_window(self):
        self.top = Toplevel(self.parent)
        self.top.title("Scale Calibration")
        self.top.geometry("1536x950")
        self.top.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def setup_variables(self): #initialize variables
        self.img_pil = Image.fromarray(cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB))
        self.original_size = self.img_pil.size
        self.scale_factor = 1.0
        self.pan_x, self.pan_y = 0, 0
        self.line_coords = {'start': None, 'end': None}
        self.real_length = None
        self.result = None
        self.drawing = False
        self.tk_image = None
        self.force_horizontal = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.is_panning = False
        
    def setup_ui(self):
        # Main frame
        self.main_frame = Frame(self.top)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for image
        self.canvas = Canvas(self.main_frame, bg='gray')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Control frame
        self.ctrl_frame = Frame(self.top)
        self.ctrl_frame.pack(fill=tk.X)
        
        # Zoom controls
        self.zoom_label = Label(self.ctrl_frame, text="Zoom: 100%")
        self.zoom_label.pack(side=tk.LEFT)
        
        # Buttons
        Button(self.ctrl_frame, text="Set Length", command=self.set_real_length).pack(side=tk.LEFT)
        Button(self.ctrl_frame, text="Reset Line", command=self.reset_line).pack(side=tk.LEFT)
        Button(self.ctrl_frame, text="Zoom In", command=lambda: self.adjust_zoom(1.2)).pack(side=tk.LEFT)
        Button(self.ctrl_frame, text="Zoom Out", command=lambda: self.adjust_zoom(0.8)).pack(side=tk.LEFT)
        Button(self.ctrl_frame, text="Accept", command=self.accept).pack(side=tk.RIGHT)
        Button(self.ctrl_frame, text="Cancel", command=self.on_close).pack(side=tk.RIGHT)
        
        # Bind events on buttons
        self.canvas.bind("<Button-1>", self.on_click_start)
        self.canvas.bind("<B1-Motion>", self.on_click_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_click_release)
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.do_pan)
        self.canvas.bind("<ButtonRelease-3>", self.end_pan)
        self.canvas.bind("<Shift_L>", lambda e: self.set_horizontal_mode(True))
        self.canvas.bind("<KeyRelease-Shift_L>", lambda e: self.set_horizontal_mode(False))
        self.canvas.focus_set()
        
    def start_pan(self, event): #the following 3 functions handle panning of the image
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
    def do_pan(self, event): #this one specifically tracks how much the image is panned, based on how much the mouse has moved and where on the image the mouse is anchored
        if self.is_panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.pan_x += dx
            self.pan_y += dy
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.display_image()
        
    def end_pan(self, event): #stop panning
        self.is_panning = False
        
    def set_horizontal_mode(self, active): #press shift to lock horizontal line
        self.force_horizontal = active
        if self.drawing and self.line_coords['start']:
            self.update_line_constraint()
    
    def update_line_constraint(self): #unlock the horizontal contraint
        if not self.force_horizontal or not self.line_coords['end']:
            return
            
        x0, y0 = self.line_coords['start']
        x1, y1 = self.line_coords['end']
        self.line_coords['end'] = (x1, y0)
        self.display_image()
        
    def display_image(self): #update image in real time when panning, drawing or zooming
        new_width = int(self.original_size[0] * self.scale_factor)
        new_height = int(self.original_size[1] * self.scale_factor)
        
        resized_img = self.img_pil.resize((new_width, new_height), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_img)
        
        self.canvas.delete("all")
        self.canvas.create_image(self.pan_x, self.pan_y, anchor=tk.NW, image=self.tk_image)
        
        if self.line_coords['start'] and self.line_coords['end']:
            disp_start = (
                self.line_coords['start'][0] * self.scale_factor + self.pan_x,
                self.line_coords['start'][1] * self.scale_factor + self.pan_y
            )
            disp_end = (
                self.line_coords['end'][0] * self.scale_factor + self.pan_x,
                self.line_coords['end'][1] * self.scale_factor + self.pan_y
            )
            self.canvas.create_line(disp_start[0], disp_start[1], 
                                  disp_end[0], disp_end[1],
                                  fill="yellow", width=3)
        
        status_text = f"Zoom: {self.scale_factor*100:.0f}%"
        mode_status = " (HORIZONTAL)" if self.force_horizontal else ""
        
        if self.line_coords['start'] and self.line_coords['end']:
            dx = self.line_coords['end'][0] - self.line_coords['start'][0]
            dy = self.line_coords['end'][1] - self.line_coords['start'][1]
            length_px = math.sqrt(dx**2 + dy**2)
            status_text += f" | Line: {length_px:.1f} px"
            if self.real_length:
                status_text += f" | Scale: 1 px = {self.real_length/length_px:.4f} units"
        
        self.canvas.create_text(10, 10, text=status_text, anchor=tk.NW, fill="red")
        self.canvas.create_text(10, 30, text=f"Mode: Hold Shift{mode_status}", 
                              anchor=tk.NW, fill="blue")
        self.zoom_label.config(text=f"Zoom: {self.scale_factor*100:.0f}%")
        
    def set_real_length(self): #pop up window to add real length
        self.real_length = simpledialog.askfloat(
            "Input Length", 
            "Enter real-world length (μm):",
            parent=self.top,
            minvalue=0.0001
        )
        self.display_image()
        
    def reset_line(self): #on button press on image
        self.line_coords = {'start': None, 'end': None}
        self.display_image()
        
    def adjust_zoom(self, factor): #zoom in
        self.scale_factor *= factor
        self.scale_factor = max(0.1, min(5.0, self.scale_factor))
        self.display_image()
        
    def on_click_start(self, event): #when draw button is pressed, get the initial coords
        self.drawing = True
        self.line_coords['start'] = (
            (event.x - self.pan_x) / self.scale_factor,
            (event.y - self.pan_y) / self.scale_factor
        )
        self.line_coords['end'] = None
        
    def on_click_drag(self, event): #when mouse is dragged, update the line end coords
        if self.drawing:
            self.line_coords['end'] = (
                (event.x - self.pan_x) / self.scale_factor,
                (event.y - self.pan_y) / self.scale_factor
            )
            if self.force_horizontal:
                self.update_line_constraint()
            self.display_image()
            
    def on_click_release(self, event): #lock the line 
        self.drawing = False
        if self.line_coords['start'] and self.line_coords['end']:
            print(f"Line drawn from {self.line_coords['start']} to {self.line_coords['end']}")
        
    def accept(self): #after drawing the desired line and typing a real length, accept scale
        if self.line_coords['start'] and self.line_coords['end'] and self.real_length:
            dx = self.line_coords['end'][0] - self.line_coords['start'][0]
            dy = self.line_coords['end'][1] - self.line_coords['start'][1]
            length_px = math.sqrt(dx**2 + dy**2)
            self.result = self.real_length / length_px
        self.top.destroy()
        
    def on_close(self):
        self.result = None
        self.top.destroy()
        
    def get_result(self):
        return self.result

def get_scale(parent, img_name):
    img_path = f"images/{img_name}"
    calibrator = ScaleCalibrator(parent, img_path)
    parent.wait_window(calibrator.top)
    return calibrator.get_result()
