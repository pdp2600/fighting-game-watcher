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

def get_match_template_score(image, template_img, template_key:str):
    """Based on the template image's key & the type of image it is, will call 
    a specific function which is tuned to most accurately match templates of 
    that category.
    -------------------------------------------------------------------------
    -=image=- Frame image to check, read in using OpenCV (numpy image object)
    -=template_img=- Template image, read in using OpenCV (numpy image object)
    -=template_key=- The key used to identify the template image name
    -------------------------------------------------------------------------
    [-return-] When a valid result, is a tuple:
               (minimum match value:float, maximum match value:float, 
                (min val x:int, min val y:int), (max val x:int, max val y:int))
               When an invalid result is (-1, -1, -1, -1)"""
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
    """Used for getting match score of template images meant to match on the 
    top Player 1 side (left) of the frame image.
    -------------------------------------------------------------------------
    -=image=- Frame image to check, read in using OpenCV (numpy image object)
    -=template_img=- Template image, read in using OpenCV (numpy image object)
    -=template_key=- The key used to identify the template image name
    -------------------------------------------------------------------------
    [-return-] When a valid result, is a tuple:
               (minimum match value:float, maximum match value:float, 
                (min val x:int, min val y:int), (max val x:int, max val y:int))"""
    edged_keys:list = ['1P_Portrait', '1P_No_Round_Lost', '1P_Round_Lost']
    red_chan_keys:list = ['1P_No_Round_Lost', '1P_Round_Lost']
    img_h, img_w = image.shape[0:2]
    #Creating mask for Player 1 top part of screen
    mask = np.zeros(image.shape[:2], dtype="uint8")
    cv2.rectangle(mask, (0, 0), (img_w // 2, round(img_h * 0.20)), 255, -1)
            
    if template_key in red_chan_keys:
        #Creating grayscale images based on the red channels of each image
        image = image[:,:,2]
        template = template[:,:,2]
    else:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)    

    masked = cv2.bitwise_and(image, image, mask=mask)
    if template_key in edged_keys:
        #convert images to edges
        masked = cv2.Canny(masked, 50, 200)
        template = cv2.Canny(template, 50, 200)
    
    result = cv2.matchTemplate(masked, template, cv2.TM_CCOEFF_NORMED)
    return cv2.minMaxLoc(result)

def _get_player_2_template_score(image, template, template_key:str):
    """Used for getting match score of template images meant to match on the 
    top Player 2 side (right) of the frame image.
    -------------------------------------------------------------------------
    -=image=- Frame image to check, read in using OpenCV (numpy image object)
    -=template_img=- Template image, read in using OpenCV (numpy image object)
    -=template_key=- The key used to identify the template image name
    -------------------------------------------------------------------------
    [-return-] When a valid result, is a tuple:
               (minimum match value:float, maximum match value:float, 
                (min val x:int, min val y:int), (max val x:int, max val y:int))"""
    edged_keys:list = ['2P_Portrait', '2P_No_Round_Lost', '2P_Round_Lost']
    red_chan_keys:list = ['2P_No_Round_Lost', '2P_Round_Lost']
    img_h, img_w = image.shape[0:2]
    
    #Creating mask for Player 2 top screen
    mask = np.zeros(image.shape[:2], dtype="uint8")
    cv2.rectangle(mask, ((img_w // 2) + 1, 0), (img_w, round(img_h * 0.20)), 255, -1)
    
    if template_key in red_chan_keys:
        #Creating grayscale images based on the red channels of each image
        image = image[:,:,2]
        template = template[:,:,2]
    else:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)        
    
    masked = cv2.bitwise_and(image, image, mask=mask)    
    if template_key in edged_keys:
        #convert images to edges
        masked = cv2.Canny(masked, 50, 200)
        template = cv2.Canny(template, 50, 200)
    
    result = cv2.matchTemplate(masked, template, cv2.TM_CCOEFF_NORMED)
    return cv2.minMaxLoc(result)

def _get_round_start_template_score(image, template, template_key:str):
    """Used for getting match score of template images which are related to 
    round start (Duel 1, 2, 3, Final, Lets Rock).
    -------------------------------------------------------------------------
    -=image=- Frame image to check, read in using OpenCV (numpy image object)
    -=template_img=- Template image, read in using OpenCV (numpy image object)
    -=template_key=- The key used to identify the template image name
    -------------------------------------------------------------------------
    [-return-] When a valid result, is a tuple:
               (minimum match value:float, maximum match value:float, 
                (min val x:int, min val y:int), (max val x:int, max val y:int))"""
    edged_keys:list = ['Number_1', 'Number_2', 'Number_3', 'Number_Final']
    red_chan_keys:list = ['Number_1', 'Number_2', 'Number_3', 'Number_Final']
    
    if template_key in red_chan_keys:
        #Creating grayscale images based on the red channels of each image
        image = image[:,:,2]
        template = template[:,:,2]
    else:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)    
    
    if template_key in edged_keys:
        #convert images to edges
        image = cv2.Canny(image, 50, 200)
        template = cv2.Canny(template, 50, 200)
    
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    return cv2.minMaxLoc(result)

def _get_round_end_template_score(image, template, template_key:str):
    """Used for getting match score of template images which are related to 
    round end (Slash, Perfect, Times Up, Double KO, P1/P2 Win, Char Win Poses).
    -------------------------------------------------------------------------
    -=image=- Frame image to check, read in using OpenCV (numpy image object)
    -=template_img=- Template image, read in using OpenCV (numpy image object)
    -=template_key=- The key used to identify the template image name
    -------------------------------------------------------------------------
    [-return-] When a valid result, is a tuple:
               (minimum match value:float, maximum match value:float, 
                (min val x:int, min val y:int), (max val x:int, max val y:int))"""
    edged_keys:list = ['Win_Pose_Left', 'Win_Pose_Right']    
    
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)    
    
    if template_key in edged_keys:
        #convert images to edges
        image = cv2.Canny(image, 50, 200)
        template = cv2.Canny(template, 50, 200)
    
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    return cv2.minMaxLoc(result)

def _get_timer_template_score(image, template, template_key:str):
    """Used for getting match score of template images which are related to 
    the Timer (Timer Outline).
    -------------------------------------------------------------------------
    -=image=- Frame image to check, read in using OpenCV (numpy image object)
    -=template_img=- Template image, read in using OpenCV (numpy image object)
    -=template_key=- The key used to identify the template image name
    -------------------------------------------------------------------------
    [-return-] When a valid result, is a tuple:
               (minimum match value:float, maximum match value:float, 
                (min val x:int, min val y:int), (max val x:int, max val y:int))"""
    edged_keys:list = ['Timer_Outline']
    img_h, img_w = image.shape[0:2]

    #Creating mask for top center screen (where the timer is)
    mask = np.zeros(image.shape[:2], dtype="uint8")
    center_w = img_w // 2
    half_timer = round(img_w * 0.045)
    x1, x2 = (center_w - half_timer), (center_w + half_timer)
    
    cv2.rectangle(mask, (x1, 0), (x2, round(img_h * 0.22)), 255, -1)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)    
    masked = cv2.bitwise_and(image, image, mask=mask)
    
    if template_key in edged_keys:
        #convert images to edges
        masked = cv2.Canny(masked, 50, 200)
        template = cv2.Canny(template, 50, 200)
    
    result = cv2.matchTemplate(masked, template, cv2.TM_CCOEFF_NORMED)
    return cv2.minMaxLoc(result)

def check_min_match_val(template_key:str, tmpl_img:dict, min_val_mappings:dict, 
                        match_val:float)->float:
    """Checks if template match score meets the minimum value set for the key.
    -------------------------------------------------------------------------
    -=template_key=- The key used to identify the template image name used
    -=tmpl_img=- Dict associated with template image used
    -=min_val_mappings=- From the config file, defines a mapping between 
      template image path key & the key used to store the minimum value for 
      that specific template image or category of template image.
    -=match_val=- Raw template match score from OpenCv template match function
    -------------------------------------------------------------------------
    [-return-] If minimum isn't met: 0, otherwise param match_val"""
    img_keys = list(min_val_mappings.keys())
    if template_key in img_keys:
        if match_val >= tmpl_img[min_val_mappings[template_key]]:
            return match_val
        else:
            return 0
    else:
        return match_val

def reorder_img_list(img_files:list)->list:
    """Reorders a list of image file names of the format 'image1.jpg', 'image2',
    ..., 'image201.jpg', ... to be in sequence, since an alpha sort would not.
    -------------------------------------------------------------------------
    -=img_files=- List of filenames, of images extracted from a video w/ the
    naming covention ['image1.jpg', 'image2.jpg', .., 'imageN.jpg']
    -------------------------------------------------------------------------
    [-return-] A list of the same file names order by the sequence of the 
     numbers in the filenames."""
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

def load_tmp_imgs(template_img_dicts:list)->list:
    """Loading all template images in each dict into memory as numpy img objs 
    so that there's only an I/O cost per template, once per video processed.
    -------------------------------------------------------------------------
    -=template_img_dicts=- Dicts from config which store required info for all
    template images being used to match.
    -------------------------------------------------------------------------
    [-return-] The same dictionaries in a list, w/ the image objects being 
     added to the key 'img_objs', & named the same as the image path key."""
    for template_img_dict in template_img_dicts:
        template_img_keys = list(template_img_dict['img_paths'].keys())
        for tmp_img_key in template_img_keys:
            tmp_img = cv2.imread(template_img_dict['img_paths'][tmp_img_key])
            template_img_dict['img_objs'][tmp_img_key] = tmp_img
    return template_img_dicts

def _high_health_detect(frame_img):
    """Using horizontal line detection, detects high health coloured health bars.
    -------------------------------------------------------------------------
    -=frame_img=- Frame image to check, read in using OpenCV (numpy image object)
    -------------------------------------------------------------------------
    [-return-] A list of 'contours', each having 4 values defining a rectangle: 
     x-coordinate, y-coordinate, width, & height"""
    high_health_lower = np.array([135,100,225])
    high_health_upper = np.array([183,224,255])

    #Mask based on presence of a colour range
    mask = cv2.inRange(frame_img, high_health_lower, high_health_upper)
    health_bars = cv2.bitwise_and(frame_img,frame_img, mask= mask)
    gray = cv2.cvtColor(health_bars, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)[1]
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    #Find Horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35,2))
    detect_horizontal = cv2.morphologyEx(close, cv2.MORPH_OPEN, 
                                         horizontal_kernel, iterations=2)
    cnts = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, 
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    
    return cnts

def _low_health_detect(frame_img):
    """Using horizontal line detection, detects low health coloured health bars.
    -------------------------------------------------------------------------
    -=frame_img=- Frame image to check, read in using OpenCV (numpy image object)
    -------------------------------------------------------------------------
    [-return-] A list of 'contours', each having 4 values defining a rectangle: 
     x-coordinate, y-coordinate, width, & height"""
    low_health_lower = np.array([2,145,225])
    low_health_upper = np.array([20,155,240])
    
    #Mask based on presence of a colour range
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
    """Calls the high & low health detect functions, & filters results based on
    minimum & maximum values to avoid false positives.
    -------------------------------------------------------------------------
    -=frame_img=- Frame image to check, read in using OpenCV (numpy image object)
    -------------------------------------------------------------------------
    [-return-] A tuple consistenting of: x-coordinate, y-coordinate, width, 
    height, & boolean value if it's low health or not. If the result is 
    (0,0,0,0,False), there was nothing detected within the valid min/max ranges."""
    (x_loc, y_loc, w_val, h_val) = (0, 0, 0, 0)
    (min_w, min_h, max_h, min_y, max_y) = (200, 15, 100, 80, 168)
    low_health:bool = False
    high_health_contours = _high_health_detect(frame_img)
    
    #Check for high health first
    for c in high_health_contours:
        x1, y1, w1, h1 = cv2.boundingRect(c)
        if w1 >= min_w and h1 >= min_h and h1 <= max_h and y1 < max_y and y1 > min_y:
            if w1 > w_val:
                (x_loc, y_loc, w_val, h_val) = (x1, y1, w1, h1)
                
    #If no high health found, check for low health    
    if w_val == 0:
        low_health_contours = _low_health_detect(frame_img)
        (x_loc, y_loc, w_val, h_val) = (0, 0, 0, 0)
        (min_w, min_h, min_y, max_y) = (1, 15, 80, 168)
        for c in low_health_contours:
            x1, y1, w1, h1 = cv2.boundingRect(c)
            if w1 >= min_w and h1 >= min_h and y1 < max_y and y1 > min_y:
                if w1 > w_val:
                    (x_loc, y_loc, w_val, h_val) = (x1, y1, w1, h1)
                    low_health = True

    return (x_loc, y_loc, w_val, h_val, low_health)

def detect_player_1_health(frame_img)->tuple[int,int]:
    """Runs health detection, for the top half of the Player 1 (left) side of 
    the screen.
    -------------------------------------------------------------------------
    -=frame_img=- Frame image to check, read in using OpenCV (numpy image object)
    -------------------------------------------------------------------------
    [-return-] A tuple consistenting of: high health value, low health value 
    which is based on the width of the detected bounding box."""
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
    
def detect_player_2_health(frame_img)->tuple[int,int]:
    """Runs health detection, for the top half of the Player 2 (right) side of 
    the screen.
    -------------------------------------------------------------------------
    -=frame_img=- Frame image to check, read in using OpenCV (numpy image object)
    -------------------------------------------------------------------------
    [-return-] A tuple consistenting of: high health value, low health value 
    which is based on the width of the detected bounding box."""
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

def get_all_tmpl_scores_vid(vid_file_path:str, template_img_dicts:list, 
                            min_val_mappings:dict, frames_per_sec:int = 2):
    """Used to check a video, against a set of template images. Template match 
    scores are filtered by minimums to determine if the template was detected 
    in each image.
    -------------------------------------------------------------------------
    -=vid_file_path=- Path of the video files' location (relative or absolute).
    -=template_img_dicts=- From the config file, a list of dicts used to define 
      the template images & other properties like match score minimums.
    -=min_val_mappings=- From the config file, defines a mapping between 
      template image path key & the key used to store the minimum value for 
      that specific template image or category of template image.
    -=frames_per_sec=- Number of frames per second to process. While it can be
      a value between 1 to 60, 2 & 4 are what testing & tuning were based on.
    -------------------------------------------------------------------------
    [-return-] A DataFrame with a row for every image frame processed, & 
    columns representing every template image defined in template_img_dicts. 
    Data if match score was below the minimum is 0, otherwise the value will be 
    the match score of that template for that image frame."""
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
            #Creating a list of the dict keys pretaining to the template images
            template_img_keys = list(template_img_dict['img_objs'].keys())
        
            for template_img_key in template_img_keys:
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

def get_all_tmpl_scores_img(img_folder:str, img_files:list, template_img_dicts:list, 
                            min_val_mappings:dict):
    """Used to check a folder of images derrived from a video, against a set of 
    template images. Template match scores are filtered by minimums to 
    determine if the template was detected in each image.
    -------------------------------------------------------------------------
    -=img_folder=- Path of the folder where the images are stored.
    -=img_files=- List of each image file to process from img_folder.
    -=template_img_dicts=- From the config file, a list of dicts used to define 
      the template images & other properties like match score minimums.
    -=min_val_mappings=- From the config file, defines a mapping between 
      template image path key & the key used to store the minimum value for 
      that specific template image or category of template image.
    -------------------------------------------------------------------------
    [-return-] A DataFrame with a row for every image frame processed, & 
    columns representing every template image defined in template_img_dicts. 
    Data if match score was below the minimum is 0, otherwise the value will be 
    the match score of that template for that image frame."""
    tmp_match_scores_df = pd.DataFrame({})
    index_num = 1
    for img_file in img_files:
        img_path = img_folder + img_file
        tmp_match_scores:dict = {'image_file_name' : img_file}
        image = cv2.imread(img_path)
        for template_img_dict in template_img_dicts:
            dict_name = template_img_dict['Name']
            #Creating a list of the dict keys pretaining to the template images
            template_img_keys = list(template_img_dict['img_objs'].keys())
        
            for img_key in template_img_keys:
                (minVal, maxVal, minLoc, maxLoc) = get_match_template_score(
                                            image, 
                                            template_img_dict['img_objs'][img_key], 
                                            img_key)
                col_name = "{}_{}".format(dict_name, img_key)
                tmp_match_scores[col_name] = check_min_match_val(img_key, 
                                                                 template_img_dict, 
                                                                 min_val_mappings, 
                                                                 maxVal)
        #Detecting 1P & 2P health bars
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
