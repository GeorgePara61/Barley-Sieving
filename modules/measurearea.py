import numpy as np
from pathlib import Path

def measure_areas(areas, scale, cutoff, in_px, img_name): #get the areas in real length units and calculate the diameters
    total = 0
    totarea = 0

    sx = scale
    sy = scale

    img_name = img_name.split(".")[0]
    diams = []

    for key in areas: #go through all the grains, calculate the areas and diameters
        total += 1
        area = areas[key] * sx * sy
        if not in_px:
            if area < cutoff: continue
        totarea += area
        diam = float(np.sqrt((area*4)/np.pi))
        print(f"Grain No. {key} has an area of {round(area, 2)} μm² and diameter {round(diam, 2)} μm")
        diams.append(diam)
        areas[key] = area

    print(f"Mean Value of area is {round(totarea/total, 2)} μm²")

    #here save the area and diameter data in csv files

    folder = Path('grain_surfaces_diameters')
    files = [str(f) for f in folder.iterdir() if f.is_file()]
    
    #if len(files) == 0:
    file_s = f"grain_surfaces_diameters\\{img_name}_surfaces_diameters.csv"

    with open(file_s, 'w') as output_s:
        output_s.write("Index,Area,Diameter\n")

        i = 0
        for key, diameter in zip(areas, diams):
            i += 1
            output_s.write(f"{i},{areas[key]},{diameter}\n")

        print(f"Τα δεδομένα επιφάνειας αποθηκεύτηκαν στον φάκελο {file_s.split("\\")[0]} με όνομα: {file_s.split("\\")[1]}")
         

    return round(totarea/total, 2), diams


