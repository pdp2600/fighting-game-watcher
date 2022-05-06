# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 19:32:52 2022

Guilty Gear Strive data Aggregator module. Functions related to aggregating & 
writing aggregation results to a variety of output formats.

@author: PDP2600
"""
import os
import pandas as pd
from collections import Counter
from datetime import datetime
import json

def get_char_portrait_col_names(df_columns:list)->list:
    #Retrieves all the P1 & P2 character portrait match column names
    char_portrait_col_names:list = []
    for col_name in df_columns:
        if "P_Portrait" in col_name:
            char_portrait_col_names.append(col_name)
            
    return char_portrait_col_names

#Defining the columns required for aggregation & creating a new DF w/ those 
#columns to be used in aggregation functions
def reduce_match_df_to_agg_df(vid_match_data_df):
    agg_col_names:list = ['Time_in_Secs', 'Frame_Number_secs']
    char_portraits:list = get_char_portrait_col_names(list(vid_match_data_df))
    other_cols_ls = ['Starter_Duel', 'Starter_Number_1', 'Starter_Number_2', 
                     'Starter_Number_3', 'Starter_Number_Final', 'Starter_Lets_Rock', 
                     'Ender_Slash', 'Ender_Double_KO', 'Ender_Draw', 'Ender_Perfect', 
                     'Ender_Times_Up', 'Ender_1P_Win', 'Ender_2P_Win', 
                     'Game_UI_Timer_Outline', '1P_High_Health', '1P_Low_Health', 
                     '2P_High_Health', '2P_Low_Health']
    agg_col_names.extend(char_portraits)
    agg_col_names.extend(other_cols_ls)
    return vid_match_data_df[agg_col_names]

def _find_duel_start_blocks(duel_df, duel_block_threshold:int)->list:
    duel_index_blocks:list = []
    prev_index:int = -1
    start_index:int = 0
    last_index = list(duel_df.index)[-1]
    for index, row in duel_df.iterrows():
        if (prev_index == -1) and (index == last_index):
            duel_index_blocks.append({'start_index': index, 'end_index': index})
        
        elif (prev_index == -1) and (index != last_index):
            start_index = index
            prev_index = index
        
        else:
            if index == last_index:
                if (index - prev_index) > duel_block_threshold:
                    duel_index_blocks.append({'start_index': start_index, 
                                              'end_index': prev_index})
                    duel_index_blocks.append({'start_index': index, 
                                              'end_index': index})
                else:
                    duel_index_blocks.append({'start_index': start_index, 
                                              'end_index': index})
            elif (index - prev_index) > duel_block_threshold:
                duel_index_blocks.append({'start_index': start_index, 
                                          'end_index': prev_index})
                start_index = index
                prev_index = index
            else:
                prev_index = index
    return duel_index_blocks

def _evaluate_round_data(round_bool_data_df)->str:
    round_sum:dict = {'Round_1': sum(round_bool_data_df.Round_1), 
                      'Round_2': sum(round_bool_data_df.Round_2), 
                      'Round_3': sum(round_bool_data_df.Round_3), 
                      'Round_Final': sum(round_bool_data_df.Round_Final)
                      }
    #Non-round 1 values count for double to avoid Duel 1 false positives
    round_sum['Round_2'] = round_sum['Round_2'] * 2
    round_sum['Round_3'] = round_sum['Round_3'] * 2
    round_sum['Round_Final'] = round_sum['Round_Final'] * 2
    
    if (round_sum['Round_1'] == 0 and round_sum['Round_2'] == 0 and 
        round_sum['Round_3'] == 0 and round_sum['Round_Final'] == 0):
        return "Unknown"
    else:
        max_round_key = max(round_sum, key=round_sum.get)
        count = 0
        for val in list(round_sum.values()):
            if val == round_sum[max_round_key]:
                count = count + 1
        if count < 2:
            return max_round_key
        else:
            return "Unknown"

def _round_number_detect(duel_df, min_delta:float):
    duel_number_cols_df = duel_df.copy()
    duel_number_cols_df = duel_number_cols_df[['Starter_Number_1', 
                                               'Starter_Number_2', 
                                               'Starter_Number_3', 
                                               'Starter_Number_Final']]
    duel_number_cols_df['Round_1'] = False
    duel_number_cols_df['Round_2'] = False
    duel_number_cols_df['Round_3'] = False
    duel_number_cols_df['Round_Final'] = False
    
    for index, row in duel_number_cols_df.iterrows():
        #Other Round number match score required to be 0 to be Round 1
        if row.Starter_Number_1 > 0:
            if ((row.Starter_Number_2 == 0) and 
                (row.Starter_Number_3 == 0) and 
                (row.Starter_Number_Final == 0)):                
                duel_number_cols_df.loc[index, 'Round_1'] = True
        
        #Doesn't check for Round 1 due to false positives based on that match
        if row.Starter_Number_2 > 0:
            if ((row.Starter_Number_2 - row.Starter_Number_3) > min_delta and 
                (row.Starter_Number_2 - row.Starter_Number_Final) > min_delta):
                duel_number_cols_df.loc[index, 'Round_2'] = True
                
        if row.Starter_Number_3 > 0:
            if ((row.Starter_Number_3 - row.Starter_Number_2) > min_delta and 
                (row.Starter_Number_3 - row.Starter_Number_Final) > min_delta):
                duel_number_cols_df.loc[index, 'Round_3'] = True
        
        if row.Starter_Number_Final > 0:
            if ((row.Starter_Number_Final - row.Starter_Number_2) > min_delta and 
                (row.Starter_Number_Final - row.Starter_Number_3) > min_delta):
                duel_number_cols_df.loc[index, 'Round_Final'] = True
    
    return _evaluate_round_data(duel_number_cols_df[['Round_1', 'Round_2', 
                                                     'Round_3', 'Round_Final']])

def _get_paired_lets_rock_block(lets_rock_df, duel_end:int, 
                                duel_to_lets_rock_buffer:int)->int:
    start = duel_end + 1
    end = start + duel_to_lets_rock_buffer
    lets_rock_within_buffer_df = lets_rock_df.loc[start: end, ]
    if len(lets_rock_within_buffer_df) == 0:
        return -1
    else:
        return list(lets_rock_within_buffer_df.index)[-1]
    
#Finds the round start blocks by index & seconds, as well as round number if
#it's available
def _round_start_processing(data_for_agg_df, agg_config:dict):
    duel_detected_df = data_for_agg_df.loc[(data_for_agg_df['Starter_Duel'] > 0.45) & 
                     (data_for_agg_df['Ender_Double_KO'] == 0) & 
                     (data_for_agg_df['Ender_Draw'] == 0) & 
                     (data_for_agg_df['Ender_Perfect'] == 0) & 
                     (data_for_agg_df['Ender_Times_Up'] == 0) & 
                     (data_for_agg_df['Starter_Lets_Rock'] == 0) & 
                     ((data_for_agg_df['Starter_Number_1'] > 0) | 
                      (data_for_agg_df['Starter_Number_2'] > 0) | 
                      (data_for_agg_df['Starter_Number_3'] > 0) | 
                      (data_for_agg_df['Starter_Number_Final'] > 0))]

    lets_rock_detected_df = data_for_agg_df.loc[data_for_agg_df['Starter_Lets_Rock'] > 0]
    round_start_df = pd.DataFrame({})
    duel_index_blocks:list = _find_duel_start_blocks(duel_detected_df, 
                                                     agg_config['duel_block_index_threshold'])
    for duel_block in duel_index_blocks:
        start:int = duel_block['start_index']
        end:int = duel_block['end_index']
        duel_block_df = duel_detected_df.copy()
        duel_block_df = duel_block_df.loc[start: end, ]
        includes_lets_rock:bool = False
        round_num = _round_number_detect(duel_block_df, 
                                         agg_config['duel_number_min_delta'])
        lets_rock_block = _get_paired_lets_rock_block(lets_rock_detected_df, end, 
                                                      agg_config['duel_to_lets_rock_frame_buffer'])
        if lets_rock_block != -1:
            end = lets_rock_block
            includes_lets_rock = True
            
        round_dict = {'start_index': start, 'end_index': end, 
                      'start_secs': data_for_agg_df.loc[start, 'Time_in_Secs'], 
                      'end_secs': data_for_agg_df.loc[end, 'Time_in_Secs'],
                      'round': round_num, 'Lets_Rock': bool(includes_lets_rock)
                      }
        round_start_df = round_start_df.append(pd.DataFrame(round_dict, index = [start]), 
                                               sort=False)
    
    return round_start_df

def _find_orphan_lets_rocks(data_for_agg_df, round_start_df):
    lets_rock_detected_df = data_for_agg_df.loc[data_for_agg_df.Starter_Lets_Rock > 0]
    orphaned_lets_rocks_df = pd.DataFrame({})
    
    for index, row in lets_rock_detected_df.iterrows():        
        isOrphaned = True
        for round_index, round_row in round_start_df.iterrows():
            #print("Round Start, start index: {} end index: {}".format(round_row.start_index, round_row.end_index))
            if (index >= round_row.start_index) and (index <= round_row.end_index):
                isOrphaned = False
        
        if isOrphaned:
            orphaned_lets_rocks_df = orphaned_lets_rocks_df.append(row, sort=False)
    
    return orphaned_lets_rocks_df

#Takes a DataFrame of "Lets Rock" rows, & consolidates adjacent rows into a round start
# block
def _find_lets_rock_solo_blocks(lets_rock_df):
    rock_index_blocks:list = []
    prev_index:int = -1
    start_index:int = 0
    last_index:int = list(lets_rock_df.index)[-1]
    for index, row in lets_rock_df.iterrows():
        if (prev_index == -1) and (index == last_index):
            start_secs = lets_rock_df.loc[index, 'Time_in_Secs']
            end_secs = lets_rock_df.loc[index, 'Time_in_Secs']
            rock_index_blocks.append({'start_index': index, 'end_index': index, 
                                      'start_secs': start_secs, 
                                      'end_secs': end_secs, 'round': "Unknown"})
        elif (prev_index == -1) and (index != last_index):
            start_index = index
            prev_index = index
        else:
            if index == last_index:
                start_secs = lets_rock_df.loc[start_index, 'Time_in_Secs']
                end_secs = lets_rock_df.loc[index, 'Time_in_Secs']
                rock_index_blocks.append({'start_index': start_index, 
                                          'end_index': index, 
                                          'start_secs': start_secs,
                                          'end_secs': end_secs,
                                          'round': "Unknown"})
            elif (index - prev_index) > 1:
                start_secs = lets_rock_df.loc[start_index, 'Time_in_Secs']
                end_secs = lets_rock_df.loc[prev_index, 'Time_in_Secs']
                rock_index_blocks.append({'start_index': start_index, 
                                          'end_index': prev_index, 
                                          'start_secs': start_secs,
                                          'end_secs': end_secs,
                                          'round': "Unknown"})
                start_index = index
                prev_index = index
            else:
                prev_index = index
    
    rock_index_blocks_df = _lets_rock_dict_to_df(rock_index_blocks)
    return rock_index_blocks_df

def _lets_rock_dict_to_df(lets_rock_block:list):
    round_start_df = pd.DataFrame({})
    for block in lets_rock_block:
        start_index = block['start_index']
        round_start_df = round_start_df.append(pd.DataFrame(block, 
                                                            index = [start_index]), 
                                               sort=False)
    return round_start_df

def load_match_csv_into_dataframe(csv_path:str):
    vid_data_df = pd.read_csv(csv_path)
    vid_data_df = vid_data_df.reset_index()
    vid_data_df = vid_data_df.drop(['Unnamed: 0'], axis='columns')
    vid_data_df = vid_data_df.drop(['index'], axis='columns')
    return vid_data_df

#When a Lets Rock isn't found to be associated with a Duel, assumes the Duel
#is missing, & the Lets Rock is the start of the round. Weirdness can happen
#if there are valid Duel/Lets Rock pairs, but the Lets Rock is outside the threshold
def _consolidate_orphans_into_round_start_blocks(orphaned_df, round_start_df):
    round_start_all_df = pd.DataFrame({})
    if len(orphaned_df) > 0:
        lets_rock_rounds = _find_lets_rock_solo_blocks(orphaned_df)
        round_start_all_df = round_start_df.append(lets_rock_rounds)
        round_start_all_df = round_start_all_df.sort_index(axis = 0)
    return round_start_all_df    

#When passed a df with a single ender type will return a list of dicts containing
#the start/end indexes of each ender block, w/ ender data all assigned false 
#(correct boolean values determined in the function which calls it)
def _get_single_ender_blocks(single_ender_df, end_block_threshold:int)->list:
    ender_index_blocks:list = []
    prev_index:int = -1
    start_index:int = 0
    last_index:int = list(single_ender_df.index)[-1]
    for index, row in single_ender_df.iterrows():
        if (prev_index == -1) and (index == last_index):
            ender_index_blocks.append({'start_index': index, 'end_index': index, 
                                       'perfect': False, 'double_ko': False,
                                       'time_out': False, 'draw': False})        
        elif (prev_index == -1) and (index != last_index):
            start_index = index
            prev_index = index        
        else:
            if index == last_index:
                ender_index_blocks.append({'start_index': start_index, 
                                          'end_index': index, 'perfect': False, 
                                          'double_ko': False, 'time_out': False, 
                                          'draw': False})
            elif (index - prev_index) > end_block_threshold:
                ender_index_blocks.append({'start_index': start_index, 
                                          'end_index': prev_index, 
                                          'perfect': False, 'double_ko': False, 
                                          'time_out': False, 'draw': False})
                start_index = index
                prev_index = index
            else:
                prev_index = index
    return ender_index_blocks

#Creates a list of dicts containing start/end indexes of each ender block & 
#sets values related to type (time out being a draw detected in calling function)
def _find_duel_end_blocks(ender_df, end_block_threshold:int)->list:
    slash_ender_df = ender_df.loc[ender_df['Ender_Slash'] > 0]
    perfect_ender_df = ender_df.loc[ender_df['Ender_Perfect'] > 0]
    double_ko_ender_df = ender_df.loc[ender_df['Ender_Double_KO'] > 0]
    times_up_ender_df = ender_df.loc[ender_df['Ender_Times_Up'] > 0]
    all_ender_blocks:list = []
    
    if len(list(slash_ender_df.index)) > 0:
        slash_blocks = _get_single_ender_blocks(slash_ender_df, end_block_threshold)
        all_ender_blocks = all_ender_blocks + slash_blocks
    
    if len(list(perfect_ender_df.index)) > 0:
        perfect_blocks = _get_single_ender_blocks(perfect_ender_df, end_block_threshold)
        for i, ender in enumerate(perfect_blocks):
            perfect_blocks[i]['perfect'] = True
            
        all_ender_blocks = all_ender_blocks + perfect_blocks
    
    if len(list(double_ko_ender_df.index)) > 0:
        double_ko_blocks = _get_single_ender_blocks(double_ko_ender_df, end_block_threshold)
        for i, ender in enumerate(double_ko_blocks):
            double_ko_blocks[i]['double_ko'] = True
            double_ko_blocks[i]['draw'] = True
            
        all_ender_blocks = all_ender_blocks + double_ko_blocks
        
    if len(list(times_up_ender_df.index)) > 0:
        times_up_blocks = _get_single_ender_blocks(times_up_ender_df, end_block_threshold)
        for i, ender in enumerate(times_up_blocks):
            times_up_blocks[i]['time_out'] = True
            
        all_ender_blocks = all_ender_blocks + times_up_blocks        
    return all_ender_blocks

#Seeing if there are any Draw enders linked to a time out ended round, returns
#end index of the draw block or -1 if none are linked
def _get_time_out_draw_block(draw_df, time_out_end:int, 
                             time_out_to_draw_buffer:int)->int:
    start:int = time_out_end + 1
    end:int = start + time_out_to_draw_buffer
    draw_within_buffer_df = draw_df.loc[start: end, ]
    if len(draw_within_buffer_df) == 0:
        return -1
    else:
        return list(draw_within_buffer_df.index)[-1]

#Finds the round ender blocks by index & seconds, as well as different round end
#properties based on the ender
def _round_end_processing(data_for_agg_df, agg_config:dict):
    ender_detected_df = data_for_agg_df.loc[(data_for_agg_df['Ender_Slash'] > 0.49) | 
                                            (data_for_agg_df['Ender_Double_KO'] > 0.49) | 
                                            (data_for_agg_df['Ender_Perfect'] > 0.49) | 
                                            (data_for_agg_df['Ender_Times_Up'] > 0.49)]
    draw_detected_df = data_for_agg_df.loc[data_for_agg_df.Ender_Draw > 0]
    round_end_df = pd.DataFrame({})
   
    ender_index_blocks:list = _find_duel_end_blocks(ender_detected_df, 
                                                    agg_config['ender_block_index_threshold'])
    for end_block in ender_index_blocks:
        start:int = end_block['start_index']
        end:int = end_block['end_index']
        ender_block_df = ender_detected_df.copy()
        ender_block_df = ender_block_df.loc[start: end, ]
        is_draw:bool = end_block['draw']
        
        if end_block['time_out'] and (len(list(draw_detected_df.index)) > 0):
            times_up_draw_buffer = agg_config['times_up_to_draw_frame_buffer']
            draw_block_end = _get_time_out_draw_block(draw_detected_df, 
                                                      end, times_up_draw_buffer)            
            if draw_block_end != -1:
                end = draw_block_end
                is_draw = True
        
        end_dict = {'start_index': start, 'end_index': end, 
                      'start_secs': data_for_agg_df.loc[start, 'Time_in_Secs'], 
                      'end_secs': data_for_agg_df.loc[end, 'Time_in_Secs'],
                      'perfect': end_block['perfect'], 
                      'double_ko': end_block['double_ko'], 
                      'time_out': end_block['time_out'], 'draw': is_draw
                      }
        
        round_end_df = round_end_df.append(pd.DataFrame(end_dict, index = [start]), 
                                               sort=False)    
    return round_end_df

def _merge_round_start_and_end_blocks(round_start_df, round_end_df):
    start_df = round_start_df.copy()
    end_df = round_end_df.copy()
    
    start_df['block_type'] = 'Starter'
    end_df['block_type'] = 'Ender'
    
    start_df['perfect'] = None
    start_df['double_ko'] = None
    start_df['time_out'] = None
    start_df['draw'] = None
    
    end_df['round'] = None
    
    all_blocks_df = start_df.append(end_df)
    all_blocks_df = all_blocks_df.sort_index(axis = 0)
    
    return all_blocks_df
    
def _create_inconclusive_dict(cur_row_df, adj_row_df, agg_config:dict, 
                              note:str)->dict:
    starter_index:int = agg_config['missing_starter_index_value']
    ender_index:int = agg_config['missing_ender_index_value']
    starter_time:int = agg_config['missing_starter_secs_value']
    ender_time:int = agg_config['missing_ender_secs_value']
    inconclusive_round:dict = {}
    if cur_row_df.loc[0,'block_type'] == 'Starter':
        end_secs = adj_row_df.loc[0,'start_secs'] - ender_time 
        end_index = adj_row_df.loc[0,'start_index'] - ender_index
        inconclusive_round = {'start_secs': cur_row_df.loc[0,'start_secs'], 
                              'start_index': cur_row_df.loc[0,'start_index'], 
                              'end_secs': end_secs, 'end_index': end_index, 
                              'round': cur_row_df.loc[0,'round'], 
                              'winner': 'Unknown', 
                              'winner_via_health': 'Unknown', 
                              'winner_via_tmplate_match': 'Unknown', 
                              'winner_confidence': None, 
                              'character_1P': 'Unknown', 
                              'character_2P': 'Unknown', 'perfect': None, 
                              'double_ko': None, 'time_out': None, 
                              'draw': None, 'inconclusive_data': True, 
                              'inconclusive_note': note
                              }
    else:
        start_secs = adj_row_df.loc[0,'end_secs'] + starter_time 
        start_index = adj_row_df.loc[0,'end_index'] + starter_index
        inconclusive_round = {'start_secs': start_secs, 
                              'start_index': start_index, 
                              'end_secs': cur_row_df.loc[0,'end_secs'], 
                              'end_index': cur_row_df.loc[0,'end_index'], 
                              'round': 'Unknown', 'winner': 'Unknown', 
                              'winner_via_health': 'Unknown', 
                              'winner_via_tmplate_match': 'Unknown', 
                              'winner_confidence': None, 
                              'character_1P': 'Unknown', 
                              'character_2P': 'Unknown', 
                              'perfect': cur_row_df.loc[0,'perfect'], 
                              'double_ko': cur_row_df.loc[0,'double_ko'], 
                              'time_out': cur_row_df.loc[0,'time_out'], 
                              'draw': cur_row_df.loc[0,'draw'], 
                              'inconclusive_data': True, 
                              'inconclusive_note': note
                              }
    
    return inconclusive_round

def _create_invalid_dict(cur_row_df, note:str)->dict:
    invalid:dict = {}
    if cur_row_df.loc[0,'block_type'] == 'Starter':
        invalid = {'start_secs': cur_row_df.loc[0,'start_secs'], 
                   'start_index': cur_row_df.loc[0,'start_index'], 
                   'end_secs': -1, 'end_index': -1, 
                   'round': cur_row_df.loc[0,'round'], 'winner': 'Unknown', 
                   'winner_via_health': 'Unknown', 
                   'winner_via_tmplate_match': 'Unknown', 
                   'winner_confidence': None, 'character_1P': 'Unknown', 
                   'character_2P': 'Unknown', 'perfect': None, 
                   'double_ko': None, 'time_out': None, 'draw': None, 
                   'inconclusive_data': True, 'inconclusive_note': note
                   }
    else:
        invalid = {'start_secs': -1, 'start_index': -1, 
                   'end_secs': cur_row_df.loc[0,'end_secs'], 
                   'end_index': cur_row_df.loc[0,'end_index'], 
                   'round': 'Unknown', 'winner': 'Unknown', 
                   'winner_via_health': 'Unknown', 
                   'winner_via_tmplate_match': 'Unknown', 
                   'winner_confidence': None, 'character_1P': 'Unknown', 
                   'character_2P': 'Unknown', 
                   'perfect': cur_row_df.loc[0,'perfect'], 
                   'double_ko': cur_row_df.loc[0,'double_ko'], 
                   'time_out': cur_row_df.loc[0,'time_out'], 
                   'draw': cur_row_df.loc[0,'draw'], 'inconclusive_data': True, 
                   'inconclusive_note': note}
    return invalid

def _create_valid_round_dict(cur_row_df, next_row_df)->dict:
    row_df = cur_row_df.copy().reset_index()
    next_row = next_row_df.copy().reset_index()
    round_dict = {'start_secs': row_df.loc[0,'start_secs'], 
                  'start_index': row_df.loc[0,'start_index'], 
                  'end_secs': next_row.loc[0,'end_secs'], 
                  'end_index': next_row.loc[0,'end_index'], 
                  'round': row_df.loc[0,'round'], 
                  'winner': 'Unknown', 'winner_via_health': 'Unknown', 
                  'winner_via_tmplate_match': 'Unknown', 
                  'winner_confidence': None, 'character_1P': 'Unknown', 
                  'character_2P': 'Unknown', 
                  'perfect': next_row.loc[0,'perfect'], 
                  'double_ko': next_row.loc[0,'double_ko'], 
                  'time_out': next_row.loc[0,'time_out'], 
                  'draw': next_row.loc[0,'draw'], 
                  'inconclusive_data': False, 
                  'inconclusive_note': ""
                 }
    return round_dict

def _resolve_missing_pair(cur_row_df, next_row_df, prev_row_df, 
                          agg_config:dict)->dict:
    cur_row = cur_row_df.copy().reset_index()
    next_row = next_row_df.copy().reset_index()
    prev_row = prev_row_df.copy().reset_index()
    next_row_exists:bool = len(list(next_row.index)) > 0
    prev_row_exists:bool = len(list(prev_row.index)) > 0

    if cur_row.loc[0,'block_type'] == 'Starter':
        if next_row_exists == False:
            invalid_note = "Invalid: Round Starter at End of Video"
            return _create_invalid_dict(cur_row, invalid_note)
        elif ((cur_row.loc[0,'round'] == 'Round_1') and 
              (next_row.loc[0,'round'] == 'Round_1')):
            inconl_note = "Missing Ender: Button Check"
            return _create_inconclusive_dict(cur_row, next_row, agg_config, 
                                             inconl_note)
        elif (((cur_row.loc[0,'round'] == 'Round_1') and 
        (next_row.loc[0,'round'] == 'Round_2')) or 
        ((cur_row.loc[0,'round'] == 'Round_2') and 
        (next_row.loc[0,'round'] == 'Round_3')) or 
        ((cur_row.loc[0,'round'] == 'Round_3') and 
        (next_row.loc[0,'round'] == 'Round_Final'))):
            inconl_note = "Missing Ender: Round in the beginning or middle of Game"
            return _create_inconclusive_dict(cur_row, next_row, agg_config, 
                                             inconl_note)
        elif (((cur_row.loc[0,'round'] == 'Round_2') and 
        (next_row.loc[0,'round'] == 'Round_1')) or 
        ((cur_row.loc[0,'round'] == 'Round_3') and 
        (next_row.loc[0,'round'] == 'Round_1')) or 
        ((cur_row.loc[0,'round'] == 'Round_Final') and 
        (next_row.loc[0,'round'] == 'Round_1'))):
            inconl_note = "Missing Ender: Last Round of Game"
            return _create_inconclusive_dict(cur_row, next_row, agg_config, 
                                             inconl_note)
        else:
            #Catch all where cur & next round aren't both R1 or sequential/new game
            inconl_note = "Missing Ender: Unknown"
            return _create_inconclusive_dict(cur_row, next_row, agg_config, 
                                             inconl_note)        
    elif cur_row.loc[0,'block_type'] == 'Ender':
        if prev_row_exists == False:
            invalid_note = "Invalid: Round Ender at Start of Video"
            return _create_invalid_dict(cur_row, invalid_note)
        else:
            inconl_note = "Missing Starter: Game aggregation will attempt to fill missing round info"
            return _create_inconclusive_dict(cur_row, prev_row, agg_config, 
                                             inconl_note)

#Transforms round starter & ender data into round data, attempts to resolve
#rounds with missing starter or ender where possible & flags those instances
def _consolidate_round_data(rounds_df, agg_config:dict):
    index_vector = list(rounds_df.index)
    last_index:int = index_vector[-1]
    round_data_df = pd.DataFrame({})
    i:int = 0
    prev_index:int = -1
    prev_row_df = pd.DataFrame({})

    while i < len(index_vector):
        index:int = index_vector[i]
        if index != last_index:
            next_index = index_vector[i+1]
            if ((rounds_df.loc[index,'block_type'] == 'Starter') and 
                (rounds_df.loc[next_index,'block_type'] == 'Ender')):
                round_dict = _create_valid_round_dict(rounds_df.loc[index:index,], 
                                                      rounds_df.loc[next_index:next_index,])
                round_data_df = round_data_df.append(pd.DataFrame(round_dict, 
                                                                  index = [index]))
                #Setting previous row index to the ender row & itterating to the row after
                prev_index = index_vector[i+1]
                i = i + 2
            else:
                if prev_index != -1:
                    prev_row_df = rounds_df.loc[prev_index:prev_index,]

                round_dict = _resolve_missing_pair(rounds_df.loc[index:index,], 
                                                   rounds_df.loc[next_index:next_index,], 
                                                   prev_row_df, agg_config)
                round_data_df = round_data_df.append(pd.DataFrame(round_dict, 
                                                                  index = [index]))
                #April 3 Added prev_index assignment to this branch (I think I missed it)
                prev_index = index_vector[i]
                i = i + 1
        else:
            #Case when it's the last index, April 3 adding passing empty df for Next row
            next_row_df = pd.DataFrame({})
            round_dict = _resolve_missing_pair(rounds_df.loc[index:index,], 
                                               next_row_df, prev_row_df, 
                                               agg_config)
            round_data_df = round_data_df.append(pd.DataFrame(round_dict, 
                                                              index = [index]))
            i = i + 1
    return round_data_df

#Validate whether there are legit Duel scores equal or above the min_score 
def _validate_duel_match_score(ggst_slice_df, min_score:float)->bool:
    duel_min_data_df = ggst_slice_df.loc[((ggst_slice_df.Starter_Duel >= min_score) &
                                          ((ggst_slice_df.Starter_Number_1 > 0) |
                                           (ggst_slice_df.Starter_Number_2 > 0) |
                                           (ggst_slice_df.Starter_Number_3 > 0) |
                                           (ggst_slice_df.Starter_Number_Final > 0)))]
    return len(duel_min_data_df) > 0

#When there are duplicate rounds or likely Duel 1 false positives (when there's no
#associated Let's Rock), filter them out
def _filter_round_start_false_positives(round_start_blocks_df, ggst_vid_data_df):
    start_blocks_df = pd.DataFrame({})
    for index, row in round_start_blocks_df.iterrows():
        #is_high_duel_score = False
        #ggst_slice_df = pd.DataFrame({})
        #if (row.start_index != -1) and (row.end_index != -1):
        ggst_slice_df = ggst_vid_data_df.loc[row.start_index:row.end_index,]
        has_high_duel_score = _validate_duel_match_score(ggst_slice_df, 0.85)
            
        if bool(round_start_blocks_df.loc[index, 'Lets_Rock']):
            round_df = pd.DataFrame({'start_index': round_start_blocks_df.loc[index, 'start_index'], 
                                     'end_index': round_start_blocks_df.loc[index, 'end_index'], 
                                     'start_secs': round_start_blocks_df.loc[index, 'start_secs'], 
                                     'end_secs': round_start_blocks_df.loc[index, 'end_secs'], 
                                     'round': round_start_blocks_df.loc[index, 'round']}, 
                                    index = [index])
            start_blocks_df = start_blocks_df.append(round_df)
            #print("Start round added with Lets Rock detected @ start index: {}".format(round_df.loc[index, 'start_index']))
            #print("Round Number: {}".format(round_df.loc[index, 'round']))
        elif ((not bool(round_start_blocks_df.loc[index, 'Lets_Rock'])) and 
              has_high_duel_score):
            round_df = pd.DataFrame({'start_index': round_start_blocks_df.loc[index, 'start_index'], 
                                     'end_index': round_start_blocks_df.loc[index, 'end_index'], 
                                     'start_secs': round_start_blocks_df.loc[index, 'start_secs'], 
                                     'end_secs': round_start_blocks_df.loc[index, 'end_secs'], 
                                     'round': round_start_blocks_df.loc[index, 'round']}, 
                                    index = [index])
            start_blocks_df = start_blocks_df.append(round_df)
            #print("Start round added with High duel score @ start index: {}".format(round_df.loc[index, 'start_index']))
            #print("Round Number: {}".format(round_df.loc[index, 'round']))
        else:
            pass
            #print("Round tossed, start_index: {}, start_sec: {}, round: {}".format(int(row.start_index), 
            #                                                                       int(row.start_secs), 
            #                                                                       str(row.round)))
            #explictly not adding the ROund start block if there's no Lets rock or high duel score
    return start_blocks_df

def _get_index_when_ui_disappears(ggst_round_df):
    #print("First index in slice: {}".format(list(ggst_round_df.head(1).index)[0]))
    no_ui_frames_df = ggst_round_df.loc[ggst_round_df.Game_UI_Timer_Outline == 0]
    no_ui_frames_df = no_ui_frames_df.sort_index()
    first_no_timer_frame = list(no_ui_frames_df.index)[0]
    #print("First no timer frame index: {}".format(first_no_timer_frame))
    return first_no_timer_frame

##########Left off here with going over var typing & 1st pass re-factor        
def _validate_unknown_round_duration(round_blocks_df, ggst_data_df):
    verified_rounds_df = round_blocks_df.copy()
    index_ls = list(verified_rounds_df.index)
    last_index = index_ls[-1]
    prev_round_end_index = -1
    #prev_round_end_secs = -1
    index_count = 0
    while index_count < len(index_ls):
        index = index_ls[index_count]
        if bool(verified_rounds_df.loc[index, 'inconclusive_data']):
            round_start_index = verified_rounds_df.loc[index, 'start_index']
            round_end_index = verified_rounds_df.loc[index, 'end_index']
            next_index = index_ls[index_count + 1] if index != last_index else -1
            if next_index != -1:
                next_round_start_secs = verified_rounds_df.loc[next_index, 'start_secs']
                next_round_start_index = verified_rounds_df.loc[next_index, 'start_index']
            
            if ((prev_round_end_index > 0) and 
                ('Missing Starter:' in verified_rounds_df.loc[index, 'inconclusive_note']) 
                and (round_start_index <= prev_round_end_index)):
                ggst_slice_df = ggst_data_df.loc[prev_round_end_index:round_end_index,]
                round_transition_index = _get_index_when_ui_disappears(ggst_slice_df)
                round_transition_secs = ggst_data_df.loc[round_transition_index, 'Time_in_Secs']
                verified_rounds_df.loc[index, 'start_secs'] = round_transition_secs
                verified_rounds_df.loc[index, 'start_index'] = round_transition_index
            elif ((index != last_index) and 
                  ('Missing Ender:' in verified_rounds_df.loc[index, 'inconclusive_note']) 
                  and (round_end_index >= next_round_start_index)):
                verified_rounds_df.loc[index, 'end_secs'] = next_round_start_secs - 1
                verified_rounds_df.loc[index, 'end_index'] = next_round_start_index - 1
        
        index_count = index_count + 1
        #prev_round_end_secs = verified_rounds_df.loc[index, 'end_secs']
        prev_round_end_index = verified_rounds_df.loc[index, 'end_index']
        
    return verified_rounds_df

#Aggregates visual data extracted into game rounds (with start/end positions, 
#round number, & extra data the ender might convey)
def aggregate_into_rounds(ggst_vid_data_df, agg_config_dict):
    round_start_blocks_df = _round_start_processing(ggst_vid_data_df, agg_config_dict)
    round_start_blocks_df = _filter_round_start_false_positives(round_start_blocks_df, 
                                                                ggst_vid_data_df)
    #Looking for "Lets Rock" states which weren't associated with a Duel State &
    # & adds them as a round block (in case video doesn't show Duel before Lets Rock) 
    orphaned_lets_rocks_df = _find_orphan_lets_rocks(ggst_vid_data_df, 
                                                     round_start_blocks_df)
    #if there are Lets Rock orphans, will add them as Round blocks sorted by index
    round_start_df = _consolidate_orphans_into_round_start_blocks(orphaned_lets_rocks_df, 
                                                                  round_start_blocks_df)
    
    #Figuring out where all the round ender indicators start and end, & if the round
    #ended in a significant state
    round_end_blocks_df = _round_end_processing(ggst_vid_data_df, agg_config_dict)
    round_end_blocks_df = round_end_blocks_df.sort_index(axis = 0)

    round_start_end_df = _merge_round_start_and_end_blocks(round_start_df, 
                                                           round_end_blocks_df)
    consolidated_rounds_df = _consolidate_round_data(round_start_end_df, 
                                                     agg_config_dict)
    consolidated_rounds_df = _validate_unknown_round_duration(consolidated_rounds_df, 
                                                              ggst_vid_data_df)
    
    return consolidated_rounds_df

#Used to swap to a new undisputed max character, used to save space in calling function
def _reset_max_char_dict(col_name, val):
    new_max_dict = {}
    new_max_dict[col_name] = val
    
    return new_max_dict

#Checks which character had the most matches & that there are no ties/disputed matches
def get_character_used(ggst_slice_data_df, character_cols_ls, min_char_delta):
    char_detected_sum_dict = {}
    for index, row in ggst_slice_data_df.iterrows():
        max_val_dict = {}        
        for col in character_cols_ls:
            char_val = ggst_slice_data_df.loc[index, col]
            if char_val > 0:
                if len(max_val_dict) == 0:
                    max_val_dict[col] = char_val
                elif len(max_val_dict) == 1:
                    cur_max_val = list(max_val_dict.values())[0]
                    if (char_val > cur_max_val):
                        if (abs(char_val - cur_max_val) > min_char_delta):
                            max_val_dict = _reset_max_char_dict(col, char_val)
                        else:
                            max_val_dict[col] = char_val
                else:
                    max_key = max(max_val_dict, key=max_val_dict.get)
                    if (char_val > max_val_dict[max_key]): 
                        if (abs(char_val - max_val_dict[max_key]) > min_char_delta):
                            max_val_dict = _reset_max_char_dict(col, char_val)
                        else:
                            max_val_dict[col] = char_val        
        #Only if there's a single undisputed max char value for the round, 
        #will it be incremented, more than one, it doesn't count towards the sum
        if len(max_val_dict) == 1:
            max_key = list(max_val_dict.keys())[0]
            if max_key in char_detected_sum_dict:
                char_detected_sum_dict[max_key] = char_detected_sum_dict[max_key] + 1
            else:
                char_detected_sum_dict[max_key] = 1    

    return _verify_character_detected(char_detected_sum_dict)

#Verifies that there's a single undisputed character which was detected
def _verify_character_detected(char_detected_dict):
    max_key = 'Unknown'
    #######Debug March 26th
    #for key, val in char_detected_dict.items():
    #    print("Verify Char Detection:")
    #    print("key: {} Value: {}".format(key, val))
    #######
    if len(char_detected_dict) > 0:
        max_key = max(char_detected_dict, key=char_detected_dict.get)
        max_val = char_detected_dict[max_key]
        
        #Check to make sure there are not more than 1 key w/ the max value
        if Counter(list(char_detected_dict.values()))[max_val] == 1:
            max_key = max_key.replace("_1P_Portrait", "") if (
                '1P' in max_key) else max_key.replace("_2P_Portrait", "")            
        else:
            max_key = 'Unknown'
    
    return max_key

#Player 1 & 2 Character detect: aggregate character names for frames in each round
def extract_played_characters(ggst_vid_data_df, rounds_df, agg_config_dict):
    char_data_rounds_df = rounds_df.copy()
    char_portraits_agg_ls = get_char_portrait_col_names(list(ggst_vid_data_df))
    player_1_characters_ls = [x for x in char_portraits_agg_ls if '1P_Portrait' in x]
    player_2_characters_ls = [x for x in char_portraits_agg_ls if '2P_Portrait' in x]
    
    for index, row in char_data_rounds_df.iterrows():
        if (row.start_index != -1) and (row.end_index != -1):
            round_slice_df = ggst_vid_data_df.loc[(row.start_index + 1):(row.end_index - 1),]
            ####Debug March 26th
            #print("Round Slice, start: {} end: {}".format((row.start_index + 1), (row.end_index - 1)))
            player_1_char = get_character_used(round_slice_df, 
                                                player_1_characters_ls, 
                                                agg_config_dict['min_character_delta'])
            player_2_char = get_character_used(round_slice_df, 
                                                player_2_characters_ls, 
                                                agg_config_dict['min_character_delta'])
            char_data_rounds_df.loc[index, 'character_1P'] = player_1_char
            char_data_rounds_df.loc[index, 'character_2P'] = player_2_char
            
    return char_data_rounds_df

#return "winner" value & a value representing the confidence in that conclusion
def _get_winner_by_health(ggst_vid_data_df, round_df, agg_config_dict):
    round_df = round_df.reset_index()
    start_index = round_df.loc[0, 'start_index']
    end_index = round_df.loc[0, 'end_index']
    last_index = list(ggst_vid_data_df.tail(1).index)[0]
    frame_buffer_legit_ender = agg_config_dict['health_after_ender_frame_buffer']
    frame_buffer_missing_ender = agg_config_dict['missing_ender_health_buffer']
    health_min_delta = agg_config_dict['player_health_min_delta']
    health_min_delta_no_ender = agg_config_dict['missing_ender_player_health_min_delta']
    frame_buffer_no_health_post_ender = agg_config_dict['no_health_after_ender_buffer']
    health_min_delta_no_health_post_ender = agg_config_dict['no_health_after_ender_delta']
    
    if 'Missing Ender' not in round_df.loc[0, 'inconclusive_note']:
        end_slice_index = end_index + frame_buffer_legit_ender
        if end_slice_index > last_index:
            end_slice_index = last_index
        ##Changed start slice index from end_index + 1 to end_index - 2
        ggst_data_slice_df = ggst_vid_data_df.loc[(end_index - 2):end_slice_index, ]
        #Function returns Winner & confidence in that result based on data
        winner_by_health, confidence = _parse_health_data_for_winner(ggst_data_slice_df, 
                                                                     health_min_delta)
        if winner_by_health != 'Unknown':
            return winner_by_health, confidence
        else:
            slice_start_index = end_index - frame_buffer_no_health_post_ender
            ggst_data_slice_df = ggst_vid_data_df.loc[slice_start_index:
                                                  (end_index - 1), ]
            return _no_health_post_ender_health_check(ggst_data_slice_df, 
                                                      health_min_delta_no_health_post_ender)
    else:
        slice_start_index = end_index - frame_buffer_missing_ender
        if slice_start_index < start_index:
            slice_start_index = start_index
        ggst_data_slice_df = ggst_vid_data_df.loc[slice_start_index:
                                                  (end_index - 1), ]
        return _no_ender_health_check(ggst_data_slice_df, health_min_delta_no_ender)

#For the case when an ender exists, but no health data extracted post-ender
def _no_health_post_ender_health_check(ggst_health_slice_df, min_delta):
    #dataframe slice index in reverse order as list
    index_ls = list(ggst_health_slice_df.sort_index(ascending=False).index)
    index_size = len(index_ls)
    index = 0
    winner = 'Unknown'
    confidence = None
    while (index < index_size) and (winner == 'Unknown'):
        df_index = index_ls[index]
        data_row_df = ggst_health_slice_df.loc[df_index:df_index,]
        winner, confidence = _pre_ender_extra_health_check(data_row_df, min_delta)
        index = index + 1
    return winner, confidence

#For the case when no ender exists for a round, returns winner by health if possible 
#& confidence
def _no_ender_health_check(ggst_health_slice_df, min_delta):
    #dataframe slice index in reverse order as list
    index_ls = list(ggst_health_slice_df.sort_index(ascending=False).index)
    index_size = len(index_ls)
    index = 0
    winner = 'Unknown'
    confidence = None
    while (index < index_size) and (winner == 'Unknown'):
        df_index = index_ls[index]
        data_row_df = ggst_health_slice_df.loc[df_index:df_index,]
        winner, confidence = _parse_health_data_for_winner(data_row_df, min_delta)
        if winner == 'Unknown':
            winner, confidence = _pre_ender_extra_health_check(data_row_df, 
                                                               min_delta)
        index = index + 1
    return winner, confidence

#Used in the case of a round which had no ender or no health data post ender
#There's a case where P1 & P2 health columns will both have non 0 values
def _pre_ender_extra_health_check(ggst_health_slice_df, min_delta):
    ggst_health_slice_df = ggst_health_slice_df.reset_index()
    Player_1_high = ggst_health_slice_df.loc[0, '1P_High_Health']
    Player_1_low = ggst_health_slice_df.loc[0, '1P_Low_Health']
    Player_2_high = ggst_health_slice_df.loc[0, '2P_High_Health']
    Player_2_low = ggst_health_slice_df.loc[0, '2P_Low_Health']
    is_UI_displayed = ggst_health_slice_df.loc[0, 'Game_UI_Timer_Outline'] > 0
    confidence = None
    
    if ((Player_1_high == 0) and (Player_1_low == 0) and (Player_2_high == 0) 
        and (Player_2_low == 0)):
        return 'Unknown', confidence
    elif ((Player_1_high > 0) and (Player_2_low >= 0) and (Player_2_high == 0) 
          and is_UI_displayed):
        if Player_2_low < min_delta:
            confidence = 'Medium'
            return 'Player 1', confidence
        else:
            confidence = 'Low'
            return 'Player 1', confidence
    elif ((Player_2_high > 0) and (Player_1_low >= 0) and (Player_1_high == 0) 
          and is_UI_displayed):
        if Player_1_low < min_delta:
            confidence = 'Medium'
            return 'Player 2', confidence
        else:
            confidence = 'Low'
            return 'Player 2', confidence
    elif (((Player_1_low > 0) or (Player_2_low > 0)) and (Player_1_high == 0) 
          and (Player_2_high == 0) and is_UI_displayed):
        confidence = 'Very Low'
        if Player_1_low == Player_2_low:
            return 'Unknown', confidence
        #added Mar 24th to prevent some health false positives
        elif abs(Player_1_low - Player_2_low) < min_delta:
            return 'Unknown', confidence
        elif Player_1_low > Player_2_low:
            return 'Player 1', confidence
        else:
            return 'Player 2', confidence
    else:
        return 'Unknown', confidence

def _parse_health_data_for_winner(ggst_health_slice_df, min_delta):
    ggst_rows_w_ui_df = ggst_health_slice_df.loc[
        ggst_health_slice_df.Game_UI_Timer_Outline > 0]
    confidence = None
    #April 7th FIltering out rows from the next round where P1 & P2 both have high health vals
    ggst_rows_w_ui_df = ggst_rows_w_ui_df.loc[((ggst_rows_w_ui_df['1P_High_Health'] == 0) |
                                               (ggst_rows_w_ui_df['2P_High_Health'] == 0))]
    if len(ggst_rows_w_ui_df) == 0:
        return 'Unknown', confidence
    Player_1_high = ggst_rows_w_ui_df['1P_High_Health'].sum()
    Player_1_low = ggst_rows_w_ui_df['1P_Low_Health'].sum()
    Player_2_high = ggst_rows_w_ui_df['2P_High_Health'].sum()
    Player_2_low = ggst_rows_w_ui_df['2P_Low_Health'].sum()
    
    if (Player_2_high == 0) and (Player_2_low == 0):
        if Player_1_high > 0:
            confidence = 'High'
            return 'Player 1', confidence
        elif Player_1_low > 0:
            if Player_1_low > min_delta:
                confidence = 'Medium'
            else:
                confidence = 'Low'
            return 'Player 1', confidence
        else:
            return 'Unknown', confidence
    elif (Player_1_high == 0) and (Player_1_low == 0):
        if Player_2_high > 0:
            confidence = 'High'
            return 'Player 2', confidence
        elif Player_2_low > 0:
            if Player_2_low > min_delta:
                confidence = 'Medium'
            else:
                confidence = 'Low'
            return 'Player 2', confidence
        else:
            return 'Unknown', confidence
    else:
        return 'Unknown', confidence

def _check_for_player_win_template(ggst_slice_df, min_delta):
    ggst_player_win_df = ggst_slice_df.loc[(ggst_slice_df.Ender_1P_Win > 0) | 
                                           (ggst_slice_df.Ender_2P_Win > 0)]
    
    if len(list(ggst_player_win_df.index)) > 0:
        player_1_win_avg = ggst_player_win_df.Ender_1P_Win.mean()
        player_2_win_avg = ggst_player_win_df.Ender_2P_Win.mean()
        
        if abs(player_1_win_avg - player_2_win_avg) > min_delta:
            if player_1_win_avg > player_2_win_avg:
                return 'Player 1'
            else:
                return 'Player 2'
        else:
            return 'Unknown'
    else:
        return 'Unknown'
    
def _get_winner_by_tmpl(ggst_vid_data_df, round_df, agg_config_dict):
    round_df = round_df.reset_index()
    start_index = round_df.loc[0, 'start_index']
    end_index = round_df.loc[0, 'end_index']
    last_index = list(ggst_vid_data_df.tail(1).index)[0]
    frame_buffer_legit_ender = agg_config_dict['player_win_after_ender_buffer']
    frame_buffer_missing_ender = agg_config_dict['missing_ender_player_win_buffer']
    win_min_delta = agg_config_dict['player_win_enders_min_delta']

    if 'Missing Ender' not in round_df.loc[0, 'inconclusive_note']:
        end_slice_index = end_index + frame_buffer_legit_ender
        if end_slice_index > last_index:
            end_slice_index = last_index
        ggst_data_slice_df = ggst_vid_data_df.loc[(end_index + 1):end_slice_index, ]
        #Function returns Winner & confidence in that result based on data
        return _check_for_player_win_template(ggst_data_slice_df, win_min_delta)
    else:
        slice_start_index = end_index - frame_buffer_missing_ender
        if slice_start_index < start_index:
            slice_start_index = start_index
        ggst_data_slice_df = ggst_vid_data_df.loc[slice_start_index:
                                                  (end_index - 1), ]        
        return _check_for_player_win_template(ggst_data_slice_df, win_min_delta)
    

def _get_overall_confidence(winner_via_template, winner_via_health, 
                                   health_confidence):
    if winner_via_template != 'Unknown':
        if winner_via_template == winner_via_health:
            if health_confidence == 'High':
                return 'Very High'
            else:
                return 'High'
        else:
            return 'High'
    else:
        return health_confidence
    
#If the player win template value was found, that's the value defaulted to
#Health can get weird for rounds where end was estimated (no ender found)
def _consolidate_win_data(winner_via_template, winner_via_health):
    if (winner_via_template == 'Unknown') and (winner_via_health != 'Unknown'):
        return winner_via_health
    elif (winner_via_template != 'Unknown') and (winner_via_health == 'Unknown'):
        return winner_via_template
    else:
        return winner_via_template

def extract_round_winner(ggst_vid_data_df, rounds_df, agg_config_dict):
    winner_by_health = 'Unknown'
    winner_by_tmpl = 'Unknown'
    confidence = None
    
    for index, row in rounds_df.iterrows():
        #April 5th Added None clause, since rounds w/o enders should have win checked
        if ((rounds_df.loc[index, 'draw'] == False) or 
        (rounds_df.loc[index, 'draw'] == None)):
            if rounds_df.loc[index, 'end_secs'] != -1:
                round_df = rounds_df.loc[index:index,]
                winner_by_health, confidence = _get_winner_by_health(ggst_vid_data_df, 
                                                                     round_df, 
                                                                     agg_config_dict)
                winner_by_tmpl = _get_winner_by_tmpl(ggst_vid_data_df, round_df, agg_config_dict)
            else:
                winner_by_health = 'Unknown'
                winner_by_tmpl = 'Unknown'
                confidence = None

            rounds_df.loc[index, 'winner_via_health'] = winner_by_health
            rounds_df.loc[index, 'winner_via_tmplate_match'] = winner_by_tmpl
            rounds_df.loc[index, 'winner'] = _consolidate_win_data(winner_by_tmpl, 
                                                                   winner_by_health)
            overall_confidence = _get_overall_confidence(winner_by_tmpl, 
                                                         winner_by_health, 
                                                         confidence)
            rounds_df.loc[index, 'winner_confidence'] = overall_confidence
            
        else:
            rounds_df.loc[index, 'winner'] = 'Draw'
            
    return rounds_df

def classify_rounds_into_games(rounds_df):
    game_rounds_df, anomally_rounds_df = _validate_rounds_for_games(rounds_df)
    ##May need to add more to handle weird cases?
    
    if len(game_rounds_df) > 0:
        game_rounds_df = game_rounds_df.drop(['index'], axis='columns')
    if len(anomally_rounds_df) > 0:
        anomally_rounds_df = anomally_rounds_df.drop(['index'], axis='columns')
    
    return game_rounds_df, anomally_rounds_df

#Assumes there are a minimum of 2 rounds for every game, attempts to organize rounds
#into games
def _validate_rounds_for_games(raw_rounds_df):
    rounds_df = raw_rounds_df.copy().reset_index()
    total_rows = len(rounds_df)
    index = 0
    game_count = 1
    anomally_count = 1
    games_df = pd.DataFrame({})
    anomallies_df = pd.DataFrame({})
    while index < total_rows:
        if ((rounds_df.loc[index, 'end_secs'] != -1) and 
            (rounds_df.loc[index, 'start_secs'] != -1) and 
            (total_rows > (index + 1))):
            if ((rounds_df.loc[index, 'round'] == 'Round_1') and 
                ((rounds_df.loc[index + 1, 'round'] == 'Round_2') or 
                 (rounds_df.loc[index + 1, 'round'] == 'Unknown'))):
                last_round_index = _get_last_game_round_index(rounds_df, index)
                games_df = _add_game_rounds_df(rounds_df.loc[index:last_round_index,], 
                                               games_df, game_count)
                index = last_round_index + 1
                game_count = game_count + 1
                
            elif ((rounds_df.loc[index, 'round'] == 'Unknown') and 
                  (rounds_df.loc[index + 1, 'round'] == 'Round_2')):
                last_round_index = _get_last_game_round_index(rounds_df, index)
                games_df = _add_game_rounds_df(rounds_df.loc[index:last_round_index,], 
                                               games_df, game_count)
                index = last_round_index + 1
                game_count = game_count + 1

            else:
                anomallies_df = _add_anomally_round_df(rounds_df.loc[index:index,], 
                                                   anomallies_df, anomally_count)
                anomally_count = anomally_count + 1
                index = index + 1
        else:
            anomallies_df = _add_anomally_round_df(rounds_df.loc[index:index,], 
                                                   anomallies_df, anomally_count)
            anomally_count = anomally_count + 1
            index = index + 1
    return games_df, anomallies_df

#Verifies round index is the 3rd/final round of a game by a player winning 2 rounds
#Doesn't address the case where there's an Unknown winner in one of the rounds
def _is_game_with_3_rounds(rounds_df, round_index, final_round_case=False):
    #The game will be at least 2 rounds which is insured before the function call
    last_round_index = round_index
    first_round = round_index - 2
    if final_round_case:
        first_round = round_index - 3
    #Check if any player won both of the previous found rounds, which means no other rounds
    first_3_rounds_df = rounds_df.loc[first_round:last_round_index,]
    player_winner = _game_won_by(first_3_rounds_df, 2)
    if ((player_winner == 'Player 1') or (player_winner == 'Player 2')):
        return True
    else:
        return False

#When the potential 3rd round is Unknown, this is a check if the time gap between
#rounds isn't above the max gap (which makes it more likely it's in the same game)
def _is_round_gap_same_game(rounds_df, round_2_index):
    max_gap_secs = 25
    round_unknown_gap = (rounds_df.loc[round_2_index + 1, 'start_secs'] - 
                         rounds_df.loc[round_2_index, 'end_secs'])
    return (round_unknown_gap < max_gap_secs)

def _get_last_game_round_index(rounds_df, round_1_index):
    #The game will be at least 2 rounds which is insured before the function call
    last_round_index = round_1_index + 1
    total_rows = len(rounds_df)
    #Check if any player won both of the previous found rounds, which means no other rounds
    first_2_rounds_df = rounds_df.loc[round_1_index:last_round_index,]
    player_winner = _game_won_by(first_2_rounds_df, 2)
    if (((player_winner == 'Player 1') or (player_winner == 'Player 2')) and 
        (len(first_2_rounds_df.loc[first_2_rounds_df['winner_confidence'] != 'Very Low'])
         == 2)):
        return last_round_index
    
    if (total_rows > (last_round_index + 1)):
        if rounds_df.loc[last_round_index + 1, 'round'] == 'Round_1':
            return last_round_index
        elif rounds_df.loc[last_round_index + 1, 'round'] == 'Round_Final':
            last_round_index = last_round_index + 1
            return last_round_index
        elif rounds_df.loc[last_round_index + 1, 'round'] == 'Round_3':
            last_round_index = last_round_index + 1
            #Check if there's a Final (4th) Round 
            if (total_rows > (last_round_index + 1)):
                if rounds_df.loc[last_round_index + 1, 'round'] == 'Round_1':
                    return last_round_index
                elif rounds_df.loc[last_round_index + 1, 'round'] == 'Round_Final':
                    last_round_index = last_round_index + 1
                    return last_round_index
                else:
                    return last_round_index
            else:
                return last_round_index

        elif rounds_df.loc[last_round_index + 1, 'round'] == 'Unknown':
            if ((total_rows > (last_round_index + 1)) and 
                _is_game_with_3_rounds(rounds_df, last_round_index + 1) and 
                _is_round_gap_same_game(rounds_df, last_round_index)):
                last_round_index = last_round_index + 1
                return last_round_index
            elif (((last_round_index - 1) >= 0) and 
                  (rounds_df.loc[last_round_index - 1, 'round'] == 'Round_1') and 
                  (rounds_df.loc[last_round_index, 'round'] == 'Round_2') and 
                _is_round_gap_same_game(rounds_df, last_round_index)):
                last_round_index = last_round_index + 1
                return last_round_index
            elif (total_rows > (last_round_index + 2) and 
                rounds_df.loc[last_round_index + 2, 'round'] == 'Round_1'):
                last_round_index = last_round_index + 1
                return last_round_index
            else:
                if (total_rows > (last_round_index + 2) and 
                rounds_df.loc[last_round_index + 2, 'round'] == 'Round_Final' and
                _is_game_with_3_rounds(rounds_df, last_round_index + 2, 
                                             final_round_case=True)):
                    last_round_index = last_round_index + 2
                    return last_round_index
                else:
                    return last_round_index
        else:
            return last_round_index
    else:
        return last_round_index
            
def _game_won_by(rounds_df, rounds_to_win_int):
    player_1_wins = len(rounds_df.loc[rounds_df.winner == 'Player 1'])
    player_2_wins = len(rounds_df.loc[rounds_df.winner == 'Player 2'])
    if player_1_wins == rounds_to_win_int:
        return 'Player 1'
    elif player_2_wins == rounds_to_win_int:
        return 'Player 2'
    else:
        return None

def _add_anomally_round_df(anomally_round_df, anomally_collection_df, anomally_num):
    anomally_round_df = anomally_round_df.copy()
    index_ls = list(anomally_round_df.index)
    for index in index_ls:
        anomally_round_df.loc[index, 'anomaly_id'] = "Anomally_{}".format(anomally_num)
    return anomally_collection_df.append(anomally_round_df, sort=False)

def _add_game_rounds_df(game_rounds_df, games_collection_df, game_num):
    game_rounds = game_rounds_df.copy()
    index_ls = list(game_rounds.index)
    for index in index_ls:
        if game_num < 10:
            game_rounds.loc[index, 'game_id'] = "Game_0{}".format(game_num)
        else:
            game_rounds.loc[index, 'game_id'] = "Game_{}".format(game_num)
    return games_collection_df.append(game_rounds, sort=False)

#From Round data classified as games, aggregates winner & character data to game level
def aggregate_into_games(game_rounds_df, anomalous_rounds_df):
    games_ls = list(set(game_rounds_df['game_id']))
    game_level_df = pd.DataFrame({})
    game_index = 0
    
    for game in games_ls:
        single_game_rounds_df = game_rounds_df.loc[game_rounds_df.game_id == game]
        game_result_dict = _aggregate_game_result(single_game_rounds_df)
        game_char_data_dict = _aggregate_game_characters(single_game_rounds_df)
        single_game_data_dict = _create_game_data_dict(single_game_rounds_df, 
                                                       game_result_dict, 
                                                       game_char_data_dict)        
        game_level_df = game_level_df.append(pd.DataFrame(single_game_data_dict, 
                                                          index = [game_index]), 
                                             sort=False)
        game_index = game_index + 1
    
    #Output to console detected anomalous or inconsistent info
    _print_anomalous_round_data(anomalous_rounds_df)
    _print_inconclusive_game_data(game_level_df)

    return game_level_df.sort_values('game_id')

#If possible aggregates what the game winner & round score is based on round results
def _aggregate_game_result(single_game_rounds_df):
    rounds_df = single_game_rounds_df.reset_index()
    total_rounds = len(rounds_df)
    #April 7th added clause in initial condition to ensure no rounds are Very Low
    #confidence, which in that case would default to last round winner
    if ((len(rounds_df.loc[rounds_df.winner == 'Draw']) == 0) and 
        (len(rounds_df.loc[rounds_df.winner == 'Unknown']) == 0) and
        (len(rounds_df.loc[rounds_df.winner_confidence == 'Very Low']) == 0)):
        player_1_wins = len(rounds_df.loc[rounds_df.winner == 'Player 1'])
        player_2_wins = len(rounds_df.loc[rounds_df.winner == 'Player 2'])
        winner = 'Player 1' if player_1_wins == 2 else 'Player 2'
        return {'player_1_rounds_won': player_1_wins, 
                'player_2_rounds_won': player_2_wins, 'winner': winner, 
                'inconclusive_data': False, 'inconclusive_note': ""}
    elif ((total_rounds == 2) and ((rounds_df.loc[1, 'winner'] != 'Unknown') and
                                   (rounds_df.loc[1, 'winner'] != 'Draw'))):
        return _game_result_based_on_last_round_winner(rounds_df)
    elif ((total_rounds == 3) and ((rounds_df.loc[2, 'winner'] != 'Unknown') and
                                   (rounds_df.loc[2, 'winner'] != 'Draw'))):
        return _game_result_based_on_last_round_winner(rounds_df)
    elif ((total_rounds == 4) and ((rounds_df.loc[3, 'winner'] != 'Unknown') and
                                   (rounds_df.loc[3, 'winner'] != 'Draw'))):
        return _game_result_based_on_last_round_winner(rounds_df)
    else:
        return _game_results_with_draw_or_unknown_winners(rounds_df)

#Finds rounds scores & game winner based on only having last round results
#Works since in most cases the winner of the last round is the game winner
def _game_result_based_on_last_round_winner(rounds_df):
    total_rounds = len(rounds_df)
    last_round_index = total_rounds - 1
    if total_rounds == 2:
        p1_wins = 2 if rounds_df.loc[last_round_index, 'winner'] == 'Player 1' else 0
        p2_wins = 2 if rounds_df.loc[last_round_index, 'winner'] == 'Player 2' else 0
    else:
        p1_wins = 2 if rounds_df.loc[last_round_index, 'winner'] == 'Player 1' else 1
        p2_wins = 2 if rounds_df.loc[last_round_index, 'winner'] == 'Player 2' else 1
    winner = rounds_df.loc[last_round_index, 'winner']
    return {'player_1_rounds_won': p1_wins, 'player_2_rounds_won': p2_wins, 
            'winner': winner, 'inconclusive_data': True, 
            'inconclusive_note': "Unknown or very low confidence winner of a round, winner based on last round result"}

#When rounds have too many unknowns or are draws, this function itterates through
#every round & attempts to figure out the winner or if it's a draw if possible
def _game_results_with_draw_or_unknown_winners(rounds_df):
    inconclusive = False
    inconclusive_note = ""
    player_1_wins = 0
    player_2_wins = 0
    winner = 'Unknown'
    for index, row in rounds_df.iterrows():
        if row.winner == 'Draw':
            if (player_1_wins == 0) and (player_2_wins == 0):
                player_1_wins = 1
                player_2_wins = 1
            elif(player_1_wins == 1) and ((player_2_wins == 0)):
                player_2_wins = 1
            elif(player_1_wins == 0) and ((player_2_wins == 1)):
                player_1_wins = 1
        elif row.winner == 'Unknown':
            inconclusive = True
            inconclusive_note = "Unknown Winner in 1 or more rounds, game results maybe incorrect"
        else:
            if row.winner == 'Player 1':
                player_1_wins = player_1_wins + 1
            else:
                player_2_wins = player_2_wins + 1
    if (player_1_wins == 1) and (player_2_wins == 1):
        winner = 'Draw'
    elif len(rounds_df == 2) and (player_1_wins == 1) and (player_2_wins == 0):
        winner = 'Player 1'
        player_1_wins = 2
    elif len(rounds_df == 2) and (player_2_wins == 1) and (player_1_wins == 0):
        winner = 'Player 2'
        player_2_wins = 2
    elif player_1_wins == 2:
        winner = 'Player 1'
    elif player_2_wins == 2:
        winner = 'Player 2'
    return {'player_1_rounds_won': player_1_wins, 
            'player_2_rounds_won': player_2_wins, 'winner': winner, 
            'inconclusive_data': inconclusive, 
            'inconclusive_note': inconclusive_note}

#Attempts to aggregrate the character data in rounds to the game level, basically
#checking for inconsistencies like multiple P1 or P2 characters in the game's rounds
def _aggregate_game_characters(single_game_rounds_df):
    p1_char_count_dict = {}
    p2_char_count_dict = {}    
    for index, row in single_game_rounds_df.iterrows():
        p1_char = row.character_1P
        p2_char = row.character_2P
        
        if p1_char in p1_char_count_dict:
            p1_char_count_dict[p1_char] = p1_char_count_dict[p1_char] + 1
        else:
            p1_char_count_dict[p1_char] = 1
        
        if p2_char in p2_char_count_dict:
            p2_char_count_dict[p2_char] = p2_char_count_dict[p2_char] + 1
        else:
            p2_char_count_dict[p2_char] = 1
    
    p1_char_results_dict = _check_character_results(p1_char_count_dict)
    p2_char_results_dict = _check_character_results(p2_char_count_dict)
    is_inconclusive = (p1_char_results_dict['inconclusive_data'] or 
                       p2_char_results_dict['inconclusive_data'])
    inconclusive_note = ""
    if ((p1_char_results_dict['inconclusive_note'] != "") and 
        (p2_char_results_dict['inconclusive_note'] != "")):
        if "in all rounds" in p1_char_results_dict['inconclusive_note']:
            inconclusive_note = p1_char_results_dict['inconclusive_note']
        elif "in all rounds" in p2_char_results_dict['inconclusive_note']:
            inconclusive_note = p2_char_results_dict['inconclusive_note']
        else:
            inconclusive_note = p1_char_results_dict['inconclusive_note']
    elif (p1_char_results_dict['inconclusive_note'] != ""):
        inconclusive_note = p1_char_results_dict['inconclusive_note']
    elif (p2_char_results_dict['inconclusive_note'] != ""):
        inconclusive_note = p2_char_results_dict['inconclusive_note']
        
    return {'character_1P': p1_char_results_dict['character'], 
            'character_2P': p2_char_results_dict['character'], 
            'inconclusive_data': is_inconclusive, 
            'inconclusive_note': inconclusive_note}

#Checks for inconsistent characters in all the rounds
def _check_character_results(char_count_dict):
    char_result_keys_ls = list(char_count_dict.keys())
    if len(char_result_keys_ls) == 1:
        if char_result_keys_ls[0] != 'Unknown':
            return {'character': char_result_keys_ls[0], 
                    'inconclusive_data': False, 'inconclusive_note': ""}
        else:
            return {'character': char_result_keys_ls[0], 
                    'inconclusive_data': True, 
                    'inconclusive_note': "Unknown character in all rounds"}
    else:
        max_count = max(char_count_dict.values())
        max_char_ls = []
        #itterating through each key (character name) and value (count)
        for char, count in char_count_dict.items():
            if count == max_count:
                max_char_ls.append(char)
        
        if len(max_char_ls) == 1:
            return {'character': max_char_ls[0], 
                    'inconclusive_data': True, 
                    'inconclusive_note': "Unknown or multiple characters in some rounds"}
        else:
            return {'character': 'Unknown', 
                    'inconclusive_data': True, 
                    'inconclusive_note': "Unknown or multiple characters in some rounds"}

#Creates the dictionary which is the game level data structure. Also will combine
#game level inconsistency notes & make a note of round level inconsistencies when
#there were no game level inconsistency flags 
def _create_game_data_dict(single_game_rounds_df, game_result_dict, game_chars_dict):
    games_df = single_game_rounds_df.reset_index()
    last_index = len(games_df) - 1
    is_inconclusive = (game_result_dict['inconclusive_data'] or 
                       game_chars_dict['inconclusive_data'])
    inconclusive_note = ""
    if (game_result_dict['inconclusive_data'] and 
        game_chars_dict['inconclusive_data']):
        inconclusive_note = "{}, and {}".format(game_result_dict['inconclusive_note'], 
                                                game_chars_dict['inconclusive_note'])
    elif game_result_dict['inconclusive_data']:
        inconclusive_note = game_result_dict['inconclusive_note']
    elif game_chars_dict['inconclusive_data']:
        inconclusive_note = game_chars_dict['inconclusive_note']
    else:
        inconclusive_rounds = len(games_df.loc[games_df.inconclusive_data == True])
        if inconclusive_rounds > 0:
            is_inconclusive = True
            inconclusive_note = "Round level inconclusive data, check round data for more details"
                
    return {'game_id': games_df.loc[0, 'game_id'], 
     'start_secs': games_df.loc[0, 'start_secs'], 
     'end_secs': games_df.loc[last_index, 'end_secs'], 
     'start_index': games_df.loc[0, 'start_index'], 
     'end_index': games_df.loc[last_index, 'end_index'], 
     'total_rounds': len(games_df), 
     'character_1P': game_chars_dict['character_1P'], 
     'character_2P': game_chars_dict['character_2P'], 
     'winner': game_result_dict['winner'], 
     'player_1_rounds_won': game_result_dict['player_1_rounds_won'],
     'player_2_rounds_won': game_result_dict['player_2_rounds_won'],
     'inconclusive_data': is_inconclusive, 
     'inconclusive_note': inconclusive_note
     }

#Prints the anomalous round data in a readable format to the console
def _print_anomalous_round_data(anomalous_rounds_df):
    if len(anomalous_rounds_df) > 0:
        
        for index, row in anomalous_rounds_df.iterrows():
            a_id = row.Anomally_id
            time_str = "[time] start: {}secs, end: {}secs".format(row.start_secs, 
                                                                  row.end_secs)
            index_str = "[index] start: {}, end: {}".format(row.start_index, 
                                                            row.end_index)
            inconclusive_notes = "[notes] {}".format(row.inconclusive_note)
            print("id: {} | {} | {} | {}".format(a_id, time_str, index_str, 
                                                 inconclusive_notes))
    else:
        print("--No anomalous rounds--")

#Prints the inconsistent games data in a readable format to the console
def _print_inconclusive_game_data(games_df):
    if ((len(games_df) > 0) and 
        (len(games_df.loc[games_df.inconclusive_data == True,]) > 0)):        
        for index, row in games_df.iterrows():
            if row.inconclusive_data == True:
                g_id = row.game_id
                time_str = "[time] start: {}secs, end: {}secs".format(row.start_secs, 
                                                                      row.end_secs)
                index_str = "[index] start: {}, end: {}".format(row.start_index, 
                                                                row.end_index)
                inconclusive_notes = "[notes] {}".format(row.inconclusive_note)
                print("id: {} | {} | {} | {}".format(g_id, time_str, index_str, 
                                                     inconclusive_notes))
    else:
        print("--No inconclusive game data--")

#Creates an output directory & writes the output to file as CSVs, JSON, etc.
def create_csv_output_files(vid_data_df, games_df, game_rounds_df, 
                            anomalous_df, vid_name='GGST_video', 
                            create_json = False, orignal_vid = "", yt_link = ""):
    dt = datetime.now()
    timestamp = "{}-{}-{}_{}-{}-{}".format(dt.year, dt.month, dt.day, dt.hour, 
                                            dt.minute, dt.second)
    new_dir = "{}_{}".format(timestamp, vid_name)
    #cur_dir = os.curdir
    cur_dir = os.getcwd()
    output_dir = "{}\\output\\{}".format(cur_dir, new_dir)
    os.makedirs(output_dir)
    vid_data_df.to_csv("{}\\Visual_detection_data_{}_{}.csv".format(output_dir, 
                                                                    vid_name, 
                                                                    timestamp))
    games_df.to_csv("{}\\Game_data_{}_{}.csv".format(output_dir, vid_name, timestamp), 
                    index=False)
    game_rounds_df.to_csv("{}\\Round_data_{}_{}.csv".format(output_dir, vid_name, 
                                                            timestamp), index=False)
    if len(anomalous_df) > 0:
        anomalous_df.to_csv("{}\\Anomalous_rounds_{}_{}.csv".format(output_dir, 
                                                                    vid_name, 
                                                                    timestamp), 
                            index=False)
    if create_json:
        create_json_file(games_df, game_rounds_df, output_dir, 
                         orignal_vid_file = orignal_vid, youtube_link = yt_link)
    
    return output_dir

#Creates a JSON file based on the games df & nests the round data into each game
def create_json_file(games_df, games_rounds_df, file_path, orignal_vid_file = "", 
                     youtube_link = ""):
    dt = datetime.now()
    timestamp = "{}-{}-{}_{}-{}-{}".format(dt.year, dt.month, dt.day, dt.hour, 
                                            dt.minute, dt.second)
    file_name = "Games_with_round_data_{}_{}.json".format(orignal_vid_file, 
                                                          timestamp)
    full_path = "{}\\{}".format(file_path, file_name)
    
    game_ids_ls = list(games_df.game_id)
    games_data_json_dict = {'original_vid_filename': orignal_vid_file,
                            'youtube_video_link': youtube_link,
                            'games': []
                            }
    if len(game_ids_ls) > 0:
        
        for game_id in game_ids_ls:
            game_df = games_df.loc[games_df.game_id == game_id]
            game_rounds_df = games_rounds_df.loc[games_rounds_df.game_id == game_id]
            game_dict = _create_game_dict_for_json(game_df, game_rounds_df)
            games_data_json_dict['games'].append(game_dict)
        #print("Just before json.dumps")
        #games_and_rounds_json = json.dumps(games_data_json_dict)
        #print("After json.dumps")
        with open(full_path, 'w') as f:
            json.dump(games_data_json_dict, f)
            #f.write(games_and_rounds_json)
        f.close()
        #print("Wrote to file")
        return full_path
    else:
        print("--No games in games dataframe, no JSON file created--")
        return ""

def _create_game_dict_for_json(game_df, game_rounds_df):
    game_df = game_df.reset_index()
    rounds = []
    
    for index, row in game_rounds_df.iterrows():
        round_dict = {'round': game_rounds_df.loc[index, 'round'], 
                      'start_secs': int(row.start_secs), 
                      'end_secs': int(row.end_secs), 
                      'start_index': int(row.start_index),
                      'end_index': int(row.end_index), 
                      'character_1P': str(row.character_1P), 
                      'character_2P': str(row.character_2P), 'winner': str(row.winner), 
                      'winner_confidence': str(row.winner_confidence), 
                      'winner_via_health': str(row.winner_via_health), 
                      'winner_via_tmplate_match': str(row.winner_via_tmplate_match), 
                      'perfect': bool(row.perfect), 'double_ko': bool(row.double_ko), 
                      'time_out': bool(row.time_out), 'draw': bool(row.draw), 
                      'inconclusive_data': bool(row.inconclusive_data), 
                      'inconclusive_note': str(row.inconclusive_note)
                      }
        rounds.append(round_dict)
    
    game_dict = {'id': game_df.loc[0, 'game_id'], 
                 'start_secs': int(game_df.loc[0, 'start_secs']), 
                 'end_secs': int(game_df.loc[0, 'end_secs']), 
                 'start_index': int(game_df.loc[0, 'start_index']), 
                 'end_index': int(game_df.loc[0, 'end_index']), 
                 'total_rounds': int(game_df.loc[0, 'total_rounds']), 
                 'character_1P': game_df.loc[0, 'character_1P'], 
                 'character_2P': game_df.loc[0, 'character_2P'], 
                 'winner': game_df.loc[0, 'winner'], 
                 'player_1_rounds_won': int(game_df.loc[0, 'player_1_rounds_won']), 
                 'player_2_rounds_won': int(game_df.loc[0, 'player_2_rounds_won']), 
                 'inconclusive_data': bool(game_df.loc[0, 'inconclusive_data']), 
                 'inconclusive_note': game_df.loc[0, 'inconclusive_note'], 
                 'rounds': rounds
                 }
    
    return game_dict

#Applies the scaling values based on FPS to the aggregate config values
def convert_agg_config_vals_based_on_fps(agg_config_dict, vals_to_multiply_ls, 
                                         vals_to_add_1, capture_fps):
    agg_config_new_vals = agg_config_dict.copy()
    #FPS scale which the frame buffer/threshold values were figured out, when aggregation
    #happens for data at a different FPS, values will be scaled (min being 1 frame if 
    #the ratio ends up < 1) as integers.
    default_fps = 4
    fps_scaling = capture_fps / default_fps

    for key in agg_config_new_vals.keys():
        if key in vals_to_multiply_ls:
            agg_config_new_vals[key] = int(agg_config_new_vals[key] * fps_scaling)
        if key in vals_to_add_1:
            agg_config_new_vals[key] = agg_config_new_vals[key] + 1
    
    return agg_config_new_vals
