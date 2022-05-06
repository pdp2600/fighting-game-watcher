# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 18:14:18 2022

Script for creating a video demo based on extracted data & related processes

@author: PDP2600
"""
import cv2
import numpy as np
import os
import pandas as pd
from datetime import datetime

wd_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader"
os.chdir(wd_path)

import conf.config_values as conf
#import conf.old_config_values as conf2
#FG Watcher computer vision extraction & aggregation functions
import FGWatcher_refactor_1 as ex
#import FGW_GGStrivagator_1 as agg

pd.set_option('display.max_rows', 2000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_colwidth', None)

def _detect_health_bar(frame_img):
    (x_loc, y_loc, w_val, h_val) = (0, 0, 0, 0)
    #Changed min_w to 200 from 230
    #adding a max height
    (min_w, min_h, max_h, min_y, max_y) = (200, 15, 100, 80, 168)
    low_health_bool = False
    
    high_health_contours = ex._high_health_detect(frame_img)
    
    #Check for high health first
    for c in high_health_contours:
        #cv2.drawContours(image, [c], -1, (36,255,12), -1)
        #Looks like these are the values to use to confirm a health bar
        x1, y1, w1, h1 = cv2.boundingRect(c)
        #print("High health y1: {} w1: {} h1: {}".format(y1, w1, h1))
        if w1 >= min_w and h1 >= min_h and h1 <= max_h and y1 < max_y and y1 > min_y:
            if w1 > w_val:
                (x_loc, y_loc, w_val, h_val) = (x1, y1, w1, h1)
                
    #If no high health found, check for low health    
    if w_val == 0:
        low_health_contours = ex._low_health_detect(frame_img)
        (x_loc, y_loc, w_val, h_val) = (0, 0, 0, 0)
        #For low health
        (min_w, min_h, min_y, max_y) = (1, 15, 80, 168)
        for c in low_health_contours:
            x1, y1, w1, h1 = cv2.boundingRect(c)
            #print("Low health y1: {} w1: {} h1: {}".format(y1, w1, h1))
            if w1 >= min_w and h1 >= min_h and y1 < max_y and y1 > min_y:
                if w1 > w_val:
                    (x_loc, y_loc, w_val, h_val) = (x1, y1, w1, h1)
                    low_health_bool = True

    return (x_loc, y_loc, w_val, h_val, low_health_bool)

def _create_frame_data_dict(input_round_df, input_game_df):
    round_df = input_round_df.copy().reset_index()
    game_df = input_game_df.copy().reset_index()
    frame_data_dict = {}
    #round_cols: list = list(round_df.columns)
    if (len(game_df) > 0):
        frame_data_dict['id'] = game_df.loc[0, 'game_id']
        frame_data_dict['total_rounds'] = game_df.loc[0, 'total_rounds']
        frame_data_dict['game_winner'] = game_df.loc[0, 'winner']
        
        if (len(round_df) > 0):
            frame_data_dict['round'] = round_df.loc[0, 'round']
            frame_data_dict['round_winner'] = round_df.loc[0, 'winner']
            frame_data_dict['p1_character'] = round_df.loc[0, 'character_1P']
            frame_data_dict['p2_character'] = round_df.loc[0, 'character_2P']
            frame_data_dict['perfect'] = True if bool(round_df.loc[0, 'perfect']) else False
            frame_data_dict['double_ko'] = True if bool(round_df.loc[0, 'double_ko']) else False
            frame_data_dict['time_out'] = True if bool(round_df.loc[0, 'time_out']) else False
        else:
            frame_data_dict['round'] = None
            frame_data_dict['round_winner'] = None
            frame_data_dict['p1_character'] = game_df.loc[0, 'character_1P']
            frame_data_dict['p2_character'] = game_df.loc[0, 'character_2P']
            frame_data_dict['perfect'] = False
            frame_data_dict['double_ko'] = False
            frame_data_dict['time_out'] = False
        
    else:
        frame_data_dict['id'] = round_df.loc[0, 'anomaly_id']
        frame_data_dict['total_rounds'] = None
        frame_data_dict['game_winner'] = None
        frame_data_dict['round'] = round_df.loc[0, 'round']
        frame_data_dict['round_winner'] = round_df.loc[0, 'winner']
        frame_data_dict['p1_character'] = round_df.loc[0, 'character_1P']
        frame_data_dict['p2_character'] = round_df.loc[0, 'character_2P']
        frame_data_dict['perfect'] = True if bool(round_df.loc[0, 'perfect']) else False
        frame_data_dict['double_ko'] = True if bool(round_df.loc[0, 'double_ko']) else False
        frame_data_dict['time_out'] = True if bool(round_df.loc[0, 'time_out']) else False
        
    return frame_data_dict

#Anomally/Game id & Specific Round
def _display_id_and_round(frame_image, frame_data_dict: dict, img_w: int=1920):
    x1, y1 = (img_w // 2)-101, 1
    x2, y2 = (img_w // 2)+101, 90
    black = (0, 0, 0)
    white = (255, 255, 255)
    font = cv2.FONT_HERSHEY_TRIPLEX
    id_list: list = str(frame_data_dict['id']).split('_')
    id_label: str = "ID: {}".format(frame_data_dict['id'])
    
    cv2.rectangle(frame_image, (x1, y1), (x2, y2), black, -1)
    
    if id_list[0] == 'Game':
        cv2.putText(frame_image, id_label, (x1 + 35, y1 + 25), font, 0.60, white, 
                    1, cv2.LINE_AA, bottomLeftOrigin=False)
    else:
        cv2.putText(frame_image, id_label, (x1 + 15, y1 + 25), font, 0.60, white, 
                    1, cv2.LINE_AA, bottomLeftOrigin=False)
    
    if frame_data_dict['round'] != None:
        cv2.putText(frame_image, 'ROUND:', (x1 + 65, y1 + 55), font, 0.60, white, 
                    1, cv2.LINE_AA, bottomLeftOrigin=False)
        if frame_data_dict['round'] == 'Round_1':
            cv2.putText(frame_image, '1', (x1 + 93, y1 + 80), font, 0.60, white, 
                        1, cv2.LINE_AA, bottomLeftOrigin=False)
        elif frame_data_dict['round'] == 'Round_2':
            cv2.putText(frame_image, '2', (x1 + 93, y1 + 80), font, 0.60, white, 
                        1, cv2.LINE_AA, bottomLeftOrigin=False)
        elif frame_data_dict['round'] == 'Round_3':
            cv2.putText(frame_image, '3', (x1 + 93, y1 + 80), font, 0.60, white, 
                        1, cv2.LINE_AA, bottomLeftOrigin=False)
        elif frame_data_dict['round'] == 'Round_Final':
            cv2.putText(frame_image, 'Final', (x1 + 72, y1 + 80), font, 0.60, 
                        white, 1, cv2.LINE_AA, bottomLeftOrigin=False)
        else:
            cv2.putText(frame_image, 'Unknown', (x1 + 52, y1 + 80), font, 0.60, 
                        white, 1, cv2.LINE_AA, bottomLeftOrigin=False)
    
    return frame_image

#Game/Round Winner
def _display_winners(frame_image, frame_data_dict: dict, img_w: int=1920, 
                     display_game_winner: bool=False):
    x1, y1 = (img_w // 2)-101, 200
    x2, y2 = (img_w // 2)+101, 300
    black = (0, 0, 0)
    white = (255, 255, 255)
    font = cv2.FONT_HERSHEY_TRIPLEX
    round_winner = frame_data_dict['round_winner']

    if round_winner != None:
        cv2.rectangle(frame_image, (x1, y1), (x2, y2), black, -1)
        cv2.putText(frame_image,'Round Winner:',(x1 + 30, y1 + 15), font, 0.55, 
                    white, 1, cv2.LINE_AA, bottomLeftOrigin=False)
        if (round_winner == 'Player 1') or (round_winner == 'Player 2'):
            cv2.putText(frame_image, round_winner, (x1 + 60, y1 + 35), font, 
                        0.60, white, 1, cv2.LINE_AA, bottomLeftOrigin=False)
        elif (round_winner == 'Draw'):
            cv2.putText(frame_image, round_winner, (x1 + 75, y1 + 35), font, 
                        0.60, white, 1, cv2.LINE_AA, bottomLeftOrigin=False)
        else:
            cv2.putText(frame_image, 'Unknown', (x1 + 55, y1 + 35), font, 0.60, 
                        white, 1, cv2.LINE_AA, bottomLeftOrigin=False)
    
    if (frame_data_dict['game_winner'] != None) and (display_game_winner):
        cv2.putText(frame_image, 'Game Winner:', (x1 + 35, y1 + 75), font, 0.55, 
                    white, 1, cv2.LINE_AA, bottomLeftOrigin=False) 
        game_winner = frame_data_dict['game_winner']
        if (game_winner == 'Player 1') or (game_winner == 'Player 2'): 
            cv2.putText(frame_image, game_winner, (x1 + 60, y1 + 95), font, 0.60, 
                        white, 1, cv2.LINE_AA, bottomLeftOrigin=False) 
        elif (game_winner == 'Draw'): 
            cv2.putText(frame_image, game_winner, (x1 + 75, y1 + 95), font, 0.60, 
                        white, 1, cv2.LINE_AA, bottomLeftOrigin=False) 
        else: 
            cv2.putText(frame_image, 'Unknown', (x1 + 55, y1 + 95), font, 0.60, 
                        white, 1, cv2.LINE_AA, bottomLeftOrigin=False)

    if bool(frame_data_dict['perfect']): 
        cv2.putText(frame_image, '<PERFECT>', (x1 + 42, y1 + 55), font, 0.60, white, 1, cv2.LINE_AA, bottomLeftOrigin=False)
    elif bool(frame_data_dict['double_ko']):
        cv2.putText(frame_image, '<DOUBLE KO>', (x1 + 30, y1 + 55), font, 0.60, white, 1, cv2.LINE_AA, bottomLeftOrigin=False)
    elif bool(frame_data_dict['time_out']):
        cv2.putText(frame_image, '<TIME OUT>', (x1 + 40, y1 + 55), font, 0.60, white, 1, cv2.LINE_AA, bottomLeftOrigin=False)
    
    return frame_image

#Characters & Total Rounds (if game not anomally)
def _display_chars_and_total_rounds(frame_image, frame_data_dict: dict, 
                                    img_w: int=1920, img_h: int=1080):
    x1, y1 = (img_w // 2)-200, img_h - 105
    x2, y2 = (img_w // 2)+200, img_h - 5
    black = (0, 0, 0)
    white = (255, 255, 255)
    font = cv2.FONT_HERSHEY_TRIPLEX
    cv2.rectangle(image, (x1, y1), (x2, y2), black, -1)
    player_1_char = frame_data_dict['p1_character'].replace('_', ' ')
    player_2_char = frame_data_dict['p2_character'].replace('_', ' ')
        
    #Character vs Text, only displayed if both characters ar not Unknown
    if (player_1_char != 'Unknown') and (player_2_char != 'Unknown'):
        p1_vs_p2_str = "{} vs {}".format(player_1_char, player_2_char)
        vs_index = p1_vs_p2_str.find('vs')
        txt_offset = int(vs_index * 12)
        width = x2 - x1
        offset_x = ((x1 + (width//2)) - 5) - txt_offset
        cv2.putText(frame_image, p1_vs_p2_str, (offset_x , y1 + 35), font, 0.60, 
                    white, 1, cv2.LINE_AA, bottomLeftOrigin=False)

    
    if frame_data_dict['total_rounds'] != None:
        total_rounds_label = "Total Rounds: {}".format(frame_data_dict['total_rounds'])
        cv2.putText(frame_image, total_rounds_label, (x1 + 120 , y1 + 70), font, 
                    0.60, white, 1, cv2.LINE_AA, bottomLeftOrigin=False)
    else:
        total_rounds_label = "Total Rounds: N/A"
        cv2.putText(frame_image, total_rounds_label, (x1 + 100 , y1 + 70), font, 0.60, 
                    white, 1, cv2.LINE_AA, bottomLeftOrigin=False)
    
    return frame_image

def _is_ui_on_screen(frame_image, game_ui_dict: dict)-> bool:
    timer_ui_img = game_ui_dict['img_objs']['Timer_Outline']
    min_timer_match = game_ui_dict['Min_Timer_Score']
    (minVal, maxVal, minLoc, maxLoc) = ex.get_match_template_score(frame_image, 
                                                                   timer_ui_img, 
                                                                   'Timer_Outline')
    
    return bool(maxVal > min_timer_match)

def _get_character_tmpl_dict(char_name: str, char_tmpl_dicts: list)-> dict:
    char_name_no_spaces: str = char_name.replace(' ', '_')
    for char_dict in char_tmpl_dicts:
        if char_name_no_spaces == char_dict['Name'].replace(' ', '_'):
            return char_dict
    
    return dict({})

def _detect_and_highlight_char_portraits(frame_image, frame_data: dict, 
                                         char_img_dicts: list):
    black, white, green = (0, 0, 0), (255, 255, 255), (0, 255, 0)
    font = cv2.FONT_HERSHEY_TRIPLEX
    player_1: dict = _get_character_tmpl_dict(frame_data['p1_character'], 
                                             char_img_dicts)
    player_2: dict = _get_character_tmpl_dict(frame_data['p2_character'], 
                                             char_img_dicts)
    p1_portrait = player_1['img_objs']['1P_Portrait']
    p2_portrait = player_2['img_objs']['2P_Portrait']
    
    (minVal, p1_maxVal, minLoc, p1_maxLoc) = ex.get_match_template_score(frame_image, 
                                                                         p1_portrait, 
                                                                         '1P_Portrait')
    (minVal, p2_maxVal, minLoc, p2_maxLoc) = ex.get_match_template_score(frame_image, 
                                                                         p2_portrait, 
                                                                         '2P_Portrait')
    if p1_maxVal > player_1['Min_Portrait_Match']:
        tmpl_h, tmpl_w = p1_portrait.shape[0:2]
        p1_x1, p1_y1 = p1_maxLoc[0], p1_maxLoc[1]
        p1_rect_xy1 = (p1_x1, p1_y1 + tmpl_h + 3)
        p1_rect_xy2 = (p1_x1 + tmpl_w + 65, p1_y1 + tmpl_h + 33)
        p1_label = "P1 {}".format(player_1['Name'].replace('_', ' '))
        cv2.rectangle(frame_image, (p1_x1, p1_y1), (p1_x1 + tmpl_w, p1_y1 + tmpl_h), 
                      green, 3)
        cv2.rectangle(frame_image, p1_rect_xy1, p1_rect_xy2, black, -1)
        cv2.putText(frame_image, p1_label, (p1_x1 + 5 , p1_y1 + tmpl_h + 23), 
                    font, 0.60, white, 1, cv2.LINE_AA, bottomLeftOrigin=False)

    if p2_maxVal > player_2['Min_Portrait_Match']:
        tmpl_h, tmpl_w = p2_portrait.shape[0:2]
        p2_x1, p2_y1 = p2_maxLoc[0], p2_maxLoc[1]
        p2_rect_xy1 = (p2_x1 - 45, p2_y1 + tmpl_h + 3)
        p2_rect_xy2 = (p2_x1 + tmpl_w + 20, p2_y1 + tmpl_h + 33)
        p2_label = "P2 {}".format(player_2['Name'].replace('_', ' '))
        cv2.rectangle(frame_image, (p2_x1, p2_y1), (p2_x1 + tmpl_w, p2_y1 + tmpl_h), 
                      green, 3)
        cv2.rectangle(frame_image, p2_rect_xy1, p2_rect_xy2, black, -1)
        cv2.putText(frame_image, p2_label, (p2_x1 - 40 , p2_y1 + tmpl_h + 23), 
                    font, 0.60, white, 1, cv2.LINE_AA, bottomLeftOrigin=False)
        
    return frame_image

def _detect_and_highlight_health_bars(frame_image):
    img_h, img_w = frame_image.shape[0:2]
    high_health_colour = (36,255,12) #Green
    low_health_colour = (36,230,230) #Yellow?
    red = (0,0,255)
    black = (0, 0, 0)
    font = cv2.FONT_HERSHEY_TRIPLEX
    #Creating mask for Player 1 top screen
    mask_P1 = np.zeros(frame_image.shape[:2], dtype="uint8")
    cv2.rectangle(mask_P1, (0, 0), (img_w // 2, round(img_h * 0.20)), 255, -1)

    #Creating mask for Player 2 top screen
    mask_P2 = np.zeros(frame_image.shape[:2], dtype="uint8")
    cv2.rectangle(mask_P2, ((img_w // 2) + 1, 0), (img_w, round(img_h * 0.20)), 255, -1)

    masked_P1 = cv2.bitwise_and(frame_image, frame_image, mask=mask_P1)
    masked_P2 = cv2.bitwise_and(frame_image, frame_image, mask=mask_P2)

    (x_P1, y_P1, w_P1, h_P1, isLowHealthP1) = _detect_health_bar(masked_P1)
    (x_P2, y_P2, w_P2, h_P2, isLowHealthP2) = _detect_health_bar(masked_P2)

    if isLowHealthP1:
        p1_label = "P1 Low Health: {}".format(w_P1)
        cv2.rectangle(frame_image, (x_P1, y_P1), (x_P1 + w_P1, y_P1 + h_P1), 
                      low_health_colour, -1)
        cv2.putText(frame_image, p1_label, (x_P1 - 150, y_P1 + 15), 
                    font, 0.60, red, 1, cv2.LINE_AA, bottomLeftOrigin=False)
    else:
        p1_label = "P1 High Health: {}".format(w_P1)
        cv2.rectangle(frame_image, (x_P1, y_P1), (x_P1 + w_P1, y_P1 + h_P1), 
                      high_health_colour, -1)
        if w_P1 > 0:
            cv2.putText(frame_image, p1_label, (x_P1 + 10 , y_P1 + 15), font, 
                        0.60, black, 1, cv2.LINE_AA, bottomLeftOrigin=False)
    
    if isLowHealthP2:
        p2_label = "P2 Low Health: {}".format(w_P2)
        cv2.rectangle(frame_image, (x_P2, y_P2), (x_P2 + w_P2, y_P2 + h_P2), 
                      low_health_colour, -1)
        cv2.putText(frame_image, p2_label, (x_P2 + 150 , y_P2 + 15), 
                    font, 0.60, red, 1, cv2.LINE_AA, bottomLeftOrigin=False)
    else:
        p2_label = "P2 High Health: {}".format(w_P2)
        cv2.rectangle(frame_image, (x_P2, y_P2), (x_P2 + w_P2, y_P2 + h_P2), 
                      high_health_colour, -1)
        if w_P2 > 0:
            cv2.putText(frame_image, p2_label, (x_P2 + 10 , y_P2 + 15), font, 
                        0.60, black, 1, cv2.LINE_AA, bottomLeftOrigin=False)
    
    return frame_image

def _create_timing_controller_df(games_df, anomallies_df = None):
    timing_controller_df = pd.DataFrame({})
    if (anomallies_df != None) and (len(anomallies_df) > 0):
        games_copy_df = games_df.copy()[['game_id', 'start_index', 'end_index']]
        games_copy_df = games_copy_df.rename(columns = {'game_id':'id'})
        anomallies_copy_df = anomallies_df.copy()[['anomaly_id', 'start_index', 
                                                   'end_index']]
        anomallies_copy_df = anomallies_copy_df.rename(columns = {'anomaly_id':'id'})
        timing_controller_df = games_copy_df.append(anomallies_copy_df)
        timing_controller_df = timing_controller_df.sort_values(['start_index'])
        timing_controller_df = timing_controller_df.reset_index()
        timing_controller_df = timing_controller_df.drop(['index'], axis = 'columns')
        
    else:
        timing_controller_df = games_df.copy()[['game_id', 'start_index', 'end_index']]
        timing_controller_df = timing_controller_df.rename(columns = {'game_id':'id'})
        timing_controller_df = timing_controller_df.sort_values(['start_index'])
        timing_controller_df = timing_controller_df.reset_index()
        timing_controller_df = timing_controller_df.drop(['index'], axis = 'columns')
    
    return timing_controller_df


def _is_within_range(data_df, cur_seconds: float, index_to_secs: float):
    display_check_secs: float = 1.0
    start_time = (data_df.loc[0, 'end_index'] * index_to_secs) - display_check_secs
    end_time = (data_df.loc[0, 'end_index'] * index_to_secs)
    
    return ((cur_seconds > start_time) and (cur_seconds < end_time))
    
def get_video_duration(ggst_vid_data_df):
    last_frame_index = list(ggst_vid_data_df.index)[-1]
    return ggst_vid_data_df.loc[last_frame_index, 'Time_in_Secs']

rounds_df = pd.read_csv('output\\2022-4-15_4-57-19_My_Baiken_Matches_90_mins\\Round_data_My_Baiken_Matches_90_mins_2022-4-15_4-57-19.csv')
games_df = pd.read_csv('output\\2022-4-15_4-57-19_My_Baiken_Matches_90_mins\\Game_data_My_Baiken_Matches_90_mins_2022-4-15_4-57-19.csv')
anomallies_df = pd.DataFrame({})
vid_data_df = pd.read_csv('output\\2022-4-15_4-57-19_My_Baiken_Matches_90_mins\\Visual_detection_data_My_Baiken_Matches_90_mins_2022-4-15_4-57-19.csv')
output_filepath = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader\\Test_Videos\\demos\\Baiken_90_mins_data_demo_2024-04-26.avi"
video_filepath = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader\\Test_Videos\\My_Baiken_Matches_90_mins_2022-03-13_16-01-57.mp4"

char_img_dicts: list = [conf.anji_templ_imgs, conf.axl_templ_imgs, 
                        conf.baiken_templ_imgs, conf.chipp_templ_imgs, 
                        conf.faust_templ_imgs, conf.giovanna_templ_imgs, 
                        conf.goldlewis_templ_imgs, conf.happy_templ_imgs, 
                        conf.ino_templ_imgs, conf.jacko_templ_imgs, 
                        conf.ky_templ_imgs, conf.leo_templ_imgs, 
                        conf.may_templ_imgs, conf.millia_templ_imgs, 
                        conf.nago_templ_imgs, conf.potemkin_templ_imgs, 
                        conf.ramlethal_templ_imgs, conf.sol_templ_imgs, 
                        conf.testament_templ_imgs, conf.zato_templ_imgs
                        ]
char_img_dicts: list = ex.load_tmp_imgs(char_img_dicts)
game_ui: dict = conf.game_ui_templ_imgs
game_ui = ex.load_tmp_imgs([game_ui])[0]

vid_fps: int = 30
processed_fps: int = 4
index_to_secs: float = 1 / processed_fps
index: int = 0
seconds: float = 0
#Frames_per_second min 1 fps & max 60 fps
frame_rate: float = (1 / np.clip(vid_fps, 1, 60))
video_length = get_video_duration(vid_data_df)

display_round_game_win: bool = False
time_for_win_screen: float = 0
win_screen_data: dict = {}
CHECK_BEFORE_END_SECS: float = 1.0
SHOW_WIN_SCR_AFTER_END_SECS: float = 2.0

total_start = datetime.now()

vidcap = cv2.VideoCapture(video_filepath)
width: int = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH ))
height: int = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT ))
#vid_framerate: float = vidcap.get(cv2.CAP_PROP_FPS) #~30fps for Baiken vid

vidout = cv2.VideoWriter(output_filepath, cv2.VideoWriter_fourcc('M','J','P','G'), 
                         vid_fps, frameSize=(width,height), isColor=True)

time_controller_df = _create_timing_controller_df(games_df)

vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
hasFrame,image = vidcap.read()

while hasFrame:    
    print("Creating Demo | Processing Time: Frame: {}(in secs) of total duration: {}secs... ".format(seconds, video_length))
    end_section_time: float = (time_controller_df.loc[index, 'end_index'] * 
                               index_to_secs)
    if seconds > end_section_time:
        index = (index + 1) if (len(time_controller_df) - 1) > index else index
        end_section_time: float = (time_controller_df.loc[index, 'end_index'] * 
                               index_to_secs)
    
    id_val: str = str(time_controller_df.loc[index, 'id'])
    id_type: str = id_val.split('_')[0]
    start_section_time: float = (time_controller_df.loc[index, 'start_index'] * 
                                 index_to_secs)
    
    #Decrement the win screen buffer when display_round_game_win is True
    time_for_win_screen = ((time_for_win_screen - frame_rate) 
                           if display_round_game_win else 0)
    
    if (seconds > start_section_time) and (seconds < end_section_time):
        frame_data_dict = {}
        timer_bool: bool = _is_ui_on_screen(image, game_ui)
        
        if id_type == 'Game':
            round_df = rounds_df.loc[rounds_df.game_id == id_val]
            round_df = round_df.loc[((round_df.start_index * index_to_secs) < seconds) & 
                                    ((round_df.end_index * index_to_secs) > seconds)]
            round_df = round_df.reset_index()
            game_df = games_df.loc[games_df.game_id == id_val]
            game_df = game_df.reset_index()
            frame_data_dict = _create_frame_data_dict(round_df, game_df)
            #Write Id & round where applicable, function does that logic
            image = _display_id_and_round(image, frame_data_dict)
            #Write total rounds & characters to bottom where applicable
            image = _display_chars_and_total_rounds(image, frame_data_dict)
            #Character Portrait image detection & drawing bounding rectangle
            image = _detect_and_highlight_char_portraits(image, frame_data_dict, 
                                                         char_img_dicts)
            #Health detection, gated behind detecting the timer outline on the the
            #UI to avoid false positives
            if timer_bool:
                image = _detect_and_highlight_health_bars(image)
                
            if time_for_win_screen > 0:
                 is_game_winning_round: bool = _is_within_range(game_df, seconds, 
                                                                index_to_secs)
                 image = _display_winners(image, win_screen_data, 
                                          display_game_winner=is_game_winning_round)
                 #time_for_win_screen = time_for_win_screen - frame_rate                 
            elif ((not display_round_game_win) and 
                  ((_is_within_range(game_df, seconds, index_to_secs)) or 
                   ((len(round_df) > 0) and (_is_within_range(round_df, seconds, 
                                                              index_to_secs))))):
                display_round_game_win = True
                end_section_secs = (round_df.loc[0, 'end_index'] if len(round_df) > 0 
                                    else game_df.loc[0, 'end_index'])
                end_section_secs = end_section_secs * index_to_secs
                
                time_for_win_screen = ((end_section_secs - seconds) + 
                                       SHOW_WIN_SCR_AFTER_END_SECS)
                win_screen_data['round_winner'] =  frame_data_dict['round_winner']
                win_screen_data['game_winner'] =  frame_data_dict['game_winner']
                win_screen_data['perfect'] = frame_data_dict['perfect']
                win_screen_data['double_ko'] = frame_data_dict['double_ko']
                win_screen_data['time_out'] = frame_data_dict['time_out']
                is_game_winning_round: bool = _is_within_range(game_df, seconds, 
                                                               index_to_secs)
                image = _display_winners(image, win_screen_data, 
                                         display_game_winner=is_game_winning_round)                
            elif (display_round_game_win and time_for_win_screen <= 0):
                display_round_game_win = False
                time_for_win_screen = 0
                win_screen_data = {}
        else:
            #For when it's an anomally
            anomally_df = anomallies_df.loc[anomallies_df.anomaly_id == id_val]
            anomally_df = anomally_df.reset_index()
            
            frame_data_dict = _create_frame_data_dict(anomally_df, pd.DataFrame({}))
            #Write Id & round where applicable, function does that logic
            image = _display_id_and_round(image, frame_data_dict)
            #Write total rounds & characters to bottom where applicable
            image = _display_chars_and_total_rounds(image, frame_data_dict)
            #Character Portrait image detection & drawing bounding rectangle
            image = _detect_and_highlight_char_portraits(image, frame_data_dict, 
                                                         char_img_dicts)
            #Health detection, gated behind detecting the timer outline on the the
            #UI to avoid false positives
            if timer_bool:
                image = _detect_and_highlight_health_bars(image)
            
            if time_for_win_screen > 0:
                 image = _display_winners(image, win_screen_data, 
                                          display_game_winner=False)
                 #time_for_win_screen = time_for_win_screen - frame_rate                 
            elif ((not display_round_game_win) and 
                  (_is_within_range(anomally_df, seconds, index_to_secs))):
                display_round_game_win = True
                end_section_secs = anomally_df.loc[0, 'end_index'] * index_to_secs
                
                time_for_win_screen = ((end_section_secs - seconds) + 
                                       SHOW_WIN_SCR_AFTER_END_SECS)
                win_screen_data['round_winner'] =  frame_data_dict['round_winner']
                win_screen_data['game_winner'] =  frame_data_dict['game_winner']
                win_screen_data['perfect'] = frame_data_dict['perfect']
                win_screen_data['double_ko'] = frame_data_dict['double_ko']
                win_screen_data['time_out'] = frame_data_dict['time_out']

                image = _display_winners(image, win_screen_data, 
                                         display_game_winner=False)                
            elif (display_round_game_win and time_for_win_screen <= 0):
                display_round_game_win = False
                time_for_win_screen = 0
                win_screen_data = {}

    vidout.write(image)
    seconds = seconds + frame_rate
    vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
    hasFrame,image = vidcap.read()
    

vidcap.release()
vidout.release()

# Closes all the frames
cv2.destroyAllWindows()

end_time = datetime.now()
vid_delta = (end_time - total_start).seconds
print("Total extraction/aggregation processing time was {} seconds".format(vid_delta))
print("Total length of video process was {} seconds.".format(video_length))


###############################################################################
##Possible Info images written into new video's frames:
##-Anamollay/Game id at top, with the Specific Round (Unknown if unknown)
##-P1 char vs P2 char, with total rounds (unless it's an anamolly) at bottom
###-P1 char vs P2 char par only appears if both characters are known
##-At top below timer, Round Winner & Game Winner (if Unknown, Unkown displayed)
###-Appears just before round/game end & will stay on screen for 2-3 seconds
##-Health bar detect drawn to screen health bars (use Timer outline to verify ui)
##-P1 & P2 Character portarites with a rectangle around the images (use Timer outline to verify ui)

"""

vidcap.set(cv2.CAP_PROP_POS_MSEC,55.75*1000)
hasFrame,image = vidcap.read()

#new_frame_img = _display_id_and_round(image, frame_data_dict, img_w=img_w)
#new_frame_img = _display_winners(new_frame_img, frame_data_dict, img_w=img_w, 
#                                 display_game_winner=False)
#new_frame_img = _display_chars_and_total_rounds(new_frame_img, frame_data_dict, 
#                                                img_w=img_w, img_h=img_h)
#timer_bool: bool = _is_ui_on_screen(new_frame_img, game_ui)

#new_frame_img = _detect_and_highlight_char_portraits(new_frame_img, frame_data_dict, 
#                                                       char_img_dicts)

#new_frame_img = _detect_and_highlight_health_bars(new_frame_img)

cv2.imshow("Data Overlay Testing", new_frame_img)
#cv2.imshow("Zato 2P Test Portrait", test_img_dicts_processed_ls[18]['img_objs']['2P_Portrait'])
cv2.waitKey(0)
cv2.destroyAllWindows()
"""
  

##############################################################################
##Used for dev testing
"""
#player_1_img = player_1['img_objs']['1P_Portrait']
#player_2_img = player_2['img_objs']['2P_Portrait']
#timer_ui_img = game_ui['img_objs']['Timer_Outline']

#id Game example
frame_data_dict = {'id': 'Game_02', 'round': 'Round_3', 
                   'round_winner': 'Player 2', 'game_winner': 'Player 2', 
                   'total_rounds': '3', 'p1_character': 'Baiken', 
                   'p2_character': 'Faust', 'perfect': False, 
                   'double_ko': False, 'time_out': False
                   }
#id Anomally example
frame_data_dict = {'id': 'Anomally_02', 'round': 'Round_2', 
                   'round_winner': 'Player 2', 'game_winner': None, 
                   'total_rounds': None, 'p1_character': 'Baiken', 
                   'p2_character': 'Faust', 'perfect': False, 
                   'double_ko': False, 'time_out': False
                   }


test_img_frame = 21.25
vidcap.set(cv2.CAP_PROP_POS_MSEC,test_img_frame*1000)
hasFrame,image = vidcap.read()
img_h, img_w = image.shape[0:2]

black = (0, 0, 0)
white = (255, 255, 255)
green = (0, 255, 0)
font = cv2.FONT_HERSHEY_TRIPLEX

new_frame_img = _display_id_and_round(image, frame_data_dict, img_w=img_w)
new_frame_img = _display_winners(new_frame_img, frame_data_dict, img_w=img_w, 
                                 display_game_winner=False)
new_frame_img = _display_chars_and_total_rounds(new_frame_img, frame_data_dict, 
                                                img_w=img_w, img_h=img_h)

timer_bool = _is_ui_on_screen(new_frame_img, game_ui)

new_frame_img = _detect_and_highlight_char_portraits(new_frame_img, frame_data_dict, 
                                                       char_img_dicts)

new_frame_img = _detect_and_highlight_health_bars(new_frame_img)




time_controller_df = _create_timing_controller_df(games_df)

cv2.imshow("Data Overlay Testing", new_frame_img)
#cv2.imshow("Zato 2P Test Portrait", test_img_dicts_processed_ls[18]['img_objs']['2P_Portrait'])
cv2.waitKey(0)
cv2.destroyAllWindows()


"""