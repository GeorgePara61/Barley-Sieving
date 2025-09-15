import cv2

def crop_img(img_name, crop): #it crops the bottom 69 pixels of the image, which, in the images this program is intented for, is the bar that gives sem settings and scale. It can't be changed externally or in the executable

    img_path = f"images\\{img_name}"
    img = cv2.imread(img_path)
    height, width = img.shape[:2]
    cropped = img[:height - crop, :]

    return cropped

