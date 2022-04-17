# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 18:02:17 2022

@author: PDP2600
"""
from pytube import YouTube
#import cv2
#import numpy as np
import os
import pandas as pd
from datetime import datetime

pd.set_option('display.max_rows', 2000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_colwidth', None)

wd_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader"
os.chdir(wd_path)
print("Start YT Download..")
total_start = datetime.now()
#NLBC 103 Top 16
#yt_vid = YouTube('https://www.youtube.com/watch?v=SEgGd-KTzZw')
#NLBC 103 Top 8
#yt_vid = YouTube('https://www.youtube.com/watch?v=1nlrWJopfKs')
#NLBC 104 Top 8 
#yt_vid = YouTube('https://www.youtube.com/watch?v=3h-l7dK2xHk')
#Frosty Faustings top 96
#yt_vid = YouTube('https://www.youtube.com/watch?v=NgTvgkzuYSs')
#E-sports Arena Week 11(Top 8?)
#yt_vid = YouTube('https://www.youtube.com/watch?v=OZMbA3p4Alo')
#Can Opener 36
#yt_vid = YouTube('https://www.youtube.com/watch?v=0qGdXGplixk')
#NLBC 106 Top 8
#yt_vid = YouTube('https://www.youtube.com/watch?v=kh2iUbKW8TI')
#E-sports Arena Week S1 Finale
#yt_vid = YouTube('https://www.youtube.com/watch?v=syviIboZ3YU')
#Tampa Never Sleeps #37 ~3hrs
#yt_vid = YouTube('https://www.youtube.com/watch?v=oeYj3kiD-zE')
#YOMI #39 ~2hrs
yt_vid = YouTube('https://www.youtube.com/watch?v=Rlmd6k6X2oY')

#1080p, Mp4
yt_vid.streams.filter(res="1080p", 
                      mime_type="video/mp4").first(
                          ).download(
                              output_path="{}\\Test_Videos\\yt_dl".format(wd_path),
                              max_retries=10)
end_time = datetime.now()
vid_delta = (end_time - total_start).seconds
print("Total download time was {} seconds".format(vid_delta))

"""
YouTube('https://youtu.be/2lAe1cqCOXo').streams.first().download()
 yt = YouTube('http://youtube.com/watch?v=2lAe1cqCOXo')
 yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download()

<Stream: itag="299" mime_type="video/mp4" res="1080p" fps="60fps" vcodec="avc1.64002a" progressive="False" type="video">
"""