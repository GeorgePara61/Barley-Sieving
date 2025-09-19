import numpy as np
import matplotlib.pyplot as plt

def merge(analyzed_imgs, bin_cnt, aspect_ratios): #this merges the surface and diameter data from all images analyzed and bins diameter data

    def read_data(cmn_name, num): #reads data for each image

        #inter = input()
        cutoff = 0
        filename = "reports" + "\\" + cmn_name + str(num) + "\\" + cmn_name + str(num) + '_surfaces_diameters.csv'

        total = 0
        totarea = 0
        diams = []
        sc_areas = []

        with open(filename, 'r') as input1:
            areas = {}
            for line in input1:
                try:
                    temp = int(line.split(",")[0])
                except ValueError:
                    continue
                sc_areas.append(float(line.split(",")[1].strip()))
                diams.append(float(line.split(",")[2].strip()))
                totarea += float(line.split(",")[1].strip())
                total += 1

        print(f"Mean Value of area is {round(totarea/total, 2)} μm²")

        '''file_d = 'test' + str(num) + '_diameters.csv'
        file_s = 'test' + str(num) + '_surfaces_real.csv'


                
        with open(file_d, 'w') as output_d:
            output_d.write("Index,Diameter\n")

            i = 0
            for diameter in diams:
                i += 1
                output_d.write(f"{i},{diameter}\n")

            print(f"Τα δεδομένα ακτίνας αποθηκεύτηκαν με όνομα: {file_d}")

        with open(file_s, 'w') as output_s:
            output_s.write("Index,Diameter\n")

            i = 0
            for key in areas:
                i += 1
                output_s.write(f"{i},{areas[key]}\n")

            print(f"Τα δεδομένα επιφάνειας αποθηκεύτηκαν με όνομα: {file_s}")'''
            

        return diams, sc_areas

    nums_temp = []
    for name in analyzed_imgs: #each image is expected to have a common name and a number for example (sample1.1, sample1.2, sample1.3... this breaks it down to sample1. and the numbers 1, 2, 3)
        numbers_list = []
        letters_list = []
        letters_prev = ''
        letters = ''
        numbers = ''
        flag = 1
        for char in reversed(name): #it goes through the name's characters, from last to first, storing the first numbers it sees in the number list. When it sees a non digit, it saves everything else in the common name
            if flag == 1:
                if char.isdigit():
                    numbers_list.append(char)
                else: 
                    flag = 0
                    letters_list.append(char)
            elif flag == 0: letters_list.append(char)
        for num in reversed(numbers_list): numbers += num
        for letter in reversed(letters_list): letters += letter
        if not letters_prev == '':
            if letters != letters_prev:
                print(f"Problem with names. One of the files has common name {letters_prev} and the other has {letters}. Both expected {letters_prev}.")
        letters_prev = letters
        nums_temp.append(numbers)

    
    global cmn_name, nums, scaling, mrg_name, bin_name, bin_count
    cmn_name = letters
    nums = nums_temp
    scaling = "1"
    mrg_name = "-"
    bin_name = "-"
    bin_count = bin_cnt

    if nums == []:
        for i in range(1, len(analyzed_imgs)): nums.append(i)

    totdiams= []
    totareas = []

    for num in nums: #request data
        diameters, scaled_areas = read_data(cmn_name, int(num))
        for diam in diameters: totdiams.append(diam)
        for area in scaled_areas: totareas.append(area)

    mrg_nums = "_" #build file names
    for num in nums:
        mrg_nums = mrg_nums + num + "_"

    if mrg_name == "-":
        file_out_diams = "merged_surfaces_diameters/" + cmn_name  + mrg_nums + "merged_surfaces_diameters.csv"
    else: 
        file_out_diams = "merged_surfaces_diameters/" + mrg_name + "_diameters.csv"

    if bin_name == "-": file_d = "merged_diameters_binned/" + cmn_name  + mrg_nums + "merged_diameters_binned.csv"
    else: file_d = "merged_diameters_binned/" + bin_name + ".csv"

    i = 1
    with open(file_out_diams, 'w') as diameter_output: #store the merged data
        diameter_output.write("Index,Area,Diameter")
        for area, diam in zip(totareas, totdiams):
            diameter_output.write(f"{i},{area},{diam}\n")
            i += 1

    counts = {}
    hist_dat = []
    hist_bins = []
    curr_step = 0
    prev_step = 0
    maxx = max(totdiams)
    step = maxx / bin_count

    while curr_step < maxx: #this bins all the diameter data
        prev_step = curr_step
        curr_step += step
        counts[curr_step] = 0
        for item in totdiams:
            if prev_step < item < curr_step:
                hist_dat.append(curr_step)
                counts[curr_step] += 1

    with open(file_d, "w") as output:
        output.write("Diameter Range,Frequency\n")

        for key in counts:
            output.write(f"{key},{counts[key]}\n")

        print(f"Τα οργανωμένα κατα διαστήματα δεδομένα ακτίνας αποθηκεύτηκαν με όνομα: {file_d}")

    max_ar = (np.ceil(max(aspect_ratios))) #this bins the total aspect ratios and makes the histogram
    if max_ar - max(aspect_ratios) > 0.25: max_ar -= 0.25
    binf = 1
    aspr_bins = {}

    while binf <= max_ar:
        aspr_bins[binf] = 0
        for aspr in aspect_ratios:
            if binf <= aspr < binf + 0.25: aspr_bins[binf] += 1
        binf += 0.25

    # Convert to arrays for plotting
    bin_indices = list(aspr_bins.keys())
    counts = list(aspr_bins.values())

    # Create bin edges and centers
    bin_edges = list(bin_indices) + [max(bin_indices) + 0.25]  # [1, 2, 3, 4, 5, 6]
    bin_centers = [edge + 0.125 for edge in bin_edges[:-1]]   # [1.5, 2.5, 3.5, 4.5, 5.5]

    plt.figure(figsize=(12, 7))

    # Create step plot (connects the bins)
    plt.step(bin_edges, [counts[0]] + counts, where='pre', 
            linewidth=2, color='steelblue', marker='o', markersize=6)

    # Add filled area under the curve (optional)
    plt.fill_between(bin_edges, [counts[0]] + counts, alpha=0.9, color='lightblue', step='pre')

    '''# Add bin edge labels
    for i, edge in enumerate(bin_edges):
        plt.text(edge, plt.ylim()[1] * 0.02, f'{edge}', 
                ha='center', va='bottom', fontweight='bold', fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))'''

    ymin, ymax = plt.ylim()
    # Add value labels on top of each step
    for i, (center, count) in enumerate(zip(bin_centers, counts)):
        if count == 0: continue
        plt.text(center, count + 0.015*ymax, f'{round((count/len(aspect_ratios)*100), 1)}%', 
                ha='center', va='bottom', fontweight='bold', fontsize=11)
        
    for i, (center, count) in enumerate(zip(bin_centers, counts)):
        if count == 0: continue
        plt.text(center, count - 0.05*ymax, f'{count}', 
                ha='center', va='bottom', fontweight='bold', fontsize=11)

    plt.xticks(bin_edges)
    plt.xlabel('Aspect Ratio', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Grain Aspect Ratio Distribution', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.ylim(0, max(counts) * 1.15)  # Add some headroom for labels
    plt.tight_layout()

    plt.show()