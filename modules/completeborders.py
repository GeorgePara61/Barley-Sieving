import cv2
from pathlib import Path
from ctypes import windll

def draw_borders(img_name, img_name_i): #this function handles drawing

    global grimg_name

    img_name_n = img_name.split("\\")[1]
    img_name_n_m = img_name_n.split("_") #these 2 lines get the previous overlay image name without the index eg: border_overlays\test_overlay_10.tif becomes test_ovelay

    img_name_n = img_name_n_m[0] + "_" + img_name_n_m[1]

    drawing = False     # True if mouse is pressed
    prev_point = None     # Initial coordinates
    line_thickness = 4  # Thickness of drawn lines
    overlay_color = (0, 255, 255)  
    mode = "draw" #default mode between draw and erase


    def draw_line(event, x, y, flags, param):
        nonlocal drawing, prev_point, img, mode
        
        current_point = (x, y)
        color = overlay_color if mode == "draw" else (0, 0, 0) #this sets the color to the drawing color (yellow by default) if mode is draw, else if it is erase it sets it to black
        
        if event == cv2.EVENT_LBUTTONDOWN: #if the user presses the left mouse button, drawing happens
            drawing = True
            prev_point = current_point
            cv2.circle(img, current_point, line_thickness//2, color, -1) #just pressing the left mouse button makes a small circle appear. This draws te initial point, just when the mouse is pressed
            
        elif event == cv2.EVENT_MOUSEMOVE: #this commands draws when and where the mouse moves, only if the left mouse button is pressed down (which set drawing = True)
            if drawing and prev_point:
                cv2.line(img, prev_point, current_point, color, line_thickness)
                prev_point = current_point
                cv2.imshow('Draw Missing Borders', img)
                
        elif event == cv2.EVENT_LBUTTONUP: #once the left mouse button is released, draw the last point and set draw = False
            if drawing and prev_point:
                cv2.line(img, prev_point, current_point, color, line_thickness)
            drawing = False
            prev_point = None
            cv2.imshow('Draw Missing Borders', img)

    cv2.namedWindow('Draw Missing Borders')
    cv2.setMouseCallback('Draw Missing Borders', draw_line) #this calls the draw_line function for every button action 

    print("Controls:")
    print("Press 'd' - Draw mode")
    print("Press 'e' - Erase mode")
    print("Press '+' - Increase thickness")
    print("Press '-' - Decrease thickness")
    print("Press 's' - Save image")
    print("Press 'q' - Quit")

    img = cv2.imread(img_name, cv2.IMREAD_COLOR)

    try:
        test = img_name.split("\\")[0].split("_")[2]
    except IndexError:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


    while True:

        screen_width = windll.user32.GetSystemMetrics(0)  #for scaling, so the window is screen-sized
        screen_height = windll.user32.GetSystemMetrics(1)
        
        cv2.namedWindow('Draw Missing Borders', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Draw Missing Borders', screen_width, screen_height)
        cv2.moveWindow('Draw Missing Borders', 0, 0)
        cv2.imshow('Draw Missing Borders', img)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('d'):  # Switch to draw mode
            mode = "draw"
            print("Mode: Draw")
        
        elif key == ord('e'):  # Switch to erase mode
            mode = "erase"
            print("Mode: Erase")

        elif key == ord('+'): #increase line thickness
            line_thickness = min(10, line_thickness + 1)
            print(f"Thickness: {line_thickness}")
            
        elif key == ord('-'): #decrease line thickness
            line_thickness = max(1, line_thickness - 1)
            print(f"Thickness: {line_thickness}")

        elif key == ord('q'):  # quit
            try:
                temp = grimg_name
            except Exception:
                grimg_name = None
            break
        elif key == ord('s'):  #save
            folder = Path('border_overlays_complete')
            files = [str(f) for f in folder.iterdir() if f.is_file()]
            
            #the following algorithm finds the index the file should have. if the previous file is named testX_diameters_56.csv this will output testX_diameters_57.csv
            if len(files) == 0:
                grimg_name = f"border_overlays_complete\\{img_name_n.split(".")[0]}_complete.tif"
            else:
                index = 0
                for f in files:
                    if f.split("\\")[1].split("_")[0] == img_name_i.split(".")[0]:
                        try:
                            temp = int(f.split("_")[-1].split(".")[0]) + 1
                        except ValueError:
                            index = 1
                            if len(files) == 1: break
                            else: continue    
                        temp = int(f.split("_")[-1].split(".")[0]) + 1
                        if temp > index: index = temp

                if index == 0: grimg_name = f"border_overlays_complete\\{img_name_n.split(".")[0]}_complete.tif"
                else: grimg_name = f"border_overlays_complete\\{img_name_n.split(".")[0]}_complete_{index}.tif"
            
            cv2.imwrite(grimg_name, img, [cv2.IMWRITE_TIFF_COMPRESSION, 1])

    cv2.destroyAllWindows()


    return grimg_name
