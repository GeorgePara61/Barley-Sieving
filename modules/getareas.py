import numpy as np
from skimage.segmentation import flood
from tqdm import tqdm
import matplotlib.pyplot as plt


def measure_grain_area(final_mask, cutoff, in_px, tolerance = 0): #this takes the black borders - white pixels and measures the grain areas

    plt.switch_backend('TkAgg')

    connectivity=2

    img = final_mask * 255
    label_map = np.zeros_like(img, dtype=np.int32)
    gray_map = np.zeros_like(img, dtype=np.int32)
    current_label = 1
    height, width = img.shape
    visited = np.zeros_like(img, dtype=bool)
    area_dict = {}

    for y in tqdm(range(height), desc="measuring Grains"): #this goes to each pixel, checks if the pixel is part of an unmeasured grain and measures it using a flood - fill algorithm
        for x in range(width):
            if not visited[y, x] and img[y, x] == 1:
                gray_val = img[y, x]
                region_mask = flood(img, seed_point=(y, x), tolerance=tolerance, connectivity=connectivity)
                flooded_pixels = np.sum(region_mask == True)
                visited |= region_mask
                if in_px:
                    if flooded_pixels < cutoff: continue
                label_map[region_mask] = current_label #save the grain label
                gray_map[region_mask] = gray_val #recreate the black - white image to double check
                area_dict[current_label] = flooded_pixels #save the pixel area
                current_label += 1


    fig, axs = plt.subplots(1, 2, figsize=(15, 5))
    axs[0].imshow(label_map, cmap='nipy_spectral')
    axs[0].set_title('Grain Map')
    axs[0].axis('off')

    axs[1].imshow(gray_map, cmap='gray')
    axs[1].set_title('Final Mask')
    axs[1].axis('off')

    fig.canvas.draw()
    plt.show()    

    return area_dict, current_label, label_map