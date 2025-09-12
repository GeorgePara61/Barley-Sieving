import cv2
from pathlib import Path

def grayscale_converter(img, img_name): #make the image grayscale (in case it isn't) and save it (save is disabled)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    folder = Path('grain_images')
    files = [str(f) for f in folder.iterdir() if f.is_file()]

    if len(files) == 0:
        grimg_name = f"grain_images\\{img_name.split(".")[0]}_grains.jpg"

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
        
        if index == 0: grimg_name = f"grain_images\\{img_name.split(".")[0]}_grains.jpg"
        else: grimg_name = f"grain_images\\{img_name.split(".")[0]}_grains_{index}.jpg"
        
    #cv2.imwrite(grimg_name, gray)

    return gray, grimg_name