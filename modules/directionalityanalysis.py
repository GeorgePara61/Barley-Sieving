import cv2
import numpy as np
from tqdm import tqdm
import pandas as pd
import matplotlib.pyplot as plt

def analyze_directionality(label_map, px_area_dict, area_dict, scale, img_name, folder): #fits ellipses, saves data, makes an aspect ratio histogram and an orientation radar diagram
    grain_properties = []
    unique_labels = np.unique(label_map)
    unique_labels = unique_labels[unique_labels != 0]
    aspect_ratios = []
    angles = []

    for label in tqdm(unique_labels, desc="Fitting Ellipses"): # Create a mask from the label_map. This will be a boolean array.
        grain_mask = (label_map == label) #this makes the whole white grains - black borders image black except for the grain it's working on
        px_area = px_area_dict[label]
        area = area_dict[label]
             
        if np.max(grain_mask) == False: # This means the mask is all False. Skip it.
            print(f"Skipping grain {label}: Mask is completely empty.")
            grain_properties.append({{"Grain Number": label,
                                         "Grain Area in μm²": area,
                                         'Grain Area in px': px_area,
                                         "Major Axis": None,
                                         "Minor Axis": None,
                                         #'Center': None,
                                         "Orientation": None,
                                         "Aspect Ratio": None}}) # Append data with None
            continue

        if px_area > 5:
            try:
                coordinates = np.where(grain_mask) # Gets the image of the grain (it asks for the coordinates of the white pixels which is the grain here)
                if len(coordinates[0]) == 0:
                    raise ValueError("No points found in mask despite positive count.")

                # Convert the coordinates to the correct format for OpenCV.
                # We need an Nx2 array of points in the form [[x1, y1], [x2, y2], ...]
                # Note: np.column_stack reverses the order from (y, x) to (x, y).
                points = np.column_stack((coordinates[1], coordinates[0])).astype(np.float32)

                # Fit the ellipse directly to the points.
                ellipse_params = cv2.fitEllipse(points)
                (center_x, center_y), (axis1, axis2), angle_deg = ellipse_params
                major_axis = max(axis1, axis2)
                minor_axis = min(axis1, axis2)
                aspect_ratio = major_axis / minor_axis

                #the following commented out block saves the images of the grains with the ellipses on them. It was used to check the ellipse fitting
                '''debug_image = np.zeros((grain_mask.shape[0], grain_mask.shape[1], 3), dtype=np.uint8)
                debug_image[grain_mask] = (255, 255, 255)  # White for the grain
                cv2.ellipse(debug_image, ellipse_params, (255, 255, 0), 2)  # Red ellipse, 2px thickness
                center = (int(center_x), int(center_y))
                cv2.circle(debug_image, center, 4, (0, 0, 255), -1)  # Green center point
                angle_rad = np.radians(angle_deg)

                # Calculate and draw the MAJOR AXIS (blue)
                # Calculate endpoints of major axis
                major_angle_rad = angle_rad + np.pi/2
                major_end1 = (
                    int(center_x + (major_axis / 2) * np.cos(major_angle_rad)),
                    int(center_y + (major_axis / 2) * np.sin(major_angle_rad))
                )
                major_end2 = (
                    int(center_x - (major_axis / 2) * np.cos(major_angle_rad)),
                    int(center_y - (major_axis / 2) * np.sin(major_angle_rad))
                )
                # Draw major axis in blue
                cv2.line(debug_image, major_end1, major_end2, (0, 0, 255), 2)  # Blue major axis

                # Calculate and draw the MINOR AXIS (cyan)
                # Minor axis is perpendicular to major axis (add 90 degrees)
                minor_angle_rad = angle_rad
                # Calculate endpoints of minor axis
                minor_end1 = (
                    int(center_x + (minor_axis / 2) * np.cos(minor_angle_rad)),
                    int(center_y + (minor_axis / 2) * np.sin(minor_angle_rad))
                )
                minor_end2 = (
                    int(center_x - (minor_axis / 2) * np.cos(minor_angle_rad)),
                    int(center_y - (minor_axis / 2) * np.sin(minor_angle_rad))
                                )
                # Draw minor axis in cyan
                cv2.line(debug_image, minor_end1, minor_end2, (0, 255, 0), 2)  # Cyan minor axis

                # 5. Save the image with a descriptive filename
                cv2.imwrite(f'ellipses/grain_{label}_fit_{label}.png', debug_image)'''

                aspect_ratios.append(aspect_ratio)
                angles.append(angle_deg)
                grain_properties.append({'Grain Number': label,
                                         'Grain Area in μm²': area,
                                         'Grain Area in px': px_area,
                                         "Major Axis": major_axis * scale,
                                         'Minor Axis': minor_axis * scale,
                                         #'Center': (center_x, center_y),
                                         'Orientation': angle_deg,
                                         'Aspect Ratio': aspect_ratio}) # Add your data
            except Exception as e:
                print(f"Could not fit ellipse to grain {label}: {e}")
                grain_properties.append({"Grain Number": label,
                                         "Grain Area in μm²": area,
                                         'Grain Area in px': px_area,
                                         "Major Axis": None,
                                         "Minor Axis": None,
                                         #'Center': None,
                                         "Orientation": None,
                                         "Aspect Ratio": None}) # Add data without ellipse params
        else:
                grain_properties.append({"Grain Number": label,
                                         "Grain Area in μm²": area,
                                         'Grain Area in px': px_area,
                                         "Major Axis": None,
                                         "Minor Axis": None,
                                         #'Center': None,
                                         "Orientation": None,
                                         "Aspect Ratio": None}) # Add data for small grains

    df_grains = pd.DataFrame(grain_properties) #store the properties

    print(df_grains)

    out_name = str(folder) + "\\" + ".".join(img_name.split('.')[:-1]) + "_directionality.csv"
    df_grains.to_csv(out_name, index=False) #save the properties

    #the following organizes the aspect ratios in bins or lenght 0.25 for the histogram
    max_ar = (np.ceil(max(aspect_ratios)))
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
    bin_edges = list(bin_indices) + [max(bin_indices) + 0.25] 
    bin_centers = [edge + 0.125 for edge in bin_edges[:-1]]  

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

    # 1. Round all angles to integers and ensure they're in 0-180 range
    rounded_angles = np.round(angles).astype(int) % 180

    # 2. Create mirrored data: for each angle, add angle + 180
    mirrored_angles = np.concatenate([rounded_angles, (rounded_angles + 180) % 360])

    # 3. Create histogram with percentage frequency for full 360° range
    num_bins = 36  # 10-degree bins (360/10 = 36)
    bin_edges = np.linspace(0, 360, num_bins + 1)
    hist, _ = np.histogram(mirrored_angles, bins=bin_edges)

    # 4. Convert counts to percentages (divide by original count, not mirrored count!)
    total_grains = len(rounded_angles)  # Use original count, not mirrored
    percentages = (hist / total_grains) * 100

    max_per = max(percentages)
    them = [20, 40, 60, 80, 100]
    limit = 100
    for it in them:
        if it - max_per < limit - max_per and it - max_per > 0: limit = it
    
    limit_ind = limit / 5


    # 4. Polar coordinates
    theta = np.deg2rad(np.linspace(0, 360, num_bins, endpoint=False))
    width = np.deg2rad(360 / num_bins)

    # 5. Create the web diagram
    plt.figure(figsize=(10, 8))
    ax = plt.subplot(111, projection='polar')

    # Plot the bars with percentages
    bars = ax.bar(theta, percentages, width=width, alpha=0.7, 
                edgecolor='black', linewidth=1, color='steelblue')

    # 6. Set 0° at top (Y-axis) for web diagram
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)  # Clockwise

    # 7. Set radial axis to percentage (0% to 100%)
    ax.set_ylim(0, limit)
    ax.set_yticks([0, limit_ind, limit_ind*2, limit_ind*3, limit_ind*4, limit_ind*5])
    ax.set_yticklabels(['0%', f'{str(limit_ind)}%', f'{str(limit_ind*2)}%', f'{str(limit_ind*3)}%', f'{str(limit_ind*4)}%', f'{str(limit_ind*5)}%'], fontsize=10)

    # 8. Customize angle labels (show every 30 degrees)
    angle_labels = []
    for angle in range(0, 360, 30):
        angle_labels.append(f'{angle}°')
    ax.set_xticks(np.deg2rad(np.arange(0, 360, 30)))
    ax.set_xticklabels(angle_labels, fontsize=10)

    # 9. Add grid and title
    ax.grid(True, alpha=0.5)
    ax.set_title('Grain Orientation Web Diagram\nPercentages reflect grains on a singe axis \n(0° at top, percentages on radial axis)', 
                fontsize=14, pad=30, fontweight='bold')

    # 10. Add value labels on peaks (optional)
    max_percentage = max(percentages)
    for i, (angle_rad, percent) in enumerate(zip(theta, percentages)):
        if percent > max_percentage * 0.3:  # Only label significant peaks
            ax.text(angle_rad, percent + 0.5, f'{percent:.1f}%', 
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow", alpha=0.7))

    plt.tight_layout()

    # Print summary statistics
    print(f"Total grains: {total_grains}")
    print(f"Angle range: {min(rounded_angles)}° to {max(rounded_angles)}°")
    print(f"Most frequent orientation: {bin_edges[np.argmax(percentages)]:.0f}° "
        f"({max(percentages):.1f}% of grains)")
    
    sum = 0
    errsum = 0
    ress = []

    for res in aspect_ratios: sum += res #get the mean and standard deviation for the aspect ratios
    mean = sum/len(aspect_ratios)

    for res in aspect_ratios: errsum += np.pow(res - mean, 2)

    err = np.sqrt(errsum/(len(aspect_ratios)*(len(aspect_ratios) - 1)))

    print(f"Mean of Aspect Ratios: {mean}, Its Error: {err}")

    plt.show()

    report = f'> Most frequent orientation: {bin_edges[np.argmax(percentages)]:.0f}° ({max(percentages):.1f}% of grains)\n> Mean of Aspect Ratios: {round(mean, 2)}, Its Error: {round(err, 2)}'

    return report, aspect_ratios