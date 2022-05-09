# -*- coding: utf-8 -*-
"""
Created on Sun May  8 19:04:15 2022

Fighting Game Watcher example script for running layered extract & aggregation 
processing function.

@author: PDP2600
"""
import os
#Only works when this python file is run or run/imported by another python file
#wd_path = os.path.dirname(__file__)
wd_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader"
os.chdir(wd_path)
import conf.config_values as conf
import modules.ggst.controller as ctrl

def _print_processing_stats(processing_stats:list):
    for video_stat in processing_stats:
        process_ratio = video_stat['Processing_Time'] / video_stat['Vid_Length']
        
        print("Video: {}\n".format(video_stat['Vid_Name']))
        print("Processing Time: {}(s)  |  Video Length: {}(s)  |  Processing Ratio: {}\n"
              .format(video_stat['Processing_Time'], video_stat['Vid_Length'], 
                      process_ratio))
        print("Output Folder: {}".format(video_stat['Output_Folder']))
        print("Video Path: {}\n".format(video_stat['Vid_Path']))
        print("---------------------------------------------------------------\n")

#fps_val = 4
fps_val = 2

#########
##Batch process a directory of videos 
#Full path to be prepended to the video folder & file name
vid_dir = 'D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader'
#videos:list = os.listdir(vid_dir)
videos:list = []
processing_stats:list = []

videos.append('Test_Videos\\GGST-My-Day_2_Testament_matches_18mins-2022-03-29 17-39-38.mp4')
#videos.append('Test_Videos\\yt_dl\\Series E S1 FINALE.mp4')
#videos.append('Test_Videos\\My_Baiken_Matches_90_mins_2022-03-13_16-01-57.mp4')
#Recentish NLBC from YT, ~40mins
videos.append('Test_Videos\\yt_dl\\NLBC 103 Top 16  Online  Tournament.mp4')
#videos.append('Test_Videos\\yt_dl\\NLBC 106 Top 8 Online Tournament.mp4')
#videos.append('Test_Videos\\yt_dl\\NLBC 104 Top 8  Online  Tournament.mp4')
#videos.append('Test_Videos\\yt_dl\\NLBC 103 Top 8  Online  Tournament.mp4')
#videos.append('Test_Videos\\yt_dl\\Can Opener Vol 36 GGST.mp4')
#videos.append('Test_Videos\\yt_dl\\Series E Sports Arena Week 11.mp4')
#videos.append('Test_Videos\\yt_dl\\Frosty Faustings 2022 - Top 96.mp4')

for video in videos:
    vid_path:str = "{}\\{}".format(vid_dir, video)
    processing_data:dict = {}
    fpath, ptime, vlen = ctrl.layered_extract_and_aggregate_video(vid_path, 
                                                                  fps_val, conf, 
                                                                  verbose_log=
                                                                  True)
    processing_data['Vid_Name'] = video.split('\\')[-1].split('.')[0]
    processing_data['Vid_Path'] = vid_path
    processing_data['Processing_Time'] = int(ptime)
    processing_data['Vid_Length'] = int(vlen)
    processing_data['Output_Folder'] = fpath
    processing_stats.append(processing_data)
    print("Output files located in the created folder: {}".format(fpath))

_print_processing_stats(processing_stats)