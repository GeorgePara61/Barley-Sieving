import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from PIL import Image, ImageTk, ImageDraw
import cv2
from pathlib import Path
import copy

class draw_borders:
    def __init__(self, parent, img_path,img_original):
        self.parent = parent
        self.win = tk.Toplevel(parent)
        self.win.title("Draw Missing Borders")
        self.win.focus_force()
        self.win.grab_set()  # make Toplevel modal

        # Load base image
        cv_img = cv2.imread(img_path, cv2.IMREAD_COLOR)
        self.original_img = Image.fromarray(img_original)
        self.base_img = Image.fromarray(cv_img)
        self.overlay_img = Image.new("RGBA", self.base_img.size, (0,0,0,0))

        # Stroke history for undo/redo
        self.strokes = []
        self.redo_stack = []

        # Canvas
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.canvas = tk.Canvas(self.win, width=self.base_img.width, height=self.base_img.height, bg="white")
        self.canvas.pack(fill="both", expand=True)
        self.tk_img = ImageTk.PhotoImage(self.base_img)
        self.canvas_img_id = self.canvas.create_image(self.offset_x, self.offset_y, anchor="nw", image=self.tk_img)

        # Drawing state
        self.drawing = False
        self.prev_x = None
        self.prev_y = None
        self.mode = "draw"
        self.line_thickness = 4
        self.draw_color = (255, 255, 0, 255)  # yellow

        # Panning state
        self.panning = False
        self.pan_start_x = None
        self.pan_start_y = None

        # Bind mouse events
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw)
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.pan)
        self.canvas.bind("<ButtonRelease-3>", self.end_pan)
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<Button-4>", self.zoom)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.zoom)  # Linux scroll down
        self.canvas.config(cursor="plus")  # approximate square cursor

        # Bind keys
        self.win.bind("<Key>", self.key_handler)

        # Buttons (optional)
        btn_frame = tk.Frame(self.win)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Draw Mode", command=self.set_draw).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Erase Mode", command=self.set_erase).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Thickness +", command=self.increase_thickness).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Thickness -", command=self.decrease_thickness).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Undo", command=self.undo).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Redo", command=self.redo).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Save", command=self.save_image).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Close", command=self.win.destroy).pack(side="left", padx=2)

        self.img_path = img_path
        self.last_saved_file = None


    # ---------------- Drawing ----------------
    def start_draw(self, event):
        """Call on mouse button press to begin a new stroke."""
        x = (event.x - self.offset_x) / self.scale
        y = (event.y - self.offset_y) / self.scale
        self.prev_x, self.prev_y = x, y
        self.drawing = True

        # Initialize current stroke
        if self.mode == "draw":
            self.current_stroke = {
                "points": [(x, y)],
                "color": self.draw_color,
                "thickness": self.line_thickness
            }
            self.stroke_points = [(x, y)]
        else:
            self.current_stroke = None  # erase mode does not track strokes
            self.stroke_points = []

    def draw(self, event):
        """Call on mouse motion while button pressed."""
        if not self.drawing:
            return

        x = (event.x - self.offset_x) / self.scale
        y = (event.y - self.offset_y) / self.scale

        # If prev_x is None, just set it and return (prevents huge initial lines)
        if self.prev_x is None:
            self.prev_x, self.prev_y = x, y
            if self.mode == "draw":
                self.stroke_points = [(x, y)]
                if self.current_stroke is None:
                    self.current_stroke = {
                        "points": [(x, y)],
                        "color": self.draw_color,
                        "thickness": self.line_thickness
                    }
            return

        if self.mode == "draw":
            # Append current point to both stroke_points and current_stroke
            self.stroke_points.append((x, y))
            if self.current_stroke is not None:
                self.current_stroke["points"].append((x, y))

            if len(self.stroke_points) >= 2:
                draw_obj = ImageDraw.Draw(self.overlay_img)
                draw_obj.line(
                    self.stroke_points,
                    fill=self.current_stroke["color"],
                    width=self.current_stroke["thickness"],
                    joint="curve"
                )

        elif self.mode == "erase":
            # Interpolate along last segment for continuous erase
            size = self.line_thickness
            dx = x - self.prev_x
            dy = y - self.prev_y
            num_steps = int(max(abs(dx), abs(dy))) or 1
            for i in range(num_steps + 1):
                xi = self.prev_x + dx * i / num_steps
                yi = self.prev_y + dy * i / num_steps
                x0 = int(max(0, xi - size / 2))
                y0 = int(max(0, yi - size / 2))
                x1 = int(min(self.base_img.width, xi + size / 2))
                y1 = int(min(self.base_img.height, yi + size / 2))
                region = self.original_img.crop((x0, y0, x1, y1))
                self.overlay_img.paste(region, (x0, y0))

        # Update previous point
        self.prev_x, self.prev_y = x, y

        # Merge base + overlay for live display
        merged = Image.alpha_composite(self.base_img.convert("RGBA"), self.overlay_img)
        w, h = merged.size
        scaled = merged.resize((int(w * self.scale), int(h * self.scale)), Image.NEAREST)
        self.tk_img = ImageTk.PhotoImage(scaled)
        self.canvas.itemconfig(self.canvas_img_id, image=self.tk_img)
        self.canvas.coords(self.canvas_img_id, self.offset_x, self.offset_y)

    def end_draw(self, event):
        """Call on mouse button release to end the current stroke."""
        self.drawing = False
        self.prev_x, self.prev_y = None, None
        self.stroke_points = []  # clear points for next stroke

    # ---------------- Panning ----------------
    def start_pan(self, event):
        self.panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def pan(self, event):
        if self.panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.offset_x += dx
            self.offset_y += dy
            self.canvas.move(self.canvas_img_id, dx, dy)
            self.pan_start_x = event.x
            self.pan_start_y = event.y

    def end_pan(self, event):
        self.panning = False

    # ---------------- Zoom ----------------
    def zoom(self, event):
        factor = 1.1 if getattr(event, "delta", 0) > 0 or getattr(event, "num", 0) == 4 else 0.9
        cursor_x = (self.canvas.canvasx(event.x) - self.offset_x)/self.scale
        cursor_y = (self.canvas.canvasy(event.y) - self.offset_y)/self.scale
        self.scale *= factor
        self.offset_x = event.x - cursor_x*self.scale
        self.offset_y = event.y - cursor_y*self.scale
        self.update_canvas()

    # ---------------- Canvas update ----------------
    def update_canvas(self):
        # Clear overlay and redraw strokes
        self.overlay_img = Image.new("RGBA", self.base_img.size, (0,0,0,0))
        for stroke in self.strokes:
            draw = ImageDraw.Draw(self.overlay_img)
            points = stroke["points"]
            color = stroke["color"] if stroke["mode"]=="draw" else (0,0,0,0)
            thickness = stroke["thickness"]
            if len(points) > 1:
                for i in range(len(points)-1):
                    draw.line([points[i], points[i+1]], fill=color, width=thickness)

        merged = Image.alpha_composite(self.base_img.convert("RGBA"), self.overlay_img)
        w, h = merged.size
        scaled = merged.resize((int(w*self.scale), int(h*self.scale)), Image.NEAREST)
        self.tk_img = ImageTk.PhotoImage(scaled)
        self.canvas.itemconfig(self.canvas_img_id, image=self.tk_img)
        self.canvas.coords(self.canvas_img_id, self.offset_x, self.offset_y)

    # ---------------- Keybinds ----------------
    def key_handler(self, event):
        key = event.keysym.lower()
        if key == "d":
            self.set_draw()
        elif key == "e":
            self.set_erase()
        elif key == "plus" or key == "equal":
            self.increase_thickness()
        elif key == "minus":
            self.decrease_thickness()
        elif key == "s":
            self.save_image()
        elif key == "q":
            self.win.destroy()
        elif key == "u":
            self.undo()
        elif key == "r":
            self.redo()

    # ---------------- Buttons ----------------
    def set_draw(self):
        self.mode = "draw"

    def set_erase(self):
        self.mode = "erase"

    def increase_thickness(self):
        self.line_thickness = min(20, self.line_thickness + 1)

    def decrease_thickness(self):
        self.line_thickness = max(1, self.line_thickness - 1)

    # ---------------- Undo/Redo ----------------
    def undo(self):
        if self.strokes:
            self.redo_stack.append(self.strokes.pop())
            self.update_canvas()

    def redo(self):
        if self.redo_stack:
            self.strokes.append(self.redo_stack.pop())
            self.update_canvas()

    # ---------------- Save ----------------
    def save_image(self):
        merged = Image.alpha_composite(self.base_img.convert("RGBA"), self.overlay_img)
        folder = Path("border_overlays_complete")
        folder.mkdir(exist_ok=True)
        base_name = Path(self.img_path).stem
        try:
            base_name = str(base_name)
            base_name = base_name.split("_")[0] + "_" + base_name.split("_")[1]
        except Exception:
            pass
        # Find existing files
        existing_files = list(folder.glob(f"{base_name}_complete*.tif"))
        if not existing_files:
            save_path = folder / f"{base_name}_complete.tif"
        else:
            # Find the highest index
            max_index = 0
            for f in existing_files:
                stem = f.stem  # e.g., image_complete_3
                parts = stem.split("_")
                if parts[-1].isdigit():
                    idx = int(parts[-1])
                    if idx > max_index:
                        max_index = idx
            save_path = "border_overlays_complete" + "\\" + f"{base_name}_complete_{max_index+1}.tif"
        merged.convert("RGB").save(save_path, compression="tiff_lzw")        
        self.last_saved_file = str(save_path)
        MessageDialog(self.parent, "Saved!", f"The Image has been saved in '\\border_overlays_complete' as:\n{save_path.split("\\")[1]}.")

        

class MessageDialog(simpledialog.Dialog):
    def __init__(self, parent, title, message):
        self.message = message
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text=self.message, wraplength=500).pack(padx=40, pady=10)
        return None  # no initial focus needed

    def buttonbox(self):
        box = tk.Frame(self)
        tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE).pack(pady=5)
        box.pack()

    def apply(self):
        pass  # nothing to return