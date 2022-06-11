# -*- coding: utf-8 -*-
"""
Created on Sun May  8 19:04:15 2022

Fighting Game Watcher example script for running layered extract & aggregation 
processing function. 

Writen to be able to batch process multiple video files.

@author: PDP2600
"""
import os
wd_path = os.path.dirname(__file__)
#If running code from IDE & not by running the file via command line, uncomment 
#& put full path of FGC_Stream_Reader directory below so it can be set as the 
#working dir manually.
#wd_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader"
os.chdir(wd_path)
#Below Imports rely on the correct working directory being set
import conf.config_values as conf
import modules.ggst.controller as ctrl

def _print_processing_stats(processing_stats:list):
    print("---------------------------------------------------------------")
    for video_stat in processing_stats:
        process_ratio = video_stat['Processing_Time'] / video_stat['Vid_Length']
        
        print("Video: {}".format(video_stat['Vid_Name']))
        print("Processing Time: {}(s)  |  Video Length: {}(s)  |  Processing Ratio: {}"
              .format(video_stat['Processing_Time'], video_stat['Vid_Length'], 
                      process_ratio))
        print("Output Folder: {}".format(video_stat['Output_Folder']))
        print("Video Path: {}".format(video_stat['Vid_Path']))
        print("---------------------------------------------------------------\n")

def main():
    #fps_val = 4
    fps_val = 2

    vid_dir = wd_path
    videos:list = []
    processing_stats:list = []
    
    videos.append("{}\\demo_video\\FGW-12min-Demo_May-31-2022.mp4".format(vid_dir))
    #videos.append("D:\\full\\path\\to\\video_file.mp4")

    for video in videos:
        vid_path:str = video
        processing_data:dict = {}
        fpath, ptime, vlen = ctrl.layered_extract_and_aggregate_video(vid_path, 
                                                                      fps_val, 
                                                                      conf, 
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

if __name__ == "__main__":
    main()