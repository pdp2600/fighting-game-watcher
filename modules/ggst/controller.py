# -*- coding: utf-8 -*-
"""
Created on Fri Mar 18 15:25:38 2022

Controller module with functions which integrate the extraction & aggregation
functions and processes.

@author: PDP2600
"""
import numpy as np
import cv2
import os
import sys
import pandas as pd
from datetime import datetime
#Loading local modules which aren't packages
dir_path = os.path.dirname(__file__)
sys.path.insert(0, dir_path)
import extraction as ex
import aggregation as agg
import output as out


##########
##########Start of changes May DD H:MMpm
def _no_duel_number_matches(match_scores_dict:dict)-> bool:
    total_duel_num_score = match_scores_dict['Starter_Number_1']
    total_duel_num_score += match_scores_dict['Starter_Number_2']
    total_duel_num_score += match_scores_dict['Starter_Number_3']
    return (total_duel_num_score == 0)
    
def _no_starter_matches(match_scores_dict:dict)-> bool:
    total_starter_score = 0 if _no_duel_number_matches(match_scores_dict) else 1
    total_starter_score += match_scores_dict['Starter_Duel']
    total_starter_score += match_scores_dict['Starter_Number_Final']
    total_starter_score += match_scores_dict['Starter_Lets_Rock']
    return (total_starter_score == 0)

#Creates a frame dict w/ all Starter & Ender scores set to 0 for 1st round of matching
def _create_zero_scores_frame_dict(time_in_secs:float)-> dict:
    return {'Time_in_Secs' : int(time_in_secs), 
            'Frame_Number_secs' : time_in_secs, 
            'Starter_Duel': 0, 'Starter_Number_1': 0, 'Starter_Number_2': 0, 
            'Starter_Number_3': 0, 'Starter_Number_Final': 0, 
            'Starter_Lets_Rock': 0, 'Ender_Slash': 0, 'Ender_Perfect': 0,
            'Ender_Double_KO': 0, 'Ender_Times_Up': 0, 'Ender_Draw': 0, 
            'Game_UI_Timer_Outline': 0
            }

def _set_duel_values_to_zero(match_scores_dict:dict)-> dict:
    match_scores_dict['Starter_Duel'] = 0
    match_scores_dict['Starter_Number_1'] = 0
    match_scores_dict['Starter_Number_2'] = 0
    match_scores_dict['Starter_Number_3'] = 0
    match_scores_dict['Starter_Number_Final'] = 0
    
    return match_scores_dict

def vet_match_score(img, tmpl_img, tmpl_key:str, tmpl_dict:dict, 
                    min_mappings:dict)-> float:           
    #Getting Template Match Score min/max w/ (x, y) location data
    (minVal, maxVal, minLoc, maxLoc) = ex.get_match_template_score(img, 
                                                                   tmpl_img, 
                                                                   tmpl_key)
    #Only reporting scores which are over configureed minimums, otherwise it's 0
    return ex.check_min_match_val(tmpl_key, tmpl_dict, min_mappings, maxVal)

def starter_ender_tmpl_scores_vid(vid_file_path:str, template_img_dicts_ls:list, 
                                  min_mappings:dict, draw_buffer:int, 
                                  frames_per_sec:int = 4, is_verbose:bool=False):
    template_img_dicts:list = ex.load_tmp_imgs(template_img_dicts_ls)
    tmp_match_scores_df = pd.DataFrame({})
    index_num:int = 0
    seconds:float = 0
    #Frames_per_second min 1 fps & max 60 fps
    frame_rate:float = (1 / np.clip(frames_per_sec, 1, 60))
    starter_dict:dict = {}
    ender_dict:dict = {}
    ui_dict:dict = {}
    for img_dict in template_img_dicts:
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

    check_for_draw:bool = False
    frames_to_check_draw:int = 0
    
    vidcap = cv2.VideoCapture(vid_file_path)
    vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
    hasFrame,image = vidcap.read()
    
    while hasFrame:
        if is_verbose:
            print("Starter<->Ender | Checking Time: {}secs, Frame: {} (in secs)... "
                  .format(int(seconds), seconds))
        #Decrement the draw buffer when check_for_draw bool is True
        frames_to_check_draw = (frames_to_check_draw - 1) if check_for_draw else 0
        match_scores:dict = _create_zero_scores_frame_dict(seconds)
        #Getting Duel score for frame, to begin starter frame template match logic
        match_scores['Starter_Duel'] = vet_match_score(image, duel_img, 'Duel', 
                                                       starter_dict, 
                                                       min_mappings)
        if match_scores['Starter_Duel'] > 0:
            match_scores['Starter_Number_1'] = vet_match_score(image, num_1_img, 
                                                               'Number_1', 
                                                               starter_dict, 
                                                               min_mappings)
            match_scores['Starter_Number_2'] = vet_match_score(image, num_2_img, 
                                                               'Number_2', 
                                                               starter_dict, 
                                                               min_mappings)
            match_scores['Starter_Number_3'] = vet_match_score(image, num_3_img, 
                                                               'Number_3', 
                                                               starter_dict, 
                                                               min_mappings)
            #If there are no duel number matches, check for duel Final
            if (_no_duel_number_matches(match_scores)):
                match_scores['Starter_Number_Final'] = vet_match_score(image, 
                                                                       num_final_img, 
                                                                       'Number_Final', 
                                                                       starter_dict, 
                                                                       min_mappings)
                #When there are no round number matches, Duel score is invalid, set to 0
                if match_scores['Starter_Number_Final'] == 0:
                    match_scores['Starter_Duel'] = 0
            
            #Duel 1 & 2 is sometimes a false positive for Ender Times Up, checking for that
            match_scores['Ender_Times_Up'] = vet_match_score(image, times_up_img, 
                                                             'Times_Up', 
                                                             ender_dict, 
                                                             min_mappings)
            #If Times Up (word to O.C.) is detected, reset Duel values
            if match_scores['Ender_Times_Up'] > 0:
                match_scores = _set_duel_values_to_zero(match_scores)
                check_for_draw = True
                frames_to_check_draw = draw_buffer
        #Made Let's Rock checked everytime due to false positives with Duel 1s
        match_scores['Starter_Lets_Rock'] = vet_match_score(image, lets_rock_img, 
                                                            'Lets_Rock', 
                                                            starter_dict, 
                                                            min_mappings)
        if check_for_draw and (frames_to_check_draw == 0):
            check_for_draw = False
        #Check for enders only if no valid Starters are detected
        if (_no_starter_matches(match_scores)):
            match_scores['Ender_Slash'] = vet_match_score(image, slash_img, 
                                                          'Slash', ender_dict, 
                                                          min_mappings)
            total_ender_scores = match_scores['Ender_Slash']
            if total_ender_scores == 0:
                match_scores['Ender_Perfect'] = vet_match_score(image, 
                                                                perfect_img, 
                                                                'Perfect', 
                                                                ender_dict, 
                                                                min_mappings)
                total_ender_scores = match_scores['Ender_Perfect']
            
            if total_ender_scores == 0:
                match_scores['Ender_Double_KO'] = vet_match_score(image, 
                                                                  double_ko_img, 
                                                                  'Double_KO', 
                                                                  ender_dict, 
                                                                  min_mappings)
                total_ender_scores = match_scores['Ender_Double_KO']
            
            if total_ender_scores == 0 and match_scores['Ender_Times_Up'] == 0:
                match_scores['Ender_Times_Up'] = vet_match_score(image, 
                                                                 times_up_img, 
                                                                 'Times_Up', 
                                                                 ender_dict, 
                                                                 min_mappings)
                if match_scores['Ender_Times_Up'] > 0:
                    check_for_draw = True
                    frames_to_check_draw = draw_buffer
            #Check for Draw if Times Up not detected & check_forDraw flag active
            if (match_scores['Ender_Times_Up'] == 0) and check_for_draw:
                match_scores['Ender_Draw'] = vet_match_score(image, draw_img, 
                                                             'Draw', ender_dict, 
                                                             min_mappings)

        match_scores['Game_UI_Timer_Outline'] = vet_match_score(image, 
                                                                timer_ui_img, 
                                                                'Timer_Outline', 
                                                                ui_dict, 
                                                                min_mappings)
        
        tmp_match_scores_df = tmp_match_scores_df.append(pd.DataFrame(match_scores, 
                                                                      index=[index_num]), 
                                                         sort=False)
        index_num = index_num + 1
        seconds = seconds + frame_rate
        vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
        hasFrame,image = vidcap.read()
    
    return tmp_match_scores_df

def _set_in_round_cols_to_zero(ggst_data_df, char_img_dicts_ls:list):
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

def get_player_win_template_data(video_path:str, ggst_data_df, rounds_df, 
                                 ender_img_dict:dict, min_mappings:dict, 
                                 win_tmpl_buffer:int, frames_after_ender:int, 
                                 is_verbose:bool = False):
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
                    vetted_score = vet_match_score(image, 
                                                   img_dict['img_objs']['1P_Win'], 
                                                   '1P_Win', ender_img_dict, 
                                                   min_mappings)
                    ggst_new_data_df.loc[index, 'Ender_1P_Win'] = vetted_score
                
                    vetted_score = vet_match_score(image, 
                                                   img_dict['img_objs']['2P_Win'], 
                                                   '2P_Win', ender_img_dict, 
                                                   min_mappings)
                    ggst_new_data_df.loc[index, 'Ender_2P_Win'] = vetted_score
    return ggst_new_data_df

#When there is adequate data, the char match is predicted & reduced to those two chars
def _get_predict_chars_dict_ls(ggst_char_pred_df, all_img_dicts:list, 
                               min_char_delta:float):
    char_portraits_agg_ls = agg.get_char_portrait_col_names(list(ggst_char_pred_df))
    player_1_characters_ls = [x for x in char_portraits_agg_ls if '1P_Portrait' in x]
    player_2_characters_ls = [x for x in char_portraits_agg_ls if '2P_Portrait' in x]
    
    player_1_char = agg.get_character_used(ggst_char_pred_df, player_1_characters_ls, 
                                           min_char_delta)
    player_2_char = agg.get_character_used(ggst_char_pred_df, player_2_characters_ls, 
                                           min_char_delta)
    if (player_1_char == 'Unknown') or (player_2_char == 'Unknown'):
        return all_img_dicts
    else:
        new_img_dict_ls = []
        for img_dict in all_img_dicts:
            if ((img_dict['Name'] == player_1_char) or (img_dict['Name'] == player_2_char)):
                new_img_dict_ls.append(img_dict)
                
        return new_img_dict_ls

#2nd phase of extratction checking for characters played & items related to player health
#Checks frames based on Round atart & end established in the phase 1 extract/aggregation
def get_in_round_data(video_path:str, ggst_data_df, rounds_df, 
                      char_img_dicts:list, min_mappings:dict, 
                      char_pred_frame_buffer:int, min_char_delta:float, 
                      post_ender_health_buffer:int, is_verbose:bool=False):
    ggst_new_data_df = _set_in_round_cols_to_zero(ggst_data_df.copy(), char_img_dicts)
    all_img_dicts:list = char_img_dicts
    all_img_dicts = ex.load_tmp_imgs(all_img_dicts)
    vidcap = cv2.VideoCapture(video_path)    
    for j, row in rounds_df.iterrows():
        start_index = row.start_index
        end_index = row.end_index
        chars_predicted = False
        img_dicts:list = all_img_dicts.copy()
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
                        img_dicts = _get_predict_chars_dict_ls(ggst_char_pred_df, 
                                                               all_img_dicts, 
                                                               min_char_delta)
                        chars_predicted = True if len(img_dicts) < 3 else False
                    #Itteration through all image dicts or predicted char image dicts
                    for img_dict in img_dicts:
                        dict_name:str = img_dict['Name']
                        #Creating a list of the dict keys pretaining to templateimage paths
                        template_img_keys = list(img_dict['img_objs'].keys())
                        #Running template matching on every image in the dict
                        for tmpl_img_key in template_img_keys:                        
                            tmpl_img = img_dict['img_objs'][tmpl_img_key]
                            col_name = "{}_{}".format(dict_name, tmpl_img_key)
                            score = vet_match_score(image, tmpl_img, 
                                                    tmpl_img_key, img_dict, 
                                                    min_mappings)
                            ggst_new_data_df.loc[index, col_name] = score
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

#Extracts only round/game start/end times (games may not be able to be accurately aggregated)
def extract_match_video_timecodes_only(video_path:str, fps_val:int, config, 
                                       verbose_log:bool=False)-> str:
    vid_filename = video_path.split('\\')[-1]
    new_agg_config = agg.convert_agg_config_vals_based_on_fps(config.agg_config_4fps, 
                                                              config.fps_scaling_vals_ls, 
                                                              config.plus_one_vals_ls, 
                                                              fps_val)
    total_start = datetime.now()
    ggst_vid_data_df = starter_ender_tmpl_scores_vid(video_path, 
                                                     config.starter_ender_img_dicts_ls, 
                                                     config.templ_img_min_val_mappings, 
                                                     new_agg_config['times_up_to_draw_frame_buffer'], 
                                                     frames_per_sec = fps_val, 
                                                     is_verbose=verbose_log)
    consolidated_rounds_df = agg.aggregate_into_rounds(ggst_vid_data_df, 
                                                       new_agg_config)
    games_by_rounds_df, anomallies_df = agg.classify_rounds_into_games(consolidated_rounds_df)
    games_agg_df = agg.aggregate_into_games(games_by_rounds_df, anomallies_df)
    games_agg_df = validate_draw_game_results(games_agg_df, games_by_rounds_df)

    output_name = vid_filename.split('.')[0][0:25].replace(' ', '_')
    output_folder = out.create_csv_output_files(ggst_vid_data_df, games_agg_df, 
                                                games_by_rounds_df, anomallies_df, 
                                                output_name, create_json = True, 
                                                orignal_vid = vid_filename)    
    #For playlist creation, requires video_path to be the full path of video
    out.create_round_based_vlc_playlist(games_by_rounds_df, ggst_vid_data_df, 
                                        video_path, output_folder, anomallies_df)
    out.create_game_based_vlc_playlist(games_agg_df, ggst_vid_data_df, 
                                       video_path, output_folder, anomallies_df)
    out.create_round_based_yt_chapters(games_by_rounds_df, output_folder, 
                                       anomallies_df=anomallies_df, 
                                       prepend_id=True)
    out.create_game_based_yt_chapters(games_agg_df, output_folder, 
                                      anomallies_df=anomallies_df, 
                                      prepend_id=True)
    end_time = datetime.now()
    vid_delta = (end_time - total_start).seconds
    video_length = out.get_video_duration(ggst_vid_data_df)
    print("Total extraction/aggregation processing time was {} seconds".format(vid_delta))
    print("Total length of video process was {} seconds.".format(video_length))
    return output_folder

#Approach to combine extraction & aggregation to limit unnecessary template matching
#Round Start/End templates found 1st, processed in round data, then those bounaries
#are used to target other template matching to limit the number of frames to check
def layered_extract_and_aggregate_video(video_path:str, fps_val:int, config, 
                                        verbose_log:bool=False)-> str:
    vid_filename = video_path.split('\\')[-1]
    new_agg_config = agg.convert_agg_config_vals_based_on_fps(config.agg_config_4fps, 
                                                              config.fps_scaling_vals_ls, 
                                                              config.plus_one_vals_ls, 
                                                              fps_val)
    total_start = datetime.now()
    ggst_vid_data_df = starter_ender_tmpl_scores_vid(video_path, 
                                                     config.starter_ender_img_dicts_ls, 
                                                     config.templ_img_min_val_mappings, 
                                                     new_agg_config['times_up_to_draw_frame_buffer'], 
                                                     frames_per_sec = fps_val, 
                                                     is_verbose=verbose_log)
    consolidated_rounds_df = agg.aggregate_into_rounds(ggst_vid_data_df, new_agg_config)
    ggst_vid_data_df = get_in_round_data(video_path, ggst_vid_data_df, 
                                         consolidated_rounds_df, 
                                         config.char_templ_img_dicts_ls, 
                                         config.templ_img_min_val_mappings,
                                         new_agg_config['char_prediction_frame_buffer'], 
                                         new_agg_config['min_character_delta'],
                                         new_agg_config['health_after_ender_frame_buffer'], 
                                         is_verbose=verbose_log)
    ggst_vid_data_df = get_player_win_template_data(video_path, ggst_vid_data_df, 
                                                    consolidated_rounds_df, 
                                                    config.round_ender_templ_imgs, 
                                                    config.templ_img_min_val_mappings, 
                                                    new_agg_config['player_win_after_ender_buffer'], 
                                                    new_agg_config['player_win_frame_after_ender_start'], 
                                                    is_verbose=verbose_log)
    characters_in_rounds_df = agg.extract_played_characters(ggst_vid_data_df, 
                                                            consolidated_rounds_df, 
                                                            new_agg_config)
    round_winners_df = agg.extract_round_winner(ggst_vid_data_df, 
                                                characters_in_rounds_df, 
                                                new_agg_config)
    games_by_rounds_df, anomallies_df = agg.classify_rounds_into_games(round_winners_df)
    
    games_agg_df = agg.aggregate_into_games(games_by_rounds_df, anomallies_df)
    games_agg_df = validate_draw_game_results(games_agg_df, games_by_rounds_df)
    games_agg_df = correct_game_scores(games_agg_df, games_by_rounds_df)
    
    output_name = vid_filename.split('.')[0][0:25].replace(' ', '_')
    output_folder = out.create_csv_output_files(ggst_vid_data_df, games_agg_df, 
                                                games_by_rounds_df, anomallies_df, 
                                                output_name, create_json = True, 
                                                orignal_vid = vid_filename)
    #For playlist creation, requires video_path to be the full path of video
    out.create_round_based_vlc_playlist(games_by_rounds_df, ggst_vid_data_df, 
                                        video_path, output_folder, anomallies_df)
    out.create_game_based_vlc_playlist(games_agg_df, ggst_vid_data_df, 
                                       video_path, output_folder, anomallies_df)
    out.create_round_based_yt_chapters(games_by_rounds_df, output_folder, 
                                       anomallies_df=anomallies_df)
    out.create_game_based_yt_chapters(games_agg_df, output_folder, 
                                      anomallies_df=anomallies_df)
    end_time = datetime.now()
    vid_delta = (end_time - total_start).seconds
    video_length = out.get_video_duration(ggst_vid_data_df)
    print("Total extraction/aggregation processing time was {} seconds".format(vid_delta))
    print("Total length of video process was {} seconds.".format(video_length))
    return output_folder

def brute_force_extract_and_aggregate_video(video_path:str, fps_val:int, config,
                                            verbose_log:bool=False)-> str:
    vid_filename = video_path.split('\\')[-1]
    #Loading template images & storing them in memory
    config.templ_img_dicts_ls = ex.load_tmp_imgs(config.templ_img_dicts_ls)
    start_time = datetime.now()
    ggst_vid_data_df = ex.get_all_tmpl_scores_vid(video_path, config.templ_img_dicts_ls, 
                                                  config.templ_img_min_val_mappings, 
                                                  frames_per_sec = fps_val)
    end_time = datetime.now()
    vid_delta = (end_time - start_time).seconds
    video_length = out.get_video_duration(ggst_vid_data_df)
    print("Total extraction processing time was {} seconds (video source)".format(vid_delta))
    print("Total length of video process was {} seconds.".format(video_length))
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
    output_folder = out.create_csv_output_files(ggst_vid_data_df, games_agg_df, 
                                                games_by_rounds_df, anomallies_df, 
                                                output_name, create_json = True, 
                                                orignal_vid = vid_filename)
    #For playlist creation, requires video_path to be the full path of video
    full_vid_path = "{}{}".format(os.getcwd(), video_path)
    out.create_round_based_vlc_playlist(games_by_rounds_df, ggst_vid_data_df, 
                                        full_vid_path, output_folder, 
                                        anomallies_df)
    out.create_game_based_vlc_playlist(games_agg_df, ggst_vid_data_df, 
                                       full_vid_path, output_folder, 
                                       anomallies_df)
    out.create_round_based_yt_chapters(games_by_rounds_df, output_folder, 
                                       anomallies_df=anomallies_df)
    out.create_game_based_yt_chapters(games_agg_df, output_folder, 
                                      anomallies_df=anomallies_df)
    return output_folder
