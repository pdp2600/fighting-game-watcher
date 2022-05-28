# -*- coding: utf-8 -*-
"""
Created on Sun May  8 11:02:20 2022

Module for functions using the data results after aggregation to create output 
files.

@author: PDP2600
"""
import os
import pandas as pd
from datetime import datetime
import json
import urllib.parse

def get_video_duration(ggst_vid_data_df)->int:
    """Finds length of video based on last row of the raw extracted data.
    -------------------------------------------------------------------------
    -=ggst_vid_data_df=- DataFrame w/ extracted raw video data.
    -------------------------------------------------------------------------
    [-return-] 'Time_in_Secs' value in the last row of the DataFrame."""
    last_frame_index = list(ggst_vid_data_df.index)[-1]
    return ggst_vid_data_df.loc[last_frame_index, 'Time_in_Secs']

def create_csv_output_files(vid_data_df, games_df, game_rounds_df, 
                            anomalous_df, vid_name:str='GGST_video', 
                            create_json:bool = False, orignal_vid:str = "", 
                            yt_link:str = "")->str:
    """Creates CSV & JSON files, based on the extracted & aggregated results.
    -------------------------------------------------------------------------
    -=vid_data_df=- DataFrame w/ extracted raw video data.
    -=games_df=- DataFrame w/ aggregated game data.
    -=game_rounds_df=- DataFrame w/ aggregated round data, classified as games.
    -=anomalous_df=- DataFrame w/ rounds classified as anomalous.
    -=vid_name=- Video name label, to be used in output folder & file names.
    -=create_json=- Boolean whether a JSON file should also be created.
    -=original_vid=- Processed videos's filename to be used in JSON meta data.
    -=yt_link=- YouTube link to video (if that's the source) for JSON meta data.
    -------------------------------------------------------------------------
    [-return-] Created output folder path which the files reside in. CSVs 
     created based on: Raw extracted match data, data aggregated to game level, 
     data aggregated to round level, anomalous rounds (if there are any 
     anomalies found in aggregation), & JSON file combining game/round 
     aggregated data (if create_json == True)."""
    dt = datetime.now()
    timestamp = "{}-{}-{}_{}-{}-{}".format(dt.year, dt.month, dt.day, dt.hour, 
                                            dt.minute, dt.second)
    new_dir:str = "{}_{}".format(timestamp, vid_name)
    cur_dir:str = os.getcwd()
    output_dir:str = "{}\\output\\{}".format(cur_dir, new_dir)
    os.makedirs(output_dir)
    vid_data_df.to_csv("{}\\Visual_detection_data_{}_{}.csv"
                       .format(output_dir, vid_name, timestamp))
    games_df.to_csv("{}\\Game_data_{}_{}.csv"
                    .format(output_dir, vid_name, timestamp), 
                    index=False)
    game_rounds_df.to_csv("{}\\Round_data_{}_{}.csv"
                          .format(output_dir, vid_name, timestamp), 
                          index=False)
    if len(anomalous_df) > 0:
        anomalous_df.to_csv("{}\\Anomalous_rounds_{}_{}.csv"
                            .format(output_dir, vid_name, timestamp), 
                            index=False)
    if create_json:
        create_json_file(games_df, game_rounds_df, output_dir, 
                         orignal_vid_file = orignal_vid, youtube_link = yt_link)
    return output_dir

def create_json_file(games_df, games_rounds_df, file_path:str, 
                     orignal_vid_file:str = "", youtube_link:str = "")->str:
    """Creates JSON file w/ games data & round data embeded for each game.
    -------------------------------------------------------------------------
    -=games_df=- DataFrame w/ aggregated game data.
    -=game_rounds_df=- DataFrame w/ aggregated round data, classified as games.
    -=file_path=- Path to the folder to write the JSON file to.
    -=original_vid_file=- Processed videos's filename to be used in JSON meta 
      data.
    -=youtube_link=- YouTube link to video (if that's the source) for JSON meta 
      data.
    -------------------------------------------------------------------------
    [-return-] Creates a JSON file out of the game, round, & some meta data."""
    dt = datetime.now()
    vidname_label = ("" if orignal_vid_file == "" 
                        else orignal_vid_file.split('.')[0].replace(' ', '_'))
    timestamp = "{}-{}-{}_{}-{}-{}".format(dt.year, dt.month, dt.day, dt.hour, 
                                            dt.minute, dt.second)
    file_name:str = "Games_with_round_data_{}_{}.json".format(vidname_label, 
                                                              timestamp)
    full_path:str = "{}\\{}".format(file_path, file_name)
    
    game_ids_ls = list(games_df.game_id)
    games_data_json:dict = {'original_vid_filename': orignal_vid_file,
                            'youtube_video_link': youtube_link,
                            'games': []
                            }
    if len(game_ids_ls) > 0:
        for game_id in game_ids_ls:
            game_df = games_df.loc[games_df.game_id == game_id]
            game_rounds_df = games_rounds_df.loc[games_rounds_df.game_id == game_id]
            game_dict = _create_game_dict_for_json(game_df, game_rounds_df)
            games_data_json['games'].append(game_dict)

        with open(full_path, 'w') as f:
            json.dump(games_data_json, f)
        f.close()
        return full_path
    else:
        print("--No games in games dataframe, no JSON file created--")
        return ""

def _create_game_dict_for_json(game_input_df, game_rounds_df)->dict:
    """Creates a dict for a single game w/ game & the game's round data, which 
    will be put into a list of games, then converted into a JSON structure.
    -------------------------------------------------------------------------
    -=game_input_df=- DataFrame w/ aggregated game data for a single game.
    -=game_rounds_df=- DataFrame w/ aggregated round data, for a single game.
    -------------------------------------------------------------------------
    [-return-] Creates a dict for a single game w/ its round data nested."""
    game_df = game_input_df.copy().reset_index()
    rounds:list = []
    for index, row in game_rounds_df.iterrows():
        round_dict = {'round': game_rounds_df.loc[index, 'round'], 
                      'start_secs': int(row.start_secs), 
                      'end_secs': int(row.end_secs), 
                      'start_index': int(row.start_index), 
                      'end_index': int(row.end_index), 
                      'character_1P': str(row.character_1P), 
                      'character_2P': str(row.character_2P), 
                      'winner': str(row.winner), 
                      'winner_confidence': str(row.winner_confidence), 
                      'winner_via_health': str(row.winner_via_health), 
                      'winner_via_tmplate_match': str(row.winner_via_tmplate_match), 
                      'perfect': bool(row.perfect), 'double_ko': bool(row.double_ko), 
                      'time_out': bool(row.time_out), 'draw': bool(row.draw), 
                      'inconclusive_data': bool(row.inconclusive_data), 
                      'inconclusive_note': str(row.inconclusive_note)
                      }
        rounds.append(round_dict)

    return {'id': game_df.loc[0, 'game_id'], 
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

def _create_anomaly_bookmark_dict(anomalies_df, df_index:int)->dict:
    """Creating a dict, used in creating custom bookmarks for VLC playlist.
    -------------------------------------------------------------------------
    -=anomalies_df=- DataFrame w/ aggregated rounds which are anomalous.
    -=df_index=- Index of row in anomalies_df to create the dict for.
    -------------------------------------------------------------------------
    [-return-] A dict w/ data from a single anomalous round."""
    return {'id': str(anomalies_df.loc[df_index, 'anomaly_id']), 
            'time': int(anomalies_df.loc[df_index, 'start_secs']), 
            'round': str(anomalies_df.loc[df_index, 'round']), 
            'character_1P': str(anomalies_df.loc[df_index, 'character_1P']), 
            'character_2P': str(anomalies_df.loc[df_index, 'character_2P'])
            }

def _create_game_round_bookmark_dict(rounds_or_games_df, df_index:int)->dict:
    """Creating a dict, used in creating custom bookmarks for VLC playlist.
    -------------------------------------------------------------------------
    -=rounds_or_games_df=- DataFrame which contains either round aggregated 
      data or game aggregated data (depends on type of VLC playlist).
    -=df_index=- Index of row in rounds_or_games_df to create the dict for.
    -------------------------------------------------------------------------
    [-return-] A dict w/ data from a single anomalous round."""
    round_bm:dict = {'id': str(rounds_or_games_df.loc[df_index, 'game_id']), 
                     'time': int(rounds_or_games_df.loc[df_index, 'start_secs']), 
                     'character_1P': str(rounds_or_games_df.loc[df_index, 
                                                                'character_1P']), 
                     'character_2P': str(rounds_or_games_df.loc[df_index, 
                                                                'character_2P'])
                     }
    #Different round value key name depending if the df is rounds or games
    if ('round' in list(rounds_or_games_df.columns)):
        round_bm['round'] = str(rounds_or_games_df.loc[df_index, 'round'])
    else:
        round_bm['round'] = str(rounds_or_games_df.loc[df_index, 'total_rounds'])
    
    return round_bm

def _create_bookmark_df(rounds_or_games_df, anomalous_df=pd.DataFrame({})):
    """Creating a DataFrame w/ all custom bookmarks for a VLC playlist or 
    bookmarks for YouTube chapters, which contains bookmarks based on 
    rounds/games data and/or anomalous data.
    -------------------------------------------------------------------------
    -=rounds_or_games_df=- DataFrame which contains either round aggregated 
      data or game aggregated data (depends on type of VLC playlist).
    -=anomalies_df=- DataFrame w/ aggregated rounds which are anomalous, 
      optional as not all extracted & aggregated results have anomalies.
    -------------------------------------------------------------------------
    [-return-] A DataFrame, which transformed the data into bookmarks to be 
     used for VLC playlists or YouTube chapters."""
    index_num:int = 0
    vid_bookmarks_df = pd.DataFrame({})

    if len(anomalous_df) > 0:
        anomalies_df = anomalous_df.loc[anomalous_df.start_secs != -1]
        if len(anomalies_df) > 0:
            for index, row in anomalies_df.iterrows():
                round_bookmark:dict = _create_anomaly_bookmark_dict(anomalies_df, 
                                                                    index)
                vid_bookmarks_df = vid_bookmarks_df.append(pd.DataFrame(round_bookmark, 
                                                                        index=
                                                                        [index_num]), 
                                                           sort=False)
                index_num = index_num + 1

    for index, row in rounds_or_games_df.iterrows():
        round_bookmark:dict = _create_game_round_bookmark_dict(rounds_or_games_df, 
                                                               index)        
        vid_bookmarks_df = vid_bookmarks_df.append(pd.DataFrame(round_bookmark, 
                                                                index=[index_num]), 
                                                   sort=False)
        index_num = index_num + 1

    vid_bookmarks_df = vid_bookmarks_df.sort_values('time')
    vid_bookmarks_df = vid_bookmarks_df.reset_index()
    vid_bookmarks_df = vid_bookmarks_df.drop(['index'], axis = 'columns')
    
    return vid_bookmarks_df

def _create_bookmark_name(single_bookmark_df)-> str:
    """Creates a bookmark name based on data for a single bookmark.
    -------------------------------------------------------------------------
    -=single_bookmark_df=- DataFrame w/ data for a single bookmark/row.
    -------------------------------------------------------------------------
    [-return-] Name to use to label the bookmark in the VLC playlist."""
    bookmark_df = single_bookmark_df.reset_index()
    round_str:str = ""
    char_info:str = ""
    individual_rounds:list = ['Round_1', 'Round_2', 'Round_3', 'Round_Final', 
                              'Unknown']
    if bookmark_df.loc[0,'round'] in individual_rounds:
        if bookmark_df.loc[0,'round'] != 'Unknown':
            round_str = ("Round - {}".format(bookmark_df.loc[0,'round']
                                             .split('_')[-1]))
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

def _create_vlc_option_tag_data(bookmarks_df)-> str:
    """Creates an XML excerpt for the option tag in a VLC playlist, w/ each row 
    of bookmarks_df represented in the resulting text.
    -------------------------------------------------------------------------
    -=bookmarks_df=- DataFrame w/ data for all the bookmarks for a VLC playlist.
    -------------------------------------------------------------------------
    [-return-] Text which contains the option XML tag for a VLC playlist, & has 
     all the bookmark data listed within the tag, in the valid syntax."""
    bookmark_num:int = 0
    last_index = list(bookmarks_df.index)[-1]
    bookmarks_data:str = "\t\t\t\t<vlc:option>bookmarks="
    
    for index, row in bookmarks_df.iterrows():
        name = _create_bookmark_name(bookmarks_df.loc[index:index,])
        bookmark_str = "{{name={} #{},time={}}}".format(name, bookmark_num, 
                                                        bookmarks_df.loc[index, 
                                                                         'time'])
        if index == last_index:
            bookmarks_data = bookmarks_data + bookmark_str + "</vlc:option>\n"
        else:
            bookmarks_data = bookmarks_data + bookmark_str + ","
            
        bookmark_num = bookmark_num + 1
    
    return bookmarks_data

def create_round_based_vlc_playlist(rounds_df, vid_data_df, video_fullpath:str, 
                                    output_folder:str, 
                                    anomalies_df=pd.DataFrame({}))-> str:
    """Creates VLC Playlist w/ custom bookmarks based on round data & anomalies. 
    Help page on VLC video playlist custom bookmarks: 
        https://www.vlchelp.com/using-custom-bookmarks-vlc-media-player/
    -------------------------------------------------------------------------
    -=rounds_df=- DataFrame w/ aggregated round data, classified as games.
    -=vid_data_df=- DataFrame w/ extracted raw video data.
    -=video_fullpath=- Fullpath to video file. Fullpath is required for VLC 
      playlists to play the video, otherwise errors will occur.
    -=output_folder=- Path of the folder to create the playlist in.
    -=anomalies_df=- DataFrame w/ aggregated rounds which are anomalous, 
      optional as not all extracted & aggregated results have anomalies.
    -------------------------------------------------------------------------
    [-return-] Filepath of the VLC Playlist created."""
    html_beginning:str = """<?xml version="1.0" encoding="UTF-8"?>\n<playlist xmlns="http://xspf.org/ns/0/" xmlns:vlc="http://www.videolan.org/vlc/playlist/ns/0/" version="1">\n"""
    html_end:str = """\t<extension application="http://www.videolan.org/vlc/playlist/0">\n\t\t<vlc:item tid="0"/>\n\t</extension>\n</playlist>"""
    path_converted:str = video_fullpath.replace('\\', '/')
    path_ls:list = path_converted.split('/')
    vid_name:str = path_ls[-1]
    new_file_path:str = urllib.parse.quote(video_fullpath)
    vid_label:str = vid_name.split('.')[0][0:32]
    vid_duration_in_ms = str(get_video_duration(vid_data_df) * 1000)

    bookmarks_df = _create_bookmark_df(rounds_df, anomalies_df)

    playlist_title:str = "Round based Playlist {}".format(vid_label)
    title:str = "\t<title>{}</title>\n".format(playlist_title)
    file_str:str = "file:///"
    location:str = "{}{}".format(file_str, new_file_path)
    track_tags:str = "\t<trackList>\n\t\t<track>\n"
    location_tag:str = "\t\t\t<location>{}</location>\n".format(location)
    duration_tag:str = "\t\t\t<duration>{}</duration>\n".format(vid_duration_in_ms)
    extension_tag:str = """\t\t\t<extension application="http://www.videolan.org/vlc/playlist/0">\n\t\t\t\t<vlc:id>0</vlc:id>\n"""
    vlc_option_tag:str = _create_vlc_option_tag_data(bookmarks_df)
    closing_tags:str = "\t\t\t</extension>\n\t\t</track>\n\t</trackList>\n"
    bookmark_tags:str = "{}{}{}{}{}{}{}".format(title, track_tags, location_tag, 
                                                duration_tag, extension_tag, 
                                                vlc_option_tag, closing_tags)
    playlist_xml:str = "{}{}{}".format(html_beginning, bookmark_tags, html_end)
    dt = datetime.now()
    timestamp:str = "{}-{}-{}_{}-{}-{}".format(dt.year, dt.month, dt.day, 
                                               dt.hour, dt.minute, dt.second)
    vid_label = vid_label.replace(' ', '_')
    output_file_name:str = "Round_Playlist_" + vid_label + "_" + timestamp + ".xspf"
    playlist_file = open(output_folder + "\\" + output_file_name, 'w')
    playlist_file.write(str(playlist_xml))
    playlist_file.close()
    
    return str(output_folder + output_file_name)

def create_game_based_vlc_playlist(games_df, vid_data_df, video_fullpath:str, 
                                   output_folder:str, 
                                   anomalies_df=pd.DataFrame({}))-> str:
    """Creates VLC Playlist w/ custom bookmarks based on game data & anomalies. 
    Help page on VLC video playlist custom bookmarks: 
        https://www.vlchelp.com/using-custom-bookmarks-vlc-media-player/
    -------------------------------------------------------------------------
    -=games_df=- DataFrame w/ aggregated game data.
    -=vid_data_df=- DataFrame w/ extracted raw video data.
    -=video_fullpath=- Fullpath to video file. Fullpath is required for VLC 
      playlists to play the video, otherwise errors will occur.
    -=output_folder=- Path of the folder to create the playlist in.
    -=anomalies_df=- DataFrame w/ aggregated rounds which are anomalous, 
      optional as not all extracted & aggregated results have anomalies.
    -------------------------------------------------------------------------
    [-return-] Filepath of the VLC Playlist created."""
    html_beginning:str = """<?xml version="1.0" encoding="UTF-8"?>\n<playlist xmlns="http://xspf.org/ns/0/" xmlns:vlc="http://www.videolan.org/vlc/playlist/ns/0/" version="1">\n"""
    html_end:str = """\t<extension application="http://www.videolan.org/vlc/playlist/0">\n\t\t<vlc:item tid="0"/>\n\t</extension>\n</playlist>"""
    path_converted:str = video_fullpath.replace('\\', '/')
    path_ls:list = path_converted.split('/')
    vid_name:str = path_ls[-1]
    new_file_path:str = urllib.parse.quote(video_fullpath)
    vid_label:str = vid_name.split('.')[0][0:32]
    vid_duration_in_ms = str(get_video_duration(vid_data_df) * 1000)

    bookmarks_df = _create_bookmark_df(games_df, anomalies_df)

    playlist_title:str = "Game based Playlist {}".format(vid_label)
    title:str = "\t<title>{}</title>\n".format(playlist_title)
    file_str:str = "file:///"
    location:str = "{}{}".format(file_str, new_file_path)
    track_tags:str = "\t<trackList>\n\t\t<track>\n"
    location_tag:str = "\t\t\t<location>{}</location>\n".format(location)
    duration_tag:str = "\t\t\t<duration>{}</duration>\n".format(vid_duration_in_ms)
    extension_tag:str = """\t\t\t<extension application="http://www.videolan.org/vlc/playlist/0">\n\t\t\t\t<vlc:id>0</vlc:id>\n"""
    vlc_option_tag:str = _create_vlc_option_tag_data(bookmarks_df)
    closing_tags:str = "\t\t\t</extension>\n\t\t</track>\n\t</trackList>\n"
    bookmark_tags:str = "{}{}{}{}{}{}{}".format(title, track_tags, location_tag, 
                                                duration_tag, extension_tag, 
                                                vlc_option_tag, closing_tags)
    playlist_xml:str = "{}{}{}".format(html_beginning, bookmark_tags, html_end)
    dt = datetime.now()
    timestamp:str = "{}-{}-{}_{}-{}-{}".format(dt.year, dt.month, dt.day, 
                                               dt.hour, dt.minute, dt.second)
    vid_label = vid_label.replace(' ', '_')
    output_file_name:str = "Game_Playlist_" + vid_label + "_" + timestamp + ".xspf"
    playlist_file = open(output_folder + "\\" + output_file_name, 'w')
    playlist_file.write(str(playlist_xml))
    playlist_file.close()
    
    return str(output_folder + output_file_name)

def _create_chapter_label(single_bookmark_df, prepend_id:bool=False, 
                          include_round_data:bool=False)-> str:
    """Creates label for a YouTube chapter based on data from a single bookmark.
    -------------------------------------------------------------------------
    -=single_bookmark_df=- DataFrame w/ data for a single bookmark/row.
    -=prepend_id=- Boolean whether the id (Game id/Anomaly id) is used at the 
      beginning of the generated label.
    -=include_round_data=- Boolean whether round data should be included in the 
      chapter label (round number for round data or total rounds for game data).
    -------------------------------------------------------------------------
    [-return-] Label the YouTube chapter represented by this bookmark."""
    bookmark_df = single_bookmark_df.reset_index()
    round_str:str = ""
    char_info:str = ""
    label:str = ""
    individual_rounds:list = ['Round_1', 'Round_2', 'Round_3', 'Round_Final', 
                              'Unknown']
    if bookmark_df.loc[0,'round'] in individual_rounds:
        if bookmark_df.loc[0,'round'] != 'Unknown':
            round_str = ("Round-{}".format(bookmark_df.loc[0,'round']
                                             .split('_')[-1]))
        else:
            round_str = "Round-Unknown"
    else:
        round_str = "Total Rounds-{}".format(bookmark_df.loc[0,'round'])
        
    if ((bookmark_df.loc[0,'character_1P'] == 'Unknown') or 
        (bookmark_df.loc[0,'character_1P'] == 'None') or 
        (bookmark_df.loc[0,'character_2P'] == 'Unknown') or 
        (bookmark_df.loc[0,'character_2P'] == 'None')):        
        
        char_info = ""
    else:
        char_info = "{} vs {}".format(bookmark_df.loc[0,'character_1P'], 
                                      bookmark_df.loc[0,'character_2P'])
    if prepend_id:
        if include_round_data:
            label = "{}-{} {}".format(bookmark_df.loc[0,'id'], round_str, 
                                     char_info)
        else:
            label = "{} {}".format(bookmark_df.loc[0,'id'], char_info)
    else:
        if include_round_data:
            label = "{} {}".format(round_str, char_info)
        else:
            label = "{}".format(char_info)
        
    return label

def _create_youtube_chapters(chapter_bookmarks_df, prepend_id:bool=False, 
                             include_round_data:bool=False)-> str:
    """Creates a set of YouTube chapters for a video based on chapter bookmarks 
    data.
    -------------------------------------------------------------------------
    -=chapter_bookmarks_df=- DataFrame w/ data all bookmarks.
    -=prepend_id=- Boolean whether the id (Game id/Anomaly id) is used at the 
      beginning of each chapter label.
    -=include_round_data=- Boolean whether round data should be included in the 
      chapter label (round number for round data or total rounds for game data).
    -------------------------------------------------------------------------
    [-return-] YouTube chapters in the txt syntax require to paste into a video 
     description or comment."""
    bookmarks_df = chapter_bookmarks_df.copy()
    chapters:str = "" 
    #If 1st game/round is 10secs or sooner, it needs to be 0:00 by YouTube rules.
    if bookmarks_df.loc[0, 'time'] > 10:
        chapters = "0:00 Lets Rock\n" 
    else:
        name:str = _create_chapter_label(bookmarks_df.loc[0:0,], 
                                         prepend_id=prepend_id, 
                                         include_round_data=include_round_data)
        chapters = "0:00 {}\n".format(name)
        bookmarks_df = bookmarks_df.loc[1:,]
    for index, row in bookmarks_df.iterrows():
        name:str = _create_chapter_label(bookmarks_df.loc[index:index,], 
                                         prepend_id=prepend_id, 
                                         include_round_data=include_round_data)
        time_min_secs:str = ""
        hours = int(bookmarks_df.loc[index, 'time'] // 3600)
        minutes:int = 0
        seconds = int(bookmarks_df.loc[index, 'time'] % 60)
        if hours > 0:
            time_min_secs = "{}:".format(str(hours))
            minutes = int((bookmarks_df.loc[index, 'time'] - (hours * 3600)) // 60)
            if minutes < 10:
                time_min_secs = "{}0{}:".format(time_min_secs, str(minutes))
            else:
                time_min_secs = "{}{}:".format(time_min_secs, str(minutes))
        else:
            minutes = int(bookmarks_df.loc[index, 'time'] // 60)
            time_min_secs:str = "{}:".format(str(minutes))
        
        if seconds < 10:
            time_min_secs = "{}0{}".format(time_min_secs, str(seconds))
        else:
            time_min_secs = "{}{}".format(time_min_secs, str(seconds))
            
        chapters += "{} {}\n".format(time_min_secs, name)
    return chapters

def create_game_based_yt_chapters(games_df, output_folder:str, 
                                  anomalies_df=pd.DataFrame({}), 
                                  vid_label:str="", prepend_id:bool=False)-> str:
    """Creates a txt file w/ YouTube chapters based on the aggregated games 
    data.
    -------------------------------------------------------------------------
    -=games_df=- DataFrame w/ aggregated game data.
    -=output_folder=- Path of the folder to create the YT chapters txt file in.
    -=anomalies_df=- DataFrame w/ aggregated rounds which are anomalous, 
      optional as not all extracted & aggregated results have anomalies.
    -=vid_label=- Optional label which will be used for generating the file 
      name. Usually video filename without the file extension.
    -=prepend_id=- Boolean whether the id (Game id/Anomaly id) is used at the 
      beginning of each chapter label.
    -------------------------------------------------------------------------
    [-return-] Filepath of the generated txt file, which contains that can be 
     copy/pasted into the description of the YouTube version of the video, for 
     chapters to become embedded in the video scrubber/seek bar."""
    vid_label:str = vid_label.replace(' ', '_')
    bookmarks_df = _create_bookmark_df(games_df, anomalies_df)    
    yt_chapters:str = _create_youtube_chapters(bookmarks_df, 
                                               prepend_id=prepend_id)
    dt = datetime.now()
    timestamp:str = "{}-{}-{}_{}-{}-{}".format(dt.year, dt.month, dt.day, 
                                               dt.hour, dt.minute, dt.second)
    output_file_name:str = ""
    if len(vid_label) > 0:
        output_file_name = ("YouTube_Game_Chapters_" + vid_label + "_" + 
                            timestamp + ".txt")
    else:
        output_file_name = "YouTube_Game_Chapters_" + timestamp + ".txt"
    playlist_file = open(output_folder + "\\" + output_file_name, 'w')
    playlist_file.write(yt_chapters)
    playlist_file.close()
    
    return str(output_folder + output_file_name)

def create_round_based_yt_chapters(rounds_df, output_folder:str, 
                                  anomalies_df=pd.DataFrame({}), 
                                  vid_label:str="", prepend_id:bool=False)-> str:
    """Creates a txt file w/ YouTube chapters based on the aggregated rounds 
    data.
    -------------------------------------------------------------------------
    -=rounds_df=- DataFrame w/ aggregated round data, classified as games.
    -=output_folder=- Path of the folder to create the YT chapters txt file in.
    -=anomalies_df=- DataFrame w/ aggregated rounds which are anomalous, 
      optional as not all extracted & aggregated results have anomalies.
    -=vid_label=- Optional label which will be used for generating the file 
      name. Usually video filename without the file extension.
    -=prepend_id=- Boolean whether the id (Game id/Anomaly id) is used at the 
      beginning of each chapter label.
    -------------------------------------------------------------------------
    [-return-] Filepath of the generated txt file, which contains that can be 
     copy/pasted into the description of the YouTube version of the video, for 
     chapters to become embedded in the video scrubber/seek bar."""
    vid_label:str = vid_label.replace(' ', '_')
    bookmarks_df = _create_bookmark_df(rounds_df, anomalies_df)    
    yt_chapters:str = _create_youtube_chapters(bookmarks_df, prepend_id=prepend_id, 
                                               include_round_data=True)
    dt = datetime.now()
    timestamp:str = "{}-{}-{}_{}-{}-{}".format(dt.year, dt.month, dt.day, 
                                               dt.hour, dt.minute, dt.second)
    output_file_name:str = ""
    if len(vid_label) > 0:
        output_file_name = ("YouTube_Round_Chapters_" + vid_label + "_" + 
                            timestamp + ".txt")
    else:
        output_file_name = "YouTube_Round_Chapters_" + timestamp + ".txt"
    playlist_file = open(output_folder + "\\" + output_file_name, 'w')
    playlist_file.write(yt_chapters)
    playlist_file.close()
    
    return str(output_folder + output_file_name)