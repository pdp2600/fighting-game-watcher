# -*- coding: utf-8 -*-
"""
Created on Thu May  5 15:10:52 2022

Fighting Game Watcher example script

@author: PDP2600
"""
import os
#Only works when this python file is run or run/imported by another python file
#wd_path = os.path.dirname(__file__)
wd_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader"
os.chdir(wd_path)
import conf.config_values as conf
import modules.ggst.controller as ctrl

#pd.set_option('display.max_rows', 2000)
#pd.set_option('display.max_columns', 500)
#pd.set_option('display.max_colwidth', None)

#video_path = "Test_Videos\\GuiltyGear-Strive_Baike-vs-Millia_2_Low_Health_for_While-2022-02-02.mp4"
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
video_path =  "Test_Videos\\GGST-My-Day_2_Testament_matches_18mins-2022-03-29 17-39-38.mp4"
#video_path =  "Test_Videos\\yt_dl\\NLBC 104 Top 8  Online  Tournament.mp4"
#video_path =  "Test_Videos\\yt_dl\\Frosty Faustings 2022 - Top 96.mp4"
#video_path =  "Test_Videos\\yt_dl\\Series E Sports Arena Week 11.mp4"
#video_path =  "Test_Videos\\yt_dl\\NLBC 106 Top 8 Online Tournament.mp4"
#video_path =  "Test_Videos\\yt_dl\\Series E S1 FINALE.mp4"

#Making the video path a fullpath (required for playlist generation)
video_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader\\{}".format(video_path)
#fps_val = 4
fps_val = 2

#output_file_path = ctrl.brute_force_extract_and_aggregate_video(video_path, fps_val, conf)
output_file_path = ctrl.layered_extract_and_aggregate_video(video_path, fps_val, 
                                                            conf, verbose_log=True)
#output_file_path = ctrl.extract_match_video_timecodes_only(video_path, fps_val, 
#                                                           conf, verbose_log=True)
#output_file_path = ctrl.timer_template_test_video(video_path, fps_val)

print("Output files located in the created folder: {}".format(output_file_path))

##Current brute force CV Extraction takes about 11 - 11.5 seconds per 1 second of video
##Layered function/approach is consistently around ~4.5 seconds per 1 second of video

#########
##Batch process a directory of videos 
#Full path to be prepended to the video folder & file name
vid_dir = 'D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader\\Test_Videos'
#videos_ls = os.listdir(vid_dir)
videos_ls = []
#videos_ls.append('GGST-My-Day_2_Testament_matches_18mins-2022-03-29 17-39-38.mp4')
#videos_ls.append('yt_dl\\Series E S1 FINALE.mp4')
#videos_ls.append('My_Baiken_Matches_90_mins_2022-03-13_16-01-57.mp4')
#videos_ls.append('yt_dl\\NLBC 103 Top 16  Online  Tournament.mp4')
#videos_ls.append('yt_dl\\NLBC 106 Top 8 Online Tournament.mp4')
#videos_ls.append('yt_dl\\NLBC 104 Top 8  Online  Tournament.mp4')
#videos_ls.append('yt_dl\\NLBC 103 Top 8  Online  Tournament.mp4')
#videos_ls.append('yt_dl\\Can Opener Vol 36 GGST.mp4')
videos_ls.append('yt_dl\\Series E Sports Arena Week 11.mp4')
videos_ls.append('yt_dl\\Frosty Faustings 2022 - Top 96.mp4')

for video in videos_ls:
    vid_path = "{}\\{}".format(vid_dir, video)
    #output_file_path = ctrl.brute_force_extract_and_aggregate_video(vid_path, fps_val, conf)
    output_file_path = ctrl.layered_extract_and_aggregate_video(vid_path, 
                                                                fps_val, conf, 
                                                                verbose_log=True)


###############################################################################

##A la Carte testing of the VLC playlist creation, it'll be included into the 
##stand alone function for just starter/ender round/game data. Might create a
##html file generator for a YT link, need to check out how chapters on posted YT
##videos work, and if that can be automated to generate
"""
import pandas as pd

vidpl_rounds_df = pd.read_csv('output\\2022-5-19_20-6-56_Can_Opener_Vol_36_GGST\\Round_data_Can_Opener_Vol_36_GGST_2022-5-19_20-6-56.csv')
vidpl_games_df = pd.read_csv('output\\2022-5-19_20-6-56_Can_Opener_Vol_36_GGST\\Game_data_Can_Opener_Vol_36_GGST_2022-5-19_20-6-56.csv')
vidpl_anomallies_df = pd.read_csv('output\\2022-5-19_20-6-56_Can_Opener_Vol_36_GGST\\Anomalous_rounds_Can_Opener_Vol_36_GGST_2022-5-19_20-6-56.csv')
vidpl_vid_data_df = pd.read_csv('output\\2022-5-19_20-6-56_Can_Opener_Vol_36_GGST\\Visual_detection_data_Can_Opener_Vol_36_GGST_2022-5-19_20-6-56.csv')
file_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader\\Test_Videos\\yt_dl\\Can Opener Vol 36 GGST.mp4"
output_folder = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader\\output\\2022-5-19_20-6-56_Can_Opener_Vol_36_GGST\\"

playlist_file = ctrl.out.create_round_based_vlc_playlist(vidpl_rounds_df, 
                                                     vidpl_vid_data_df, 
                                                     file_path, output_folder, 
                                                     vidpl_anomallies_df)
print("{}".format(playlist_file))
playlist_file = ctrl.out.create_game_based_vlc_playlist(vidpl_games_df, 
                                                    vidpl_vid_data_df, 
                                                    file_path, output_folder, 
                                                    vidpl_anomallies_df)
print("{}".format(playlist_file))
"""
###############################################################################
##A la carte test of the YouTube Chapter format txt file generation
"""
ytch_rounds_df = pd.read_csv('output\\2022-5-19_20-6-56_Can_Opener_Vol_36_GGST\\Round_data_Can_Opener_Vol_36_GGST_2022-5-19_20-6-56.csv')
ytch_games_df = pd.read_csv('output\\2022-5-19_20-6-56_Can_Opener_Vol_36_GGST\\Game_data_Can_Opener_Vol_36_GGST_2022-5-19_20-6-56.csv')
ytch_anomallies_df = pd.read_csv('output\\2022-5-19_20-6-56_Can_Opener_Vol_36_GGST\\Anomalous_rounds_Can_Opener_Vol_36_GGST_2022-5-19_20-6-56.csv')
#ytch_anomallies_df = pd.DataFrame({})
#ytch_vid_data_df = pd.read_csv('output\\2022-4-11_8-25-4_Series_E_Sports_Arena_Wee\\Visual_detection_data_Series_E_Sports_Arena_Wee_2022-4-11_8-25-4.csv')
#file_path = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader\\Test_Videos\\yt_dl\\Series E Sports Arena Week 11.mp4"
output_folder = "D:\\Libraries\\Documents\\Data_Science\\Projects\\FGC_Stream_Reader\\output\\2022-5-19_20-6-56_Can_Opener_Vol_36_GGST\\"

chapter_file = ctrl.out.create_round_based_yt_chapters(ytch_rounds_df, output_folder, 
                                                   vid_label="Baiken matches", 
                                                   prepend_id=True)
print("{}".format(chapter_file))
chapter_file = ctrl.out.create_game_based_yt_chapters(ytch_games_df, output_folder, 
                                                  vid_label="Baiken Matches", 
                                                  prepend_id=True)
print("{}".format(chapter_file))
"""
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

