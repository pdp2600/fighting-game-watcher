# -*- coding: utf-8 -*-
"""
Created on Fri Mar 18 15:25:38 2022

Mastermind module for functions that integrate the extraction & aggregation
functions and processes

Early this will also run the code (probably should create a fgwatcher.py which 
is meant to be the main module)

@author: PDP2600
"""
import cv2
import numpy as np
import os
import pandas as pd
from datetime import datetime
import urllib.parse

wd_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader"
os.chdir(wd_path)

import conf.config_values as conf
#import conf.old_config_values as conf2
#FG Watcher computer vision extraction & aggregation functions
import FGWatcher_refactor_1 as ex
import FGW_GGStrivagator_1 as agg

pd.set_option('display.max_rows', 2000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_colwidth', None)

def _no_duel_number_matches(match_scores_dict):
    total_duel_num_score = match_scores_dict['Starter_Number_1']
    total_duel_num_score = match_scores_dict['Starter_Number_2'] + total_duel_num_score
    total_duel_num_score = match_scores_dict['Starter_Number_3'] + total_duel_num_score
    return (total_duel_num_score == 0)
    
def _no_starter_matches(match_scores_dict):
    total_starter_score = 0 if _no_duel_number_matches(match_scores_dict) else 1
    total_starter_score = match_scores_dict['Starter_Duel'] + total_starter_score
    total_starter_score = match_scores_dict['Starter_Number_Final'] + total_starter_score
    total_starter_score = match_scores_dict['Starter_Lets_Rock'] + total_starter_score
    return (total_starter_score == 0)

#Creates a frame dict w/ all Starter & Ender scores set to 0 for 1st round of matching
def _create_zero_scores_frame_dict(time_in_secs):
    return {'Time_in_Secs' : int(time_in_secs), 
            'Frame_Number_secs' : time_in_secs, 
            'Starter_Duel': 0, 'Starter_Number_1': 0, 'Starter_Number_2': 0, 
            'Starter_Number_3': 0, 'Starter_Number_Final': 0, 
            'Starter_Lets_Rock': 0, 'Ender_Slash': 0, 'Ender_Perfect': 0,
            'Ender_Double_KO': 0, 'Ender_Times_Up': 0, 'Ender_Draw': 0, 
            'Game_UI_Timer_Outline': 0
            }
def _set_duel_values_to_zero(match_scores_dict):
    match_scores_dict['Starter_Duel'] = 0
    match_scores_dict['Starter_Number_1'] = 0
    match_scores_dict['Starter_Number_2'] = 0
    match_scores_dict['Starter_Number_3'] = 0
    match_scores_dict['Starter_Number_Final'] = 0
    
    return match_scores_dict

def get_vetted_match_score(img, tmpl_img, tmpl_key, tmpl_dict, min_mappings_dict):           
    #Getting Template Match Score min/max w/ (x, y) location data
    (minVal, maxVal, minLoc, maxLoc) = ex.get_match_template_score(img, 
                                                                   tmpl_img, 
                                                                   tmpl_key)
    #Only reporting scores which are over configureed minimums, otherwise it's 0
    return ex.check_min_match_val(tmpl_key, tmpl_dict, min_mappings_dict, maxVal)

def starter_ender_tmpl_scores_vid(vid_file_path, template_img_dicts_ls, 
                                  min_mappings_dict, draw_buffer, frames_per_sec = 4, 
                                  is_verbose=False):
    template_img_dicts_ls = ex.load_tmp_imgs(template_img_dicts_ls)
    tmp_match_scores_df = pd.DataFrame({})
    index_num = 0
    seconds = 0
    #Frames_per_second min 1 fps & max 60 fps
    frame_rate = (1 / np.clip(frames_per_sec, 1, 60))
    starter_dict = {}
    ender_dict = {}
    ui_dict = {}
    for img_dict in template_img_dicts_ls:
        starter_dict = img_dict if img_dict['Name'] == 'Starter' else starter_dict
        ender_dict = img_dict if img_dict['Name'] == 'Ender' else ender_dict
        ui_dict = img_dict if img_dict['Name'] == 'Game_UI' else ui_dict
    
    duel_img = starter_dict['img_objs']['Duel']
    num_1_img = starter_dict['img_objs']['Number_1']
    num_2_img = starter_dict['img_objs']['Number_2']
    num_3_img = starter_dict['img_objs']['Number_3']
    num_final_img = starter_dict['img_objs']['Number_Final']
    lets_rock_img = starter_dict['img_objs']['Lets_Rock']
    slash_img = ender_dict['img_objs']['Slash']
    double_ko_img = ender_dict['img_objs']['Double_KO']
    draw_img = ender_dict['img_objs']['Draw']
    perfect_img = ender_dict['img_objs']['Perfect']
    times_up_img = ender_dict['img_objs']['Times_Up']
    timer_ui_img = ui_dict['img_objs']['Timer_Outline']

    check_for_draw = False
    frames_to_check_draw = 0
    
    vidcap = cv2.VideoCapture(vid_file_path)
    vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
    hasFrame,image = vidcap.read()
    
    while hasFrame:
        if is_verbose:
            print("Starter<->Ender | Checking Time: {}secs, Frame: {} (in secs)... ".format(int(seconds), seconds))
        #Decrement the draw buffer when check_for_draw bool is True
        frames_to_check_draw = (frames_to_check_draw - 1) if check_for_draw else 0
        match_scores_dict = _create_zero_scores_frame_dict(seconds)
        #Getting Duel score for frame, to begin starter frame template match logic
        match_scores_dict['Starter_Duel'] = get_vetted_match_score(image, 
                                                                   duel_img, 
                                                                   'Duel', 
                                                                   starter_dict, 
                                                                   min_mappings_dict)
        if match_scores_dict['Starter_Duel'] > 0:
            match_scores_dict['Starter_Number_1'] = get_vetted_match_score(image, 
                                                                           num_1_img, 
                                                                           'Number_1', 
                                                                           starter_dict, 
                                                                           min_mappings_dict)
            match_scores_dict['Starter_Number_2'] = get_vetted_match_score(image, 
                                                                           num_2_img, 
                                                                           'Number_2', 
                                                                           starter_dict, 
                                                                           min_mappings_dict)
            match_scores_dict['Starter_Number_3'] = get_vetted_match_score(image, 
                                                                           num_3_img, 
                                                                           'Number_3', 
                                                                           starter_dict, 
                                                                           min_mappings_dict)
            #If there are no duel number matches, check for duel Final
            if (_no_duel_number_matches(match_scores_dict)):
                match_scores_dict['Starter_Number_Final'] = get_vetted_match_score(image, 
                                                                                   num_final_img, 
                                                                                   'Number_Final', 
                                                                                   starter_dict, 
                                                                                   min_mappings_dict)
                #When there are no round number matches, Duel score is invalid, set to 0
                if match_scores_dict['Starter_Number_Final'] == 0:
                    match_scores_dict['Starter_Duel'] = 0
            
            #Duel 1 & 2 is sometimes a false positive for Ender Times Up, checking for that
            match_scores_dict['Ender_Times_Up'] = get_vetted_match_score(image, 
                                                                      times_up_img, 
                                                                      'Times_Up', 
                                                                      ender_dict, 
                                                                      min_mappings_dict)
            #If Times Up (word to O.C.) is detected, reset Duel values
            if match_scores_dict['Ender_Times_Up'] > 0:
                match_scores_dict = _set_duel_values_to_zero(match_scores_dict)
                check_for_draw = True
                frames_to_check_draw = draw_buffer
        #Made Let's Rock checked everytime due to false positives with Duel 1s
        match_scores_dict['Starter_Lets_Rock'] = get_vetted_match_score(image, 
                                                                        lets_rock_img, 
                                                                        'Lets_Rock', 
                                                                        starter_dict, 
                                                                        min_mappings_dict)
        if check_for_draw and (frames_to_check_draw == 0):
            check_for_draw = False
        #Check for enders only if no valid Starters are detected
        if (_no_starter_matches(match_scores_dict)):
            match_scores_dict['Ender_Slash'] = get_vetted_match_score(image, 
                                                                      slash_img, 
                                                                      'Slash', 
                                                                      ender_dict, 
                                                                      min_mappings_dict)
            total_ender_scores = match_scores_dict['Ender_Slash']
            if total_ender_scores == 0:
                match_scores_dict['Ender_Perfect'] = get_vetted_match_score(image, 
                                                                      perfect_img, 
                                                                      'Perfect', 
                                                                      ender_dict, 
                                                                      min_mappings_dict)
                total_ender_scores = match_scores_dict['Ender_Perfect']
            
            if total_ender_scores == 0:
                match_scores_dict['Ender_Double_KO'] = get_vetted_match_score(image, 
                                                                      double_ko_img, 
                                                                      'Double_KO', 
                                                                      ender_dict, 
                                                                      min_mappings_dict)
                total_ender_scores = match_scores_dict['Ender_Double_KO']
            
            if total_ender_scores == 0 and match_scores_dict['Ender_Times_Up'] == 0:
                match_scores_dict['Ender_Times_Up'] = get_vetted_match_score(image, 
                                                                      times_up_img, 
                                                                      'Times_Up', 
                                                                      ender_dict, 
                                                                      min_mappings_dict)
                if match_scores_dict['Ender_Times_Up'] > 0:
                    check_for_draw = True
                    frames_to_check_draw = draw_buffer
            #Check for Draw if Times Up not detected & check_forDraw flag active
            if (match_scores_dict['Ender_Times_Up'] == 0) and check_for_draw:
                match_scores_dict['Ender_Draw'] = get_vetted_match_score(image, 
                                                                         draw_img, 
                                                                         'Draw', 
                                                                         ender_dict, 
                                                                         min_mappings_dict)

        match_scores_dict['Game_UI_Timer_Outline'] = get_vetted_match_score(image, 
                                                                            timer_ui_img, 
                                                                            'Timer_Outline', 
                                                                            ui_dict, 
                                                                            min_mappings_dict)
        
        tmp_match_scores_df = tmp_match_scores_df.append(pd.DataFrame(match_scores_dict, 
                                                                      index=[index_num]), 
                                                         sort=False)
        index_num = index_num + 1
        seconds = seconds + frame_rate
        vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
        hasFrame,image = vidcap.read()
    
    return tmp_match_scores_df

def _set_in_round_cols_to_zero(ggst_data_df, char_img_dicts_ls):
    ggst_zero_data_df = ggst_data_df.copy()
    for char_dict in char_img_dicts_ls:
        char_P1_col_name = "{}_1P_Portrait".format(char_dict['Name'])
        char_P2_col_name = "{}_2P_Portrait".format(char_dict['Name'])
        ggst_zero_data_df[char_P1_col_name] = 0
        ggst_zero_data_df[char_P2_col_name] = 0
    
    #ggst_zero_data_df['Game_UI_Timer_Outline'] = 0
    ggst_zero_data_df['1P_High_Health'] = 0
    ggst_zero_data_df['1P_Low_Health'] = 0
    ggst_zero_data_df['2P_High_Health'] = 0
    ggst_zero_data_df['2P_Low_Health'] = 0
    
    return ggst_zero_data_df

def get_player_win_template_data(video_path, ggst_data_df, rounds_df, ender_img_dict, 
                                 min_mappings_dict, win_tmpl_buffer, frames_after_ender, 
                                 is_verbose = False):
    ggst_new_data_df = ggst_data_df.copy()
    ggst_new_data_df['Ender_1P_Win'] = 0
    ggst_new_data_df['Ender_2P_Win'] = 0
    all_img_dicts_ls = [ender_img_dict]
    all_img_dicts_ls = ex.load_tmp_imgs(all_img_dicts_ls)
    img_dict = all_img_dicts_ls[0]
    
    vidcap = cv2.VideoCapture(video_path)
    
    for j, row in rounds_df.iterrows():
        if (row.end_index != -1):
            start_index = row.end_index + frames_after_ender
            end_index = row.end_index + win_tmpl_buffer
            last_index = list(ggst_new_data_df.index)[-1]
            start_index = last_index if start_index > last_index else start_index
            end_index = last_index if end_index > last_index else end_index
        
            ggst_round_data_df = ggst_new_data_df.loc[start_index:end_index]

            for index, row in ggst_round_data_df.iterrows():
                seconds = row.Frame_Number_secs
                vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
                hasFrame,image = vidcap.read()
                if is_verbose:
                    print("Checking 1P/2P Win Templates | Checking Time: {}secs, Frame: {} (in secs)... ".format(int(seconds), seconds))
            
                if hasFrame:
                    vetted_score = get_vetted_match_score(image, 
                                                          img_dict['img_objs']['1P_Win'], 
                                                          '1P_Win', ender_img_dict, 
                                                          min_mappings_dict)
                    ggst_new_data_df.loc[index, 'Ender_1P_Win'] = vetted_score
                
                    vetted_score = get_vetted_match_score(image, 
                                                          img_dict['img_objs']['2P_Win'], 
                                                          '2P_Win', ender_img_dict, 
                                                          min_mappings_dict)
                    ggst_new_data_df.loc[index, 'Ender_2P_Win'] = vetted_score
    return ggst_new_data_df

#When there is adequate data, the char match is predicted & reduced to those two chars
def _get_predict_chars_dict_ls(ggst_char_pred_df, all_img_dicts_ls, min_char_delta):
    char_portraits_agg_ls = agg.get_char_portrait_col_names(list(ggst_char_pred_df))
    player_1_characters_ls = [x for x in char_portraits_agg_ls if '1P_Portrait' in x]
    player_2_characters_ls = [x for x in char_portraits_agg_ls if '2P_Portrait' in x]
    
    player_1_char = agg.get_character_used(ggst_char_pred_df, player_1_characters_ls, 
                                           min_char_delta)
    player_2_char = agg.get_character_used(ggst_char_pred_df, player_2_characters_ls, 
                                           min_char_delta)
    if (player_1_char == 'Unknown') or (player_2_char == 'Unknown'):
        return all_img_dicts_ls
    else:
        new_img_dict_ls = []
        for img_dict in all_img_dicts_ls:
            if ((img_dict['Name'] == player_1_char) or (img_dict['Name'] == player_2_char)):
                new_img_dict_ls.append(img_dict)
                
        return new_img_dict_ls

#2nd phase of extratction checking for characters played & items related to player health
#Checks frames based on Round atart & end established in the phase 1 extract/aggregation
def get_in_round_data(video_path, ggst_data_df, rounds_df, char_img_dicts_ls, 
                      min_mappings_dict, char_pred_frame_buffer, min_char_delta, 
                      post_ender_health_buffer, is_verbose=False):
    
    ggst_new_data_df = _set_in_round_cols_to_zero(ggst_data_df.copy(), char_img_dicts_ls)
    all_img_dicts_ls = char_img_dicts_ls
    all_img_dicts_ls = ex.load_tmp_imgs(all_img_dicts_ls)
    vidcap = cv2.VideoCapture(video_path)    
    for j, row in rounds_df.iterrows():
        start_index = row.start_index
        end_index = row.end_index
        chars_predicted = False
        img_dicts_ls = all_img_dicts_ls.copy()
        #Only run template matching when a round has a defined start & end index
        if (start_index != -1) and (end_index != -1):
            #April 5th expanded the data rows by health post ender buffer 
            if len(ggst_new_data_df) > (end_index + post_ender_health_buffer):
                end_index = end_index + post_ender_health_buffer
            ggst_round_data_df = ggst_new_data_df.loc[start_index:end_index]
            for index, row in ggst_round_data_df.iterrows():
                seconds = row.Frame_Number_secs
                vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
                hasFrame,image = vidcap.read()
                if is_verbose:
                    print("Char Portraits//Health | Checking Time: {}secs, Frame: {} (in secs)... ".format(int(seconds), seconds))            
                if hasFrame:
                    if ((chars_predicted != True) and 
                        ((index - start_index) > char_pred_frame_buffer)):
                        ggst_char_pred_df = ggst_new_data_df.loc[start_index:(index - 1)]
                        img_dicts_ls = _get_predict_chars_dict_ls(ggst_char_pred_df, 
                                                                  all_img_dicts_ls, 
                                                                  min_char_delta)
                        chars_predicted = True if len(img_dicts_ls) < 3 else False
                    #Itteration through all image dicts or predicted char image dicts
                    for img_dict in img_dicts_ls:
                        dict_name = img_dict['Name']
                        #Creating a list of the dict keys pretaining to templateimage paths
                        template_img_keys = list(img_dict['img_objs'].keys())
                        #Running template matching on every image in the dict
                        for tmpl_img_key in template_img_keys:                        
                            tmpl_img = img_dict['img_objs'][tmpl_img_key]
                            score_column_name = "{}_{}".format(dict_name, tmpl_img_key)
                            vetted_score = get_vetted_match_score(image, tmpl_img, 
                                                                  tmpl_img_key, 
                                                                  img_dict, 
                                                                  min_mappings_dict)
                            ggst_new_data_df.loc[index, score_column_name] = vetted_score
                    #Detecting 1P & 2P health bars
                    (high_health_1P, low_health_1P) = ex.detect_player_1_health(image)
                    (high_health_2P, low_health_2P) = ex.detect_player_2_health(image)        
                    ggst_new_data_df.loc[index, '1P_High_Health'] = high_health_1P
                    ggst_new_data_df.loc[index, '1P_Low_Health'] = low_health_1P
                    ggst_new_data_df.loc[index, '2P_High_Health'] = high_health_2P
                    ggst_new_data_df.loc[index, '2P_Low_Health'] = low_health_2P
                        
    return ggst_new_data_df

#Used to validate that Draw game winner results are actual draws. Game draws are
#very rare, & are usually due to there not being conclusive round data
#If a game result isn't a Draw, game result changed to Unknown to better reflect the situation
def validate_draw_game_results(games_df, rounds_df):
    draw_games_df = games_df.loc[games_df.winner == 'Draw']
    if len(draw_games_df) == 0:
        return games_df
    else:
        games_copy_df = games_df.copy()
        for index, row in draw_games_df.iterrows():
            game_rounds_df = rounds_df.loc[rounds_df.game_id == row.game_id]
            final_round_df = game_rounds_df.loc[game_rounds_df['round'] == 'Round_Final']
            final_round_df = final_round_df.reset_index()
            if len(final_round_df) == 0:
                games_copy_df.loc[index, 'winner'] = 'Unknown'
            else:
                if final_round_df.loc[0, 'winner'] != 'Draw':
                    games_copy_df.loc[index, 'winner'] = 'Unknown'
                    
        return games_copy_df

#For correcting Game score errors which can be resolved w/ the 1st being 3-0 round scores
def correct_game_scores(games_df, rounds_df):
    #Checking if there are any games with a 3-0 round score
    if (((len(games_df.loc[games_df.player_1_rounds_won > 2]) > 0) or 
        (len(games_df.loc[games_df.player_2_rounds_won > 2]) > 0))):
        games_copy_df = games_df.copy()
        for index, row in games_copy_df.iterrows():
            if ((games_copy_df.loc[index, 'total_rounds'] >= 3) and 
                (games_copy_df.loc[index, 'player_1_rounds_won'] > 2)):
                games_copy_df.loc[index, 'player_1_rounds_won'] = 2
                games_copy_df.loc[index, 'player_2_rounds_won'] = 1
            elif ((games_copy_df.loc[index, 'total_rounds'] >= 3) and 
                  (games_copy_df.loc[index, 'player_2_rounds_won'] > 2)):
                games_copy_df.loc[index, 'player_1_rounds_won'] = 1
                games_copy_df.loc[index, 'player_2_rounds_won'] = 2
        return games_copy_df
    else:
        return games_df
    
def get_video_duration(ggst_vid_data_df):
    last_frame_index = list(ggst_vid_data_df.index)[-1]
    return ggst_vid_data_df.loc[last_frame_index, 'Time_in_Secs']

def _create_bookmark_df(rounds_or_games_df, anomallies_df=pd.DataFrame({})):
    index_num = 0
    vid_bookmarks_df = pd.DataFrame({})

    if len(anomallies_df) > 0:
        anomallies_df = anomallies_df.loc[anomallies_df.start_secs != -1]
        if len(anomallies_df) > 0:
            for index, row in anomallies_df.iterrows():
                round_bookmark_dict = {'id': str(anomallies_df.loc[index, 'Anomally_id']), 
                                       'time': anomallies_df.loc[index, 'start_secs'], 
                                       'round': str(anomallies_df.loc[index, 'round']), 
                                       'character_1P': str(anomallies_df.loc[index, 'character_1P']), 
                                       'character_2P': str(anomallies_df.loc[index, 'character_2P'])
                                       }
                vid_bookmarks_df = vid_bookmarks_df.append(pd.DataFrame(round_bookmark_dict, 
                                                                        index=[index_num]), 
                                                           sort=False)
                index_num = index_num + 1

    is_round_df = 'round' in list(rounds_or_games_df.columns)
    for index, row in rounds_or_games_df.iterrows():
        
        round_bookmark_dict = {'id': str(rounds_or_games_df.loc[index, 'game_id']), 
                               'time': rounds_or_games_df.loc[index, 'start_secs'], 
                               'character_1P': str(rounds_or_games_df.loc[index, 'character_1P']), 
                               'character_2P': str(rounds_or_games_df.loc[index, 'character_2P'])
                               }
        if is_round_df:
            round_bookmark_dict['round'] = str(rounds_or_games_df.loc[index, 'round'])
        else:
            round_bookmark_dict['round'] = str(rounds_or_games_df.loc[index, 'total_rounds'])
        
        vid_bookmarks_df = vid_bookmarks_df.append(pd.DataFrame(round_bookmark_dict, 
                                                                index=[index_num]), 
                                                   sort=False)
        index_num = index_num + 1

    vid_bookmarks_df = vid_bookmarks_df.sort_values('time')
    vid_bookmarks_df = vid_bookmarks_df.reset_index()
    vid_bookmarks_df = vid_bookmarks_df.drop(['index'], axis = 'columns')
    
    return vid_bookmarks_df

def _create_bookmark_name(single_bookmark_df):
    bookmark_df = single_bookmark_df.reset_index()
    round_str = ""
    char_info = ""
    individual_rounds_ls = ['Round_1', 'Round_2', 'Round_3', 'Round_Final', 'Unknown']
    if bookmark_df.loc[0,'round'] in individual_rounds_ls:
        if bookmark_df.loc[0,'round'] != 'Unknown':
            round_str = "Round - {}".format(bookmark_df.loc[0,'round'].split('_')[-1])
        else:
            round_str = "Round - Unknown"
    else:
        round_str = "Total Rounds - {}".format(bookmark_df.loc[0,'round'])
        
    if ((bookmark_df.loc[0,'character_1P'] == 'Unknown') or 
        (bookmark_df.loc[0,'character_1P'] == 'None') or 
        (bookmark_df.loc[0,'character_2P'] == 'Unknown') or 
        (bookmark_df.loc[0,'character_2P'] == 'None')):
        
        char_info = ""
    else:
        char_info = " {} vs {}".format(bookmark_df.loc[0,'character_1P'], 
                                      bookmark_df.loc[0,'character_2P'])

    return "{} {}{}".format(bookmark_df.loc[0,'id'], round_str, char_info)

def _create_vlc_option_tag_data(bookmarks_df):
    bookmark_num = 0
    last_index = list(bookmarks_df.index)[-1]
    bookmarks_data = "\t\t\t\t<vlc:option>bookmarks="
    
    for index, row in bookmarks_df.iterrows():
        name = _create_bookmark_name(bookmarks_df.loc[index:index,])
        bookmark_str = "{{name={} #{},time={}}}".format(name, bookmark_num, 
                                                        bookmarks_df.loc[index, 'time'])
        if index == last_index:
            bookmarks_data = bookmarks_data + bookmark_str + "</vlc:option>\n"
        else:
            bookmarks_data = bookmarks_data + bookmark_str + ","
            
        bookmark_num = bookmark_num + 1
    
    return bookmarks_data

#Help page on VLC video playlist custom bookmarks: https://www.vlchelp.com/using-custom-bookmarks-vlc-media-player/
def create_round_based_vlc_playlist(rounds_df, vid_data_df, video_fullpath, 
                                    output_folder, anomallies_df=pd.DataFrame({})):
    html_beginning = """<?xml version="1.0" encoding="UTF-8"?>\n<playlist xmlns="http://xspf.org/ns/0/" xmlns:vlc="http://www.videolan.org/vlc/playlist/ns/0/" version="1">\n"""
    html_end = """\t<extension application="http://www.videolan.org/vlc/playlist/0">\n\t\t<vlc:item tid="0"/>\n\t</extension>\n</playlist>"""
    path_converted = video_fullpath.replace('\\', '/')
    path_ls = path_converted.split('/')
    vid_name = path_ls[-1]
    del path_ls[-1]
    folder_path = '/'.join(path_ls)
    santized_vid_name = urllib.parse.quote(vid_name)
    new_file_path = "{}/{}".format(folder_path, santized_vid_name)
    vid_label = vid_name.split('.')[0][0:32]
    vid_duration_in_ms = str(get_video_duration(vid_data_df) * 1000)

    bookmarks_df = _create_bookmark_df(rounds_df, anomallies_df)

    playlist_title = "Round based Playlist {}".format(vid_label)
    title = "\t<title>{}</title>\n".format(playlist_title)
    file_str = "file:///"
    location = "{}{}".format(file_str, new_file_path)
    track_tags = "\t<trackList>\n\t\t<track>\n"
    location_tag = "\t\t\t<location>{}</location>\n".format(location)
    duration_tag = "\t\t\t<duration>{}</duration>\n".format(vid_duration_in_ms)
    extension_tag = """\t\t\t<extension application="http://www.videolan.org/vlc/playlist/0">\n\t\t\t\t<vlc:id>0</vlc:id>\n"""
    vlc_option_tag = _create_vlc_option_tag_data(bookmarks_df)
    closing_tags = "\t\t\t</extension>\n\t\t</track>\n\t</trackList>\n"

    bookmark_tags = "{}{}{}{}{}{}{}".format(title, track_tags, location_tag, 
                                            duration_tag, extension_tag, 
                                            vlc_option_tag, closing_tags)
    playlist_xml = "{}{}{}".format(html_beginning, bookmark_tags, html_end)
    
    dt = datetime.now()
    timestamp = "{}-{}-{}_{}-{}-{}".format(dt.year, dt.month, dt.day, dt.hour, 
                                            dt.minute, dt.second)
    vid_label = vid_label.replace(' ', '_')
    output_file_name = "Round_Playlist_" + vid_label + "_" + timestamp + ".xspf"
    playlist_file = open(output_folder + output_file_name, 'w')
    playlist_file.write(str(playlist_xml))
    playlist_file.close()
    
    return str(output_folder + output_file_name)

def create_game_based_vlc_playlist(games_df, vid_data_df, video_fullpath, 
                                   output_folder, anomallies_df=pd.DataFrame({})):
    html_beginning = """<?xml version="1.0" encoding="UTF-8"?>\n<playlist xmlns="http://xspf.org/ns/0/" xmlns:vlc="http://www.videolan.org/vlc/playlist/ns/0/" version="1">\n"""
    html_end = """\t<extension application="http://www.videolan.org/vlc/playlist/0">\n\t\t<vlc:item tid="0"/>\n\t</extension>\n</playlist>"""
    path_converted = video_fullpath.replace('\\', '/')
    path_ls = path_converted.split('/')
    vid_name = path_ls[-1]
    del path_ls[-1]
    folder_path = '/'.join(path_ls)
    santized_vid_name = urllib.parse.quote(vid_name)
    new_file_path = "{}/{}".format(folder_path, santized_vid_name)
    vid_label = vid_name.split('.')[0][0:32]
    vid_duration_in_ms = str(get_video_duration(vid_data_df) * 1000)

    bookmarks_df = _create_bookmark_df(games_df, anomallies_df)

    playlist_title = "Game based Playlist {}".format(vid_label)
    title = "\t<title>{}</title>\n".format(playlist_title)
    file_str = "file:///"
    location = "{}{}".format(file_str, new_file_path)
    track_tags = "\t<trackList>\n\t\t<track>\n"
    location_tag = "\t\t\t<location>{}</location>\n".format(location)
    duration_tag = "\t\t\t<duration>{}</duration>\n".format(vid_duration_in_ms)
    extension_tag = """\t\t\t<extension application="http://www.videolan.org/vlc/playlist/0">\n\t\t\t\t<vlc:id>0</vlc:id>\n"""
    vlc_option_tag = _create_vlc_option_tag_data(bookmarks_df)
    closing_tags = "\t\t\t</extension>\n\t\t</track>\n\t</trackList>\n"

    bookmark_tags = "{}{}{}{}{}{}{}".format(title, track_tags, location_tag, 
                                            duration_tag, extension_tag, 
                                            vlc_option_tag, closing_tags)
    playlist_xml = "{}{}{}".format(html_beginning, bookmark_tags, html_end)
    
    dt = datetime.now()
    timestamp = "{}-{}-{}_{}-{}-{}".format(dt.year, dt.month, dt.day, dt.hour, 
                                            dt.minute, dt.second)
    vid_label = vid_label.replace(' ', '_')
    output_file_name = "Game_Playlist_" + vid_label + "_" + timestamp + ".xspf"
    playlist_file = open(output_folder + output_file_name, 'w')
    playlist_file.write(str(playlist_xml))
    playlist_file.close()
    
    return str(output_folder + output_file_name)

#Approach to combine extraction & aggregation to limit unnecessary template matching
#Round Start/End templates found 1st, processed in round data, then those bounaries
#are used to target other template matching to limit the number of frames to check
def layered_extract_and_aggregate_video(video_path, fps_val, config):
    vid_filename = video_path.split('\\')[-1]
    new_agg_config = agg.convert_agg_config_vals_based_on_fps(config.agg_config_4fps, 
                                                              config.fps_scaling_vals_ls, 
                                                              config.plus_one_vals_ls, 
                                                              fps_val)
    total_start = datetime.now()
    #start_time = datetime.now()
    #Starter & Ender template matching function
    ggst_vid_data_df = starter_ender_tmpl_scores_vid(video_path, 
                                                     config.starter_ender_img_dicts_ls, 
                                                     config.templ_img_min_val_mappings, 
                                                     new_agg_config['times_up_to_draw_frame_buffer'], 
                                                     frames_per_sec = fps_val, 
                                                     is_verbose=True)
    #end_time = datetime.now()
    #vid_delta = (end_time - start_time).seconds
    #print("Round Start/End extraction processing time was {} seconds".format(vid_delta))
    consolidated_rounds_df = agg.aggregate_into_rounds(ggst_vid_data_df, new_agg_config)

    ##Function to get data in game rounds: character portraits, timer outline & health
    #start_time = datetime.now()
    ggst_vid_data_df = get_in_round_data(video_path, ggst_vid_data_df, 
                                         consolidated_rounds_df, 
                                         config.char_templ_img_dicts_ls, 
                                         config.templ_img_min_val_mappings,
                                         new_agg_config['char_prediction_frame_buffer'], 
                                         new_agg_config['min_character_delta'],
                                         new_agg_config['health_after_ender_frame_buffer'], 
                                         is_verbose=True)
    #end_time = datetime.now()
    #vid_delta = (end_time - start_time).seconds
    #print("Character Portraits/Health processing time was {} seconds".format(vid_delta))
    
    ##Function to check for 1P/2P WIn template match after Ender
    #start_time = datetime.now()
    ggst_vid_data_df = get_player_win_template_data(video_path, ggst_vid_data_df, 
                                                    consolidated_rounds_df, 
                                                    config.round_ender_templ_imgs, 
                                                    config.templ_img_min_val_mappings, 
                                                    new_agg_config['player_win_after_ender_buffer'], 
                                                    new_agg_config['player_win_frame_after_ender_start'], 
                                                    is_verbose=True)
    #end_time = datetime.now()
    #vid_delta = (end_time - start_time).seconds
    #print("1P/2P WIn Template processing time was {} seconds".format(vid_delta))
    characters_in_rounds_df = agg.extract_played_characters(ggst_vid_data_df, 
                                                            consolidated_rounds_df, 
                                                            new_agg_config)
    round_winners_df = agg.extract_round_winner(ggst_vid_data_df, 
                                                characters_in_rounds_df, 
                                                new_agg_config)
    games_by_rounds_df, anomallies_df = agg.classify_rounds_into_games(round_winners_df)

    ##Debugging March 25th
    #games_by_rounds_df.to_csv("test_Mar_25th_Game_rounds.csv")
    #anomallies_df.to_csv("test_Mar_25th_anomallies.csv")
    ################
    
    games_agg_df = agg.aggregate_into_games(games_by_rounds_df, anomallies_df)
    games_agg_df = validate_draw_game_results(games_agg_df, games_by_rounds_df)
    games_agg_df = correct_game_scores(games_agg_df, games_by_rounds_df)
    
    output_name = vid_filename.split('.')[0][0:25].replace(' ', '_')
    output_folder = agg.create_csv_output_files(ggst_vid_data_df, games_agg_df, 
                                                games_by_rounds_df, anomallies_df, 
                                                output_name, create_json = True, 
                                                orignal_vid = vid_filename)
    end_time = datetime.now()
    vid_delta = (end_time - total_start).seconds
    video_length = get_video_duration(ggst_vid_data_df)
    print("Total extraction/aggregation processing time was {} seconds".format(vid_delta))
    print("Total length of video process was {} seconds.".format(video_length))
    return output_folder

def brute_force_extract_and_aggregate_video(video_path, fps_val, config):
    vid_filename = video_path.split('\\')[-1]
    #Loading template images & storing them in memory
    config.templ_img_dicts_ls = ex.load_tmp_imgs(config.templ_img_dicts_ls)

    start_time = datetime.now()
    #Brute force template matching function
    ggst_vid_data_df = ex.get_all_tmpl_scores_vid(video_path, config.templ_img_dicts_ls, 
                                                  config.templ_img_min_val_mappings, 
                                                  frames_per_sec = fps_val)
    end_time = datetime.now()
    vid_delta = (end_time - start_time).seconds
    print("Total extraction processing time was {} seconds (video source)".format(vid_delta))

    new_agg_config = agg.convert_agg_config_vals_based_on_fps(config.agg_config_4fps, 
                                                              config.fps_scaling_vals_ls, 
                                                              config.plus_one_vals_ls, 
                                                              fps_val)

    ggst_data_for_agg_df = agg.reduce_match_df_to_agg_df(ggst_vid_data_df)

    consolidated_rounds_df = agg.aggregate_into_rounds(ggst_data_for_agg_df, 
                                                       new_agg_config)

    characters_in_rounds_df = agg.extract_played_characters(ggst_data_for_agg_df, 
                                                            consolidated_rounds_df, 
                                                            new_agg_config)

    round_winners_df = agg.extract_round_winner(ggst_data_for_agg_df, 
                                                characters_in_rounds_df, 
                                                new_agg_config)

    games_by_rounds_df, anomallies_df = agg.classify_rounds_into_games(round_winners_df)

    games_agg_df = agg.aggregate_into_games(games_by_rounds_df, anomallies_df)
    
    games_agg_df = validate_draw_game_results(games_agg_df, games_by_rounds_df)
    games_agg_df = correct_game_scores(games_agg_df, games_by_rounds_df)
    
    output_name = vid_filename.split('.')[0][0:25]
    output_folder = agg.create_csv_output_files(ggst_vid_data_df, games_agg_df, 
                                                games_by_rounds_df, anomallies_df, 
                                                output_name, create_json = True, 
                                                orignal_vid = vid_filename)
    return output_folder

#video_path = "Test_Videos\\GuiltyGear-Strive_Baike-vs-Millia_2_Low_Health_for_While-2022-02-02.mp4"
#video_path = "{}\\{}".format(vid_dir, videos_ls[-1])
#video_path = "Test_Videos\\Guilty_Gear-Strive-Baiken-vs-Ram_2022-02-02.mp4"
#video_path = "Test_Videos\\Guilty_GearStrive-2021-11-01 21-Jack-O_vs_Ky_Double_KO.mp4"
#video_path = "Test_Videos\\Guilty_Gear-Strive-Baike-vs-button_pushing_Potemkin-2022-02-02.mp4"
#video_path = "Test_Videos\\Sept_11th-Jack-o-vs-Zato_1.mp4"
#video_path = "Test_Videos\\Happy_Chaos_Faust_Time_Out-Draw_Final_ROund_2022-01-27.mp4"
#90min Long video made from my matches
#video_path = "Test_Videos\\My_Baiken_Matches_90_mins_2022-03-13_16-01-57.mp4"
#Recentish NLBC from YT, ~40mins
#video_path =  "Test_Videos\\yt_dl\\NLBC 103 Top 16  Online  Tournament.mp4"
#video_path =  "Test_Videos\\yt_dl\\NLBC 103 Top 8  Online  Tournament.mp4"
#video_path =  "Test_Videos\\GGST-My-Day_2_Testament_matches_18mins-2022-03-29 17-39-38.mp4"
#video_path =  "Test_Videos\\yt_dl\\NLBC 104 Top 8  Online  Tournament.mp4"
video_path =  "Test_Videos\\yt_dl\\Frosty Faustings 2022 - Top 96.mp4"
#video_path =  "Test_Videos\\yt_dl\\Series E Sports Arena Week 11.mp4"
fps_val = 4
#fps_val = 2

#output_file_path = brute_force_extract_and_aggregate_video(video_path, fps_val, conf)
output_file_path = layered_extract_and_aggregate_video(video_path, fps_val, conf)
#output_file_path = timer_template_test_video(video_path, fps_val)

print("Output files located in the created folder: {}".format(output_file_path))

##Current brute force CV Extraction takes about 11 - 11.5 seconds per 1 second of video
##Layered function/approach is consistently around ~4.5 seconds per 1 second of video

#########
##Batch process a directory of videos 
vid_dir = 'Test_Videos'
#videos_ls = os.listdir(vid_dir)
videos_ls = []
#videos_ls.append('GGST-My-Day_2_Testament_matches_18mins-2022-03-29 17-39-38.mp4')
videos_ls.append('yt_dl\\NLBC 103 Top 16  Online  Tournament.mp4')
#videos_ls.append('My_Baiken_Matches_90_mins_2022-03-13_16-01-57.mp4')
videos_ls.append('yt_dl\\NLBC 104 Top 8  Online  Tournament.mp4')
#videos_ls.append('yt_dl\\Frosty Faustings 2022 - Top 96.mp4')
#videos_ls.append('yt_dl\\NLBC 103 Top 8  Online  Tournament.mp4')
#videos_ls.append('yt_dl\\Series E Sports Arena Week 11.mp4')
#videos_ls.append('yt_dl\\Can Opener Vol 36 GGST.mp4')
#videos_ls.remove('Guilty_Gear-Strive-Baike-vs-button_pushing_Potemkin-2022-02-02.mp4')

for video in videos_ls:
    vid_path = "{}\\{}".format(vid_dir, video)
    #output_file_path = brute_force_extract_and_aggregate_video(vid_path, fps_val, conf)
    output_file_path = layered_extract_and_aggregate_video(vid_path, fps_val, conf)
    print("Output files located in the created folder: {}".format(output_file_path))

###############################################################################
##A la Carte testing of the VLC playlist creation, it'll be included into the 
##stand alone function for just starter/ender round/game data. Might create a
##html file generator for a YT link, need to check out how chapters on posted YT
##videos work, and if that can be automated to generate

vidpl_rounds_df = pd.read_csv('output\\2022-4-11_8-25-4_Series_E_Sports_Arena_Wee\\Round_data_Series_E_Sports_Arena_Wee_2022-4-11_8-25-4.csv')
vidpl_games_df = pd.read_csv('output\\2022-4-11_8-25-4_Series_E_Sports_Arena_Wee\\Game_data_Series_E_Sports_Arena_Wee_2022-4-11_8-25-4.csv')
vidpl_anomallies_df = pd.read_csv('output\\2022-4-11_8-25-4_Series_E_Sports_Arena_Wee\\Anomalous_rounds_Series_E_Sports_Arena_Wee_2022-4-11_8-25-4.csv')
vidpl_vid_data_df = pd.read_csv('output\\2022-4-11_8-25-4_Series_E_Sports_Arena_Wee\\Visual_detection_data_Series_E_Sports_Arena_Wee_2022-4-11_8-25-4.csv')
file_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader\\Test_Videos\\yt_dl\\Series E Sports Arena Week 11.mp4"
output_folder = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader\\output\\2022-4-11_8-25-4_Series_E_Sports_Arena_Wee\\"

playlist_file = create_round_based_vlc_playlist(vidpl_rounds_df, vidpl_vid_data_df, 
                                                file_path, output_folder, 
                                                vidpl_anomallies_df)
print("{}".format(playlist_file))
playlist_file = create_game_based_vlc_playlist(vidpl_games_df, vidpl_vid_data_df, 
                                               file_path, output_folder, 
                                               vidpl_anomallies_df)
print("{}".format(playlist_file))
###############################################################################
"""
##Re-processing Game data APril 6th after finding a bug with correct_game_scores
#ggst_test_rounds_df = pd.read_csv('output\\2022-4-6_10-42-53_NLBC_104_Top_8__Online__T\\Round_data_NLBC_104_Top_8__Online__T_2022-4-6_10-42-53.csv')
#test_anomalies_df = pd.read_csv('output\\2022-4-6_10-42-53_NLBC_104_Top_8__Online__T\\Anomalous_rounds_NLBC_104_Top_8__Online__T_2022-4-6_10-42-53.csv')
ggst_test_rounds_df = pd.read_csv('output\\2022-4-6_17-26-24_My_Baiken_Matches_90_mins\\Round_data_My_Baiken_Matches_90_mins_2022-4-6_17-26-24.csv')
test_anomalies_df = pd.DataFrame({})
games_test_df = agg.aggregate_into_games(ggst_test_rounds_df, test_anomalies_df)
games_test_df = validate_draw_game_results(games_test_df, ggst_test_rounds_df)
games_test_df = correct_game_scores(games_test_df, ggst_test_rounds_df)
games_test_df = games_test_df.reset_index()

#games_test_df.to_csv("output\\2022-4-6_10-42-53_NLBC_104_Top_8__Online__T\\Game_Data_Manually_re-processed_NBLC_104_Top_8.csv", index=False)
games_test_df.to_csv("output\\2022-4-6_17-26-24_My_Baiken_Matches_90_mins\\Game_Data_Manually_re-processed_My_Baiken_Matches.csv", index=False)
"""
"""
ggst_vid_data_df = pd.read_csv('output\\2022-3-26_9-47-44_My_Baiken_Matches_90_mins\\Visual_detection_data_My_Baiken_Matches_90_mins_2022-3-26_9-47-44.csv')
##test_bool = agg._validate_duel_match_score(ggst_vid_data_df, 0.85)
#ggst_games_df = pd.read_csv('output\\2022-3-23_2-37-33_Guilty_Gear_Strive__Top_1\\Game_data_Guilty_Gear_Strive__Top_1_2022-3-23_2-37-33.csv')
ggst_rounds_df = pd.read_csv('output\\2022-3-26_9-47-44_My_Baiken_Matches_90_mins\\Round_data_My_Baiken_Matches_90_mins_2022-3-26_9-47-44.csv')
test_rounds_df = ggst_rounds_df.loc[((ggst_rounds_df.game_id == 'Game_25') | 
                                     (ggst_rounds_df.game_id == 'Game_24') |
                                     (ggst_rounds_df.game_id == 'Game_26'))]
test_rounds_df['character_1P'] = 'Unknown'
test_rounds_df['character_2P'] = 'Unknown'
#test_rounds_df.loc[58, 'character_1P'] = 'Unknown'
#test_rounds_df.loc[58, 'character_2P'] = 'Unknown'
#test_rounds_df = test_rounds_df.loc[57:57,]
import FGW_GGStrivagator_1 as agg
validated_rounds_df = agg._validate_unknown_round_duration(test_rounds_df, ggst_vid_data_df)
validated_rounds_df['character_1P'] = 'Unknown'
validated_rounds_df['character_2P'] = 'Unknown'
#validated_rounds_df = validated_rounds_df.loc[57:57,]
new_agg_config = agg.convert_agg_config_vals_based_on_fps(conf.agg_config_4fps, 
                                                          conf.fps_scaling_vals_ls, 
                                                          conf.plus_one_vals_ls, 
                                                          4)
test_new_char_rounds_df = agg.extract_played_characters(ggst_vid_data_df, validated_rounds_df, new_agg_config)
"""
#test_games_df = validate_draw_game_results(ggst_games_df, ggst_rounds_df)
###############################################################################
#Health Detect Test------------Remove when this is confirmed.
def detect_health_bar(frame_img):
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
        print("High health y1: {} w1: {} h1: {}".format(y1, w1, h1))
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
            print("Low health y1: {} w1: {} h1: {}".format(y1, w1, h1))
            if w1 >= min_w and h1 >= min_h and y1 < max_y and y1 > min_y:
                if w1 > w_val:
                    (x_loc, y_loc, w_val, h_val) = (x1, y1, w1, h1)
                    low_health_bool = True

    return (x_loc, y_loc, w_val, h_val, low_health_bool)

#Single image visul test
#img_path = 'output\\2022-3-23_2-37-33_Guilty_Gear_Strive__Top_1\\I-no-v-Axl_Health_detect_colour_issue_example.png'
img_path = 'output\\2022-3-24_4-9-34_Guilty_Gear_Strive__Top_1\\Health_Descripancy_17mins-10secs.png'
#img_path = 'output\\2022-3-24_4-9-34_Guilty_Gear_Strive__Top_1\\Health_Descripancy_17mins-11secs.png'

image = cv2.imread(img_path)
img_h, img_w = image.shape[0:2]

#Creating mask for Player 1 top screen
mask_P1 = np.zeros(image.shape[:2], dtype="uint8")
cv2.rectangle(mask_P1, (0, 0), (img_w // 2, round(img_h * 0.20)), 255, -1)

#Creating mask for Player 2 top screen
mask_P2 = np.zeros(image.shape[:2], dtype="uint8")
cv2.rectangle(mask_P2, ((img_w // 2) + 1, 0), (img_w, round(img_h * 0.20)), 255, -1)

masked_P1 = cv2.bitwise_and(image, image, mask=mask_P1)
masked_P2 = cv2.bitwise_and(image, image, mask=mask_P2)

(x_P1, y_P1, w_P1, h_P1, isLowHealthP1) = detect_health_bar(masked_P1)
(x_P2, y_P2, w_P2, h_P2, isLowHealthP2) = detect_health_bar(masked_P2)

high_health_colour = (36,255,12) #Green
low_health_colour = (36,230,230) #Yellow?

if isLowHealthP1:
    cv2.rectangle(image, (x_P1, y_P1), (x_P1 + w_P1, y_P1 + h_P1), high_health_colour, -1)
else:
    cv2.rectangle(image, (x_P1, y_P1), (x_P1 + w_P1, y_P1 + h_P1), low_health_colour, -1)
    
if isLowHealthP2:
    cv2.rectangle(image, (x_P2, y_P2), (x_P2 + w_P2, y_P2 + h_P2), high_health_colour, -1)
else:
    cv2.rectangle(image, (x_P2, y_P2), (x_P2 + w_P2, y_P2 + h_P2), low_health_colour, -1)
    

#cv2.rectangle(image, (x_P1, y_P1), (x_P1 + w_P1, y_P1 + h_P1), (36,255,12), -1)
#cv2.rectangle(image, (x_P2, y_P2), (x_P2 + w_P2, y_P2 + h_P2), (36,255,12), -1)

cv2.imshow("Health Bar detect", image)
#cv2.imshow("Zato 2P Test Portrait", test_img_dicts_processed_ls[18]['img_objs']['2P_Portrait'])
cv2.waitKey(0)
cv2.destroyAllWindows()
"""
##Testing starter_ender_tmple_scores_vid function
new_agg_config = agg.convert_agg_config_vals_based_on_fps(conf.agg_config_4fps, 
                                                          conf.fps_scaling_vals_ls, 
                                                          conf.plus_one_vals_ls, 
                                                          fps_val)
start_time = datetime.now()
#Brute force template matching function
ggst_vid_data_df = starter_ender_tmpl_scores_vid(video_path, 
                                                 conf.starter_ender_img_dicts_ls, 
                                                 conf.templ_img_min_val_mappings, 
                                                 new_agg_config['times_up_to_draw_frame_buffer'], 
                                                 frames_per_sec = fps_val)
end_time = datetime.now()
vid_delta = (end_time - start_time).seconds
print("Total extraction processing time was {} seconds (video source)".format(vid_delta))

consolidated_rounds_df = agg.aggregate_into_rounds(ggst_vid_data_df, new_agg_config)

ggst_in_round_data_df = get_in_round_data(video_path, ggst_vid_data_df, 
                                          consolidated_rounds_df, 
                                          conf.char_templ_img_dicts_ls, 
                                          conf.timer_templ_img_dict_ls, 
                                          conf.templ_img_min_val_mappings)
"""


"""
#################################################################
##Test code for finding video dimensions
##Use this to modify the template image load function to scale templates if res
## isn't 1080x1920 (I think that's accurate for 1080p)
vcap = cv2.VideoCapture('video.avi')

width = vcap.get(cv2.CAP_PROP_FRAME_WIDTH )
height = vcap.get(cv2.CAP_PROP_FRAME_HEIGHT )
"""