# -*- coding: utf-8 -*-
"""
Created on Sat Sep 25 20:57:51 2021

Write the functions to be stand alone, then need to write a server version where
FGWatcher is integrated with the video extract: frame isn't saved to file, it's
used as is, has templates run against it, then a data row is generated (write 
time in seconds & the frame number to columns), etc.
    -Only doubt is how this will run with big video files, will it crash?
    -Also perfect fit for the Template stored in memory refactor, so everything
    is as efficent as you can get for low effort
-In FGWatcher, need to figure out a way to order the image files, though, the 
 server refactor would also make that logic irrelvavent 

@author: PDP2600
"""

import cv2
import os

wd_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader"
os.chdir(wd_path)

#Copy/Pasta of the sample code, will need to customize a lot, but good initially

vidcap = cv2.VideoCapture('Test_Videos\\Sept_11th-Jack-o-vs-Zato_1.mp4')
def getFrame(sec):
    vidcap.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
    hasFrames,image = vidcap.read()
    if hasFrames:
        cv2.imwrite("Vid_Ex_Tmp_Images\\Test_Cap_4fps_Nov14th\\image"+str(count)+".jpg", image)
    return hasFrames
sec = 0
frameRate = 0.25 #//it will capture image in each 0.25 second
#frameRate = 0.5 #//it will capture image in each 0.5 second
#frameRate = 1 #//it will capture image in each second
count = 1
success = getFrame(sec)
while success:
    count = count + 1
    sec = sec + frameRate
    sec = round(sec, 2)
    success = getFrame(sec)