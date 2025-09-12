from pathlib import Path

def bin_diameters(diameters, iter, img_name): #this function handles data bining

    counts = {} #suppose you want to find the number n of measurements in (x1, x2). This dict stores data like this -> x1: n
    hist_bins = []
    curr_step = 0
    prev_step = 0
    maxx = max(diameters)
    step = maxx / iter #the lenght of (x1, x2)
    img_name = img_name.split(".")[0]

    while curr_step < maxx: #starting at zero and finishing when reaching the max value
        prev_step = curr_step #this sets the previous x2 as the current x1
        curr_step += step #this is added on the previous x2, making it the current x2
        counts[curr_step] = 0 #this initializes n as 0
        for item in diameters:
            if prev_step < item < curr_step: #if the measurement falls within (x1, x2), increase n by 1
                counts[curr_step] += 1

    #the following algorithm finds the index the file should have. if the previous file is named testX_diameters_56.csv this will output testX_diameters_57.csv
    folder = Path('diameters_binned')
    files = [str(f) for f in folder.iterdir() if f.is_file()]
    
    if len(files) == 0:
        file_d = f"diameters_binned\\{img_name}_diameters_binned.csv"
    else:
        index = 0
        for f in files:
            if f.split("\\")[1].split("_")[0] == img_name:
                try:
                    temp = int(f.split("_")[-1].split(".")[0]) + 1
                except ValueError:
                    index = 1
                    if len(files) == 1: break
                    else: continue    
                temp = int(f.split("_")[-1].split(".")[0]) + 1
                if temp > index: index = temp

        if index == 0: file_d = f"diameters_binned\\{img_name}_diameters_binned.csv"
        else: file_d = f"diameters_binned\\{img_name}_diameters_binned_{index}.csv"

    with open(file_d, "w") as output: #write the output file
        output.write("Diameter Range,Frequency\n")

        for key in counts:
            output.write(f"{key},{counts[key]}\n")

        print(f"Τα οργανωμένα κατα διαστήματα δεδομένα ακτίνας αποθηκεύτηκαν με όνομα: {file_d}")

    return