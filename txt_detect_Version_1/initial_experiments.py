# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 14:04:42 2019

@author: PDP2600
"""
from imutils.object_detection import non_max_suppression
import numpy as np
import cv2
#import tesserocr
import pytesseract
import argparse
import os
#Set to location of this file which should be the same location twitter_api.py is in too
dir_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader"
os.chdir(dir_path)




##May need to first mess around with the code used to get this function's input
##values to better understand the expected format of the data and to better
##understand what's being done
def decode_predictions(scores, geometry):
	#Extracting the "Height" (rows) & "Width" (columns) from the confidence 
    #score array from the EAST model layer: 'feature_fusion/Conv_7/Sigmoid'
    ##I believe the socres & geometry (which is an output from another layer)
    ##arrays share the same H & W dimensions, so it's only grabbed from scores
	#Initialize empty lists to collect the bounding boxes & their confidences
	(numRows, numCols) = scores.shape[2:4]
	boxes = []
	confidences = []

	#Iterating through each row of the data matrices
	for y in range(0, numRows):
		# extract the scores (probabilities), followed by the
		# geometrical data used to derive potential bounding box
		# coordinates that surround text
		scoresData = scores[0, 0, y]
		xHeight0 = geometry[0, 0, y]
		xWidth1 = geometry[0, 1, y]
		xHeight2 = geometry[0, 2, y]
		xWidth3 = geometry[0, 3, y]
		anglesData = geometry[0, 4, y]

		#Iterating through each column of the data matrices
		for x in range(0, numCols):
			#If current score does not have high enough probability, skip it
			if scoresData[x] < args["min_confidence"]:
				continue

			# compute the offset factor as our resulting feature
			# maps will be 4x smaller than the input image
			(offsetX, offsetY) = (x * 4.0, y * 4.0)

			# extract the rotation angle for the prediction and
			# then compute the sin and cosine
			angle = anglesData[x]
			cos = np.cos(angle)
			sin = np.sin(angle)

			# use the geometry volume to derive the width and height
			# of the bounding box
			h = xHeight0[x] + xHeight2[x]
			w = xWidth1[x] + xWidth3[x]

			# compute both the starting and ending (x, y)-coordinates
			# for the text prediction bounding box
			endX = int(offsetX + (cos * xWidth1[x]) + (sin * xHeight2[x]))
			endY = int(offsetY - (sin * xWidth1[x]) + (cos * xHeight2[x]))
			startX = int(endX - w)
			startY = int(endY - h)

			# add the bounding box coordinates and probability score
			# to our respective lists
			boxes.append((startX, startY, endX, endY))
			confidences.append(scoresData[x])

	# return a tuple of the bounding boxes and associated confidences
	return (boxes, confidences)
