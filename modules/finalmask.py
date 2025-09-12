
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

def create_binary_mask(output_image_path, kernel_v): #this takes the finalized, drawn image and turns it to a black borders - white pixels image

    plt.switch_backend('TkAgg')

    # Read the output image
    img = cv2.imread(output_image_path)
    
    if img is None:
        raise FileNotFoundError(f"Could not load image: {output_image_path}")
    
    # Convert BGR to RGB (if needed)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Create mask where yellow pixels (255,255,0) are True
    yellow_pixels = np.all(img_rgb == [255, 255, 0], axis=-1)
    
    # Create binary mask (yellow=black, others=white)
    binary_mask = np.where(yellow_pixels, 0, 255).astype(np.uint8)

    #the following tries to close small holes and connect disconnected pixel wide openings in borders

    _, binary_mask = cv2.threshold(binary_mask, 127, 255, cv2.THRESH_BINARY)

    if not kernel_v == (0,0): kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)) 
    else: kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

    inverted = cv2.bitwise_not(binary_mask)

    inverted = cv2.morphologyEx(inverted, cv2.MORPH_CLOSE, kernel, iterations=3)

    binary_mask = cv2.bitwise_not(inverted)

    '''binary_mask = cv2.erode(binary_mask, kernel, iterations=1)
    binary_mask = cv2.dilate(binary_mask, kernel, iterations=1)'''

    #the following creates the preview image with the options to get the grain sizes for this image of skip it

    def button1_callback(event):
        global measure
        measure = True
        plt.close()

    def button2_callback(event):
        global measure
        measure = False 
        plt.close()
    
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.2)
    
    # Display the mask
    ax.imshow(binary_mask, cmap='gray', vmin=0, vmax=255)
    ax.set_title('Binary Mask')

    ax_button1 = plt.axes([0.3, 0.05, 0.2, 0.075])  # [left, bottom, width, height]
    ax_button2 = plt.axes([0.6, 0.05, 0.2, 0.075])

    # Create the button objects
    button1 = Button(ax_button1, 'Measure')
    button2 = Button(ax_button2, 'Skip')

    # Connect the buttons to their callbacks
    button1.on_clicked(button1_callback)
    button2.on_clicked(button2_callback)

    fig.canvas.draw()

    plt.show()
    
    return binary_mask, measure