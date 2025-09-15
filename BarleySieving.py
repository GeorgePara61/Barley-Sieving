import matplotlib
matplotlib.use("TkAgg")
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from tkinter import scrolledtext
import ctypes
import sys
import numpy as np
import cv2
from pathlib import Path

from modules import cropper
from modules import grayconv
from modules import preproccess
from modules import findborders
from modules import overlay
from modules import completeborders
from modules import finalmask
from modules import getareas
from modules import measurearea
from modules import scaling
from modules import bin
from modules import merging
from modules import directionalityanalysis

def set_dpi_awareness():
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # system DPI aware
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

def get_scaling_factor(root):   # Accessing Window's scaling to properly scale fonts in guis
    return root.winfo_fpixels('1i') / 96

def generate_input_GUI(parent, user_inputs): #generating a gui to input parameters
    win = tk.Toplevel(parent)
    win.title(f"Grain Size Calculator - Parameter Input")

    scaling = get_scaling_factor(parent) #request the scaling factor

    win.geometry(f"{int(560* scaling)}x{int(520* scaling)}") #gui dimensions (widthxheight)

    win.focus()

    small_font = tkFont.Font(family="Segoe UI", size=7, weight="normal")

    tk.Label(win, text="Picture Name and Crop").grid(row=0, column=0, columnspan=6, sticky="w", padx=10, pady=(10, 0)) #these commands create labels on the gui
    folder = Path('images')
    images = [str(f).split("\\")[1] for f in folder.iterdir() if f.is_file()]
    img_sel = ttk.Combobox(win,values = images)
    img_sel.grid(row=2, column=0, columnspan=2, padx=10, pady=5)
    img_sel.set("")  # Default value
    img_sel.bind('<Button-1>', lambda e: img_sel.event_generate('<Down>'))
    tk.Label(win, text="Should be in {app directory}\\images", font = small_font).grid(row=1, column=0, columnspan= 2, sticky = "w", padx=10, pady=0)
    entry16 = tk.Entry(win, width=26)
    entry16.grid(row=2, column=2, columnspan=2, padx=10, pady=5)
    tk.Label(win, text="Scale (μm/px) ('-' for manual)", font = small_font).grid(row=1, column=2, columnspan= 2, sticky = "w", padx=10, pady=0)

    tk.Label(win, text="Should it be cropped? Input height (px)", font = small_font).grid(row=1, column=4, columnspan=2, sticky="w", padx=10, pady=(10, 0))

    frame = tk.Frame(win)
    frame.grid(row=2, column=4, columnspan=2)

    entry17 = tk.Entry(frame, width=18)
    entry17.pack(side="left", padx=(0, 5))

    options = ["Yes", "No"]
    crop_sel = ttk.Combobox(frame,values = options, width=4)
    crop_sel = ttk.Combobox(frame,values = options, width=4)
    crop_sel.pack(side="left")
    crop_sel.set("Yes")  # Default value
    crop_sel.bind('<Button-1>', lambda e: crop_sel.event_generate('<Down>'))

    tk.Label(win, text="1) Pre Contrast Adjustment Smoothing Parameters").grid(row=4, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(win, text="Smoothing Range:", font = small_font, pady=0).grid(row=5, column=0, columnspan= 3, sticky="w", padx=10, pady=0)
    tk.Label(win, text="Standard Deviation (px):", font = small_font, pady=0).grid(row=5, column=3, columnspan= 3, sticky="w", padx=10, pady=0)

    entry2 = tk.Entry(win, width=39)
    entry2.grid(row=6, column=0, columnspan= 3, padx=10, pady=5)
    entry3 = tk.Entry(win, width=39)
    entry3.grid(row=6, column=3, columnspan= 3, padx=10, pady=5)

    tk.Label(win, text="2) Contrast Enhancement Parameters:").grid(row=8, column=0, columnspan=6, sticky="w", padx=10, pady=(10, 0))
    tk.Label(win, text="Intensity:", font = small_font, pady=0).grid(row=9, column=0, columnspan= 3, sticky="w", padx=10, pady=0)
    tk.Label(win, text="Transitions (px):", font = small_font, pady=0).grid(row=9, column=3, columnspan= 3, sticky="w", padx=10, pady=0)

    entry4 = tk.Entry(win, width=39)
    entry4.grid(row=10, column=0, columnspan=3, padx=10, pady=5)
    entry5 = tk.Entry(win, width=39)
    entry5.grid(row=10, column=3, columnspan=3, padx=10, pady=5)

    tk.Label(win, text="3) Post Contrast Adjustment Smoothing Parameters").grid(row=12, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(win, text="Smoothing Range (px):", font = small_font, pady=0).grid(row=13, column=0, columnspan= 2, sticky="w", padx=10, pady=0)
    tk.Label(win, text="Affected Color Range (gv):", font = small_font, pady=0).grid(row=13, column=2, columnspan= 2, sticky="w", padx=10, pady=0)
    tk.Label(win, text="Affected Area Range (px):", font = small_font, pady=0).grid(row=13, column=4, columnspan= 2, sticky="w", padx=10, pady=0)

    entry6 = tk.Entry(win, width=24)
    entry6.grid(row=14, column=0, columnspan= 2, padx=10, pady=5)
    entry7 = tk.Entry(win, width=24)
    entry7.grid(row=14, column=2, columnspan= 2, padx=10, pady=5)
    entry8 = tk.Entry(win, width=24)
    entry8.grid(row=14, column=4, columnspan= 2, padx=10, pady=5)

    tk.Label(win, text="4) Gradient Enhancement Parameters - Boundary Prominence:").grid(row=16, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(win, text="Thickness:", font = small_font, pady=0).grid(row=17, column=0, columnspan= 2, sticky="w", padx=10, pady=0)
    tk.Label(win, text="Blend Factor:", font = small_font, pady=0).grid(row=17, column=2, columnspan= 2, sticky="w", padx=10, pady=0)
    tk.Label(win, text="Gamma:", font = small_font, pady=0).grid(row=17, column=4, columnspan= 2, sticky="w", padx=10, pady=0)

    entry9 = tk.Entry(win, width=24)
    entry9.grid(row=18, column=0, columnspan= 2, padx=10, pady=5)
    entry10 = tk.Entry(win, width=24)
    entry10.grid(row=18, column=2, columnspan= 2, padx=10, pady=5)
    entry11 = tk.Entry(win, width=24)
    entry11.grid(row=18, column=4, columnspan= 2, padx=10, pady=5)

    tk.Label(win, text="5) Canny Parameters").grid(row=20, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(win, text="Canny Threshold 1 (gv/px):", font = small_font, pady=0).grid(row=21, column=0, columnspan= 3, sticky="w", padx=10, pady=0)
    tk.Label(win, text="Canny Threshold 2 (gv/px):", font = small_font, pady=0).grid(row=21, column=3, columnspan= 3, sticky="w", padx=10, pady=0)

    entry12 = tk.Entry(win, width=39)
    entry12.grid(row=22, column=0, columnspan=3, padx=10, pady=5)
    entry13 = tk.Entry(win, width=39)
    entry13.grid(row=22, column=3, columnspan=3, padx=10, pady=5)

    tk.Label(win, text="5) Gap and Noise Removal").grid(row=24, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(win, text="Gap Bridge Parameter:", font = small_font, pady=0).grid(row=25, column=0, columnspan= 3, sticky="w", padx=10, pady=0)
    tk.Label(win, text="Minimum Object Size (px):", font = small_font, pady=0).grid(row=25, column=3, columnspan= 3, sticky="w", padx=10, pady=0)

    entry14 = tk.Entry(win, width=39)
    entry14.grid(row=26, column=0, columnspan=3, padx=10, pady=5)
    entry15 = tk.Entry(win, width=39)
    entry15.grid(row=26, column=3, columnspan=3, padx=10, pady=5)

    try: #this tries to import default data from defaults.txt
        img_sel.insert(0, user_inputs.pop(0))
        entry2.insert(0, user_inputs.pop(0))
        entry3.insert(0, user_inputs.pop(0))
        entry4.insert(0, user_inputs.pop(0))
        entry5.insert(0, user_inputs.pop(0))
        entry6.insert(0, user_inputs.pop(0))
        entry7.insert(0, user_inputs.pop(0))
        entry8.insert(0, user_inputs.pop(0))
        entry9.insert(0, user_inputs.pop(0))
        entry10.insert(0, user_inputs.pop(0))
        entry11.insert(0, user_inputs.pop(0))
        entry12.insert(0, user_inputs.pop(0))
        entry13.insert(0, user_inputs.pop(0))
        entry14.insert(0, user_inputs.pop(0))
        entry15.insert(0, user_inputs.pop(0))
        entry16.insert(0, user_inputs.pop(0))
        entry17.insert(0, user_inputs.pop(0))

    except IndexError:
        pass

    def on_continue(event=None): #read the parameters and start working
        user_inputs.append(img_sel.get())
        user_inputs.append(entry2.get())
        user_inputs.append(entry3.get())
        user_inputs.append(entry4.get())
        user_inputs.append(entry5.get())
        user_inputs.append(entry6.get())
        user_inputs.append(entry7.get())
        user_inputs.append(entry8.get())
        user_inputs.append(entry9.get())
        user_inputs.append(entry10.get())
        user_inputs.append(entry11.get())
        user_inputs.append(entry12.get())
        user_inputs.append(entry13.get())
        user_inputs.append(entry14.get())
        user_inputs.append(entry15.get())
        user_inputs.append(entry16.get())
        user_inputs.append(entry17.get())
        global crop #this variable determines if the image will be cropped
        if crop_sel.get() == 'Yes':
            crop =True
        elif crop_sel.get() == 'No':
            crop = False
        win.destroy()
        global info #this tells the program that the info panel wasn't requested
        info = False

    def on_exit(event=None): #exit the program
        win.destroy()
        global rerun #this variable handles whether the program will re run. It defaults to false here and the user gets to choose in the end
        rerun = False
        global info
        info = False
    
    def on_info(event=None): #save input and generate the info gui
        user_inputs.append(img_sel.get())
        user_inputs.append(entry2.get())
        user_inputs.append(entry3.get())
        user_inputs.append(entry4.get())
        user_inputs.append(entry5.get())
        user_inputs.append(entry6.get())
        user_inputs.append(entry7.get())
        user_inputs.append(entry8.get())
        user_inputs.append(entry9.get())
        user_inputs.append(entry10.get())
        user_inputs.append(entry11.get())
        user_inputs.append(entry12.get())
        user_inputs.append(entry13.get())
        user_inputs.append(entry14.get())
        user_inputs.append(entry15.get())
        user_inputs.append(entry16.get())
        user_inputs.append(entry17.get())
        win.destroy()

    tk.Button(win, width = 24, text="Run", command=on_continue).grid(row=28, column=0, columnspan=2, pady=10) #this command creates and places a button on the gui
    tk.Button(win, width = 24, text="Info", command=on_info).grid(row=28, column=2, columnspan=2, pady=10)
    tk.Button(win, width = 24, text="Exit", command=on_exit).grid(row=28, column=4, columnspan=2, pady=10)


    win.bind("<Return>", on_continue)
    win.bind("<Delete>", on_exit)

    win.grab_set()
    win.wait_window()

def generate_output_GUI(parent, mean, grains, anal_imgs, dir_report, mean_d): #after work, generate a gui with results and next actions
    win = tk.Toplevel(parent)
    win.title(f"Grain Size Calculator - Results")

    scaling = get_scaling_factor(parent)

    win.geometry(f"{int(420* scaling)}x{int(240* scaling)}")
    win.focus()

    if grains != None and mean != None and mean_d != None: #Following is the text creation the user sees when this gui is generated
        text = f"> Found a total of {grains} grains!\n> Mean grain area is {mean} μm²!\nMean Diameter is {mean_d} μm!\n"
    else: 
        text = f'> Grains Not Found\n> Mean area not calculated\n> Mean Diameter not calculated\n'

    if len(anal_imgs) > 0:
        strimg = "> Analyzed Images so far: "
        for image in anal_imgs:
            if len(anal_imgs) > 1:
                if not image == anal_imgs[len(anal_imgs) - 1]: strimg = strimg + image + ", "
                else: strimg = strimg + image
            elif len(anal_imgs) == 1: strimg = strimg + image
        strimg = strimg + ".\n"
    else: strimg = '> No Images have been analyzed.\n'

    if dir_report == None: dir_report = 'No directionality data.'

    text = text + strimg + dir_report

    text_area = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Segoe UI Symbol", 12))
    text_area.insert(tk.END, text)
    text_area.configure(state='disabled')
    text_area.grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 5), sticky="nsew")

    for r in range(4):
        win.rowconfigure(r, weight=1) 
    for c in range(4):
        win.columnconfigure(c, weight=1)

    def on_continue(event=None): #rerun the program keeping previous input parameters
        win.destroy() 

    def on_exit(event=None): #exit the program
        win.destroy()
        global rerun
        rerun = False

    tk.Button(win, width = 24, text="Run Again?", command=on_continue).grid(row=4, column=0, columnspan=2, pady=10)
    tk.Button(win, width = 24, text="Exit", command=on_exit).grid(row=4, column=2, columnspan=2, pady=10)

    win.bind("<Return>", on_continue)
    win.bind("<Delete>", on_exit)

    win.grab_set()       
    win.wait_window()

def generate_info_GUI(parent): #generate a gui detailing the parameters asked in input
    win = tk.Toplevel(parent)
    win.title(f"Grain Size Calculator - Application Info")

    scaling = get_scaling_factor(parent)

    win.geometry(f"{int(600* scaling)}x{int(650* scaling)}")

    win.focus()

    def read_info(): #the info comes from the file guide.txt which can be edited
        file = f"guide.txt"
        with open(file, "r", encoding='utf-8') as input: return input.read()

    text = read_info()

    text_area = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Segoe UI Symbol", 12))
    text_area.insert(tk.END, text)
    text_area.configure(state='disabled')  # Make it read-only
    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

    button_frame = tk.Frame(win)
    button_frame.pack(pady=10)

    def on_return(event = None): #go back to the input gui
        win.destroy()
    def on_exit(event = None): #exit the program
        win.destroy()
        global rerun
        rerun = False


    tk.Button(button_frame, width = 30, text="Return", command=on_return).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, width = 30, text="Exit", command=on_exit).pack(side=tk.LEFT, padx=10)

    win.bind("<Return>", on_return)
    win.bind("<Delete>", on_exit)

    win.grab_set()
    win.wait_window()

def generate_pre_measure_GUI(parent): #generate a gui to confirm area measurement, and input the number of histogram bins and minimum grain size
    win = tk.Toplevel(parent)
    win.title(f"Grain Size Calculator - measuring Parameters")

    scaling = get_scaling_factor(parent)

    win.geometry(f"{int(550* scaling)}x{int(250*scaling)}")

    win.focus()

    small_font = tkFont.Font(family="Segoe UI", size=7, weight="normal")

    tk.Label(win, text="Complete Picture Name").grid(row=0, column=0, columnspan=6, sticky="w", padx=10, pady=(10, 0))
    entry1 = tk.Entry(win, width=81)
    entry1.grid(row=2, column=0, columnspan=6, padx=10, pady=5)
    tk.Label(win, text="Should be located in \\border_overlays_complete", font = small_font).grid(row=1, column=0, columnspan= 6, sticky = "w", padx=10, pady=0)

    tk.Label(win, text="1) measure Parameters").grid(row=4, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(win, text="Grain Min Diameter (μm or px):", font = small_font, pady=0).grid(row=5, column=0, columnspan= 3, sticky="w", padx=10, pady=0)
    tk.Label(win, text="Scaling Factor (μm/px):", font = small_font, pady=0).grid(row=5, column=3, columnspan= 3, sticky="w", padx=10, pady=0)
   
    frame = tk.Frame(win)
    frame.grid(row=6, column=0, columnspan=3)

    entry3 = tk.Entry(frame, width=30)
    #entry3.grid(row=6, column=0, columnspan= 2, padx=10, pady=5)
    entry3.pack(side="left", padx=(0, 5))
    entry2 = tk.Entry(win, width=36)
    entry2.grid(row=6, column=3, columnspan= 3, padx=10, pady=5)

    options = ["px", "μm"] #user can choose to give a minimum grain size in pixel count or squared micrometers
    px_or_μm = ttk.Combobox(frame,values = options, width=4)
    #px_or_μm.grid(row=6, column=2, columnspan=1, padx=(0, 10), pady=5)
    px_or_μm.pack(side="left")
    px_or_μm.set("px")  # Default value
    px_or_μm.bind('<Button-1>', lambda e: px_or_μm.event_generate('<Down>'))

    tk.Label(win, text="2) Histogram Bin Count").grid(row=8, column=0, columnspan=6, sticky="w", padx=10)
    entry4 = tk.Entry(win, width=81)
    entry4.grid(row=9, column=0, columnspan=6, padx=10, pady=5)


    try: #this imputs previous data
        entry1.insert(0, measure_inputs.pop(0))
        entry2.insert(0, measure_inputs.pop(0))
        entry3.insert(0, measure_inputs.pop(0))
        entry4.insert(0, measure_inputs.pop(0))


    except IndexError:
        pass

    def on_measure(event=None): #read the parameters and start working
        measure_inputs.append(entry1.get())
        measure_inputs.append(entry2.get())
        measure_inputs.append(entry3.get())
        measure_inputs.append(entry4.get())
        try: # if the user input test_overlay_complete.tif instead of border_overlays_complete\test_overlay_complete.tif, it adds the border_overlays_complete\
            temp = measure_inputs[0].split("\\")[1]
        except IndexError:
            measure_inputs[0] = "border_overlays_complete\\" + measure_inputs[0]
        global in_px
        if px_or_μm.get() == 'px': 
            in_px = True
        elif px_or_μm.get() == 'μm':
            in_px = False
        win.destroy()
        global measure
        measure = True

    def on_skip(event=None): #skip measuring stage
        win.destroy()
        global measure
        measure = False
    

    tk.Button(win, width = 36, text="Measure", command=on_measure).grid(row=11, column=0, columnspan=3, pady=10)
    tk.Button(win, width = 36, text="Skip", command=on_skip).grid(row=11, column=3, columnspan=3, pady=10)


    win.bind("<Return>", on_measure)
    win.bind("<Delete>", on_skip)

    win.grab_set()
    win.wait_window()


def generate_draw_GUI(parent, img_name): #generate a gui to give option to draw on an image
    win = tk.Toplevel(parent)
    win.title(f"Grain Size Calculator - Drawing Image Selection")

    scaling = get_scaling_factor(parent)

    win.geometry(f"{int(350* scaling)}x{int(120* scaling)}")

    win.focus()

    small_font = tkFont.Font(family="Segoe UI", size=7, weight="normal")

    tk.Label(win, text="Select Which Image to draw on").grid(row=0, column=0, columnspan=6, sticky="w", padx=10, pady=(10, 0))
    entry1 = tk.Entry(win, width=40) #the user can choose previous images as well
    entry1.grid(row=2, column=0, columnspan=6, padx=10, pady=5)
    tk.Label(win, text="Should be located in \\border_overlays_complete or in \\border_overlays", font = small_font).grid(row=1, column=0, columnspan= 6, sticky = "w", padx=10, pady=0)


    entry1.insert(0, img_name)


    def on_confirm(event=None): #read the parameters and start working
        global overimg_name
        overimg_name = entry1.get()
        win.destroy()
    

    tk.Button(win, width = 40, text="Confirm", command=on_confirm).grid(row=24, column=0, columnspan=6, pady=10)


    win.bind("<Return>", on_confirm)

    win.grab_set()
    win.wait_window()

def generate_merge_promt_GUI(parent): #if the user analyzes many images, this promt appears that gives the option to merge all the surface and diameter data from these images and bin them
    win = tk.Toplevel(parent)
    win.title(f"Grain Size Calculator - Merger")

    scaling = get_scaling_factor(parent)

    win.geometry(f"{int(350* scaling)}x{int(200* scaling)}")
    win.focus()

    tk.Label(win, text="Would you like to merge and bin all the data of this session?").grid(row=0, column=0, columnspan=4, sticky="w", padx=10)

    for r in range(4):
        win.rowconfigure(r, weight=1) 
    for c in range(4):
        win.columnconfigure(c, weight=1)

    def on_continue(event=None): #rerun the program keeping previous input parameters
        win.destroy() 
        global merge
        merge = True
    def on_exit(event=None): #exit the program
        win.destroy()

    tk.Button(win, width = 15, text="Yes", command=on_continue).grid(row=4, column=0, columnspan=2, pady=10)
    tk.Button(win, width = 15, text="No", command=on_exit).grid(row=4, column=2, columnspan=2, pady=10)

    win.bind("<Return>", on_continue)
    win.bind("<Delete>", on_exit)

    win.grab_set()       
    win.wait_window()

set_dpi_awareness()

global measure_inputs, overimg_name, analyzed_imgs #the inputs from the pre measure gui, the name of the overlayed image, the images analyzed in a session
measure_inputs = []
rerun = True #handles the rerun function
root = tk.Tk() #creation of the main gui
root.withdraw()
user_inputs = [] #the inputs from the first gui
analyzed_imgs = []
merge = False #handles the merge function
aspect_ratios_all = [] #stores aspect ratios of all images

file = f"defaults.txt"
with open(file, "r") as input: #load default parameters
    for line in input:
        user_inputs.append(line.split("|")[0])

while rerun: #looping the program, unless exit is pressed which sets rerun = False
    
    info = True #this hanles whether the info panel will show. Not choosing info on the first gui sets it to false
    while info: #this gives the ability to loop from the info to the input gui while the latter is open
        if not rerun: exit(-1)
        generate_input_GUI(root, user_inputs)
        if not info: break

        generate_info_GUI(root)
        
    if not rerun: exit(-1)

    img_name, kernel_g, stdev, conval, tgs_s, d, sc, ss, ksize, blend_strength, gamma, thr1, thr2, kernel_s, min_size, scale, crop = user_inputs[0], user_inputs[1], float(user_inputs[2]), float(user_inputs[3]), user_inputs[4], int(user_inputs[5]), float(user_inputs[6]), float(user_inputs[7]), int(user_inputs[8]), float(user_inputs[9]), float(user_inputs[10]), int(user_inputs[11]), int(user_inputs[12]), (user_inputs[13]), int(user_inputs[14]), user_inputs[15], int(user_inputs[16])
    analyzed_imgs.append(img_name.split(".")[0])

    tgs = (int(tgs_s.split(",")[0]),int(tgs_s.split(",")[1]))
    kernel = (int(kernel_s.split(",")[0]),int(kernel_s.split(",")[1]))
    kernel_gf = (int(kernel_g.split(",")[0]), int(kernel_g.split(",")[0]))

    if scale == '-': scale = scaling.get_scale(root, img_name) #this opens a window where the user draws a line on the scale bar to get the scale
    print(scale)
    user_inputs[15] = str(scale)

    if crop: img = cropper.crop_img(img_name, crop) #this crops the info bar
    else:
        img_path = f"images\\{img_name}"
        img = cv2.imread(img_path)
    
    grayed, grayed_name = grayconv.grayscale_converter(img, img_name) #this converts the cropped image to grayscale and saves it
    preproccessed = preproccess.img_prep(grayed, kernel_gf, stdev, conval, tgs, d, sc, ss, ksize, blend_strength, gamma) #preproccessing of the image

    #print(f"Η εικόνα χωρίς την κάρτα πληροφοριών αποθηκεύτηκε ως {grayed_name.split("\\")[1]} στον φάκελο {grayed_name.split("\\")[0]}.")

    outline_img = findborders.border_seeking(preproccessed, img_name, thr1, thr2, kernel, min_size) #this finds the borders

    overlay_img, overimg_name, user_inputs[11], user_inputs[12], user_inputs[1], user_inputs[2], user_inputs[3], user_inputs[4], user_inputs[5], user_inputs[6], user_inputs[7], user_inputs[8], user_inputs[9], user_inputs[10] = overlay.overlay_borders(grayed, img_name, preproccessed, thr1, thr2, kernel, min_size, outline_img, kernel_g.split(",")[0], stdev, conval, tgs_s.split(",")[0], d, sc, ss, ksize, blend_strength, gamma) #this overlays the detected borders to the original. Sliders that can change the different parameters exist

    print(f"Η εικόνα των συνώρων αποθηκεύτηκε ως {overimg_name.split("\\")[1]} στον φάκελο {overimg_name.split("\\")[0]}.")

    generate_draw_GUI(root, overimg_name) #this gui requests the name of the image to draw on. The image the program was just working on is default, but it takes any image in \border_overlays and \border_overlays_complete

    draw = completeborders.draw_borders(root, overimg_name, grayed) #user drawn borders
    root.wait_window(draw.win)
    overfinal_name = draw.last_saved_file

    if overfinal_name != None: print(f"Η εικόνα των ολοκληρωμένων συνώρων αποθηκεύτηκε ως {overfinal_name.split("\\")[1]} στον φάκελο {overfinal_name.split("\\")[0]}.")

    if overfinal_name == None: overfinal_name = 'Enter Image name or press SKIP' #if the user didn't save an image from the draw phase, the program requests an image from border_overlays_complete
    if scale == None: 
        scale == 'Input scale in μm/px'
        cutoff = 'Input in px ONLY!!'
    elif scale != None: 
        cutoff = 'Input in μm or px (select unit)'
    iter = 'Input the bin count for the histogram'

    measure_inputs = []
    measure_inputs.append(overfinal_name)
    measure_inputs.append(str(scale))
    measure_inputs.append(str(cutoff))
    measure_inputs.append(str(iter))

    generate_pre_measure_GUI(root)

    if scale == None: in_px = True

    if measure: #skip sets measure = False 

        overfinal_name, scale, cutoff, iter = measure_inputs[0], float(measure_inputs[1]), float(measure_inputs[2]), float(measure_inputs[3])
        cutoff = np.pi*pow(cutoff/2, 2)

        final_mask, measure = finalmask.create_binary_mask(overfinal_name, kernel) #finallized white grains - black borders image
        if measure: 
            areas, grains, labels =  getareas.measure_grain_area(final_mask, cutoff, in_px) #get grain areas in px
            px_areas = areas.copy()
            print(f"Found {grains} grains.")
            mean, diams, mean_d = measurearea.measure_areas(areas, scale, cutoff, in_px, img_name) #get grain areas in μm^2 and diameters
            bin.bin_diameters(diams, iter, img_name) #bin diameters

            report1, aspect_ratios = directionalityanalysis.analyze_directionality(labels, px_areas, areas, scale, img_name) #get grain directions and aspect ratios
            aspect_ratios_all = aspect_ratios_all + aspect_ratios

        
    if not measure: 
        mean, grains, report1, mean_d = None, None, None, None
        analyzed_imgs.pop()

    generate_output_GUI(root, mean, grains, analyzed_imgs, report1, mean_d)

if len(analyzed_imgs) > 1: generate_merge_promt_GUI(root)

if merge == True: merging.merge(analyzed_imgs, iter, aspect_ratios_all) #merge surface and diameters, bin diameters, show total aspect ratios histogram