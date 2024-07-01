import cv2 as cv
import os
import numpy as np

def check_image_orientation(img_path:str):
    images = os.listdir(img_path)

    for img in images:
        img = cv.imread(os.path.join(img_path, img))
        height, width, _ = img.shape
        if height > width:
            print(f"{img_path}/{img} is bigger vertically than horizontally.")
        else:
           pass 