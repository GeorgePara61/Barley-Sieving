import cv2
import numpy as np

def img_prep(img, kernel_gf, stdev, conval, tgs, d, sc, ss, ksize, sobel_blend, gamma, edge_preserve=True): #preproccess image

    img_corrected = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
    img_corrected = np.power(img_corrected/255.0, gamma) * 255
    img_corrected = img_corrected.astype(np.uint8)
     #1. Gaussian Blur
    denoised = cv2.GaussianBlur(img_corrected, kernel_gf, sigmaX=stdev)

    # 2. Dynamic contrast enhancement
    clahe = cv2.createCLAHE(
        clipLimit=conval,
        tileGridSize=tgs  
    )

    enhanced = clahe.apply(denoised)
    enhanced = cv2.bilateralFilter(enhanced, d=d, sigmaColor=sc, sigmaSpace=ss)

    # 3. Directional gradient enhancement
    if edge_preserve:
        sobel_x = cv2.Sobel(enhanced, cv2.CV_32F, 1, 0, ksize)
        sobel_y = cv2.Sobel(enhanced, cv2.CV_32F, 0, 1, ksize)
        gradient_mag = np.sqrt(sobel_x**2 + sobel_y**2)
        gradient_norm = cv2.normalize(gradient_mag, None, 0, 255, cv2.NORM_MINMAX)
        gradient_norm = cv2.convertScaleAbs(gradient_norm)

    else:
        sobel = cv2.Sobel(enhanced, cv2.CV_16S, 1, 1, ksize)
        gradient_norm = cv2.convertScaleAbs(sobel)

    # Edge-preserving blend
    final = cv2.addWeighted(
        enhanced, 1-sobel_blend,
        gradient_norm, sobel_blend,
        0
    )

    #final = cv2.medianBlur(final, 3)
    
    '''name = "example.tif"
    cv2.imwrite(name, final, [cv2.IMWRITE_TIFF_COMPRESSION, 5])'''

    return final
