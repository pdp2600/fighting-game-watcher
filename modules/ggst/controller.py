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


def _no_duel_number_matches(match_scores:dict)-> bool:
    """Returns whether every "Duel" number had match scores of 0.
    -------------------------------------------------------------------------
    -=match_scores=- Dict w/ "Duel" number match scores for a frame/row.
    -------------------------------------------------------------------------
    [-return-] Boolean value of if all the "Duel" number match scores are 0."""
    total_duel_num_score = match_scores['Starter_Number_1']
    total_duel_num_score += match_scores['Starter_Number_2']
    total_duel_num_score += match_scores['Starter_Number_3']
    return (total_duel_num_score == 0)
    
def _no_starter_matches(match_scores:dict)-> bool:
    """Returns whether every "Starter" template had a match score of 0.
    -------------------------------------------------------------------------
    -=match_scores=- Dict w/ "Duel" number match scores for a frame/row.
    -------------------------------------------------------------------------
    [-return-] Boolean value of if all the "Starter" match scores are 0."""
    total_starter_score = 0 if _no_duel_number_matches(match_scores) else 1
    total_starter_score += match_scores['Starter_Duel']
    total_starter_score += match_scores['Starter_Number_Final']
    total_starter_score += match_scores['Starter_Lets_Rock']
    return (total_starter_score == 0)

def _create_zero_scores_frame_dict(time_in_secs:float)-> dict:
    """Creates a match score dict for a frame/row, w/ Starter/Ender scores set 
    to zero.
    -------------------------------------------------------------------------
    -=match_scores=- Dict w/ "Duel" number match scores for a frame/row.
    -------------------------------------------------------------------------
    [-return-] Match score dict for a frame/row w/ scores set to zero."""
    return {'Time_in_Secs' : int(time_in_secs), 
            'Frame_Number_secs' : time_in_secs, 
            'Starter_Duel': 0, 'Starter_Number_1': 0, 'Starter_Number_2': 0, 
            'Starter_Number_3': 0, 'Starter_Number_Final': 0, 
            'Starter_Lets_Rock': 0, 'Ender_Slash': 0, 'Ender_Perfect': 0,
            'Ender_Double_KO': 0, 'Ender_Times_Up': 0, 'Ender_Draw': 0, 
            'Game_UI_Timer_Outline': 0
            }

def _set_duel_values_to_zero(match_scores:dict)-> dict:
    """Resets all template match scores related to "Duel" matches, to 0.
    -------------------------------------------------------------------------
    -=match_scores=- Dict w/ "Duel" number match scores for a frame/row.
    -------------------------------------------------------------------------
    [-return-] Match score dict w/ "Duel" scores reset to 0."""
    new_match_scores:dict = match_scores.copy()
    new_match_scores['Starter_Duel'] = 0
    new_match_scores['Starter_Number_1'] = 0
    new_match_scores['Starter_Number_2'] = 0
    new_match_scores['Starter_Number_3'] = 0
    new_match_scores['Starter_Number_Final'] = 0
    
    return new_match_scores

#Checks a template image against a frame image & changes score to 0 if minimum
#score is not met for the category of template image.
def vet_match_score(img, tmpl_img, tmpl_key:str, tmpl_dict:dict, 
                    min_mappings:dict)-> float:           
    """Gets the template match score for a template in an image, & checks if 
    the score meets the minimum for that specific or category of template.
    -------------------------------------------------------------------------
    -=img=- Frame image to check, read in using OpenCV (numpy image object).
    -=tmpl_img=- Template image, read in using OpenCV (numpy image object).
    -=tmpl_key=- The key used to identify the template image name.
    -=tmpl_dict=- Dict associated with template image used.
    -=min_mappings=- From the config file, defines a mapping between template 
      image path key & the key used to store the minimum value for that 
      specific template image or category of template image.
    -------------------------------------------------------------------------
    [-return-] Match score for template when it's above its minimum score, or 0."""
    (minVal, maxVal, minLoc, maxLoc) = ex.get_match_template_score(img, 
                                                                   tmpl_img, 
                                                                   tmpl_key)
    return ex.check_min_match_val(tmpl_key, tmpl_dict, min_mappings, maxVal)

def starter_ender_tmpl_scores_vid(vid_file_path:str, tmpl_img_dicts:list, 
                                  min_mappings:dict, draw_buffer:int, 
                                  frames_per_sec:int = 4, is_verbose:bool=False):
    """Does template matching for all Starter/Ender related template images, 
    for a video. Number of frames per second dictates granularity of processing.
    -------------------------------------------------------------------------
    -=vid_file_path=- Path of the video files' location (relative or absolute).
    -=tmpl_img_dicts=- From the config file, a list of dicts used to define the 
      template images & other properties like match score minimums.
    -=min_mappings=- From the config file, defines a mapping between template 
      image path key & the key used to store the minimum value for that 
      specific template image or category of template image.
    -=draw_buffer=- Config value, number of frames after "Times Up" Ender is 
      detected to check for "Draw" Ender template.
    -=frames_per_sec=- Number of frames per second to process. While it can be
      a value between 1 to 60, 2 & 4 are what testing & tuning were based on.
    -=is_verbose=- Whether progress updates are printed to console.
    -------------------------------------------------------------------------
    [-return-] DataFrame w/ all the Starter/Ender template match scores for a 
     video. Number of rows = Length of Video / (1 / frames_per_sec)"""
    template_img_dicts:list = ex.load_tmp_imgs(tmpl_img_dicts)
    tmp_match_scores_df = pd.DataFrame({})
    index_num:int = 0
    seconds:float = 0
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
        frames_to_check_draw = ((frames_to_check_draw - 1) if check_for_draw 
                                else 0)
        match_scores:dict = _create_zero_scores_frame_dict(seconds)

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
            if (_no_duel_number_matches(match_scores)):
                match_scores['Starter_Number_Final'] = vet_match_score(image, 
                                                                       num_final_img, 
                                                                       'Number_Final', 
                                                                       starter_dict, 
                                                                       min_mappings)
                #When "number" match scores are all 0, Duel score is reset to 0.
                if match_scores['Starter_Number_Final'] == 0:
                    match_scores['Starter_Duel'] = 0
            
            match_scores['Ender_Times_Up'] = vet_match_score(image, times_up_img, 
                                                             'Times_Up', 
                                                             ender_dict, 
                                                             min_mappings)
            #Duel 1/2 is sometimes a false positive for Ender Times Up,
            #When Times Up is detected, reset Duel match scores to 0
            if match_scores['Ender_Times_Up'] > 0:
                match_scores = _set_duel_values_to_zero(match_scores)
                check_for_draw = True
                frames_to_check_draw = draw_buffer
        #Let's Rock checked everytime due to false positives with Duel 1
        match_scores['Starter_Lets_Rock'] = vet_match_score(image, lets_rock_img, 
                                                            'Lets_Rock', 
                                                            starter_dict, 
                                                            min_mappings)
        if check_for_draw and (frames_to_check_draw == 0):
            check_for_draw = False
        #Check for other enders only if no valid Starters are detected
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
                                                                      index=
                                                                      [index_num]), 
                                                         sort=False)
        index_num = index_num + 1
        seconds = seconds + frame_rate
        vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
        hasFrame,image = vidcap.read()

    return tmp_match_scores_df

def _set_in_round_cols_to_zero(ggst_data_df, char_img_dicts:list):
    """Adds character portrait & health value columns w/ values of 0.
    -------------------------------------------------------------------------
    -=ggst_data_df=- DataFrame w/ template match scores that have been 
      extracted.
    -=char_img_dicts=- From config file, dicts related to character templates.
    -------------------------------------------------------------------------
    [-return-] Passed in DataFrame, w/ character portrait & health columns 
     added, which are populated w/ placeholder values of 0."""
    ggst_zero_data_df = ggst_data_df.copy()
    for char_dict in char_img_dicts:
        char_P1_col_name = "{}_1P_Portrait".format(char_dict['Name'])
        char_P2_col_name = "{}_2P_Portrait".format(char_dict['Name'])
        ggst_zero_data_df[char_P1_col_name] = 0
        ggst_zero_data_df[char_P2_col_name] = 0
    
    ggst_zero_data_df['1P_High_Health'] = 0
    ggst_zero_data_df['1P_Low_Health'] = 0
    ggst_zero_data_df['2P_High_Health'] = 0
    ggst_zero_data_df['2P_Low_Health'] = 0
    
    return ggst_zero_data_df

def get_player_win_template_data(video_path:str, ggst_data_df, rounds_df, 
                                 ender_img_dict:dict, min_mappings:dict, 
                                 win_tmpl_buffer:int, frames_after_ender:int, 
                                 is_verbose:bool = False):
    """Based on previous extracted template match scores, check for player win 
    templates. Requires Starter/Ender processing results to be processed into 
    consolidated round blocks. In practice, these templates are not found often, 
    since players usually press buttons before these player win images show up.
    -------------------------------------------------------------------------
    -=video_path=- Path of the video files' location (relative or absolute).
    -=ggst_data_df=- DataFrame w/ template match scores that have been 
      extracted.
    -=rounds_df=- DataFrame w/ consolidated round blocks.
    -=ender_img_dict=- From the config file, defines Ender template images & 
      minimums.
    -=min_mappings=- From the config file, defines a mapping between template 
      image path key & the key used to store the minimum value for that 
      specific template image or category of template image.
    -=win_tmpl_buffer=- Config value, how many frames after the ender ends to 
      check for player win templates.
    -=frames_after_ender=- Config value, how many frames past the end of the 
      ender to start checking for player win templates.
    -=is_verbose=- Whether progress updates are printed to console.
    -------------------------------------------------------------------------
    [-return-] DataFrame w/ all the existing template match scores, added w/ 
     the results of player win template matching."""
    ggst_new_data_df = ggst_data_df.copy()
    ggst_new_data_df['Ender_1P_Win'] = 0
    ggst_new_data_df['Ender_2P_Win'] = 0
    all_img_dicts:list = [ender_img_dict]
    all_img_dicts = ex.load_tmp_imgs(all_img_dicts)
    img_dict:dict = all_img_dicts[0]
    vidcap = cv2.VideoCapture(video_path)
    
    for j, row in rounds_df.iterrows():
        if (row.end_index != -1):
            start_index:int = row.end_index + frames_after_ender
            end_index:int = row.end_index + win_tmpl_buffer
            last_index:int = list(ggst_new_data_df.index)[-1]
            start_index = last_index if start_index > last_index else start_index
            end_index = last_index if end_index > last_index else end_index
            ggst_round_data_df = ggst_new_data_df.loc[start_index:end_index]

            for index, row in ggst_round_data_df.iterrows():
                seconds:float = row.Frame_Number_secs
                vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
                hasFrame,image = vidcap.read()
                if is_verbose:
                    print("Checking 1P/2P Win Templates | Checking Time: {}secs, Frame: {} (in secs)... "
                          .format(int(seconds), seconds))
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

def _get_predict_chars_dict_ls(ggst_char_pred_df, all_img_dicts:list, 
                               min_char_delta:float)->list:
    """When the character detection data so far for the round has sufficent 
    data to predict the P1 & P2 characters being used, the template images used 
    for character portrait matches is reduced to those 2 character (or 1 in the 
    case of a mirror match). Optimization step for character portrait detection.
    -------------------------------------------------------------------------
    -=ggst_char_pred_df=- DataFrame w/ raw extracted data from the start of a 
      round to the number of frames defined to be able to make confident 
      character predictions.
    -=all_img_dicts=- From config file, all character template image dicts.
    -=min_char_delta=- Config value. Minimum difference in match score to 
      decide if there's an undisputed character in the case of multiple 
      characters detected for the same frame.
    -------------------------------------------------------------------------
    [-return-] List of character dicts. Is either all_img_dicts, or only the 
     character dicts of the characters predicted for the given data."""
    char_portraits_agg:list = agg.get_char_portrait_col_names(list(ggst_char_pred_df))
    player_1_characters = [x for x in char_portraits_agg if '1P_Portrait' in x]
    player_2_characters = [x for x in char_portraits_agg if '2P_Portrait' in x]
    
    player_1_char = agg.get_character_used(ggst_char_pred_df, player_1_characters, 
                                           min_char_delta)
    player_2_char = agg.get_character_used(ggst_char_pred_df, player_2_characters, 
                                           min_char_delta)
    if (player_1_char == 'Unknown') or (player_2_char == 'Unknown'):
        return all_img_dicts
    else:
        new_img_dicts:list = []
        for img_dict in all_img_dicts:
            if ((img_dict['Name'] == player_1_char) or 
                (img_dict['Name'] == player_2_char)):
                new_img_dicts.append(img_dict)
                
        return new_img_dicts

def get_in_round_data(video_path:str, ggst_data_df, rounds_df, 
                      char_img_dicts:list, min_mappings:dict, 
                      char_pred_frame_buffer:int, min_char_delta:float, 
                      post_ender_health_buffer:int, is_verbose:bool=False):
    """Based on previous extracted template match scores, it checks the frames 
    which belong to game rounds, & extracts player characters & health data.
    -------------------------------------------------------------------------
    -=video_path=- Path of the video files' location (relative or absolute).
    -=ggst_data_df=- DataFrame w/ template match scores that have been 
      extracted.
    -=rounds_df=- DataFrame w/ consolidated round blocks.
    -=char_img_dicts=- From config file, dicts related to character templates.
    -=min_mappings=- From the config file, defines a mapping between template 
      image path key & the key used to store the minimum value for that 
      specific template image or category of template image.
    -=char_pred_frame_buffer=- Config value, frames after start of round, to 
      attempt to predict characters, for optimizing character portrait matches.
    -=min_char_delta=- Config value. Minimum difference in match score to 
      decide if there's an undisputed character in the case of multiple 
      characters detected for the same frame.
    -=post_ender_health_buffer=- Config value. Number of frames after the end 
      of the ender to check health data to predict the round winner.
    -=is_verbose=- Whether progress updates are printed to console.
    -------------------------------------------------------------------------
    [-return-] DataFrame w/ all the existing template match scores, added w/ 
     the results of player character template matches & health data extraction."""
    ggst_new_data_df = _set_in_round_cols_to_zero(ggst_data_df.copy(), 
                                                  char_img_dicts)
    all_img_dicts:list = char_img_dicts.copy()
    all_img_dicts = ex.load_tmp_imgs(all_img_dicts)
    vidcap = cv2.VideoCapture(video_path)    
    for j, row in rounds_df.iterrows():
        start_index:int = row.start_index
        end_index:int = row.end_index
        chars_predicted:bool = False
        img_dicts:list = all_img_dicts.copy()
        #Only run template matching when a round has a defined start & end index
        if (start_index != -1) and (end_index != -1):
            if len(ggst_new_data_df) > (end_index + post_ender_health_buffer):
                end_index = end_index + post_ender_health_buffer
            ggst_round_data_df = ggst_new_data_df.loc[start_index:end_index]
            for index, row in ggst_round_data_df.iterrows():
                seconds:float = row.Frame_Number_secs
                vidcap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
                hasFrame,image = vidcap.read()
                if is_verbose:
                    print("Char Portraits//Health | Checking Time: {}secs, Frame: {} (in secs)... "
                          .format(int(seconds), seconds))            
                if hasFrame:
                    if ((chars_predicted != True) and 
                        ((index - start_index) > char_pred_frame_buffer)):
                        ggst_char_pred_df = ggst_new_data_df.loc[start_index:(index - 1)]
                        img_dicts = _get_predict_chars_dict_ls(ggst_char_pred_df, 
                                                               all_img_dicts, 
                                                               min_char_delta)
                        chars_predicted = True if len(img_dicts) < 3 else False

                    for img_dict in img_dicts:
                        dict_name:str = img_dict['Name']
                        template_img_keys = list(img_dict['img_objs'].keys())
                        #Running template matching on every image in the dict
                        for tmpl_img_key in template_img_keys:                        
                            tmpl_img = img_dict['img_objs'][tmpl_img_key]
                            col_name = "{}_{}".format(dict_name, tmpl_img_key)
                            score = vet_match_score(image, tmpl_img, 
                                                    tmpl_img_key, img_dict, 
                                                    min_mappings)
                            ggst_new_data_df.loc[index, col_name] = score
                    #Detecting 1P & 2P health bar values
                    (high_health_1P, low_health_1P) = ex.detect_player_1_health(image)
                    (high_health_2P, low_health_2P) = ex.detect_player_2_health(image)        
                    ggst_new_data_df.loc[index, '1P_High_Health'] = high_health_1P
                    ggst_new_data_df.loc[index, '1P_Low_Health'] = low_health_1P
                    ggst_new_data_df.loc[index, '2P_High_Health'] = high_health_2P
                    ggst_new_data_df.loc[index, '2P_Low_Health'] = low_health_2P
                        
    return ggst_new_data_df

def validate_draw_game_results(games_df, rounds_df):
    """Checks if game outcomes which are draws, are actual draw games. Draw 
    games are very rare & are usually a result of there being inconclusive 
    round outcome data. Changes false Draw outcomes to Unknown to better 
    reflect the data.
    -------------------------------------------------------------------------
    -=games_df=- DataFrame w/ fully aggregated game data.
    -=rounds_df=- DataFrame w/ fully aggregated round data.
    -------------------------------------------------------------------------
    [-return-] DataFrame that's games_df, w/ any false 'Draw' outcomes changed 
     to 'Unknown'."""
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

def correct_game_scores(games_df, rounds_df):
    """Corrects game results which have impossible round scores for the best 2 
    out of 3 default in GGST. Most common case this catches is 3-0 round win 
    due to an incorrect winner predicted for one of the game's rounds.
    -------------------------------------------------------------------------
    -=games_df=- DataFrame w/ fully aggregated game data.
    -=rounds_df=- DataFrame w/ fully aggregated round data.
    -------------------------------------------------------------------------
    [-return-] DataFrame that's games_df, w/ invalid 3-0 outcomes being 
     corrected to 2-1."""
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

def extract_match_video_timecodes_only(video_path:str, fps_val:int, config, 
                                       verbose_log:bool=False
                                       )-> tuple[str,int,int]:
    """Extracts only round/game start/end times, & aggregates into rounds & 
    games as best as it can w/ the given data. Main use is for creating VLC 
    playlist bookmarks or YouTube chapters, w/ the round/game start times for 
    video editing or for manual viewing, w/ the quicker processing @ the 
    expense of other data points like characters used & predicted winners.
    -------------------------------------------------------------------------
    -=video_path=- Path of the video files' location (should be the full path 
      so VLC playlist created works correctly).
    -=fps_val=- Number of frames per second to process. While it can be a value 
      between 1 to 60, 2 & 4 are what testing & tuning were based on.
    -=config=- All config values imported from the config file.
    -=verbose_log=- Whether progress updates are printed to console.
    -------------------------------------------------------------------------
    [-return-] Tuple which is the created folder w/ the generated files, total 
     processing time, & length/duration of the video processed."""
    vid_filename:str = video_path.split('\\')[-1]
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
    games_by_rounds_df, anomalies_df = agg.classify_rounds_into_games(consolidated_rounds_df)
    games_agg_df = agg.aggregate_into_games(games_by_rounds_df, anomalies_df)
    games_agg_df = validate_draw_game_results(games_agg_df, games_by_rounds_df)

    output_name:str = vid_filename.split('.')[0][0:25].replace(' ', '_')
    output_folder:str = out.create_csv_output_files(ggst_vid_data_df, 
                                                    games_agg_df, 
                                                    games_by_rounds_df, 
                                                    anomalies_df, output_name, 
                                                    create_json = True, 
                                                    orignal_vid = vid_filename)    
    #For playlist creation, requires video_path to be the full path of video
    out.create_round_based_vlc_playlist(games_by_rounds_df, ggst_vid_data_df, 
                                        video_path, output_folder, anomalies_df)
    out.create_game_based_vlc_playlist(games_agg_df, ggst_vid_data_df, 
                                       video_path, output_folder, anomalies_df)
    out.create_round_based_yt_chapters(games_by_rounds_df, output_folder, 
                                       anomalies_df=anomalies_df, 
                                       prepend_id=True)
    out.create_game_based_yt_chapters(games_agg_df, output_folder, 
                                      anomalies_df=anomalies_df, 
                                      prepend_id=True)
    end_time = datetime.now()
    vid_delta = (end_time - total_start).seconds
    video_length = out.get_video_duration(ggst_vid_data_df)
    print("Total extraction/aggregation processing time was {} seconds"
          .format(vid_delta))
    print("Total length of video processed was {} seconds.".format(video_length))
    return output_folder, vid_delta, video_length

def layered_extract_and_aggregate_video(video_path:str, fps_val:int, config, 
                                        verbose_log:bool=False
                                        )-> tuple[str,int,int]:
    """Approach which combines & layers extraction & aggregation, to limit 
    unnecessary template matching, & run more optimally. 1st Round Start/End 
    templates are detected, processed into round blocks. Then the round 
    boundaries used to target the other template matching, limiting the number 
    of frames to check.
    -------------------------------------------------------------------------
    -=video_path=- Path of the video files' location (should be the full path 
      so VLC playlist created works correctly).
    -=fps_val=- Number of frames per second to process. While it can be a value 
      between 1 to 60, 2 & 4 are what testing & tuning were based on.
    -=config=- All config values imported from the config file.
    -=verbose_log=- Whether progress updates are printed to console.
    -------------------------------------------------------------------------
    [-return-] Tuple which is the created folder w/ the generated files, total 
     processing time, & length/duration of the video processed."""
    vid_filename:str = video_path.split('\\')[-1]
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
    games_by_rounds_df, anomalies_df = agg.classify_rounds_into_games(round_winners_df)
    
    games_agg_df = agg.aggregate_into_games(games_by_rounds_df, anomalies_df)
    games_agg_df = validate_draw_game_results(games_agg_df, games_by_rounds_df)
    games_agg_df = correct_game_scores(games_agg_df, games_by_rounds_df)
    
    output_name:str = vid_filename.split('.')[0][0:25].replace(' ', '_')
    output_folder:str = out.create_csv_output_files(ggst_vid_data_df, 
                                                    games_agg_df, 
                                                    games_by_rounds_df, 
                                                    anomalies_df, output_name, 
                                                    create_json = True, 
                                                    orignal_vid = vid_filename)
    #For playlist creation, requires video_path to be the full path of video
    out.create_round_based_vlc_playlist(games_by_rounds_df, ggst_vid_data_df, 
                                        video_path, output_folder, anomalies_df)
    out.create_game_based_vlc_playlist(games_agg_df, ggst_vid_data_df, 
                                       video_path, output_folder, anomalies_df)
    out.create_round_based_yt_chapters(games_by_rounds_df, output_folder, 
                                       anomalies_df=anomalies_df)
    out.create_game_based_yt_chapters(games_agg_df, output_folder, 
                                      anomalies_df=anomalies_df)
    end_time = datetime.now()
    vid_delta = (end_time - total_start).seconds
    video_length = out.get_video_duration(ggst_vid_data_df)
    print("Total extraction/aggregation processing time was {} seconds"
          .format(vid_delta))
    print("Total length of video processed was {} seconds.".format(video_length))
    return output_folder, vid_delta, video_length

def brute_force_extract_and_aggregate_video(video_path:str, fps_val:int, config,
                                            verbose_log:bool=False
                                            )-> tuple[str,int,int]:
    """Every frame of the video, has template match applied to every single 
    template image defined in a list of template image dicts, defined in the 
    config file. Then the raw match scores are aggregated. It's use is for 
    testing template matching, since it's open ended input design allows you to 
    add as many dicts as needed for template matching. In practical application, 
    it shouldn't be used as it runs more than 2 times as long as the layered 
    extraction & aggregation function (last benchmarks: for every 1 sec of 
    video processing takes between 10.5-11.5 secs).
    -------------------------------------------------------------------------
    -=video_path=- Path of the video files' location (should be the full path 
      so VLC playlist created works correctly).
    -=fps_val=- Number of frames per second to process. While it can be a value 
      between 1 to 60, 2 & 4 are what testing & tuning were based on.
    -=config=- All config values imported from the config file.
    -=verbose_log=- Whether progress updates are printed to console.
    -------------------------------------------------------------------------
    [-return-] Tuple which is the created folder w/ the generated files, total 
     processing time, & length/duration of the video processed."""
    vid_filename:str = video_path.split('\\')[-1]
    config.templ_img_dicts_ls = ex.load_tmp_imgs(config.templ_img_dicts_ls)
    start_time = datetime.now()
    ggst_vid_data_df = ex.get_all_tmpl_scores_vid(video_path, 
                                                  config.templ_img_dicts_ls, 
                                                  config.templ_img_min_val_mappings, 
                                                  frames_per_sec = fps_val)
    end_time = datetime.now()
    vid_delta = (end_time - start_time).seconds
    video_length = out.get_video_duration(ggst_vid_data_df)
    print("Total extraction processing time was {} seconds (video source)"
          .format(vid_delta))
    print("Total length of video processed was {} seconds.".format(video_length))
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

    games_by_rounds_df, anomalies_df = agg.classify_rounds_into_games(round_winners_df)
    games_agg_df = agg.aggregate_into_games(games_by_rounds_df, anomalies_df)
    games_agg_df = validate_draw_game_results(games_agg_df, games_by_rounds_df)
    games_agg_df = correct_game_scores(games_agg_df, games_by_rounds_df)
    
    output_name:str = vid_filename.split('.')[0][0:25]
    output_folder:str = out.create_csv_output_files(ggst_vid_data_df, 
                                                    games_agg_df, 
                                                    games_by_rounds_df, 
                                                    anomalies_df, output_name, 
                                                    create_json = True, 
                                                    orignal_vid = vid_filename)
    #For playlist creation, requires video_path to be the full path of video
    full_vid_path = "{}{}".format(os.getcwd(), video_path)
    out.create_round_based_vlc_playlist(games_by_rounds_df, ggst_vid_data_df, 
                                        full_vid_path, output_folder, 
                                        anomalies_df)
    out.create_game_based_vlc_playlist(games_agg_df, ggst_vid_data_df, 
                                       full_vid_path, output_folder, 
                                       anomalies_df)
    out.create_round_based_yt_chapters(games_by_rounds_df, output_folder, 
                                       anomalies_df=anomalies_df)
    out.create_game_based_yt_chapters(games_agg_df, output_folder, 
                                      anomalies_df=anomalies_df)
    return output_folder, vid_delta, video_length