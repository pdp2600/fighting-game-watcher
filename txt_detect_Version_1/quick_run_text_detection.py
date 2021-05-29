# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 10:56:17 2019

@author: PDP2600
"""
import numpy as np
import cv2
import argparse
import os
from imutils.object_detection import non_max_suppression
import time
#Set to location of this file which should be the same location twitter_api.py is in too
dir_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader"
os.chdir(dir_path)

######################################
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", type=str,
	help="path to input image")
ap.add_argument("-east", "--east", type=str,
	help="path to input EAST text detector")
ap.add_argument("-c", "--min-confidence", type=float, default=0.5,
	help="minimum probability required to inspect a region")
ap.add_argument("-w", "--width", type=int, default=320,
	help="resized image width (should be multiple of 32)")
ap.add_argument("-e", "--height", type=int, default=320,
	help="resized image height (should be multiple of 32)")
args = vars(ap.parse_args())
######################################
#modelHeight = 960
#modelWidth = 960
modelHeight = 736
modelWidth = 1280
minConfidenceScore = 0.2

text_rec_net = cv2.dnn.readNet('frozen_east_text_detection.pb')
img_path = "test_imgs\\MK11_Defend_the_North_720_resize_02.jpg"
image_1 = cv2.imread(img_path)
orig_img_1 = image_1.copy()
(Height, Width) = image_1.shape[:2]
rW = Width / float(modelWidth)
rH = Height / float(modelHeight)

#Test Image filtering#
retVal, image_1 = cv2.threshold(image_1,127,255,cv2.THRESH_BINARY_INV)

image_1 = cv2.cvtColor(image_1, cv2.COLOR_BGR2GRAY)
# Apply dilation and erosion to remove some noise
kernel = np.ones((1, 1), np.uint8)
image_1 = cv2.dilate(image_1, kernel, iterations=1)
image_1 = cv2.erode(image_1, kernel, iterations=1)

#image_1 = cv2.adaptiveThreshold(cv2.medianBlur(image_1, 7), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
#image_1 = cv2.adaptiveThreshold(cv2.medianBlur(image_1, 5), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
#retVal, image_1 = cv2.threshold(image_1,127,255,cv2.THRESH_BINARY_INV)

cv2.imshow("Filter Results", image_1)
cv2.waitKey(500)
#cv2.destroyAllWindows()
######################

image_1 = cv2.resize(image_1, (modelWidth, modelHeight))
(H, W) = image_1.shape[:2]

#For processing grayscale/Black & WHite images with single channels
image_1 =  cv2.merge((image_1,image_1,image_1))

img_blobbed = cv2.dnn.blobFromImage(image_1, 1.0, (W, H), 
                                   (123.68, 116.78, 103.94), True, False)
outputLayers = []
outputLayers.append("feature_fusion/Conv_7/Sigmoid")
outputLayers.append("feature_fusion/concat_3")

text_rec_net.setInput(img_blobbed)
text_rec_output = text_rec_net.forward(outputLayers)
scores = text_rec_output[0]
geometry = text_rec_output[1]
####################################
(numRows, numCols) = scores.shape[2:4]
rects = []
confidences = []
 
# loop over the number of rows
for y in range(0, numRows):
	# extract the scores (probabilities), followed by the geometrical
	# data used to derive potential bounding box coordinates that
	# surround text
	scoresData = scores[0, 0, y]
	xData0 = geometry[0, 0, y]
	xData1 = geometry[0, 1, y]
	xData2 = geometry[0, 2, y]
	xData3 = geometry[0, 3, y]
	anglesData = geometry[0, 4, y]

	for x in range(0, numCols):
		# if our score does not have sufficient probability, ignore it
		if scoresData[x] < minConfidenceScore:
			continue
 
		# compute the offset factor as our resulting feature maps will
		# be 4x smaller than the input image
		(offsetX, offsetY) = (x * 4.0, y * 4.0)
 
		# extract the rotation angle for the prediction and then
		# compute the sin and cosine
		angle = anglesData[x]
		cos = np.cos(angle)
		sin = np.sin(angle)
 
		# use the geometry volume to derive the width and height of
		# the bounding box
		h = xData0[x] + xData2[x]
		w = xData1[x] + xData3[x]
 
		# compute both the starting and ending (x, y)-coordinates for
		# the text prediction bounding box
		endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
		endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
		startX = int(endX - w)
		startY = int(endY - h)
 
		# add the bounding box coordinates and probability score to
		# our respective lists
		rects.append((startX, startY, endX, endY))
		confidences.append(scoresData[x])

boxes = non_max_suppression(np.array(rects), probs=confidences)
 
# loop over the bounding boxes
for (startX, startY, endX, endY) in boxes:
	# scale the bounding box coordinates based on the respective
	# ratios
	startX = int(startX * rW)
	startY = int(startY * rH)
	endX = int(endX * rW)
	endY = int(endY * rH)
 
	# draw the bounding box on the image
	cv2.rectangle(orig_img_1, (startX, startY), (endX, endY), (0, 255, 0), 2)
 
# show the output image
cv2.imshow("Text Detection", orig_img_1)
cv2.waitKey(0)
cv2.destroyAllWindows()