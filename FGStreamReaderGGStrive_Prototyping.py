# -*- coding: utf-8 -*-
"""
Created on Sat May 29 18:24:43 2021

@author: PDP2600
"""
import cv2
import numpy as np
import os

wd_path = "D:\\Libraries\\Documents\\Data_Science\\Learning\\PyImageSearchBooks\\Practical Python and OpenCV\\My_Code"
os.chdir(wd_path)

#img_path = "images\\trex.png"
#image = cv2.imread(img_path)

#Creating a 300 x 300 martix, with 3 layers, the layer emulate colour channels
canvas = np.zeros((300, 300, 3), dtype = "uint8")

