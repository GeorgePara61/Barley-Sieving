import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from PIL import Image, ImageTk, ImageDraw
import cv2
from pathlib import Path
import copy

class draw_borders:
    def __init__(self, parent, img_path, img_original, folder):
        self.parent = parent
        self.win = tk.Toplevel(parent)
        self.win.title("Draw Missing Borders")
        self.win.focus_force()
        self.win.grab_set()  # make Toplevel modal

        # Load base image
        cv_img = cv2.imread(img_path, cv2.IMREAD_COLOR)
        if img_path.split("_")[-1] == 'complete.tif' or img_path.split("_")[-2] == 'complete':
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
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
        self.folder = folder

    def smooth_line(self, points, steps=20):
        """Generate smooth points from Catmull–Rom spline."""
        if len(points) < 4:
            return points

        smooth = []
        for i in range(1, len(points) - 2):
            p0, p1, p2, p3 = points[i-1], points[i], points[i+1], points[i+2]
            for t in [j/steps for j in range(steps+1)]:
                x = 0.5 * ((2*p1[0]) +
                        (-p0[0] + p2[0]) * t +
                        (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t*t +
                        (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t*t*t)
                y = 0.5 * ((2*p1[1]) +
                        (-p0[1] + p2[1]) * t +
                        (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t*t +
                        (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t*t*t)
                smooth.append((x, y))
        return smooth

    def _apply_stroke_to_overlay(self, stroke):
        """Replay a stroke on the overlay (for redraws)."""
        if stroke["mode"] == "draw":
            draw = ImageDraw.Draw(self.overlay_img)
            points = stroke["points"]
            if len(points) > 1:
                smooth_points = self.smooth_line(points, steps=20)
                for i in range(len(smooth_points) - 1):
                    draw.line(
                        [smooth_points[i], smooth_points[i + 1]],
                        fill=stroke["color"],
                        width=stroke["thickness"]
                    )


        elif stroke["mode"] == "erase":
            size = stroke["thickness"]
            points = stroke["points"]
            for i in range(1, len(points)):
                x0 = int(max(0, points[i][0] - size / 2))
                y0 = int(max(0, points[i][1] - size / 2))
                x1 = int(min(self.base_img.width, points[i][0] + size / 2))
                y1 = int(min(self.base_img.height, points[i][1] + size / 2))
                region = self.original_img.crop((x0, y0, x1, y1))
                self.overlay_img.paste(region, (x0, y0))


    def _apply_stroke_to_base(self, stroke):
        """Flatten a stroke into the base image permanently."""
        if stroke["mode"] == "draw":
            draw = ImageDraw.Draw(self.base_img)
            points = stroke["points"]
            if len(points) > 1:
                smooth_points = self.smooth_line(points, steps=20)
                for i in range(len(smooth_points) - 1):
                    draw.line(
                        [smooth_points[i], smooth_points[i + 1]],
                        fill=stroke["color"],
                        width=stroke["thickness"]
                    )


        elif stroke["mode"] == "erase":
            size = stroke["thickness"]
            points = stroke["points"]
            for i in range(1, len(points)):
                x0 = int(max(0, points[i][0] - size / 2))
                y0 = int(max(0, points[i][1] - size / 2))
                x1 = int(min(self.base_img.width, points[i][0] + size / 2))
                y1 = int(min(self.base_img.height, points[i][1] + size / 2))
                region = self.original_img.crop((x0, y0, x1, y1))
                self.base_img.paste(region, (x0, y0))

    # ---------------- Drawing ----------------
    def start_draw(self, event):
        """Call on mouse button press to begin a new stroke."""
        x = (event.x - self.offset_x) / self.scale
        y = (event.y - self.offset_y) / self.scale
        self.prev_x, self.prev_y = x, y
        self.drawing = True

        # Initialize current stroke for both draw and erase
        self.current_stroke = {
            "points": [(x, y)],
            "mode": self.mode,
            "color": self.draw_color if self.mode == "draw" else None,
            "thickness": self.line_thickness
        }
        self.stroke_points = [(x, y)]

    def draw(self, event):
        """Call on mouse motion while button pressed."""
        if not self.drawing:
            return

        x = (event.x - self.offset_x) / self.scale
        y = (event.y - self.offset_y) / self.scale

        if self.prev_x is None:
            self.prev_x, self.prev_y = x, y
            self.stroke_points.append((x, y))
            self.current_stroke["points"].append((x, y))
            return

        # Append the new point
        self.stroke_points.append((x, y))

        if self.mode == "draw":
            self.current_stroke["points"].append((x, y))
            draw_obj = ImageDraw.Draw(self.overlay_img)
            points = self.current_stroke["points"]

            # Use the last 4 points for smoothing
            if len(points) > 3:
                smooth_points = self.smooth_line(points[-4:], steps=20)
                for i in range(len(smooth_points)-1):
                    draw_obj.line(
                        [smooth_points[i], smooth_points[i+1]],
                        fill=self.current_stroke["color"],
                        width=self.current_stroke["thickness"]
                    )
            else:
                # fallback: draw simple line segment
                draw_obj.line(
                    [points[-2], points[-1]],
                    fill=self.current_stroke["color"],
                    width=self.current_stroke["thickness"]
                )

        elif self.mode == "erase":
            size = self.line_thickness
            dx = x - self.prev_x
            dy = y - self.prev_y
            num_steps = int(max(abs(dx), abs(dy))) or 1
            for i in range(num_steps+1):
                xi = self.prev_x + dx * i / num_steps
                yi = self.prev_y + dy * i / num_steps
                self.current_stroke["points"].append((xi, yi))

                x0 = int(max(0, xi - size/2))
                y0 = int(max(0, yi - size/2))
                x1 = int(min(self.base_img.width, xi + size/2))
                y1 = int(min(self.base_img.height, yi + size/2))
                if x1 > x0 and y1 > y0:
                    region = self.original_img.crop((x0, y0, x1, y1))
                    self.overlay_img.paste(region, (x0, y0))

        self.prev_x, self.prev_y = x, y

        # Live merge and show
        base_rgba = self.base_img.convert("RGBA")
        if self.overlay_img.mode != "RGBA" or self.overlay_img.size != base_rgba.size:
            self.overlay_img = base_rgba.copy()
        merged = Image.alpha_composite(base_rgba, self.overlay_img)
        scaled = merged.resize((int(merged.width * self.scale), int(merged.height * self.scale)), Image.NEAREST)
        self.tk_img = ImageTk.PhotoImage(scaled)
        self.canvas.itemconfig(self.canvas_img_id, image=self.tk_img)
        self.canvas.coords(self.canvas_img_id, self.offset_x, self.offset_y)

    def end_draw(self, event=None):
        """Finalize the stroke and add it to history."""
        if not self.drawing:
            return

        self.drawing = False
        if self.current_stroke and len(self.current_stroke["points"]) > 1:
            # Save stroke
            self.strokes.append(self.current_stroke)
            self.redo_stack.clear()  # new stroke clears redo

            # Cap stroke history to last 10
            if len(self.strokes) > 10:
                # Take the oldest stroke and flatten it
                old_stroke = self.strokes.pop(0)
                self._apply_stroke_to_base(old_stroke)

        self.current_stroke = None
        self.stroke_points.clear()

        self.update_canvas()


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
        """Redraw everything from base + strokes."""
        # Ensure overlay is RGBA
        self.overlay_img = self.base_img.convert("RGBA").copy()

        # Replay all strokes
        for stroke in self.strokes:
            self._apply_stroke_to_overlay(stroke)

        # Merge and show
        merged = self.overlay_img
        scaled = merged.resize((int(merged.width * self.scale), int(merged.height * self.scale)), Image.NEAREST)
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
        """Undo the last stroke (if available)."""
        if not self.strokes:
            return  # nothing to undo

        stroke = self.strokes.pop()       # remove latest stroke
        self.redo_stack.append(stroke)    # save it for redo
        self.update_canvas()              # redraw without it

    def redo(self):
        """Redo the most recently undone stroke."""
        if not self.redo_stack:
            return  # nothing to redo

        stroke = self.redo_stack.pop()    # get the stroke back
        self.strokes.append(stroke)       # reapply it

        # if strokes exceed 10 after redo, flatten oldest one
        if len(self.strokes) > 10:
            old_stroke = self.strokes.pop(0)
            self._apply_stroke_to_base(old_stroke)

        self.update_canvas()

    # ---------------- Save ----------------
    def save_image(self):
        merged = Image.alpha_composite(self.base_img.convert("RGBA"), self.overlay_img)
        base_name = ".".join(self.img_path.split(".")[:-1]).split("\\")[2]
        if base_name.split("_")[-1] == 'complete': base_name = '_'.join(base_name.split("_")[:-1])
        elif base_name.split("_")[-1].isdigit(): 
            if base_name.split("_")[-2] == 'complete':
                base_name = '_'.join(base_name.split("_")[:-2])
            else: base_name = '_'.join(base_name.split("_")[:-1])
        try:
            base_name = str(base_name)
        except Exception:
            pass
        # Find existing files
        folder = self.folder
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
            save_path = str(folder) + "\\" + f"{base_name}_complete_{max_index+1}.tif"
        merged.convert("RGB").save(save_path, compression="tiff_lzw")        
        self.last_saved_file = str(save_path)
        MessageDialog(self.parent, "Saved!", f"The Image has been saved in {str(folder)} as:\n{str(save_path).split("\\")[2]}.")

        

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