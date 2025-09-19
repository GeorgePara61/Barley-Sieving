import matplotlib.pyplot as plt
import cv2
import numpy as np
from matplotlib.widgets import Slider, Button
from modules import preproccess
from pathlib import Path

def overlay_borders(original_img, img_name, img_s, thr1, thr2, kernel_v, min_grain_size, border_mask, 
                   kernel_gf, stdev, conval, tgs, d, sc, ss, ksize, sobel_blend, gamma, folder,
                   edge_preserve=True, color=(255, 255, 0), thickness=2): #this overlays the detected borders on the original image or the blurred, and provides sliders to change parameters
    
    # Global variables to track state
    global overlay, final_overlay, preproccessed, blurred
    grayed = original_img.copy()
    preproccessed = preproccess.img_prep(grayed, (int(kernel_gf), int(kernel_gf)), stdev, conval, 
                                       (int(tgs), int(tgs)), d, sc, ss, ksize, sobel_blend, gamma)
    blurred = False
    
    # Initialize overlay images
    if len(original_img.shape) == 2:
        overlay = cv2.cvtColor(original_img, cv2.COLOR_GRAY2BGR)
    else:
        overlay = original_img.copy()
    final_overlay = overlay.copy()
    
    # Process border mask
    if len(border_mask.shape) == 3:
        border_mask = cv2.cvtColor(border_mask, cv2.COLOR_BGR2GRAY)
    border_mask = border_mask.astype(np.uint8)
    if border_mask.max() <= 1: 
        border_mask = (border_mask * 255).astype(np.uint8)

    # Create figure
    plt.switch_backend('TkAgg')
    fig = plt.figure(figsize=(12, 8))
    img_ax = plt.axes([0.1, 0.2, 0.6, 0.7])
    img_display = img_ax.imshow(overlay, cmap='gray')
    img_ax.set_title("Interactive Border Adjustment")
    img_ax.axis('off')

    # Create controls
    ax_button1 = plt.axes([0.75, 0.1, 0.175, 0.030])
    ax_button2 = plt.axes([0.75, 0.15, 0.175, 0.030])
    button1 = Button(ax_button1, 'Generate')
    button2 = Button(ax_button2, "Switch")

    # Slider configurations
    right_params = {
        'Smoothing Range (Pre)': {'val': int(kernel_gf), 'range': (1, 25), 'step': 2},
        'Standard Deviation': {'val': float(stdev), 'range': (0, 5), 'step': 0.1},
        'Contrast Intensity': {'val': float(conval), 'range': (0, 10), 'step': 0.1},
        'Transitions': {'val': int(tgs), 'range': (0, 24), 'step': 1},
        'Smoothing Range (Post)': {'val': int(d), 'range': (1, 35), 'step': 2},
        'Affected Color Range': {'val': int(sc), 'range': (0, 150), 'step': 1},
        'Affected Area Range': {'val': int(ss), 'range': (0, 150), 'step': 1},
        'Thickness': {'val': int(ksize), 'range': (-1, 15), 'step': 2},
        'Blend Factor': {'val': float(sobel_blend), 'range': (0, 1), 'step': 0.01},
        'Gamma': {'val': float(gamma), 'range': (0.1, 3.0), 'step': 0.1}
    }

    right_sliders = []
    for i, (label, params) in enumerate(right_params.items()):
        ax = plt.axes([0.75, 0.8-i*0.065, 0.15, 0.06])
        ax.text(0.5, 1.0, label, transform=ax.transAxes, ha='center', va='center', fontsize=9)
        slider = Slider(ax, label='', valmin=params['range'][0], valmax=params['range'][1],
                       valinit=params['val'], valstep=params['step'], facecolor='#ffff00')
        right_sliders.append(slider)

    bottom_params = {
        'Low Threshold': {'val': float(thr1), 'range': (0, 255), 'step': 1},
        'High Threshold': {'val': float(thr2), 'range': (0, 255), 'step': 1}
    }

    bottom_sliders = []
    for i, (label, params) in enumerate(bottom_params.items()):
        ax = plt.axes([0.15, 0.15-i*0.05, 0.55, 0.03])
        slider = Slider(ax, label=label, valmin=params['range'][0], valmax=params['range'][1],
                       valinit=params['val'], valstep=params['step'], facecolor='#ffff00')
        bottom_sliders.append(slider)

    def update_pre(val): #updates pre proccess parameters. Triggered by pressing generate
        global overlay, final_overlay, preproccessed
        
        params = {
            'kernel_gf': int(right_sliders[0].val),
            'stdev': float(right_sliders[1].val),
            'conval': float(right_sliders[2].val),
            'tgs': (int(right_sliders[3].val), int(right_sliders[3].val)),
            'd': int(right_sliders[4].val),
            'sc': int(right_sliders[5].val),
            'ss': int(right_sliders[6].val),
            'ksize': int(right_sliders[7].val),
            'sobel_blend': float(right_sliders[8].val),
            'gamma': float(right_sliders[9].val),
            'thr1': int(bottom_sliders[0].val),
            'thr2': int(bottom_sliders[1].val)
        }
        
        if params['thr2'] <= params['thr1']: #Canny Threshold 1 must always be less than Threshold 2
            params['thr2'] = params['thr1'] + 1
            bottom_sliders[1].set_val(params['thr2'])
        
        #following is the image analysis as conducted before
        preproccessed = preproccess.img_prep(
            grayed, 
            (params['kernel_gf'], params['kernel_gf']), params['stdev'], 
            params['conval'], params['tgs'], params['d'], params['sc'], params['ss'], 
            (params['ksize'], params['ksize']), params['sobel_blend'], params['gamma']
        )
        
        edges = cv2.Canny(preproccessed, params['thr1'], params['thr2'])

        if not kernel_v == (0,0):
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            grain_mask = np.zeros_like(img_s, dtype=np.uint8)
            for cnt in contours:
                if cv2.contourArea(cnt) >= min_grain_size:
                    cv2.drawContours(grain_mask, [cnt], -1, 255, -1)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_v)
            grain_mask = cv2.morphologyEx(grain_mask, cv2.MORPH_CLOSE, kernel)
            output = (grain_mask * 255).astype(np.uint8) if grain_mask.max() <= 1 else grain_mask
        else: 
            output = (edges * 255).astype(np.uint8) if edges.max() <= 1 else edges
        
        if blurred: 
            over_image = preproccessed 
        else: 
            over_image = original_img
            
        overlay = cv2.cvtColor(over_image, cv2.COLOR_GRAY2BGR) if len(over_image.shape) == 2 else over_image.copy()

        if not kernel_v == (0,0):
            contours, _ = cv2.findContours(output, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(overlay, contours, -1, color, thickness)
        else:
            overlay[output == 255] = (0, 255, 255)  # Vectorized operation

        final_overlay = overlay.copy()  # Update final version
        img_display.set_data(overlay)
        fig.canvas.draw_idle()

    def update_can(val): #Triggered when canny sliders change
        update_pre(val)  # Reuse the same update logic

    def show_blur(event): #switch between blur and original
        global blurred
        blurred = not blurred
        update_pre(None)

    # Connect controls
    button1.on_clicked(update_pre)
    button2.on_clicked(show_blur)
    for slider in bottom_sliders:
        slider.on_changed(update_can)

    # Show and wait for window to close
    plt.show()

    if blurred:
        show_blur("event")

    temp_files = list(folder.glob(f"{".".join(img_name.split(".")[:-1])}_overlay*.tif"))

    files = []

    for file in temp_files:
        file_t = ".".join(str(file).split(".")[:-1])
        if not (file_t.split("_")[-1] == 'complete' or (file_t.split("_")[-1].isdigit() and file_t.split("_")[-2] == 'complete')):
            files.append(file)
            
    if len(files) == 0:
        grimg_name = f"{str(folder)}\\{".".join(img_name.split(".")[:-1])}_overlay.tif"

    else:
        index = 0
        for f in files:
            f = str(f).split("\\")[2]
            if f.split("_")[0] == ".".join(img_name.split(".")[:-1]):
                try:
                    temp = int(".".join(f.split("_")[-1].split(".")[:-1])) + 1
                except Exception:
                    index = 1
                    if len(files) == 1: break
                    else: continue    
                temp = int(".".join(f.split("_")[-1].split(".")[:-1])) + 1
                if temp > index: index = temp
        
        if index == 0: grimg_name = f"{str(folder)}\\{".".join(img_name.split(".")[:-1])}_overlay.tif"
        else: grimg_name = f"{str(folder)}\\{".".join(img_name.split(".")[:-1])}_overlay_{index}.tif"
    
    cv2.imwrite(grimg_name, overlay, [cv2.IMWRITE_TIFF_COMPRESSION, 5])
    
    # Prepare return values
    return_values = (
        final_overlay,
        grimg_name,
        str(bottom_sliders[0].val),
        str(bottom_sliders[1].val),
        f"{right_sliders[0].val},{right_sliders[0].val}",
        str(right_sliders[1].val),
        str(round(float(right_sliders[2].val), 2)),
        f"{right_sliders[3].val},{right_sliders[3].val}",
        str(right_sliders[4].val),
        str(right_sliders[5].val),
        str(round(float(right_sliders[6].val), 2)),
        str(right_sliders[7].val),
        str(right_sliders[8].val),
        str(right_sliders[9].val),
    )
    
    plt.close('all')
    return return_values