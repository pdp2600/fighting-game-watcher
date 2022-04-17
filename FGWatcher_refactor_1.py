# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 12:47:41 2021

Refactoring the threshold scripts to function in memory & being given a video
v1.0 

Still need to add the aggregator.

After Aggregator first pass & doing optimization in detection (removing unused
template matching), split the functions off into a module for visual detection 
& use this script as a driver/example driver script for matching + aggregration

@author: PDP2600
"""

import cv2
import numpy as np
import os
import pandas as pd

wd_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader"
os.chdir(wd_path)
#import imutils
#import conf.config_values as conf

#
#Returns a tuple w/ (minValue, maxValue, minLocation, maxLocation)
def get_match_template_score(image, template_img, template_key):
    #print("Checking Template key {} against frame image".format(template_key))
    templates_for_player_1_mask_ls = ['1P_Portrait', '1P_No_Round_Lost', 
                                      '1P_Round_Lost']
    templates_for_player_2_mask_ls = ['2P_Portrait', '2P_No_Round_Lost', 
                                      '2P_Round_Lost']
    templates_for_timer_mask_ls = ['Timer_Outline']
    templates_for_round_start_ls = ['Duel', 'Round_1', 'Round_2', 'Round_3', 
                                    'Round_Final', 'Number_1', 'Number_2', 
                                    'Number_3', 'Number_Final', 'Lets_Rock']
    templates_for_duel_num_mask = []
    templates_for_round_end_ls = ['Win_Pose_Left', 'Win_Pose_Right', 'Slash', 
                                  'Double_KO', 'Draw', 'Perfect', 'Times_Up', 
                                  '1P_Win', '2P_Win']
    
    #print("Template key: {}".format(template_key))
    if template_key in templates_for_player_1_mask_ls:
        result = _get_player_1_template_score(image, template_img, template_key)
    elif template_key in templates_for_player_2_mask_ls:
        result = _get_player_2_template_score(image, template_img, template_key)
    elif template_key in templates_for_timer_mask_ls:
        result = _get_timer_template_score(image, template_img, template_key)
    elif template_key in templates_for_round_start_ls:
        result = _get_round_start_template_score(image, template_img, template_key)
    elif template_key in templates_for_duel_num_mask:
        #Width dimensions of pixel is ~32% from each side to center
        #Height is 12% from the top & 37.5% from the bottom 
        pass
    elif template_key in templates_for_round_end_ls:
        result = _get_round_end_template_score(image, template_img, template_key)
    else:
        print("Key from template dictionary {}, does not exist.".format(
                template_key))
        return (-1, -1, -1, -1)    
    #result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    ##result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF)
    return result

def _get_player_1_template_score(image, template, template_key):
    #Template keys to utilize edge detection
    edged_keys = ['1P_Portrait', '1P_No_Round_Lost', '1P_Round_Lost']
    red_chan_keys = ['1P_No_Round_Lost', '1P_Round_Lost']
    img_h, img_w = image.shape[0:2]

    #Creating mask for Player 1 top screen
    mask = np.zeros(image.shape[:2], dtype="uint8")
    cv2.rectangle(mask, (0, 0), (img_w // 2, round(img_h * 0.20)), 255, -1)
            
    if template_key in red_chan_keys:
        #Saving a grayscale image from the red channel of the colour image
        image = image[:,:,2]
        template = template[:,:,2]
    else:
        #Converting template & image to grayscale & applying mask to image
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)    
        
    #Applying mask to the converted image
    masked = cv2.bitwise_and(image, image, mask=mask)
    
    #convert template & image to edges
    if template_key in edged_keys:
        masked = cv2.Canny(masked, 50, 200)
        template = cv2.Canny(template, 50, 200)
    
    result = cv2.matchTemplate(masked, template, cv2.TM_CCOEFF_NORMED)
    #result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF)
    return cv2.minMaxLoc(result)

def _get_player_2_template_score(image, template, template_key):
    #Image template matching using edge detection?
    edged_keys = ['2P_Portrait', '2P_No_Round_Lost', '2P_Round_Lost']
    red_chan_keys = ['2P_No_Round_Lost', '2P_Round_Lost']
    img_h, img_w = image.shape[0:2]
    
    #Creating mask for Player 2 top screen
    mask = np.zeros(image.shape[:2], dtype="uint8")
    cv2.rectangle(mask, ((img_w // 2) + 1, 0), (img_w, round(img_h * 0.20)), 255, -1)
    
    if template_key in red_chan_keys:
        #Saving a grayscale image from the red channel of the colour image
        image = image[:,:,2]
        template = template[:,:,2]
    else:
        #Converting template & image to grayscale & applying mask to image
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)    
    
    #Applying mask to the converted image
    masked = cv2.bitwise_and(image, image, mask=mask)    
    
    #convert template & image to edges
    if template_key in edged_keys:
        masked = cv2.Canny(masked, 50, 200)
        template = cv2.Canny(template, 50, 200)
    
    result = cv2.matchTemplate(masked, template, cv2.TM_CCOEFF_NORMED)
    #result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF)
    return cv2.minMaxLoc(result)

def _get_round_start_template_score(image, template, template_key):
    #Image template matching using edge detection?
    #Oct 1st Testing numbers with Edge also
    edged_keys = ['Number_1', 'Number_2', 'Number_3', 'Number_Final']
    red_chan_keys = ['Number_1', 'Number_2', 'Number_3', 'Number_Final']
    
    if template_key in red_chan_keys:
        #Saving a grayscale image from the red channel of the colour image
        image = image[:,:,2]
        template = template[:,:,2]
    else:
        #Converting template & image to grayscale & applying mask to image
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)    
    
    #convert template & image to edges
    if template_key in edged_keys:
        image = cv2.Canny(image, 50, 200)
        template = cv2.Canny(template, 50, 200)
    
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    #result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF)
    return cv2.minMaxLoc(result)

#Currently the most vanilla type of score
def _get_round_end_template_score(image, template, template_key):
    #Image template matching using edge detection?
    edged_keys = ['Win_Pose_Left', 'Win_Pose_Right']
    
    #Converting template & image to grayscale & applying mask to image
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)    
    
    #convert template & image to edges
    if template_key in edged_keys:
        image = cv2.Canny(image, 50, 200)
        template = cv2.Canny(template, 50, 200)
    
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    #result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF)
    return cv2.minMaxLoc(result)

def _get_timer_template_score(image, template, template_key):
    #Template keys to utilize edge detection
    edged_keys = ['Timer_Outline']
    img_h, img_w = image.shape[0:2]

    #Creating mask for top center screen (where the timer is)
    mask = np.zeros(image.shape[:2], dtype="uint8")
    center_w = img_w // 2
    half_timer = round(img_w * 0.045)
    cv2.rectangle(mask, (center_w - half_timer, 0), (center_w + half_timer, 
                                                     round(img_h * 0.22)), 255, -1)            
    #Converting template & image to grayscale & applying mask to image
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)    
        
    #Applying mask to the converted image
    masked = cv2.bitwise_and(image, image, mask=mask)
    
    #convert template & image to edges
    if template_key in edged_keys:
        masked = cv2.Canny(masked, 50, 200)
        template = cv2.Canny(template, 50, 200)
    
    result = cv2.matchTemplate(masked, template, cv2.TM_CCOEFF_NORMED)
    #result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF)
    return cv2.minMaxLoc(result)

def check_min_match_val(template_key, template_img_dict, min_val_mappings_dict, 
                           match_val):
    img_keys = list(min_val_mappings_dict.keys())
    if template_key in img_keys:
        if match_val >= template_img_dict[min_val_mappings_dict[template_key]]:
            return match_val
        else:
            return 0
    else:
        return match_val

def reorder_img_list(img_files_ls):
    imgs_order_dict = {}
    pre_label = "image"
    post_char = "."
    reorder_img_files_ls = []
    for img_file in img_files_ls:
        num_start = img_file.find(pre_label) + len(pre_label)
        num_end = img_file.find(post_char)
        frame_num = int(img_file[num_start : num_end])
        imgs_order_dict[frame_num] = img_file
    for i in range(1,len(imgs_order_dict)):
        reorder_img_files_ls.append(imgs_order_dict[i])
    
    return reorder_img_files_ls

#Add the numpy image objs to the template dictionaries to reduce I/O
#These changes happen on the configure objects which are loaded
def load_tmp_imgs(template_img_dicts_ls):
    for template_img_dict in template_img_dicts_ls:
        template_img_keys = list(template_img_dict['img_paths'].keys())
        for tmp_img_key in template_img_keys:
            tmp_img = cv2.imread(template_img_dict['img_paths'][tmp_img_key])
            template_img_dict['img_objs'][tmp_img_key] = tmp_img
    return template_img_dicts_ls

def _high_health_detect(frame_img):
    high_health_lower = np.array([135,100,225])
    high_health_upper = np.array([183,224,255])

    mask = cv2.inRange(frame_img, high_health_lower, high_health_upper)
    health_bars = cv2.bitwise_and(frame_img,frame_img, mask= mask)
    gray = cv2.cvtColor(health_bars, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)[1]
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    #Find Horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35,2))
    detect_horizontal = cv2.morphologyEx(close, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    cnts = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    
    return cnts

def _low_health_detect(frame_img):
    low_health_lower = np.array([2,145,225])
    low_health_upper = np.array([20,155,240])

    mask = cv2.inRange(frame_img, low_health_lower, low_health_upper)
    health_bars = cv2.bitwise_and(frame_img,frame_img, mask= mask)
    gray = cv2.cvtColor(health_bars, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)[1]
        
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    #Find Horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35,2))
    detect_horizontal = cv2.morphologyEx(close, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    cnts = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    
    if len(cnts) == 0:
        cnts = cv2.findContours(close, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    
    return cnts

def _detect_health_bar(frame_img):
    (x_loc, y_loc, w_val, h_val) = (0, 0, 0, 0)
    #March 23 changed min_w to 200 from 230 for case where health not detected
    #March 24th added max_h value for high health to reduce false positives
    (min_w, min_h, max_h, min_y, max_y) = (200, 15, 100, 80, 168)
    low_health_bool = False
    
    high_health_contours = _high_health_detect(frame_img)
    
    #Check for high health first
    for c in high_health_contours:
        #cv2.drawContours(image, [c], -1, (36,255,12), -1)
        #Looks like these are the values to use to confirm a health bar
        x1, y1, w1, h1 = cv2.boundingRect(c)
        if w1 >= min_w and h1 >= min_h and h1 <= max_h and y1 < max_y and y1 > min_y:
            if w1 > w_val:
                (x_loc, y_loc, w_val, h_val) = (x1, y1, w1, h1)
                
    #If no high health found, check for low health    
    if w_val == 0:
        low_health_contours = _low_health_detect(frame_img)
        (x_loc, y_loc, w_val, h_val) = (0, 0, 0, 0)
        #For low health
        (min_w, min_h, min_y, max_y) = (1, 15, 80, 168)
        for c in low_health_contours:
            x1, y1, w1, h1 = cv2.boundingRect(c)
            if w1 >= min_w and h1 >= min_h and y1 < max_y and y1 > min_y:
                if w1 > w_val:
                    (x_loc, y_loc, w_val, h_val) = (x1, y1, w1, h1)
                    low_health_bool = True

    return (x_loc, y_loc, w_val, h_val, low_health_bool)

#Creates a mask for the Player 1 side, top screen & runs the health bar detection functions
def detect_player_1_health(frame_img):
    img_h, img_w = frame_img.shape[0:2]

    #Creating mask for Player 1 top screen
    mask_P1 = np.zeros(frame_img.shape[:2], dtype="uint8")
    cv2.rectangle(mask_P1, (0, 0), (img_w // 2, round(img_h * 0.20)), 255, -1)

    masked_P1 = cv2.bitwise_and(frame_img, frame_img, mask=mask_P1)
    (x_P1, y_P1, w_P1, h_P1, isLowHealthP1) = _detect_health_bar(masked_P1)
    
    if isLowHealthP1:
        high_health = 0
        low_health = w_P1
    else:
        high_health = w_P1
        low_health = 0
    
    return (high_health, low_health)
    
#Creates a mask for the Player 2 side, top screen & runs the health bar detection functions
def detect_player_2_health(frame_img):
    img_h, img_w = frame_img.shape[0:2]
    
    #Creating mask for Player 2 top screen
    mask_P2 = np.zeros(frame_img.shape[:2], dtype="uint8")
    cv2.rectangle(mask_P2, ((img_w // 2) + 1, 0), (img_w, round(img_h * 0.20)), 255, -1)
    
    masked_P2 = cv2.bitwise_and(frame_img, frame_img, mask=mask_P2)
    (x_P2, y_P2, w_P2, h_P2, isLowHealthP2) = _detect_health_bar(masked_P2)
    
    if isLowHealthP2:
        high_health = 0
        low_health = w_P2
    else:
        high_health = w_P2
        low_health = 0
    
    return (high_health, low_health)

#Used to check a video, against a set of template images
#Returns a data from with the template match score results
def get_all_tmpl_scores_vid(vid_file_path, template_img_dicts_ls, 
                            min_val_mappings_dict, frames_per_sec = 4):
    tmp_match_scores_df = pd.DataFrame({})
    index_num = 1
    seconds = 0
    #Frames_per_second min 1 fps & max 60 fps
    frame_rate = (1 / np.clip(frames_per_sec, 1, 60))
    
    vidcap = cv2.VideoCapture(vid_file_path)
    vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
    hasFrame,image = vidcap.read()
    
    while hasFrame:
        print("Checking Time: {}secs, Frame: {} (in secs)... ".format(int(seconds), seconds))
        tmp_match_scores_dict = {'Vid_file_name' : vid_file_path, 
                                 'Time_in_Secs' : int(seconds), 
                                 'Frame_Number_secs' : seconds
                                 }
        for template_img_dict in template_img_dicts_ls:
            dict_name = template_img_dict['Name']
            #Creating a list of the dict keys pretaining to templateimage paths
            template_img_keys = list(template_img_dict['img_objs'].keys())
        
            for template_img_key in template_img_keys:
                #Non-edged version match score
                (minVal, maxVal, minLoc, maxLoc) = get_match_template_score(
                                    image, 
                                    template_img_dict['img_objs'][template_img_key], 
                                    template_img_key)
                score_column_name = "{}_{}".format(dict_name, template_img_key)
                tmp_match_scores_dict[score_column_name] = check_min_match_val(
                                                        template_img_key, 
                                                        template_img_dict, 
                                                        min_val_mappings_dict, 
                                                        maxVal)
        
        #Detecting 1P & 2P health bars, & setting the value to the width
        (high_health_1P, low_health_1P) = detect_player_1_health(image)
        (high_health_2P, low_health_2P) = detect_player_2_health(image)
        
        tmp_match_scores_dict['1P_High_Health'] = high_health_1P
        tmp_match_scores_dict['1P_Low_Health'] = low_health_1P
        
        tmp_match_scores_dict['2P_High_Health'] = high_health_2P
        tmp_match_scores_dict['2P_Low_Health'] = low_health_2P
        
        tmp_match_scores_df = tmp_match_scores_df.append(pd.DataFrame(
                tmp_match_scores_dict, index=[index_num]), sort=False)
        index_num = index_num + 1
        
        seconds = seconds + frame_rate
        vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
        hasFrame,image = vidcap.read()
    
    return tmp_match_scores_df

#Used to check a list of images (with paths), against a set of template images
#Returns a data from with the template match score results
def get_all_tmpl_scores_img(img_folder, img_files_ls, template_img_dicts_ls, 
                            min_val_mappings_dict):
    tmp_match_scores_df = pd.DataFrame({})
    index_num = 1
    for img_file in img_files_ls:
        img_path = img_folder + img_file
        tmp_match_scores_dict = {'image_file_name' : img_file}
        image = cv2.imread(img_path)
        for template_img_dict in template_img_dicts_ls:
            dict_name = template_img_dict['Name']
            #Creating a list of the dict keys pretaining to templateimage paths
            template_img_keys = list(template_img_dict['img_objs'].keys())
        
            for template_img_key in template_img_keys:
                #Non-edged version match score
                (minVal, maxVal, minLoc, maxLoc) = get_match_template_score(
                                    image, 
                                    template_img_dict['img_objs'][template_img_key], 
                                    template_img_key)
                score_column_name = "{}_{}".format(dict_name, template_img_key)
                tmp_match_scores_dict[score_column_name] = check_min_match_val(
                                                        template_img_key, 
                                                        template_img_dict, 
                                                        min_val_mappings_dict, 
                                                        maxVal)
                
        #Detecting 1P & 2P health bars, & setting the value to the width
        (high_health_1P, low_health_1P) = detect_player_1_health(image)
        (high_health_2P, low_health_2P) = detect_player_2_health(image)
        
        tmp_match_scores_dict['1P_High_Health'] = high_health_1P
        tmp_match_scores_dict['1P_Low_Health'] = low_health_1P
        
        tmp_match_scores_dict['2P_High_Health'] = high_health_2P
        tmp_match_scores_dict['2P_Low_Health'] = low_health_2P
    
        tmp_match_scores_df = tmp_match_scores_df.append(pd.DataFrame(
                tmp_match_scores_dict, index=[index_num]), sort=False)
        index_num = index_num + 1
    
    return tmp_match_scores_df


"""
from datetime import datetime
start_time = datetime.now()
#Loading template images & storing them in memory
conf.templ_img_dicts_ls = load_tmp_imgs(conf.templ_img_dicts_ls)
video_path = "Test_Videos\\GuiltyGear-Strive_Baike-vs-Millia_2_Low_Health_for_While-2022-02-02.mp4"
fps_val = 4
all_templ_match_scores_df = get_all_tmpl_scores_vid(video_path,  
                                                    conf.templ_img_dicts_ls, 
                                                    conf.templ_img_min_val_mappings, 
                                                    frames_per_sec = fps_val)

all_templ_match_scores_df.to_csv('Baiken_vs_Millia_4fps_Low_Health-2022-02-03.csv')
#'Baiken_mirror_4fps_Perfect-2022-02-03.csv'
#'HC_Faust_double_Timeout_draw_FInal_round-2022-01-27.csv'
#'Benchmark_4FPS_Vid_Test_1_Jack-O-Zato_Nov_13th_2021.csv'
#'Vid_4FPS_Off_Video_Test_2_Jack-O-Ky_Nov_13th_2021.csv'

end_time = datetime.now()
vid_delta = (end_time - start_time).seconds
print("Total processing time was {} seconds (video source)".format(vid_delta))

##Implement a function to extract images from video & make it an optional path
##for this flow 
#####Old code using a folder full of the images to detect templates with 
from datetime import datetime
start_time = datetime.now()
#Parent folder of template images
template_img_folder = "template_imgs\\"
#Location of test images
#img_folder = "GGStrive_Raw_Imgs_v1\\"
img_folder = "Vid_Ex_Tmp_Images\\Test_Cap_4fps\\"
img_files_ls = os.listdir(img_folder)
#Removing files which are not .jpg, .png, or .jpeg
img_files_ls = [x for x in img_files_ls if x.endswith(".jpg") or 
                x.endswith(".png") or x.endswith(".jpeg")]

#Reordering for the temp video extract img filename format
img_files_ls = reorder_img_list(img_files_ls)

#conf.templ_img_dicts_ls = load_tmp_imgs(conf.templ_img_dicts_ls)


all_templ_match_scores_df = get_all_tmpl_scores_img(img_folder, img_files_ls, 
                                                    conf.templ_img_dicts_ls, 
                                                    conf.templ_img_min_val_mappings)

all_templ_match_scores_df.to_csv('Health_bar_4FPS_Img_Test_2_Jack-O-Zato_Dec_18th_2021.csv')

end_time = datetime.now()
img_delta = (end_time - start_time).seconds
print("Total processing time was {} seconds (img file source)".format(img_delta))

print("\nVideo process Delta {}secs vs Image process Delta {}secs".format(vid_delta, img_delta))

"""
#####

##Sept 14th
#-Write video to image functions (no YouTube support, write that after the aggregator)
#-Test those images with the threshold test, but implement storing images as
#numpy objects for templates ASAP to reduce the number of disk loads
#-Implement this script into a more final version (driver & more split module files)
#-Start writing the aggregation related functions:
##First find the round start and end indicators
###Probably need to figure out how to handle all the case wher template is accross multiple frames
##Then can use aggregration tricks for the data rows between those, by creating
## a dataframe of booleans, then can sum competing columns to see which is most likely
## and even have a "confidence score" (number of frames are true divided by total rows)

##July 21st
#Re-write the methods to be more efficent with the image loading & conversion
#Duel/Round detection has a lot of issues w/ detecting the specific round shown
##Is this a candidate for a more complex detection method? I can try re-making the
##template asset (& include some of the inkblot to the number to see if that helps)
#Need to implement the Left/Right Win pose images too (add to dict, images are created)
#When this stuff seems in an ok state, start on the timer stuff and benchmarking

#Implement stopping template checks when certain templates ar confirmed win poses for sure,
##maybe all the enders (some will still show portraits/time, but with an out of focus filter)
##Note: enders like TIme out and DOuble KO, will also follow with Draw (I think Time out isn't gauranteed a draw)

#test_123 = "_".join(["1", "2", "3"])

"""
#Example function call
(minVal, maxVal, minLoc, maxLoc) = get_match_template_score(
        "GGStrive_Raw_Imgs_v1\\Ky_Millia_Timer_98.jpg", 
        ramlethal_template_imgs['P1_portrait'], edged = True)



#Creating a 300 x 300 martix, with 3 layers, the layer emulate colour channels
canvas = np.zeros((300, 300, 3), dtype = "uint8")
"""
"""
##For testing out image manipulation, to check it visually
#img_path = 'GGStrive_Raw_Imgs_v1\\Zato_Sol_Timer_96.jpg'
img_path = 'D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader\\Old_Files_Mar2022\\GGStrive_Raw_Imgs_v1\\Zato_Sol_Timer_96.jpg'
template_img_path = 'GGStrive_Template_imgs_v2\\Round_Starters\\Duel_1.png'
image = cv2.imread(img_path)
template = cv2.imread(template_img_path)    
img_h, img_w = image.shape[0:2]
mask = np.zeros(image.shape[:2], dtype="uint8")
#cv2.rectangle(mask, (0, 0), (img_w // 2, round(img_h * 0.20 )), 255, -1)
center_w = img_w // 2
half_timer = round(img_w * 0.045)
cv2.rectangle(mask, (center_w - half_timer, 0), (center_w + half_timer, 
                                                 round(img_h * 0.22)), 255, -1)

#cv2.rectangle(mask, ((img_w // 2) + 1, 0), (img_w, round(img_h * 0.20)), 255, -1)    
    #Converting to gray scale
image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
masked = cv2.bitwise_and(image, image, mask=mask)
template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)    
#just resizing because the images are too big for the screen to display
masked = cv2.resize(masked, (0,0), fx=0.5, fy=0.5)
#masked = cv2.Canny(masked, 50, 200)
cv2.imshow("Canvas", masked)
cv2.waitKey(0)
cv2.destroyAllWindows()
"""
"""
    #If the function was called to template match edged version, imgs are converted
if edged is True:
    masked = cv2.Canny(masked, 50, 200)
    template = cv2.Canny(template, 50, 200)
"""
    
"""
cv2.imshow("Canvas", canvas)
cv2.waitKey(0)
cv2.destroyAllWindows()
"""