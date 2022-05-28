# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 19:32:52 2022

Guilty Gear Strive data Aggregator module. Functions related to aggregating & 
validating aggregation results to ensure game data/outcomes are as accurate as 
possible based on the extracted data.

@author: PDP2600
"""
import pandas as pd
from collections import Counter

def get_char_portrait_col_names(df_columns:list)->list:
    """Retrieves all the P1 & P2 character portrait match column names from a
    list of column names.
    -------------------------------------------------------------------------
    -=df_columns=- List of all the column names from the DataFrawm w/ the raw 
      extracted match data.
    -------------------------------------------------------------------------
    [-return-] A list w/ the names of all the P1/P2 character portrait columns."""
    char_portrait_col_names:list = []
    for col_name in df_columns:
        if "P_Portrait" in col_name:
            char_portrait_col_names.append(col_name)
            
    return char_portrait_col_names

def reduce_match_df_to_agg_df(vid_match_data_df):
    """Creates a new DataFrame from the raw data extraction DataFrame, with 
    only the columns required for aggregation.
    -------------------------------------------------------------------------
    -=vid_match_data_df=- DataFrame w/ raw extracted match data.
    -------------------------------------------------------------------------
    [-return-] A DataFrame which only has the columns required for aggregation."""
    agg_col_names:list = ['Time_in_Secs', 'Frame_Number_secs']
    char_portraits:list = get_char_portrait_col_names(list(vid_match_data_df))
    other_cols:list = ['Starter_Duel', 'Starter_Number_1', 'Starter_Number_2', 
                       'Starter_Number_3', 'Starter_Number_Final', 
                       'Starter_Lets_Rock', 'Ender_Slash', 'Ender_Double_KO', 
                       'Ender_Draw', 'Ender_Perfect', 'Ender_Times_Up', 
                       'Ender_1P_Win', 'Ender_2P_Win', 'Game_UI_Timer_Outline', 
                       '1P_High_Health', '1P_Low_Health', '2P_High_Health', 
                       '2P_Low_Health']
    agg_col_names.extend(char_portraits)
    agg_col_names.extend(other_cols)
    return vid_match_data_df[agg_col_names]

def _find_duel_start_blocks(duel_df, duel_block_threshold:int)->list:
    """Creates a list of dicts which contain the start & end frames/indexs of 
    all the "Duel" starters detected. Depending on processing FPS, the same
    starter/ender can be detected in multiple frames (sometimes not 
    consequectively), this function combines them as a "block".
    -------------------------------------------------------------------------
    -=duel_df=- DataFrame w/ match data, filtered to only be valid "Duel" 
      detections.
    -=duel_block_threshold=- Config value denoting the distance in frames where
      non-consequective detected "Duels" can be considered in the same "block"
    -------------------------------------------------------------------------
    [-return-] List of dicts w/ the start & end indexes of every valid "Duel" 
     detected."""
    duel_index_blocks:list = []
    prev_index:int = -1
    start_index:int = 0
    last_index:int = list(duel_df.index)[-1]
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
    """Evaluates round match scores submitted fora single "Duel" block to 
    determine if a specific round number can be determined w/ confidence.
    -------------------------------------------------------------------------
    -=round_bool_data_df=- DataFrame. which has rows from a single "Duel" block 
     & only contains boolean value columns for each of the 4 possible round 
     values, which are determined in function _round_number_detect.
    -------------------------------------------------------------------------
    [-return-] A str which is either 'Unknown' if round data is inconclusive, 
     or is one of the values: 'Round_1', 'Round_2', 'Round_3', 'Round_Final'."""
    round_sum = {'Round_1': sum(round_bool_data_df.Round_1), 
                 'Round_2': sum(round_bool_data_df.Round_2), 
                 'Round_3': sum(round_bool_data_df.Round_3), 
                 'Round_Final': sum(round_bool_data_df.Round_Final)
                 }
    #Non-round 1 scores count for double to avoid false positives w/ Duel 1
    round_sum['Round_2'] = round_sum['Round_2'] * 2
    round_sum['Round_3'] = round_sum['Round_3'] * 2
    round_sum['Round_Final'] = round_sum['Round_Final'] * 2
    
    if (round_sum['Round_1'] == 0 and round_sum['Round_2'] == 0 and 
        round_sum['Round_3'] == 0 and round_sum['Round_Final'] == 0):
        return "Unknown"
    else:
        max_round_key:str = max(round_sum, key=round_sum.get)
        count:int = 0
        for val in list(round_sum.values()):
            if val == round_sum[max_round_key]:
                count = count + 1
        if count < 2:
            return max_round_key
        else:
            return "Unknown"

def _round_number_detect(duel_df, min_delta:float)->str:
    """Evaluates round match scores submitted for a single "Duel" block to 
    determine if a specific round number can be determined w/ confidence.
    -------------------------------------------------------------------------
    -=duel_df=- DataFrame. which has rows from a single "Duel" block 
      & has the raw extracted match score data for those frames.
    -=min_delta=- Config value, which is the minimum score difference between 
      multiple Duel "number" scores in the same frame, to consider one of the 
      round number values what is the best guess of the actual round number.
    -------------------------------------------------------------------------
    [-return-] A str which is either 'Unknown' if round data is inconclusive, 
     or is one of the values: 'Round_1', 'Round_2', 'Round_3', 'Round_Final'."""
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
        #Non-Duel 1 round numbers need to be 0 to avoid false positives
        if row.Starter_Number_1 > 0:
            if ((row.Starter_Number_2 == 0) and 
                (row.Starter_Number_3 == 0) and 
                (row.Starter_Number_Final == 0)):
                duel_number_cols_df.loc[index, 'Round_1'] = True

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
    """Finds if there's a "Lets Rock" template detected which is associated w/ 
    a "Duel" block, returning the end index of the "Lets Rock" block.
    -------------------------------------------------------------------------
    -=lets_rock_df=- DataFrame. which all rows w/ non-zero "Lets Rock" match 
      scores & has the raw extracted match score data for those frames.
    -=duel_end=- End index of a "Duel" block.
    -=duel_to_lets_rock_buffer=- Config value, denoting how many frames from 
      the end of a "Duel" block a detected "Lets Rock" can be considered a part 
      of the same round "Starter" block.
    -------------------------------------------------------------------------
    [-return-] Either -1 if there was no "Lets Rock" within the buffer, or the 
     end index frame of the "Lets Rock" block that's paired w/ the "Duel" block."""
    start:int = duel_end + 1
    end:int = start + duel_to_lets_rock_buffer
    lets_rock_within_buffer_df = lets_rock_df.loc[start: end, ]
    if len(lets_rock_within_buffer_df) == 0:
        return -1
    else:
        return list(lets_rock_within_buffer_df.index)[-1]

def _round_start_processing(data_for_agg_df, agg_config:dict):
    """Determines all the instances of round start indicators, combining where
    applicable, denoting where the start blocks start/end, & the detected round
    number when possible.
    -------------------------------------------------------------------------
    -=data_for_agg_df=- DataFrame w/ raw match data & only columns used for 
      aggregation.
    -=agg_config=- Config values for aggregation processing in a dict
    -------------------------------------------------------------------------
    [-return-] DataFrame where each row is a round start block, with the 
     columns/data: start_index:int, end_index:int, start_secs:int, end_secs:int, 
     round:str, & Lets_Rock:bool (whether Lets Rock was detected in the block)."""
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
        round_num:str = _round_number_detect(duel_block_df, 
                                             agg_config['duel_number_min_delta'])
        lets_rock_block:int = _get_paired_lets_rock_block(lets_rock_detected_df, 
                                                          end, 
                                                          agg_config['duel_to_lets_rock_frame_buffer'])
        if lets_rock_block != -1:
            end = lets_rock_block
            includes_lets_rock = True
            
        round_dict = {'start_index': start, 'end_index': end, 
                      'start_secs': data_for_agg_df.loc[start, 'Time_in_Secs'], 
                      'end_secs': data_for_agg_df.loc[end, 'Time_in_Secs'],
                      'round': round_num, 'Lets_Rock': bool(includes_lets_rock)
                      }
        round_start_df = round_start_df.append(pd.DataFrame(round_dict, 
                                                            index=[start]), 
                                               sort=False)
    return round_start_df

def _find_orphan_lets_rocks(data_for_agg_df, round_start_df):
    """Finds if there are any detected Lets Rocks rows which weren't associated 
    w/ a "Duel" (previous processing starts w/ detected "Duel" blocks).
    -------------------------------------------------------------------------
    -=data_for_agg_df=- DataFrame w/ raw match data & only columns used for 
      aggregation.
    -=round_start_df=- DataFrame w/ the processed round start block data.
    -------------------------------------------------------------------------
    [-return-] DataFrame w/ all rows which had "Lets Rock" detected, but were 
     not included in the previously processed round start blocks."""
    lets_rock_detected_df = data_for_agg_df.loc[data_for_agg_df.Starter_Lets_Rock > 0]
    orphaned_lets_rocks_df = pd.DataFrame({})
    
    for index, row in lets_rock_detected_df.iterrows():        
        isOrphaned:bool = True
        for round_index, round_row in round_start_df.iterrows():
            if (index >= round_row.start_index) and (index <= round_row.end_index):
                isOrphaned = False
        
        if isOrphaned:
            orphaned_lets_rocks_df = orphaned_lets_rocks_df.append(row, sort=False)
    
    return orphaned_lets_rocks_df

def _find_lets_rock_solo_blocks(lets_rock_df):
    """With a DataFrame of orphaned "Lets Rock"s, consolidates adjacent rows 
    detecting the same "Lets Rock" into round start blocks.
    -------------------------------------------------------------------------
    -=lets_rock_df=- DataFrame which contains raw match data for all the "Lets 
      Rock"s detected w/o associated "Duels" (orphaned "Lets Rock"s)
    -------------------------------------------------------------------------
    [-return-] DataFrame where the orphaned "Lets Rock"s are transformed into 
     round start blocks: start_index:int, end_index:int, start_secs:int, 
     start_secs:int, & round:str (all round values "Unknown")."""
    rock_index_blocks:list = []
    prev_index:int = -1
    start_index:int = 0
    last_index = list(lets_rock_df.index)[-1]
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
    """Turns a list of round start block dicts, into DataFrames w/ the 
    start_index of each dict set as the df row index.
    -------------------------------------------------------------------------
    -=lets_rock_block=- List of dicts w/ "Lets Rock" round start block data.
    -------------------------------------------------------------------------
    [-return-] DataFrame out of the round start dicts w/ start_index being used 
     as each df row's index: start_index:int, end_index:int, start_secs:int, 
     start_secs:int, & round:str (all round values "Unknown")."""
    round_start_df = pd.DataFrame({})
    for block in lets_rock_block:
        start_index = block['start_index']
        round_start_df = round_start_df.append(pd.DataFrame(block, 
                                                            index=[start_index]), 
                                               sort=False)
    return round_start_df

def load_match_csv_into_dataframe(csv_path:str):
    """Loads csvs created from a previous extraction/aggregation process into 
    a DataFrame.
    -------------------------------------------------------------------------
    -=csv_path=- Filepath of FGW csv to load into DataFrame.
    -------------------------------------------------------------------------
    [-return-] DataFrame w/ csv's data loaded & index reset."""
    vid_data_df = pd.read_csv(csv_path)
    vid_data_df = vid_data_df.reset_index()
    vid_data_df = vid_data_df.drop(['Unnamed: 0'], axis='columns')
    vid_data_df = vid_data_df.drop(['index'], axis='columns')
    return vid_data_df

def _consolidate_orphans_into_round_start_blocks(orphaned_df, round_start_df):
    """Combines the round start blocks found based on "Duel"s & the orphaned 
    "Lets Rock" round start blocks.
    -------------------------------------------------------------------------
    -=orphaned_df=- DataFrame w/ orphaned "Lets Rock" round start blocks.
    -=round_start_df=- DataFrame w/ the processed "Duel" round start block data.
    -------------------------------------------------------------------------
    [-return-] DataFrame w/ all round start blocks merged & sorted by index."""
    if len(orphaned_df) > 0:
        lets_rock_rounds = _find_lets_rock_solo_blocks(orphaned_df)
        round_start_df = round_start_df.append(lets_rock_rounds)
        round_start_df = round_start_df.sort_index(axis = 0)
    return round_start_df    

def _get_single_ender_blocks(single_ender_df, end_block_threshold:int)->list:
    """Transforms instances of specific enders into round end blocks. Combines 
    multiple rows/frames detecting the same ender for a single round.
    -------------------------------------------------------------------------
    -=single_ender_df=- DataFrame which contains raw match data filtered to 
      rows/frames where a specific ender (Slash, Perfect, Double KO, Times Up) 
      has been detected.
    -=end_block_threshold=- Config value, max difference in index/frame for 
      adjacent rows/frames to be considered the same ender for the same round.
    -------------------------------------------------------------------------
    [-return-] List of dicts, transforming data into round end blocks: 
     start_index:int, end_index:int, perfect: False, double_ko: False, 
     time_out: False, & draw: False."""
    ender_index_blocks:list = []
    prev_index:int = -1
    start_index:int = 0
    last_index = list(single_ender_df.index)[-1]
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

def _find_round_end_blocks(ender_df, end_block_threshold:int)->list:
    """With a DataFrame of the raw extract data filtered by enders detected, 
    transforms it into a list of round end blocks for each round's ender.
    -------------------------------------------------------------------------
    -=ender_df=- DataFrame which contains raw match data filtered to 
      rows/frames where an ender (Slash, Perfect, Double KO, Times Up) has a 
      valid match score.
    -=end_block_threshold=- Config value, max difference in index/frame for 
      adjacent rows/frames to be considered the same ender for the same round.
    -------------------------------------------------------------------------
    [-return-] List of dicts, transforming data into round end blocks: 
     start_index:int, end_index:int, perfect:bool, double_ko:bool, 
     time_out:bool, & draw:bool."""
    slash_ender_df = ender_df.loc[ender_df['Ender_Slash'] > 0]
    perfect_ender_df = ender_df.loc[ender_df['Ender_Perfect'] > 0]
    double_ko_ender_df = ender_df.loc[ender_df['Ender_Double_KO'] > 0]
    times_up_ender_df = ender_df.loc[ender_df['Ender_Times_Up'] > 0]
    all_ender_blocks:list = []
    
    if len(list(slash_ender_df.index)) > 0:
        slash_blocks = _get_single_ender_blocks(slash_ender_df, 
                                                end_block_threshold)
        all_ender_blocks = all_ender_blocks + slash_blocks
    
    if len(list(perfect_ender_df.index)) > 0:
        perfect_blocks = _get_single_ender_blocks(perfect_ender_df, 
                                                  end_block_threshold)
        for i, ender in enumerate(perfect_blocks):
            perfect_blocks[i]['perfect'] = True
            
        all_ender_blocks = all_ender_blocks + perfect_blocks
    
    if len(list(double_ko_ender_df.index)) > 0:
        double_ko_blocks = _get_single_ender_blocks(double_ko_ender_df, 
                                                    end_block_threshold)
        for i, ender in enumerate(double_ko_blocks):
            double_ko_blocks[i]['double_ko'] = True
            double_ko_blocks[i]['draw'] = True
            
        all_ender_blocks = all_ender_blocks + double_ko_blocks
        
    if len(list(times_up_ender_df.index)) > 0:
        times_up_blocks = _get_single_ender_blocks(times_up_ender_df, 
                                                   end_block_threshold)
        for i, ender in enumerate(times_up_blocks):
            times_up_blocks[i]['time_out'] = True
            
        all_ender_blocks = all_ender_blocks + times_up_blocks        
    return all_ender_blocks

def _get_time_out_draw_block(draw_df, time_out_end:int, 
                             time_out_to_draw_buffer:int)->int:
    """Checks for linked "Draw" ender template match, after instance of "Time 
    Out" ender has been detected.
    -------------------------------------------------------------------------
    -=draw_df=- DataFrame which contains raw match data filtered to 
      rows/frames which "Draw" has a valid match score.
    -=time_out_end=- Index where a "Time Out" block ends
    -=time_out_to_draw_buffer=- Config value, the number of rows/frames to 
      check after a "Time Out" block ends for an associated "Draw" ender.
    -------------------------------------------------------------------------
    [-return-] End index of the "Draw" block if it exists, or -1 when no "Draw"."""
    start:int = time_out_end + 1
    end:int = start + time_out_to_draw_buffer
    draw_within_buffer_df = draw_df.loc[start: end, ]
    if len(draw_within_buffer_df) == 0:
        return -1
    else:
        return list(draw_within_buffer_df.index)[-1]

def _round_end_processing(data_for_agg_df, agg_config:dict):
    """Runs functions to process raw data & aggregate it into round end data. 
    Creates round ender blocks w/ the intervals of frames each round end takes 
    up & captures any special outcomes the round may have ended in.
    -------------------------------------------------------------------------
    -=data_for_agg_df=- DataFrame w/ raw match data & only columns used for 
      aggregation.
    -=agg_config=- Config values for aggregation processing in a dict
    -------------------------------------------------------------------------
    [-return-] DataFrame where each row is a round end block, w/ the 
     columns/data: start_index:int, end_index:int, start_secs:int, end_secs:int, 
     perfect:bool, double_ko:bool, time_out:bool, & draw:bool."""
    ender_detected_df = data_for_agg_df.loc[(data_for_agg_df['Ender_Slash'] 
                                             > 0.49) | 
                                            (data_for_agg_df['Ender_Double_KO'] 
                                             > 0.49) | 
                                            (data_for_agg_df['Ender_Perfect'] 
                                             > 0.49) | 
                                            (data_for_agg_df['Ender_Times_Up'] 
                                             > 0.49)]
    draw_detected_df = data_for_agg_df.loc[data_for_agg_df.Ender_Draw > 0]
    round_end_df = pd.DataFrame({})
    ender_index_blocks:list = _find_round_end_blocks(ender_detected_df, 
                                                    agg_config['ender_block_index_threshold'])
    for end_block in ender_index_blocks:
        start:int = end_block['start_index']
        end:int = end_block['end_index']
        is_draw:bool = end_block['draw']
        ender_block_df = ender_detected_df.copy()
        ender_block_df = ender_block_df.loc[start: end, ]
        
        if end_block['time_out'] and (len(list(draw_detected_df.index)) > 0):
            times_up_draw_buffer = agg_config['times_up_to_draw_frame_buffer']
            draw_block_end:int = _get_time_out_draw_block(draw_detected_df, end, 
                                                          times_up_draw_buffer)            
            if draw_block_end != -1:
                end = draw_block_end
                is_draw = True
        
        end_dict = {'start_index': start, 'end_index': end, 
                    'start_secs': data_for_agg_df.loc[start, 'Time_in_Secs'], 
                    'end_secs': data_for_agg_df.loc[end, 'Time_in_Secs'], 
                    'perfect': end_block['perfect'], 
                    'double_ko': end_block['double_ko'], 
                    'time_out': end_block['time_out'], 'draw': is_draw}
        
        round_end_df = round_end_df.append(pd.DataFrame(end_dict, index = [start]), 
                                               sort=False)    
    return round_end_df

def _merge_round_start_and_end_blocks(round_start_df, round_end_df):
    """Combines the round start & end blocks into a DataFrame, sorted by index. 
    When there are no false positives detected & no missed starter/enders in 
    the video, it's expected starter & ender rows will alternate.'
    -------------------------------------------------------------------------
    -=round_start_df=- DataFrame w/ the processed round start block data.
    -=round_end_df=- DataFrame w/ the processed round end block data.
    -------------------------------------------------------------------------
    [-return-] DataFrame w/ all round start & end blocks merged & sorted by 
     index."""
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
    """Creates a round dictionary when there's either a missing round start or
    end block. This can be caused by false positves & missed detection.
    -------------------------------------------------------------------------
    -=cur_row_df=- DataFrame w/ the current round block being checked.
    -=adj_row_df=- DataFrame w/ the next or previous round block w/ respect to 
      cur_row_df. Only used for round start/end estimation for missing element.
    -=agg_config=- Config values for aggregation processing in a dict
    -=note=- String w/ a specific message about how the row is inconclusive.
    -------------------------------------------------------------------------
    [-return-] Round dict w/ estimated start/end depending what's missing. 
    Contains dynamic time/index start/end data, & all the data from the round 
    blocks, but winner/character data will have filler 'Unknown' values."""
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
    """Creates a round dictionary for invalid rounds at the beginning or end of 
    the video.
    -------------------------------------------------------------------------
    -=cur_row_df=- DataFrame w/ the current round block being checked.
    -=note=- String w/ a specific message about how the row is invalid.
    -------------------------------------------------------------------------
    [-return-] Round dict which has start or end values being -1 depending on 
     why it's invalid. Winner/character data will have filler 'Unknown' values."""
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
                   'draw': cur_row_df.loc[0,'draw'], 
                   'inconclusive_data': True, 'inconclusive_note': note
                   }
    return invalid

def _create_valid_round_dict(cur_row_df, next_row_df)->dict:
    """Creates a round dictionary where cur_row_df is a round start block & 
    next_row_df is a round end block, combining their data into a single round.
    -------------------------------------------------------------------------
    -=cur_row_df=- DataFrame w/ the current round block being checked.
    -=next_row_df=- DataFrame w/ the next round block w/ respect to cur_row_df.
    -------------------------------------------------------------------------
    [-return-] Round dict which contains dynamic time/index start/end data, & 
    all the data from the round blocks, but winner/character data will have 
    filler 'Unknown' values."""
    cur_row = cur_row_df.copy().reset_index()
    next_row = next_row_df.copy().reset_index()
    round_dict = {'start_secs': cur_row.loc[0,'start_secs'], 
                  'start_index': cur_row.loc[0,'start_index'], 
                  'end_secs': next_row.loc[0,'end_secs'], 
                  'end_index': next_row.loc[0,'end_index'], 
                  'round': cur_row.loc[0,'round'], 
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
    """Called for round blocks which either are not Starters and/or the next 
    round block is not an Ender, which indicates a false positive or missing 
    Starter/Ender detection.
    -------------------------------------------------------------------------
    -=cur_row_df=- DataFrame w/ the current round block being checked.
    -=next_row_df=- DataFrame w/ the next round block w/ respect to cur_row_df.
    -=prev_row_df=- DataFrame w/ the previous round block w/ respect to 
      cur_row_df.
    -=agg_config=- Config values for aggregation processing in a dict.
    -------------------------------------------------------------------------
    [-return-] Round dict created by _create_invalid_dict or 
     _create_inconclusive_dict, depend on the issue w/ the round blocks."""
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
            inconl_note = "Missing Ender: Button Check or False positive"
            return _create_inconclusive_dict(cur_row, next_row, agg_config, 
                                             inconl_note)
        elif (((cur_row.loc[0,'round'] == 'Round_1') and 
        (next_row.loc[0,'round'] == 'Round_2')) or 
        ((cur_row.loc[0,'round'] == 'Round_2') and 
        (next_row.loc[0,'round'] == 'Round_3')) or 
        ((cur_row.loc[0,'round'] == 'Round_3') and 
        (next_row.loc[0,'round'] == 'Round_Final'))):
            inconl_note = "Missing Ender: Middle of a Game"
            return _create_inconclusive_dict(cur_row, next_row, agg_config, 
                                             inconl_note)
        elif (((cur_row.loc[0,'round'] == 'Round_2') and 
        (next_row.loc[0,'round'] == 'Round_1')) or 
        ((cur_row.loc[0,'round'] == 'Round_3') and 
        (next_row.loc[0,'round'] == 'Round_1')) or 
        ((cur_row.loc[0,'round'] == 'Round_Final') and 
        (next_row.loc[0,'round'] == 'Round_1'))):
            inconl_note = "Missing Ender: Last Round of a Game"
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

def _consolidate_round_data(rounds_df, agg_config:dict):
    """Transforms Round Start & End data into Round data, & attempts to resolve 
    rounds with missing starter or ender where possible & flags those instances.
    -------------------------------------------------------------------------
    -=rounds_df=- DataFrame w/ the merged round start/end block data.
    -=agg_config=- Config values for aggregation processing in a dict.
    -------------------------------------------------------------------------
    [-return-] DataFrame of Round data created from combining start/end blocks. 
     They contain all data start/end round blocks did, plus winner/character 
     fields which have filler 'Unknown' values."""
    index_vector = list(rounds_df.index)
    last_index:int = index_vector[-1]
    i:int = 0
    prev_index:int = -1
    round_data_df = pd.DataFrame({})
    prev_row_df = pd.DataFrame({})

    while i < len(index_vector):
        index = index_vector[i]
        if index != last_index:
            next_index = index_vector[i+1]
            if ((rounds_df.loc[index,'block_type'] == 'Starter') and 
                (rounds_df.loc[next_index,'block_type'] == 'Ender')):
                round_dict = _create_valid_round_dict(rounds_df.loc[index:index,], 
                                                      rounds_df.loc[next_index:
                                                                    next_index,])
                round_data_df = round_data_df.append(pd.DataFrame(round_dict, 
                                                                  index=[index]))
                #Setting previous row index to the ender row
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
                prev_index = index_vector[i]
                i = i + 1
        else:
            next_row_df = pd.DataFrame({})
            round_dict = _resolve_missing_pair(rounds_df.loc[index:index,], 
                                               next_row_df, prev_row_df, 
                                               agg_config)
            round_data_df = round_data_df.append(pd.DataFrame(round_dict, 
                                                              index = [index]))
            i = i + 1
    return round_data_df

def _validate_duel_match_score(ggst_slice_df, min_score:float)->bool:
    """Checks if any frames/rows in a defined round start block 1)Have a "Duel" 
    match score higher or equal to min_score & 2)There are match values above 0 
    for any of the possible Round number templates (1, 2, 3, Final).
    -------------------------------------------------------------------------
    -=ggst_slice_df=- DataFrame w/ raw video extract data sliced based on a 
      single Round start block's start/end indexes.
    -=min_score=- Minimum score for "Duel" template detection to be a valid 
      "Duel" frame/row.
    -------------------------------------------------------------------------
    [-return-] Boolean value whether the round start data is considered high 
     enough quality, to be trusted to not be a false positive."""
    duel_min_data_df = ggst_slice_df.loc[((ggst_slice_df.Starter_Duel >= 
                                           min_score) &
                                          ((ggst_slice_df.Starter_Number_1 
                                            > 0) |
                                           (ggst_slice_df.Starter_Number_2 
                                            > 0) |
                                           (ggst_slice_df.Starter_Number_3 
                                            > 0) |
                                           (ggst_slice_df.Starter_Number_Final 
                                            > 0)))]
    return len(duel_min_data_df) > 0

def _filter_round_start_false_positives(round_start_df, ggst_vid_data_df):
    """Filters out round start blocks which seem like they might be false 
    positives. Round start blocks w/ associated "Lets Rock" templates detected, 
    and/or "Duel" template scores consider high enough are kept.
    -------------------------------------------------------------------------
    -=round_start_df=- DataFrame w/ the processed round start block data.
    -=ggst_vid_data_df=- DataFrame w/ raw match data
    -------------------------------------------------------------------------
    [-return-] DataFrame of Round start blocks, w/ likely starter false 
     positives filtered out."""
    start_blocks_df = pd.DataFrame({})
    for index, row in round_start_df.iterrows():
        ggst_slice_df = ggst_vid_data_df.loc[row.start_index:row.end_index,]
        has_high_duel_score:bool = _validate_duel_match_score(ggst_slice_df, 
                                                              0.85)
        if bool(round_start_df.loc[index, 'Lets_Rock']):
            round_df = pd.DataFrame({'start_index': round_start_df.loc[index, 
                                                                       'start_index'], 
                                     'end_index': round_start_df.loc[index, 
                                                                     'end_index'], 
                                     'start_secs': round_start_df.loc[index, 
                                                                      'start_secs'], 
                                     'end_secs': round_start_df.loc[index, 
                                                                    'end_secs'], 
                                     'round': round_start_df.loc[index, 'round']}, 
                                    index = [index])
            start_blocks_df = start_blocks_df.append(round_df)
        elif ((not bool(round_start_df.loc[index, 'Lets_Rock'])) and 
              has_high_duel_score):
            round_df = pd.DataFrame({'start_index': round_start_df.loc[index, 
                                                                       'start_index'], 
                                     'end_index': round_start_df.loc[index, 
                                                                     'end_index'], 
                                     'start_secs': round_start_df.loc[index, 
                                                                      'start_secs'], 
                                     'end_secs': round_start_df.loc[index, 
                                                                    'end_secs'], 
                                     'round': round_start_df.loc[index, 'round']}, 
                                    index = [index])
            start_blocks_df = start_blocks_df.append(round_df)
        else:
            pass
    return start_blocks_df
    
def _get_index_when_ui_disappears(ggst_round_df):
    """Used to correct overlaps between different Round ends & starts, which 
    can happen when there are missing starters. Given the frames in the round, 
    it finds the first frame/instance the UI is off screen (based on Timer 
    outline template match score).
    -------------------------------------------------------------------------
    -=ggst_round_df=- DataFrame w/ raw match data, for a single round.
    -------------------------------------------------------------------------
    [-return-] The index of the 1st frame without the UI present, to be used as 
     the new round start for the overlapping round."""
    no_ui_frames_df = ggst_round_df.loc[ggst_round_df.Game_UI_Timer_Outline == 0]
    no_ui_frames_df = no_ui_frames_df.sort_index()
    first_no_timer_frame = list(no_ui_frames_df.index)[0]
    return first_no_timer_frame
        
def _validate_unknown_round_duration(round_blocks_df, ggst_data_df):
    """Checks rounds w/ inconclusive data (missing Starter or Ender), & if 
    there's an overlap between that round & an adjacent one, round start or end 
    will be adjusted so there's no more overlap.
    -------------------------------------------------------------------------
    -=round_blocks_df=- DataFrame w/ combined round block data.
    -=ggst_data_df=- DataFrame w/ raw match data
    -------------------------------------------------------------------------
    [-return-] DataFrame of Round blocks, w/ the adjusted start or end times 
     which now avoid overlapping w/ another Round block."""
    verified_rounds_df = round_blocks_df.copy()
    index_ls = list(verified_rounds_df.index)
    last_index:int = index_ls[-1]
    prev_round_end_index:int = -1
    index_count:int = 0
    while index_count < len(index_ls):
        index = index_ls[index_count]
        if bool(verified_rounds_df.loc[index, 'inconclusive_data']):
            round_start_index = verified_rounds_df.loc[index, 'start_index']
            round_end_index = verified_rounds_df.loc[index, 'end_index']
            next_index = (index_ls[index_count + 1] if index != last_index 
                          else -1)
            if next_index != -1:
                next_round_start_secs = verified_rounds_df.loc[next_index, 
                                                               'start_secs']
                next_round_start_index = verified_rounds_df.loc[next_index, 
                                                                'start_index']
            if ((prev_round_end_index > 0) and 
                ('Missing Starter:' in verified_rounds_df.loc[index, 
                                                              'inconclusive_note']) 
                and (round_start_index <= prev_round_end_index)):
                ggst_slice_df = ggst_data_df.loc[prev_round_end_index:round_end_index,]
                round_transition_index = _get_index_when_ui_disappears(ggst_slice_df)
                round_transition_secs = ggst_data_df.loc[round_transition_index, 
                                                         'Time_in_Secs']
                verified_rounds_df.loc[index, 'start_secs'] = round_transition_secs
                verified_rounds_df.loc[index, 'start_index'] = round_transition_index
            elif ((index != last_index) and 
                  ('Missing Ender:' in verified_rounds_df.loc[index, 
                                                              'inconclusive_note']) 
                  and (round_end_index >= next_round_start_index)):
                verified_rounds_df.loc[index, 'end_secs'] = (next_round_start_secs 
                                                             - 1)
                verified_rounds_df.loc[index, 'end_index'] = (next_round_start_index 
                                                              - 1)
        index_count = index_count + 1
        prev_round_end_index = verified_rounds_df.loc[index, 'end_index']
        
    return verified_rounds_df

def aggregate_into_rounds(ggst_vid_data_df, agg_config:dict):
    """Aggregates extracted raw video data into game rounds, & runs other 
    validation functions to help make sure aggregation is accurate.
    -------------------------------------------------------------------------
    -=ggst_vid_data_df=- DataFrame w/ raw match data.
    -=agg_config=- Config values for aggregation processing in a dict.
    -------------------------------------------------------------------------
    [-return-] DataFrame of Round blocks. Data defines their start/end 
     intervals, any round start or end data (round number, end state, etc), & 
     winner/character fields with filler 'Unknown' values."""
    round_start_blocks_df = _round_start_processing(ggst_vid_data_df, agg_config)
    round_start_blocks_df = _filter_round_start_false_positives(round_start_blocks_df, 
                                                                ggst_vid_data_df)
    #Finds instances of "Lets Rock" which weren't coupled w/ "Duel" matches
    orphaned_lets_rocks_df = _find_orphan_lets_rocks(ggst_vid_data_df, 
                                                     round_start_blocks_df)
    round_start_df = _consolidate_orphans_into_round_start_blocks(orphaned_lets_rocks_df, 
                                                                  round_start_blocks_df)

    round_end_blocks_df = _round_end_processing(ggst_vid_data_df, agg_config)
    round_end_blocks_df = round_end_blocks_df.sort_index(axis = 0)

    round_start_end_df = _merge_round_start_and_end_blocks(round_start_df, 
                                                           round_end_blocks_df)
    consolidated_rounds_df = _consolidate_round_data(round_start_end_df, 
                                                     agg_config)
    consolidated_rounds_df = _validate_unknown_round_duration(consolidated_rounds_df, 
                                                              ggst_vid_data_df)
    
    return consolidated_rounds_df

def _reset_max_char_dict(col_name:str, val:float)->dict:
    """Resets the character counter dict to a single key & value."""
    new_max:dict = {}
    new_max[col_name] = val
    
    return new_max

def get_character_used(ggst_slice_data_df, character_cols:list, 
                       min_char_delta:float)->str:
    """Checks the raw data frames/rows of a round, counting the number of times 
    each character for a player is detected, then outputs the character name.
    -------------------------------------------------------------------------
    -=ggst_slice_data_df=- DataFrame w/ raw video extract data sliced based on a 
      single Round block's start/end indexes.
    -=character_cols=- List of the character portrait column names to check. 
      Should be the columns for just one player (Player 1 or 2).
    -=min_char_delta=- Config value. Minimum difference in match score to 
      decide if there's an undisputed character in the case of multiple 
      characters detected for the same frame.
    -------------------------------------------------------------------------
    [-return-] String of the character detected or 'Unknown' if there's not a 
     good enough consensus of the character detected in the Round."""
    char_detected_sum:dict = {}
    for index, row in ggst_slice_data_df.iterrows():
        max_val_dict = {}        
        for col in character_cols:
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
        #When there's a single undisputed max char value for the round, 
        if len(max_val_dict) == 1:
            max_key = list(max_val_dict.keys())[0]
            if max_key in char_detected_sum:
                char_detected_sum[max_key] = char_detected_sum[max_key] + 1
            else:
                char_detected_sum[max_key] = 1    

    return _verify_character_detected(char_detected_sum)

def _verify_character_detected(char_detected:dict)->str:
    """Based on the dict w/ character detected counts, outputs the detected 
    character name.
    -------------------------------------------------------------------------
    -=char_detected=- Contains the count of each character portrait key 
      detected in the round. More often than not it will only have 1 key.
    -------------------------------------------------------------------------
    [-return-] String of the character detected or 'Unknown' if there's more 
    than 1 max value key in the dict."""
    max_key:str = 'Unknown'
    if len(char_detected) > 0:
        max_key = max(char_detected, key=char_detected.get)
        max_val = char_detected[max_key]
        #Check to make sure there are not more than 1 key w/ the max value
        if Counter(list(char_detected.values()))[max_val] == 1:
            max_key = max_key.replace("_1P_Portrait", "") if (
                '1P' in max_key) else max_key.replace("_2P_Portrait", "")            
        else:
            max_key = 'Unknown'
    
    return max_key

def extract_played_characters(ggst_vid_data_df, rounds_df, agg_config:dict):
    """Calls functions to aggregate the P1 & P2 characters for each round, & 
    assigns those character values to a new DataFrame of Rounds.
    -------------------------------------------------------------------------
    -=ggst_vid_data_df=- DataFrame w/ extracted raw video data.
    -=rounds_df=- DataFrame w/ processed round block data.
    -=agg_config=- Config values for aggregation processing in a dict.
    -------------------------------------------------------------------------
    [-return-] DataFrame w/ all the Rounds contained in rounds_df, but w/ P1 & 
     P2 character values assigned based on character aggregation functions."""
    char_data_rounds_df = rounds_df.copy()
    char_portraits_agg:list = get_char_portrait_col_names(list(ggst_vid_data_df))
    player_1_characters:list = [x for x in char_portraits_agg 
                                if '1P_Portrait' in x]
    player_2_characters:list = [x for x in char_portraits_agg 
                                if '2P_Portrait' in x]
    
    for index, row in char_data_rounds_df.iterrows():
        if (row.start_index != -1) and (row.end_index != -1):
            start:int = row.start_index + 1
            end:int = row.end_index - 1
            round_slice_df = ggst_vid_data_df.loc[start:end,]
            player_1_char:str = get_character_used(round_slice_df, 
                                                   player_1_characters, 
                                                   agg_config['min_character_delta'])
            player_2_char:str = get_character_used(round_slice_df, 
                                                   player_2_characters, 
                                                   agg_config['min_character_delta'])
            char_data_rounds_df.loc[index, 'character_1P'] = player_1_char
            char_data_rounds_df.loc[index, 'character_2P'] = player_2_char
            
    return char_data_rounds_df

def _get_winner_by_health(ggst_vid_data_df, round_input_df, 
                          agg_config:dict)->tuple[str,str]:
    """Attempts to find the winner based on health, checking after ender 1st 
    (players can press buttons to skip to next round after ender), & then 
    before ender or another method if the round had no ender dectected.
    -------------------------------------------------------------------------
    -=ggst_vid_data_df=- DataFrame w/ extracted raw video data.
    -=round_input_df=- DataFrame w/ a single round block.
    -=agg_config=- Config values for aggregation processing in a dict.
    -------------------------------------------------------------------------
    [-return-] A tuple of strings, the winner ('Player 1', 'Player 2', 
     'Unknown') & confidence (None, 'Very Low', 'Low', 'Medium', 'High')"""
    round_df = round_input_df.copy().reset_index()
    start_index:int = round_df.loc[0, 'start_index']
    end_index:int = round_df.loc[0, 'end_index']
    last_index = list(ggst_vid_data_df.tail(1).index)[0]
    frame_buffer_legit_ender:int = agg_config['health_after_ender_frame_buffer']
    frame_buffer_missing_ender:int = agg_config['missing_ender_health_buffer']
    health_min_delta:float = agg_config['player_health_min_delta']
    health_min_delta_no_ender:float = agg_config['missing_ender_player_health_min_delta']
    frame_buffer_no_health_post_ender:int = agg_config['no_health_after_ender_buffer']
    health_min_delta_no_health_post_ender:float = agg_config['no_health_after_ender_delta']
    
    if 'Missing Ender' not in round_df.loc[0, 'inconclusive_note']:
        end_slice_index:int = end_index + frame_buffer_legit_ender
        if end_slice_index > last_index:
            end_slice_index = last_index
            
        ggst_data_slice_df = ggst_vid_data_df.loc[(end_index - 2):end_slice_index, ]
        winner_by_health, confidence = _parse_health_data_for_winner(ggst_data_slice_df, 
                                                                     health_min_delta)
        if winner_by_health != 'Unknown':
            return winner_by_health, confidence
        else:
            slice_start_index:int = end_index - frame_buffer_no_health_post_ender
            ggst_data_slice_df = ggst_vid_data_df.loc[slice_start_index:
                                                  (end_index - 1), ]
            return _no_health_post_ender_health_check(ggst_data_slice_df, 
                                                      health_min_delta_no_health_post_ender)
    else:
        slice_start_index:int = end_index - frame_buffer_missing_ender
        if slice_start_index < start_index:
            slice_start_index = start_index
        ggst_data_slice_df = ggst_vid_data_df.loc[slice_start_index:
                                                  (end_index - 1), ]
        return _no_ender_health_check(ggst_data_slice_df, health_min_delta_no_ender)

def _no_health_post_ender_health_check(ggst_health_slice_df, 
                                       min_delta:float)->tuple[str,str]:
    """When an ender for the round exists, but there isn't enough conclusive 
    health data after the ender, health is checked pre-ender for each raw data 
    frame from the ender for a frame/row w/ a decisive winner outcome.
    -------------------------------------------------------------------------
    -=ggst_health_slice_df=- DataFrame w/ extracted raw video data, rows 
      encompass a buffer value of frames before the end of ender to the end of
      the ender.
    -=min_delta=- Config value. Minimum value between P1/P2 low health values 
      to declare a winner in that case.
    -------------------------------------------------------------------------
    [-return-] A tuple of strings, the winner ('Player 1', 'Player 2', 
     'Unknown') & confidence (None, 'Very Low', 'Low', 'Medium', 'High')"""
    #Dataframe slice index in reverse order as list
    index_ls = list(ggst_health_slice_df.sort_index(ascending=False).index)
    index_size:int = len(index_ls)
    index:int = 0
    winner:str = 'Unknown'
    confidence:str = None
    while (index < index_size) and (winner == 'Unknown'):
        df_index:int = index_ls[index]
        data_row_df = ggst_health_slice_df.loc[df_index:df_index,]
        winner, confidence = _pre_ender_extra_health_check(data_row_df, 
                                                           min_delta)
        index = index + 1
    return winner, confidence

def _no_ender_health_check(ggst_health_slice_df, min_delta:float)->tuple[str,str]:
    """When there's no ender for the round, does similiar checks to post & pre 
    ender health winner processing, but w/ buffer values specific for no enders.
    -------------------------------------------------------------------------
    -=ggst_health_slice_df=- DataFrame w/ extracted raw video data, rows 
      encompass a buffer value of frames before the round end estimate to the 
      end of the round end estimate.
    -=min_delta=- Config value. Minimum value between P1/P2 low health values 
      to declare a winner in that case.
    -------------------------------------------------------------------------
    [-return-] A tuple of strings, the winner ('Player 1', 'Player 2', 
     'Unknown') & confidence (None, 'Very Low', 'Low', 'Medium', 'High')"""
    #dataframe slice index in reverse order as list
    index_ls = list(ggst_health_slice_df.sort_index(ascending=False).index)
    index_size:int = len(index_ls)
    index:int = 0
    winner:str = 'Unknown'
    confidence:str = None
    while (index < index_size) and (winner == 'Unknown'):
        df_index:int = index_ls[index]
        data_row_df = ggst_health_slice_df.loc[df_index:df_index,]
        winner, confidence = _parse_health_data_for_winner(data_row_df, 
                                                           min_delta)
        if winner == 'Unknown':
            winner, confidence = _pre_ender_extra_health_check(data_row_df, 
                                                               min_delta)
        index = index + 1
    return winner, confidence

def _pre_ender_extra_health_check(ggst_slice_df, min_delta:float)->tuple[str,str]:
    """Checking health health data pre-ender for each raw data frame from the 
    ender for a frame/row w/ a decisive winner outcome.
    -------------------------------------------------------------------------
    -=ggst_slice_df=- DataFrame w/ a single row/frame of extracted raw video 
      data.
    -=min_delta=- Config value. Minimum value between P1/P2 low health values 
      to declare a winner in that case.
    -------------------------------------------------------------------------
    [-return-] A tuple of strings, the winner ('Player 1', 'Player 2', 
     'Unknown') & confidence (None, 'Very Low', 'Low', 'Medium', 'High')"""
    ggst_health_slice_df = ggst_slice_df.copy().reset_index()
    Player_1_high:int = ggst_health_slice_df.loc[0, '1P_High_Health']
    Player_1_low:int = ggst_health_slice_df.loc[0, '1P_Low_Health']
    Player_2_high:int = ggst_health_slice_df.loc[0, '2P_High_Health']
    Player_2_low:int = ggst_health_slice_df.loc[0, '2P_Low_Health']
    is_UI_displayed:bool = (ggst_health_slice_df.loc[0, 'Game_UI_Timer_Outline'] 
                            > 0)
    confidence:str = None
    
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
        elif abs(Player_1_low - Player_2_low) < min_delta:
            return 'Unknown', confidence
        elif Player_1_low > Player_2_low:
            return 'Player 1', confidence
        else:
            return 'Player 2', confidence
    else:
        return 'Unknown', confidence

def _parse_health_data_for_winner(ggst_slice_df, min_delta:float)->tuple[str,str]:
    """Used to check health post-ender. Health value columns are summed for all 
    the rows in ggst_slice_df to see if a conclusive winner can be deduced.
    -------------------------------------------------------------------------
    -=ggst_slice_df=- DataFrame w/ extracted raw video data, slice from 2 
      frames before end of ender to a buffer value of frames after ender.
    -=min_delta=- Config value specific to post ender case. Minimum value 
      between P1/P2 low health values to declare a winner in that case.
    -------------------------------------------------------------------------
    [-return-] A tuple of strings, the winner ('Player 1', 'Player 2', 
     'Unknown') & confidence (None, 'Very Low', 'Low', 'Medium', 'High')"""
    ggst_rows_w_ui_df = ggst_slice_df.loc[(ggst_slice_df.Game_UI_Timer_Outline 
                                           > 0)]
    confidence:str = None
    ggst_rows_w_ui_df = ggst_rows_w_ui_df.loc[((ggst_rows_w_ui_df['1P_High_Health']
                                                == 0) |
                                               (ggst_rows_w_ui_df['2P_High_Health']
                                                == 0))]
    if len(ggst_rows_w_ui_df) == 0:
        return 'Unknown', confidence
    Player_1_high:int = ggst_rows_w_ui_df['1P_High_Health'].sum()
    Player_1_low:int = ggst_rows_w_ui_df['1P_Low_Health'].sum()
    Player_2_high:int = ggst_rows_w_ui_df['2P_High_Health'].sum()
    Player_2_low:int = ggst_rows_w_ui_df['2P_Low_Health'].sum()
    
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

def _check_for_player_win_template(ggst_slice_df, min_delta:float)->str:
    """Checking for Player Win template matches after round ender.
    -------------------------------------------------------------------------
    -=ggst_slice_df=- DataFrame w/ extracted raw video data, slice from end of 
      ender to a config value buffer of frames for checking player win templates.
    -=min_delta=- Config value. Minimum value between P1/P2 Win template match 
      scores, to choose the one w/ the higher score as the winner via template. 
    -------------------------------------------------------------------------
    [-return-] A string, the winner via template ('Player 1', 'Player 2', 
     'Unknown')."""
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
    
def _get_winner_by_tmpl(ggst_vid_data_df, round_input_df, agg_config:dict)->str:
    """Attempts to find the winner based on Player win template matches. These 
    aren't present too often as players can skip round/game end screens before 
    these appear (they take a few seconds to show after round/game win poses).
    -------------------------------------------------------------------------
    -=ggst_vid_data_df=- DataFrame w/ extracted raw video data.
    -=round_input_df=- DataFrame w/ a single round block.
    -=agg_config=- Config values for aggregation processing in a dict.
    -------------------------------------------------------------------------
    [-return-] A string, the winner via template ('Player 1', 'Player 2', 
     'Unknown')."""
    round_df = round_input_df.copy().reset_index()
    start_index:int = round_df.loc[0, 'start_index']
    end_index:int = round_df.loc[0, 'end_index']
    last_index = list(ggst_vid_data_df.tail(1).index)[0]
    frame_buffer_legit_ender:int = agg_config['player_win_after_ender_buffer']
    frame_buffer_missing_ender:int = agg_config['missing_ender_player_win_buffer']
    win_min_delta:float = agg_config['player_win_enders_min_delta']

    if 'Missing Ender' not in round_df.loc[0, 'inconclusive_note']:
        end_slice_index:int = end_index + frame_buffer_legit_ender
        if end_slice_index > last_index:
            end_slice_index = last_index
        ggst_data_slice_df = ggst_vid_data_df.loc[(end_index + 1):
                                                  end_slice_index, ]
        return _check_for_player_win_template(ggst_data_slice_df, win_min_delta)
    else:
        slice_start_index:int = end_index - frame_buffer_missing_ender
        if slice_start_index < start_index:
            slice_start_index = start_index
        ggst_data_slice_df = ggst_vid_data_df.loc[slice_start_index:
                                                  (end_index - 1), ]        
        return _check_for_player_win_template(ggst_data_slice_df, win_min_delta)

def _get_overall_confidence(winner_via_template:str, winner_via_health:str, 
                            health_confidence:str)->str:
    """Upgrades confidence if there was a Winner via Template detected. The 
    Player win template matches are very reliable in determining round winners.
    -------------------------------------------------------------------------
    -=winner_via_template=- Either 'Player 1', 'Player 2', or 'Unknown'.
    -=winner_via_health=- Either 'Player 1', 'Player 2', or 'Unknown'.
    -=health_confidence=- Either 'Very Low', 'Low', 'Medium', 'High', or None.
    -------------------------------------------------------------------------
    [-return-] Value which is 'High', 'Very High', or the passed in value in 
     health_confidence."""
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

def _consolidate_win_data(winner_via_template:str, winner_via_health:str)->str:
    """If Template Winner was found, that's used as the overall winner, 
    otherwise value of winner_via_health is the overall winner.
    -------------------------------------------------------------------------
    -=winner_via_template=- Either 'Player 1', 'Player 2', or 'Unknown'.
    -=winner_via_health=- Either 'Player 1', 'Player 2', or 'Unknown'.
    -------------------------------------------------------------------------
    [-return-] Value which is either 'Player 1', 'Player 2', or 'Unknown'."""
    if (winner_via_template == 'Unknown') and (winner_via_health != 'Unknown'):
        return winner_via_health
    elif (winner_via_template != 'Unknown') and (winner_via_health == 'Unknown'):
        return winner_via_template
    else:
        #Covers 2 cases: both winner types 'Unknown', or both are not 'Unknown'
        return winner_via_template

def extract_round_winner(ggst_vid_data_df, rounds_input_df, agg_config:dict):
    """Attempts to deduce the outcome of each aggregated round via the health 
    data or matches on the Player win templates.
    -------------------------------------------------------------------------
    -=ggst_vid_data_df=- DataFrame w/ extracted raw video data.
    -=rounds_input_df=- DataFrame w/ all round data blocks.
    -=agg_config=- Config values for aggregation processing in a dict.
    -------------------------------------------------------------------------
    [-return-] A DataFrame w/ Round Blocks data passed in, updated for all 
     detected winner data."""
    winner_by_health:str = 'Unknown'
    winner_by_tmpl:str = 'Unknown'
    confidence:str = None
    rounds_df = rounds_input_df.copy()
    
    for index, row in rounds_df.iterrows():
        if ((rounds_df.loc[index, 'draw'] == False) or 
        (rounds_df.loc[index, 'draw'] == None)):
            if rounds_df.loc[index, 'end_secs'] != -1:
                round_df = rounds_df.loc[index:index,]
                winner_by_health, confidence = _get_winner_by_health(ggst_vid_data_df, 
                                                                     round_df, 
                                                                     agg_config)
                winner_by_tmpl = _get_winner_by_tmpl(ggst_vid_data_df, round_df, 
                                                     agg_config)
            else:
                winner_by_health = 'Unknown'
                winner_by_tmpl = 'Unknown'
                confidence = None

            rounds_df.loc[index, 'winner_via_health'] = winner_by_health
            rounds_df.loc[index, 'winner_via_tmplate_match'] = winner_by_tmpl
            rounds_df.loc[index, 'winner'] = _consolidate_win_data(winner_by_tmpl, 
                                                                   winner_by_health)
            overall_confidence:str = _get_overall_confidence(winner_by_tmpl, 
                                                             winner_by_health, 
                                                             confidence)
            rounds_df.loc[index, 'winner_confidence'] = overall_confidence
        else:
            rounds_df.loc[index, 'winner'] = 'Draw'
            
    return rounds_df

def classify_rounds_into_games(rounds_df):
    """Classifies round blocks into game & anamalous rounds.
    -------------------------------------------------------------------------
    -=rounds_input_df=- DataFrame w/ all round data blocks.
    -------------------------------------------------------------------------
    [-return-] A tuple of 2 DataFrames: game_rounds_df which are rounds 
     classified into games w/ a 'game_id' column for the game identifiers, & 
     anomally_rounds_df which are rounds that couldn't be classified into games 
     e/ an 'anomaly_id' column w/ unique anomaly identifiers."""
    game_rounds_df, anomally_rounds_df = _validate_rounds_for_games(rounds_df)
    
    if len(game_rounds_df) > 0:
        game_rounds_df = game_rounds_df.drop(['index'], axis='columns')
    if len(anomally_rounds_df) > 0:
        anomally_rounds_df = anomally_rounds_df.drop(['index'], axis='columns')
    
    return game_rounds_df, anomally_rounds_df

def _validate_rounds_for_games(rounds_input_df):
    """1st step for round classification, operates under the assumption a valid 
    game will have at least 2 rounds. It's an initial check that consecutive 
    round blocks have valid round values before proceeding to other checks.
    -------------------------------------------------------------------------
    -=rounds_input_df=- DataFrame w/ all round data blocks.
    -------------------------------------------------------------------------
    [-return-] A tuple of 2 DataFrames: game_rounds_df which are rounds 
     classified into games w/ a 'game_id' column for the game identifiers, & 
     anomally_rounds_df which are rounds that couldn't be classified into games 
     e/ an 'anomaly_id' column w/ unique anomaly identifiers."""
    rounds_df = rounds_input_df.copy().reset_index()
    total_rows:int = len(rounds_df)
    index:int = 0
    game_count:int = 1
    anomally_count:int = 1
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
                anomallies_df = _add_anomaly_round_df(rounds_df.loc[index:index,], 
                                                   anomallies_df, anomally_count)
                anomally_count = anomally_count + 1
                index = index + 1
        else:
            anomallies_df = _add_anomaly_round_df(rounds_df.loc[index:index,], 
                                                   anomallies_df, anomally_count)
            anomally_count = anomally_count + 1
            index = index + 1
    return games_df, anomallies_df

def _is_game_with_3_rounds(rounds_df, round_index:int, 
                           final_round_case:bool=False)->bool:
    """Verifies round index is the 3rd/final round of a game, where a player 
    wins 2 rounds. Doesn't address the case where there's an Unknown winner in 
    one of a game's rounds.
    -------------------------------------------------------------------------
    -=rounds_df=- DataFrame w/ all round data blocks.
    -=round_index=- Index value of what's being checked as the 3rd/4th round 
      of a game being classified.'
    -=final_round_case=- Whether conditions indicate a game might have 4 rounds. 
      In the rare case that a "Final" round is a part of a 3 round game (where 
      first 2 rounds are Draws), this value is passed in as False.
    -------------------------------------------------------------------------
    [-return-] A boolean denoting if an undisputed winner could be determined 
     under the assumption the game is comprised of 3-4 rounds."""
    #The game will be at least 2 rounds which is insured before the function call
    last_round_index = round_index
    first_round = round_index - 2
    if final_round_case:
        first_round = round_index - 3
    
    first_3_rounds_df = rounds_df.loc[first_round:last_round_index,]
    player_winner = _game_won_by(first_3_rounds_df, 2)
    if ((player_winner == 'Player 1') or (player_winner == 'Player 2')):
        return True
    else:
        return False

def _is_round_gap_same_game(rounds_df, round_2_index:int)->bool:
    """When the potential 3rd round is Unknown, this is a check if the time gap 
    between round 2 & 3 isn't above the max gap (hard coded to 25 secs atm), 
    which makes it more likely it's a part of the same game.
    -------------------------------------------------------------------------
    -=rounds_df=- DataFrame w/ all round data blocks.
    -=round_2_index=- Index value of what's being checked as the 2nd round of a 
    game being classified.'
    -------------------------------------------------------------------------
    [-return-] Boolean value whether the gap between the end of round 2 & start 
     of the potential round 3 is less than the hard coded max gap value."""
    max_gap_secs:int = 25
    round_unknown_gap:int = (rounds_df.loc[round_2_index + 1, 'start_secs'] - 
                             rounds_df.loc[round_2_index, 'end_secs'])
    return (round_unknown_gap < max_gap_secs)

def _get_last_game_round_index(rounds_df, round_1_index:int)->int:
    """Attempts to find the last round of a game, returning its index.
    -------------------------------------------------------------------------
    -=rounds_df=- DataFrame w/ all round data blocks.
    -=round_1_index=- Index value of the 1st round of a game being classified.
    -------------------------------------------------------------------------
    [-return-] Index of the round block found to likely be the last round of 
     the same game the passed in 1st round belongs to."""
    #The game will be at least 2 rounds which is insured before the function call
    last_round_index:int = round_1_index + 1
    total_rows:int = len(rounds_df)
    first_2_rounds_df = rounds_df.loc[round_1_index:last_round_index,]
    player_winner:str = _game_won_by(first_2_rounds_df, 2)
    
    #2 round game check, based on wins where confidence higher than 'Very Low'
    if (((player_winner == 'Player 1') or (player_winner == 'Player 2')) and 
        (len(first_2_rounds_df.loc[first_2_rounds_df['winner_confidence'] 
                                   != 'Very Low']) == 2)):
        return last_round_index
    
    if (total_rows > (last_round_index + 1)):
        if rounds_df.loc[last_round_index + 1, 'round'] == 'Round_1':
            return last_round_index
        elif rounds_df.loc[last_round_index + 1, 'round'] == 'Round_Final':
            last_round_index = last_round_index + 1
            return last_round_index
        elif rounds_df.loc[last_round_index + 1, 'round'] == 'Round_3':
            last_round_index = last_round_index + 1
            #Check if there's a Duel Final (4th round) 
            if (total_rows > (last_round_index + 1)):
                if rounds_df.loc[last_round_index + 1, 'round'] == 'Round_1':
                    return last_round_index
                elif rounds_df.loc[last_round_index + 1, 'round'] == 'Round_Final':
                    last_round_index = last_round_index + 1
                    return last_round_index
                else:
                    #'Unknown' round case, may need to add more conditions later
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
            #'Unknown' round case, may need to add more conditions later
            return last_round_index
    else:
        return last_round_index
            
def _game_won_by(rounds_df, rounds_to_win:int)->str:
    """Based on rounds submitted, returns the player which won enough rounds to
    be considered the winner of the game.
    -------------------------------------------------------------------------
    -=rounds_df=- DataFrame w/ round data blocks, predicted to be the same game.
    -=rounds_to_win=- Number of rounds won to consider the game won by a player.
    -------------------------------------------------------------------------
    [-return-] The game winner 'Player 1'/'Player 2', or None if a game winner 
     couldn't be determined based on the given data & game winner condition."""
    player_1_wins = len(rounds_df.loc[rounds_df.winner == 'Player 1'])
    player_2_wins = len(rounds_df.loc[rounds_df.winner == 'Player 2'])
    if player_1_wins == rounds_to_win:
        return 'Player 1'
    elif player_2_wins == rounds_to_win:
        return 'Player 2'
    else:
        return None

def _add_anomaly_round_df(anomaly_round_input_df, anomaly_collection_df, 
                          anomaly_num:int):
    """Adds an anomalous round w/ 'anomaly_id' to the anomaly_collection_df.
    -------------------------------------------------------------------------
    -=anomaly_round_input_df=- DataFrame w/ single round data block, which was 
      determined to be anomalous.
    -=anomaly_collection_df=- DataFrame, collecting all anomalous rounds w/ ids.
    -=anomaly_num=- Used to generate the unique 'anomaly_id' identifier.
    -------------------------------------------------------------------------
    [-return-] DataFrame anomaly_collection_df w/ the new anomalous round 
     added to it."""
    anomaly_round_df = anomaly_round_input_df.copy()
    index_ls = list(anomaly_round_df.index)
    for index in index_ls:
        if anomaly_num < 10:
            anomaly_round_df.loc[index, 'anomaly_id'] = ("Anomaly_0{}"
                                                         .format(anomaly_num))
        else:
            anomaly_round_df.loc[index, 'anomaly_id'] = ("Anomaly_{}"
                                                         .format(anomaly_num))
    return anomaly_collection_df.append(anomaly_round_df, sort=False)

def _add_game_rounds_df(game_rounds_input_df, games_collection_df, game_num:int):
    """Adds rounds classified as a part of the same game, to the 
    games_collection_df, w/ a new 'game_id' identifier.
    -------------------------------------------------------------------------
    -=game_rounds_input_df=- DataFrame w/ round data blocks, for rounds 
      determined to be a part of the same game.
    -=games_collection_df=- DataFrame, collecting all rounds which have been 
      classified into games, w/ ids.
    -=game_num=- Used to generate the unique 'game_id' identifier for rounds.
    -------------------------------------------------------------------------
    [-return-] DataFrame games_collection_df w/ the rounds belonging to a new 
     game added to it."""
    game_rounds_df = game_rounds_input_df.copy()
    index_ls = list(game_rounds_df.index)
    for index in index_ls:
        if game_num < 10:
            game_rounds_df.loc[index, 'game_id'] = "Game_0{}".format(game_num)
        else:
            game_rounds_df.loc[index, 'game_id'] = "Game_{}".format(game_num)
    return games_collection_df.append(game_rounds_df, sort=False)

def aggregate_into_games(game_rounds_df, anomalous_rounds_df):
    """For rounds classified as games, aggregates start/end, winner & character 
    data to the game level. Also ouputs anomalous rounds & inconclusive data 
    flags to the console during runtime.
    -------------------------------------------------------------------------
    -=game_rounds_df=- DataFrame w/ rounds classified as games.
    -=anomalous_rounds_df=- DataFrame w/ rounds classified as anomalous.
    -------------------------------------------------------------------------
    [-return-] DataFrame w/ rounds classified as games data aggregated to the 
     game level. Has the following columns: 
       'game_id':str, 'start_secs':int, 'end_secs':int, 'start_index':int, 
       'end_index':int,  'total_rounds':int, 'character_1P':str, 
       'character_2P':str, 'winner':str, 'player_1_rounds_won':int, 
       'player_2_rounds_won':int, 'inconclusive_data':bool, & 
       'inconclusive_note':str"""
    games_ls = list(set(game_rounds_df.game_id))
    game_index:int = 0
    game_level_df = pd.DataFrame({})
    
    for game in games_ls:
        single_game_rounds_df = game_rounds_df.loc[game_rounds_df.game_id == game]
        game_result:dict = _aggregate_game_result(single_game_rounds_df)
        game_char_data:dict = _aggregate_game_characters(single_game_rounds_df)
        single_game_data:dict = _create_game_data_dict(single_game_rounds_df, 
                                                       game_result, 
                                                       game_char_data)
        game_level_df = game_level_df.append(pd.DataFrame(single_game_data, 
                                                          index = [game_index]), 
                                             sort=False)
        game_index = game_index + 1
    #Output to console any detected anomalous or inconsistent results
    _print_anomalous_round_data(anomalous_rounds_df)
    _print_inconclusive_game_data(game_level_df)

    return game_level_df.sort_values('game_id')

def _aggregate_game_result(single_game_rounds_df)->dict:
    """When possible, aggregates the game winner & round score base don round 
    results.
    -------------------------------------------------------------------------
    -=single_game_rounds_df=- DataFrame w/ rounds classified as games, for a 
      single game.
    -------------------------------------------------------------------------
    [-return-] Dict w/ the game level aggregated data related to the outcome of
     the game. Has the following keys: 
        'player_1_rounds_won':int, 'player_2_rounds_won':int, 
        'winner':str (value is: 'Player 1', 'Player 2', 'Draw', or 'Unknown'), 
        'inconclusive_data':bool, & 'inconclusive_note':str"""
    rounds_df = single_game_rounds_df.reset_index()
    total_rounds = len(rounds_df)
    #If any rounds are Very Low confidence, default to last round winner
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

def _game_result_based_on_last_round_winner(single_game_rounds_df)->dict:
    """Finds a game's outcome & P1/P2 round scores based on last round's result. 
    -------------------------------------------------------------------------
    -=single_game_rounds_df=- DataFrame w/ rounds classified as games, for a 
      single game.
    -------------------------------------------------------------------------
    [-return-] Dict w/ the game level aggregated data related to the outcome of
     the game. Has the following keys: 
        'player_1_rounds_won':int, 'player_2_rounds_won':int, 
        'winner':str (value is: 'Player 1', 'Player 2', 'Draw', or 'Unknown'), 
        'inconclusive_data':bool, & 'inconclusive_note':str"""
    rounds_df = single_game_rounds_df.reset_index()
    total_rounds = len(rounds_df)
    last_round_index:int = total_rounds - 1
    if total_rounds == 2:
        p1_wins = (2 if rounds_df.loc[last_round_index, 'winner'] == 'Player 1' 
                     else 0)
        p2_wins = (2 if rounds_df.loc[last_round_index, 'winner'] == 'Player 2' 
                     else 0)
    else:
        p1_wins = (2 if rounds_df.loc[last_round_index, 'winner'] == 'Player 1' 
                     else 1)
        p2_wins = (2 if rounds_df.loc[last_round_index, 'winner'] == 'Player 2' 
                     else 1)
    winner:str = rounds_df.loc[last_round_index, 'winner']
    return {'player_1_rounds_won': p1_wins, 'player_2_rounds_won': p2_wins, 
            'winner': winner, 'inconclusive_data': True, 
            'inconclusive_note': "Unknown or very low confidence winner of a round, winner based on last round result"}

def _game_results_with_draw_or_unknown_winners(rounds_df)->dict:
    """For games w/ too many rounds with Unknown or draw outcomes, this 
    function itterates through the rounds attmepting to figure out the outcome. 
    -------------------------------------------------------------------------
    -=rounds_df=- DataFrame w/ rounds classified as games, for a single game.
    -------------------------------------------------------------------------
    [-return-] Dict w/ the game level aggregated data related to the outcome of
     the game. Has the following keys: 
        'player_1_rounds_won':int, 'player_2_rounds_won':int, 
        'winner':str (value is: 'Player 1', 'Player 2', 'Draw', or 'Unknown'), 
        'inconclusive_data':bool, & 'inconclusive_note':str"""
    inconclusive:bool = False
    inconclusive_note:str = ""
    player_1_wins:int = 0
    player_2_wins:int = 0
    winner:str = 'Unknown'
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

def _aggregate_game_characters(single_game_rounds_df)->dict:
    """Aggregates round character data to the game level, checking for 
    inconsistencies (multiple P1 or P2 characters detected in different rounds).
    -------------------------------------------------------------------------
    -=single_game_rounds_df=- DataFrame w/ rounds classified as games, for a 
      single game.
    -------------------------------------------------------------------------
    [-return-] Dict w/ the game level aggregated data related to the outcome of
     the game. Has the following keys: 
        'character_1P':str, 'character_1P':str, 'inconclusive_data':bool, & 
        'inconclusive_note':str"""
    p1_char_count:dict = {}
    p2_char_count:dict = {}
    for index, row in single_game_rounds_df.iterrows():
        p1_char:str = row.character_1P
        p2_char:str = row.character_2P
        
        if p1_char in p1_char_count:
            p1_char_count[p1_char] = p1_char_count[p1_char] + 1
        else:
            p1_char_count[p1_char] = 1
        
        if p2_char in p2_char_count:
            p2_char_count[p2_char] = p2_char_count[p2_char] + 1
        else:
            p2_char_count[p2_char] = 1
    
    p1_char_results:dict = _check_character_results(p1_char_count)
    p2_char_results:dict = _check_character_results(p2_char_count)
    is_inconclusive:bool = (p1_char_results['inconclusive_data'] or 
                            p2_char_results['inconclusive_data'])
    inconclusive_note:str = ""
    if ((p1_char_results['inconclusive_note'] != "") and 
        (p2_char_results['inconclusive_note'] != "")):
        if "in all rounds" in p1_char_results['inconclusive_note']:
            inconclusive_note = p1_char_results['inconclusive_note']
        elif "in all rounds" in p2_char_results['inconclusive_note']:
            inconclusive_note = p2_char_results['inconclusive_note']
        else:
            inconclusive_note = p1_char_results['inconclusive_note']
    elif (p1_char_results['inconclusive_note'] != ""):
        inconclusive_note = p1_char_results['inconclusive_note']
    elif (p2_char_results['inconclusive_note'] != ""):
        inconclusive_note = p2_char_results['inconclusive_note']
        
    return {'character_1P': p1_char_results['character'], 
            'character_2P': p2_char_results['character'], 
            'inconclusive_data': is_inconclusive, 
            'inconclusive_note': inconclusive_note}

def _check_character_results(char_count:dict)->dict:
    """Checks for inconsistent characters in all the rounds of a game.
    -------------------------------------------------------------------------
    -=char_count=- Dict w/ a tally of all the characters for a single player 
    in all the game's rounds. In practice it's usually a single character.
    -------------------------------------------------------------------------
    [-return-] Dict which has the following keys: 
        'character':str, 'inconclusive_data':bool, & 'inconclusive_note':str"""
    char_result_keys = list(char_count.keys())
    if len(char_result_keys) == 1:
        if char_result_keys[0] != 'Unknown':
            return {'character': char_result_keys[0], 
                    'inconclusive_data': False, 'inconclusive_note': ""}
        else:
            return {'character': char_result_keys[0], 
                    'inconclusive_data': True, 
                    'inconclusive_note': "Unknown character in all rounds"}
    else:
        max_count = max(char_count.values())
        max_char:list = []

        for char, count in char_count.items():
            if count == max_count:
                max_char.append(char)
        
        if len(max_char) == 1:
            return {'character': max_char[0], 
                    'inconclusive_data': True, 
                    'inconclusive_note': "Unknown or multiple characters in some rounds"}
        else:
            return {'character': 'Unknown', 
                    'inconclusive_data': True, 
                    'inconclusive_note': "Unknown or multiple characters in some rounds"}

def _create_game_data_dict(single_game_rounds_df, game_result:dict, 
                           game_chars:dict)->dict:
    """Creates the dictionary which is the game level data structure. Also will 
    combine game level inconsistency notes & make a note of round level 
    inconsistencies when there were no game level inconsistency flags.
    -------------------------------------------------------------------------
    -=single_game_rounds_df=- DataFrame w/ rounds classified as games, for a 
      single game.
    -=game_result=- Output from game level result aggregagtion.
    -=game_chars=- Output from game level character aggregation.
    -------------------------------------------------------------------------
    [-return-] Dict w/ game level aggregation of game rounds' results & 
     characters. Has the following keys: 
       'game_id':str, 'start_secs':int, 'end_secs':int, 'start_index':int, 
       'end_index':int,  'total_rounds':int, 'character_1P':str, 
       'character_2P':str, 'winner':str, 'player_1_rounds_won':int, 
       'player_2_rounds_won':int, 'inconclusive_data':bool, & 
       'inconclusive_note':str"""
    games_df = single_game_rounds_df.copy().reset_index()
    last_index:int = len(games_df) - 1
    is_inconclusive:bool = (game_result['inconclusive_data'] or 
                            game_chars['inconclusive_data'])
    inconclusive_note:str = ""
    if (game_result['inconclusive_data'] and 
        game_chars['inconclusive_data']):
        inconclusive_note = "{}, and {}".format(game_result['inconclusive_note'], 
                                                game_chars['inconclusive_note'])
    elif game_result['inconclusive_data']:
        inconclusive_note = game_result['inconclusive_note']
    elif game_chars['inconclusive_data']:
        inconclusive_note = game_chars['inconclusive_note']
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
            'character_1P': game_chars['character_1P'], 
            'character_2P': game_chars['character_2P'], 
            'winner': game_result['winner'], 
            'player_1_rounds_won': game_result['player_1_rounds_won'], 
            'player_2_rounds_won': game_result['player_2_rounds_won'], 
            'inconclusive_data': is_inconclusive, 
            'inconclusive_note': inconclusive_note}

def _print_anomalous_round_data(anomalous_rounds_df):
    """Outputs to runtime console each row in anomalous_rounds_df, in a 
    readable format.
    -------------------------------------------------------------------------
    -=anomalous_rounds_df=- DataFrame w/ rounds classified as anomalous."""
    if len(anomalous_rounds_df) > 0:
        
        for index, row in anomalous_rounds_df.iterrows():
            a_id = row.anomaly_id
            time_str = "[time] start: {}secs, end: {}secs".format(row.start_secs, 
                                                                  row.end_secs)
            index_str = "[index] start: {}, end: {}".format(row.start_index, 
                                                            row.end_index)
            inconclusive_notes = "[notes] {}".format(row.inconclusive_note)
            print("id: {} | {} | {} | {}".format(a_id, time_str, index_str, 
                                                 inconclusive_notes))
    else:
        print("--No anomalous rounds--")

def _print_inconclusive_game_data(games_df):
    """Outputs to runtime console each row in games_df, w/ an inconclusive note 
    in a readable format.
    -------------------------------------------------------------------------
    -=games_df=- DataFrame w/ fully aggregated game data."""
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

#Applies the scaling values based on FPS to the aggregate config values
def convert_agg_config_vals_based_on_fps(agg_config:dict, vals_to_multiply:list, 
                                         vals_to_add_1:list, 
                                         capture_fps:int)->dict:
    """Scales the config values for aggregation based on the frames per second 
    the video is being processed at. Original config values are based on the 
    default processing FPS which is 4.
    -------------------------------------------------------------------------
    -=agg_config=- Config values based on the default FPS. Stored in config 
      file.
    -=vals_to_multiply=- Config values, which are the keys in agg_config which 
      should have scaling applied. Stored in config file.
    -=vals_to_add_1=- Config values, which are the keys in agg_config which 
      should have the value of 1 added after scaling. Stored in config file.
    -=capture_fps=- Frames per second the video will be processed.
    -------------------------------------------------------------------------
    [-return-] Values of agg_config w/ scaling/transformation applied, to be 
     used for video processing at the given FPS."""
    agg_config_new_vals:dict = agg_config.copy()
    #config values based on 4FPS, calculating the scale based on the FPS processed
    default_fps = 4
    fps_scaling = capture_fps / default_fps

    for key in agg_config_new_vals.keys():
        if key in vals_to_multiply:
            agg_config_new_vals[key] = int(agg_config_new_vals[key] * fps_scaling)
        if key in vals_to_add_1:
            agg_config_new_vals[key] = agg_config_new_vals[key] + 1
    
    return agg_config_new_vals