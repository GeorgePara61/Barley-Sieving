import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def border_seeking(img, img_name, thr1, thr2, kernel_v, min_grain_size): #this applies the canny algorithm to find the borders, does the post-proccessing by removing small objects and closing small gaps, shows and saves the image

    plt.switch_backend('TkAgg')

    edges = cv2.Canny(img, thr1, thr2) #get the borders
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) #get the contours, to post - proccess them
    
    grain_mask = np.zeros_like(img, dtype=np.uint8)
    for cnt in contours: #draw the borders on black background
        if cv2.contourArea(cnt) >= min_grain_size: #exclude small grains
            cv2.drawContours(grain_mask, [cnt], -1, 255, -1)  # Fill contours

    #these 2 if statements handle morphology fixing (cover small holes, connect small gaps)
    if not kernel_v == (0,0):
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_v)
        grain_mask = cv2.morphologyEx(grain_mask, cv2.MORPH_CLOSE, kernel)

        if grain_mask.dtype == bool:
            output = grain_mask.astype(np.uint8) * 255
        else:
            output = grain_mask
        
        if output.max() <= 1:
            output = (output * 255).astype(np.uint8)

    if kernel_v == (0,0):
        if edges.dtype == bool:
            output = edges.astype(np.uint8) * 255
        else:
            output = edges
        
        if output.max() <= 1:
            output = (output * 255).astype(np.uint8)

    fig, axes = plt.subplots(1, 2, figsize=(15,5)) #print and save image
    axes[0].imshow(edges, cmap='gray')
    axes[0].set_title("Canny Edges")
    axes[1].imshow(output, cmap='gray', vmin=0, vmax=255)
    axes[1].set_title("Final Segmentation")

    fig.canvas.draw()

    plt.show()

    #the following algorithm finds the index the file should have. if the previous file is named testX_diameters_56.csv this will output testX_diameters_57.csv
    #!!!!!!SAVING DISABLED

    '''folder = Path('border_outlines')
    files = [str(f) for f in folder.iterdir() if f.is_file()]

    if len(files) == 0:
        grimg_name = f"border_outlines\\{img_name.split(".")[0]}_borders.tif"

    else:
        index = 0
        for f in files:
            if f.split("\\")[1].split("_")[0] == img_name.split(".")[0]:
                try:
                    temp = int(f.split("_")[3].split(".")[0]) + 1
                except IndexError:
                    index = 1
                    if len(files) == 1: break
                    else: continue    
                temp = int(f.split("_")[3].split(".")[0]) + 1
                if temp > index: index = temp
        
        if index == 0: grimg_name = f"border_outlines\\{img_name.split(".")[0]}_borders.tif"
        else: grimg_name = f"border_outlines\\{img_name.split(".")[0]}_borders_{index}.tif"'''

    
    #cv2.imwrite(grimg_name, output, [cv2.IMWRITE_TIFF_COMPRESSION, 1])
    
    return output#, grimg_name