# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 12:47:41 2021

Module for extracting Guilty Gear Strive match data via video.

Current version the input video resoloution needs to be 1080x1920 & GGST game 
footage needs to be in the full frame (not as a part of the stream's overlay 
scaling it down)

@author: PDP2600
"""
import numpy as np
import cv2
import pandas as pd

#Returns a tuple w/ (minValue, maxValue, minLocation, maxLocation)
def get_match_template_score(image, template_img, template_key:str):
    #print("Checking Template key {} against frame image".format(template_key))
    templates_for_player_1_mask:list = ['1P_Portrait', '1P_No_Round_Lost', 
                                        '1P_Round_Lost']
    templates_for_player_2_mask:list = ['2P_Portrait', '2P_No_Round_Lost', 
                                        '2P_Round_Lost']
    templates_for_timer_mask:list = ['Timer_Outline']
    templates_for_round_start:list = ['Duel', 'Round_1', 'Round_2', 'Round_3', 
                                      'Round_Final', 'Number_1', 'Number_2', 
                                      'Number_3', 'Number_Final', 'Lets_Rock']
    templates_for_round_end:list = ['Win_Pose_Left', 'Win_Pose_Right', 'Slash', 
                                    'Double_KO', 'Draw', 'Perfect', 'Times_Up', 
                                    '1P_Win', '2P_Win']
    #print("Template key: {}".format(template_key))
    if template_key in templates_for_player_1_mask:
        return _get_player_1_template_score(image, template_img, template_key)
    elif template_key in templates_for_player_2_mask:
        return _get_player_2_template_score(image, template_img, template_key)
    elif template_key in templates_for_timer_mask:
        return _get_timer_template_score(image, template_img, template_key)
    elif template_key in templates_for_round_start:
        return _get_round_start_template_score(image, template_img, template_key)
    elif template_key in templates_for_round_end:
        return _get_round_end_template_score(image, template_img, template_key)
    else:
        print("Key from template dictionary {}, does not exist.".format(
                template_key))
        return (-1, -1, -1, -1)

def _get_player_1_template_score(image, template, template_key:str):
    #Template keys to utilize edge detection
    edged_keys:list = ['1P_Portrait', '1P_No_Round_Lost', '1P_Round_Lost']
    red_chan_keys:list = ['1P_No_Round_Lost', '1P_Round_Lost']
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

def _get_player_2_template_score(image, template, template_key:str):
    #Image template matching using edge detection?
    edged_keys:list = ['2P_Portrait', '2P_No_Round_Lost', '2P_Round_Lost']
    red_chan_keys:list = ['2P_No_Round_Lost', '2P_Round_Lost']
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

def _get_round_start_template_score(image, template, template_key:str):
    #Image template matching using edge detection?
    edged_keys:list = ['Number_1', 'Number_2', 'Number_3', 'Number_Final']
    red_chan_keys:list = ['Number_1', 'Number_2', 'Number_3', 'Number_Final']
    
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
def _get_round_end_template_score(image, template, template_key:str):
    #Image template matching using edge detection
    edged_keys:list = ['Win_Pose_Left', 'Win_Pose_Right']    
    
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

def _get_timer_template_score(image, template, template_key:str):
    #Template keys to utilize edge detection
    edged_keys:list = ['Timer_Outline']
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

def check_min_match_val(template_key:str, tmpl_img:dict, min_val_mappings:dict, 
                        match_val:float)->float:
    img_keys = list(min_val_mappings.keys())
    if template_key in img_keys:
        if match_val >= tmpl_img[min_val_mappings[template_key]]:
            return match_val
        else:
            return 0
    else:
        return match_val

def reorder_img_list(img_files:list)->list:
    imgs_order:dict = {}
    pre_label = "image"
    post_char = "."
    reorder_img_files:list = []
    for img_file in img_files:
        num_start = img_file.find(pre_label) + len(pre_label)
        num_end = img_file.find(post_char)
        frame_num = int(img_file[num_start : num_end])
        imgs_order[frame_num] = img_file
    for i in range(1,len(imgs_order)):
        reorder_img_files.append(imgs_order[i])
    
    return reorder_img_files

#Add the numpy image objs to the template dictionaries to reduce I/O
#These changes happen on the configure objects which are loaded
def load_tmp_imgs(template_img_dicts:list)->list:
    for template_img_dict in template_img_dicts:
        template_img_keys = list(template_img_dict['img_paths'].keys())
        for tmp_img_key in template_img_keys:
            tmp_img = cv2.imread(template_img_dict['img_paths'][tmp_img_key])
            template_img_dict['img_objs'][tmp_img_key] = tmp_img
    return template_img_dicts

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

def _detect_health_bar(frame_img)->tuple[int,int,int,int,bool]:
    (x_loc, y_loc, w_val, h_val) = (0, 0, 0, 0)
    (min_w, min_h, max_h, min_y, max_y) = (200, 15, 100, 80, 168)
    low_health:bool = False
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
                    low_health = True

    return (x_loc, y_loc, w_val, h_val, low_health)

#Creates a mask for the Player 1 side, top screen & runs the health bar detection functions
def detect_player_1_health(frame_img)->tuple[int,int]:
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
def detect_player_2_health(frame_img)->tuple[int,int]:
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
#Returns data from with the template match score results
def get_all_tmpl_scores_vid(vid_file_path:str, template_img_dicts:list, 
                            min_val_mappings:dict, frames_per_sec:int = 2):
    tmp_match_scores_df = pd.DataFrame({})
    index_num:int = 1
    seconds:float = 0
    frame_rate:float = (1 / np.clip(frames_per_sec, 1, 60))
    vidcap = cv2.VideoCapture(vid_file_path)
    vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
    hasFrame,image = vidcap.read()
    
    while hasFrame:
        print("Checking Time: {}secs, Frame: {} (in secs)... ".format(int(seconds), 
                                                                      seconds))
        tmp_match_scores:dict = {'Vid_file_name' : vid_file_path, 
                                 'Time_in_Secs' : int(seconds), 
                                 'Frame_Number_secs' : seconds}
        for template_img_dict in template_img_dicts:
            dict_name = template_img_dict['Name']
            #Creating a list of the dict keys pretaining to templateimage paths
            template_img_keys = list(template_img_dict['img_objs'].keys())
        
            for template_img_key in template_img_keys:
                #Non-edged version match score
                (minVal, maxVal, minLoc, maxLoc) = get_match_template_score(
                                    image, 
                                    template_img_dict['img_objs'][template_img_key], 
                                    template_img_key)
                col_name = "{}_{}".format(dict_name, template_img_key)
                tmp_match_scores[col_name] = check_min_match_val(template_img_key, 
                                                                 template_img_dict, 
                                                                 min_val_mappings, 
                                                                 maxVal)

        #Detecting 1P & 2P health bars, & setting the value to the width
        (high_health_1P, low_health_1P) = detect_player_1_health(image)
        (high_health_2P, low_health_2P) = detect_player_2_health(image)        
        tmp_match_scores['1P_High_Health'] = high_health_1P
        tmp_match_scores['1P_Low_Health'] = low_health_1P        
        tmp_match_scores['2P_High_Health'] = high_health_2P
        tmp_match_scores['2P_Low_Health'] = low_health_2P
        
        tmp_match_scores_df = tmp_match_scores_df.append(pd.DataFrame(
                             tmp_match_scores, index=[index_num]), sort=False)
        index_num = index_num + 1        
        seconds = seconds + frame_rate
        vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
        hasFrame,image = vidcap.read()
    
    return tmp_match_scores_df

#Used to check a list of images (with paths), against a set of template images
#Returns a data from with the template match score results
def get_all_tmpl_scores_img(img_folder:str, img_files:list, template_img_dicts:list, 
                            min_val_mappings:dict):
    tmp_match_scores_df = pd.DataFrame({})
    index_num = 1
    for img_file in img_files:
        img_path = img_folder + img_file
        tmp_match_scores:dict = {'image_file_name' : img_file}
        image = cv2.imread(img_path)
        for template_img_dict in template_img_dicts:
            dict_name = template_img_dict['Name']
            #Creating a list of the dict keys pretaining to templateimage paths
            template_img_keys = list(template_img_dict['img_objs'].keys())
        
            for img_key in template_img_keys:
                #Non-edged version match score
                (minVal, maxVal, minLoc, maxLoc) = get_match_template_score(
                                            image, 
                                            template_img_dict['img_objs'][img_key], 
                                            img_key)
                col_name = "{}_{}".format(dict_name, img_key)
                tmp_match_scores[col_name] = check_min_match_val(img_key, 
                                                                 template_img_dict, 
                                                                 min_val_mappings, 
                                                                 maxVal)
                
        #Detecting 1P & 2P health bars, & setting the value to the width
        (high_health_1P, low_health_1P) = detect_player_1_health(image)
        (high_health_2P, low_health_2P) = detect_player_2_health(image)
        
        tmp_match_scores['1P_High_Health'] = high_health_1P
        tmp_match_scores['1P_Low_Health'] = low_health_1P
        
        tmp_match_scores['2P_High_Health'] = high_health_2P
        tmp_match_scores['2P_Low_Health'] = low_health_2P
    
        tmp_match_scores_df = tmp_match_scores_df.append(pd.DataFrame(
                tmp_match_scores, index=[index_num]), sort=False)
        index_num = index_num + 1    
    return tmp_match_scores_df
