# -*- coding: utf-8 -*-
"""
Created on Thu Aug 26 20:42:55 2021

Module to store config parameters (image path locations, match threshold 
minimums, image key to min match value mappings)

@author: PDP2600
"""
###Aggregation Config Values

###Template Matching Config Values
template_img_folder = "GGStrive_Template_imgs_v2\\"

anji_templ_imgs = {'Name': 'Anji_Mito', 
                   'Min_Portrait_Match': 0.2, 
                   'Min_Win_Pose_Match': 0.3, 
                   'img_paths': {
                               '1P_Portrait': template_img_folder + 
                                   'Characters\\Anji_Mito\\Anji_Mito_Portrait_P1.png',
                               '2P_Portrait': template_img_folder + 
                                   'Characters\\Anji_Mito\\Anji_Mito_Portrait_P2.png',
                               'Win_Pose_Left': template_img_folder + 
                                   'Characters\\Anji_Mito\\Anji_Mito_Win_Pose_Left.png', 
                               'Win_Pose_Right': template_img_folder + 
                                   'Characters\\Anji_Mito\\Anji_Mito_Win_Pose_Right.png'
                                }, 
                   'img_objs': {}
                  }
axl_templ_imgs = {'Name': 'Axl', 
                  'Min_Portrait_Match': 0.25, 
                  'Min_Win_Pose_Match': 0.3, 
                  'img_paths': {
                              '1P_Portrait': template_img_folder + 
                                  'Characters\\Axl\\Axl_Portrait_P1.png', 
                              '2P_Portrait': template_img_folder + 
                                  'Characters\\Axl\\Axl_Portrait_P2.png', 
                              'Win_Pose_Left': template_img_folder + 
                                  'Characters\\Axl\\Axl_Win_Pose_Left.png', 
                              'Win_Pose_Right': template_img_folder + 
                                  'Characters\\Axl\\Axl_Win_Pose_Right.png'
                               }, 
                   'img_objs': {}
                  }
baiken_templ_imgs =  {'Name': 'Baiken', 
					  'Min_Portrait_Match': 0.25, 'Min_Win_Pose_Match': 0.3, 
                      'img_paths': {
									'1P_Portrait': template_img_folder + 
									  'Characters\\Baiken\\Baiken_Portrait_P1.png', 
                                    '2P_Portrait': template_img_folder + 
                                      'Characters\\Baiken\\Baiken_Portrait_P2.png', 
                                    'Win_Pose_Left': template_img_folder + 
                                      'Characters\\Baiken\\Baiken_Win_Pose_Left.png', 
                                    'Win_Pose_Right': template_img_folder + 
                                      'Characters\\Baiken\\Baiken_Win_Pose_Right.png'
                                  }, 
                      'img_objs': {}
                     }
chipp_templ_imgs = {'Name': 'Chipp', 
                    'Min_Portrait_Match': 0.25, 
                    'Min_Win_Pose_Match': 0.3, 
                    'img_paths': {
                                '1P_Portrait': template_img_folder + 
                                    'Characters\\Chipp\\Chipp_Portrait_P1.png', 
                                '2P_Portrait': template_img_folder + 
                                    'Characters\\Chipp\\Chipp_Portrait_P2.png', 
                                'Win_Pose_Left': template_img_folder + 
                                    'Characters\\Chipp\\Chipp_Win_Pose_Left.png', 
                                'Win_Pose_Right': template_img_folder + 
                                    'Characters\\Chipp\\Chipp_Win_Pose_Right.png'
                                 }, 
                   'img_objs': {}
                    }
faust_templ_imgs = {'Name': 'Faust', 
                    'Min_Portrait_Match': 0.2, 
                    'Min_Win_Pose_Match': 0.3, 
                    'img_paths': {
                                '1P_Portrait': template_img_folder + 
                                    'Characters\\Faust\\Faust_Portrait_P1.png', 
                                '2P_Portrait': template_img_folder + 
                                    'Characters\\Faust\\Faust_Portrait_P2.png', 
                                'Win_Pose_Left': template_img_folder + 
                                    'Characters\\Faust\\Faust_Win_Pose_Left.png', 
                                'Win_Pose_Right': template_img_folder + 
                                    'Characters\\Faust\\Faust_Win_Pose_Right.png'
                                 }, 
                   'img_objs': {}
                    }
giovanna_templ_imgs = {'Name': 'Giovanna', 
                       'Min_Portrait_Match': 0.25, 
                       'Min_Win_Pose_Match': 0.3, 
                       'img_paths': {
                                   '1P_Portrait': template_img_folder + 
                                       'Characters\\Giovanna\\Giovanna_Portrait_P1.png', 
                                   '2P_Portrait': template_img_folder + 
                                       'Characters\\Giovanna\\Giovanna_Portrait_P2.png', 
                                   'Win_Pose_Left': template_img_folder + 
                                       'Characters\\Giovanna\\Giovanna_Win_Pose_Left.png', 
                                   'Win_Pose_Right': template_img_folder + 
                                       'Characters\\Giovanna\\Giovanna_Win_Pose_Right.png'
                                    }, 
                       'img_objs': {}
                      }
goldlewis_templ_imgs = {'Name': 'Goldlewis', 
                        'Min_Portrait_Match': 0.25, 
                        'Min_Win_Pose_Match': 0.3, 
                        'img_paths': {
                                    '1P_Portrait': template_img_folder + 
                                        'Characters\\Goldlewis\\Goldlewis_Portrait_P1.png', 
                                    '2P_Portrait': template_img_folder + 
                                        'Characters\\Goldlewis\\Goldlewis_Portrait_P2.png', 
                                    'Win_Pose_Left': template_img_folder + 
                                        'Characters\\Goldlewis\\Goldlewis_Win_Pose_Left.png', 
                                    'Win_Pose_Right': template_img_folder + 
                                        'Characters\\Goldlewis\\Goldlewis_Win_Pose_Right.png'
                                     }, 
                        'img_objs': {}
                       }
happy_templ_imgs =  {'Name': 'Happy Chaos', 
                     'Min_Portrait_Match': 0.25, 
                     'Min_Win_Pose_Match': 0.3, 
                     'img_paths': {
                                  '1P_Portrait': template_img_folder + 
                                      'Characters\\Happy_Chaos\\Happy_Chaos_Portrait_P1.png', 
                                  '2P_Portrait': template_img_folder + 
                                      'Characters\\Happy_Chaos\\Happy_Chaos_Portrait_P2.png', 
                                  'Win_Pose_Left': template_img_folder + 
                                      'Characters\\Happy_Chaos\\Happy_Chaos_Win_Pose_Left.png', 
                                  'Win_Pose_Right': template_img_folder + 
                                      'Characters\\Happy_Chaos\\Happy_Chaos_Win_Pose_Right.png'
                                  }, 
                     'img_objs': {}
                    }
ino_templ_imgs = {'Name': 'I-no', 
                  'Min_Portrait_Match': 0.25, 
                  'Min_Win_Pose_Match': 0.3, 
                  'img_paths': {
                              '1P_Portrait': template_img_folder + 
                                  'Characters\\I-no\\I-no_Portrait_P1.png', 
                              '2P_Portrait': template_img_folder + 
                                  'Characters\\I-no\\I-no_Portrait_P2.png', 
                              'Win_Pose_Left': template_img_folder + 
                                  'Characters\\I-no\\I-no_Win_Pose_Left.png', 
                              'Win_Pose_Right': template_img_folder + 
                                  'Characters\\I-no\\I-no_Win_Pose_Right.png'
                               }, 
                  'img_objs': {}
                 }
jacko_templ_imgs =  {'Name': 'Jack-O', 
                     'Min_Portrait_Match': 0.25, 
                     'Min_Win_Pose_Match': 0.3, 
                     'img_paths': {
                                  '1P_Portrait': template_img_folder + 
                                      'Characters\\Jack-O\\Jack-O_Portrait_P1.png', 
                                  '2P_Portrait': template_img_folder + 
                                      'Characters\\Jack-O\\Jack-O_Portrait_P2.png', 
                                  'Win_Pose_Left': template_img_folder + 
                                      'Characters\\Jack-O\\Jack-o_Win_Pose_Left.png', 
                                  'Win_Pose_Right': template_img_folder + 
                                      'Characters\\Jack-O\\Jack-o_Win_Pose_Right.png'
                                  }, 
                     'img_objs': {}
                    }
ky_templ_imgs = {'Name': 'Ky', 
                 'Min_Portrait_Match': 0.25, 
                 'Min_Win_Pose_Match': 0.3, 
                 'img_paths': {
                             '1P_Portrait': template_img_folder + 
                                 'Characters\\Ky\\Ky_Portrait_P1.png', 
                             '2P_Portrait': template_img_folder + 
                                 'Characters\\Ky\\Ky_Portrait_P2.png', 
                             'Win_Pose_Left': template_img_folder + 
                                 'Characters\\Ky\\Ky_Win_Pose_Left.png', 
                             'Win_Pose_Right': template_img_folder + 
                                 'Characters\\Ky\\Ky_Win_Pose_Right.png'
                              }, 
                 'img_objs': {}
                }
leo_templ_imgs = {'Name': 'Leo', 
                  'Min_Portrait_Match': 0.2, 
                  'Min_Win_Pose_Match': 0.3, 
                  'img_paths': {
                              '1P_Portrait': template_img_folder + 
                                  'Characters\\Leo\\Leo_Portrait_P1.png', 
                              '2P_Portrait': template_img_folder + 
                                  'Characters\\Leo\\Leo_Portrait_P2.png', 
                              'Win_Pose_Left': template_img_folder + 
                                  'Characters\\Leo\\Leo_Win_Pose_Left.png', 
                              'Win_Pose_Right': template_img_folder + 
                                  'Characters\\Leo\\Leo_Win_Pose_Right.png'
                               }, 
                  'img_objs': {}
                 }
may_templ_imgs = {'Name': 'May', 
                  'Min_Portrait_Match': 0.2, 
                  'Min_Win_Pose_Match': 0.3, 
                  'img_paths': {
                              '1P_Portrait': template_img_folder + 
                                  'Characters\\May\\May_Portrait_P1.png', 
                              '2P_Portrait': template_img_folder + 
                                  'Characters\\May\\May_Portrait_P2.png', 
                              'Win_Pose_Left': template_img_folder + 
                                  'Characters\\May\\May_Win_Pose_Left.png',
                              'Win_Pose_Right': template_img_folder + 
                                  'Characters\\May\\May_Win_Pose_Right.png'
                               }, 
                  'img_objs': {}
                 }
millia_templ_imgs = {'Name': 'Millia', 
                     'Min_Portrait_Match': 0.2, 
                     'Min_Win_Pose_Match': 0.25, 
                     'img_paths': {
                                 '1P_Portrait': template_img_folder + 
                                     'Characters\\Millia\\Millia_Portrait_P1.png', 
                                 '2P_Portrait': template_img_folder + 
                                     'Characters\\Millia\\Millia_Portrait_P2.png', 
                                 'Win_Pose_Left': template_img_folder + 
                                     'Characters\\Millia\\Millia_Win_Pose_Left.png', 
                                 'Win_Pose_Right': template_img_folder + 
                                     'Characters\\Millia\\Millia_Win_Pose_Right.png'
                                  }, 
                     'img_objs': {}
                    }
nago_templ_imgs = {'Name': 'Nagoriyuki', 
                   'Min_Portrait_Match': 0.2, 
                   'Min_Win_Pose_Match': 0.3, 
                   'img_paths': {
                               '1P_Portrait': template_img_folder + 
                                   'Characters\\Nagoriyuki\\Nagoriyuki_Portrait_P1.png', 
                               '2P_Portrait': template_img_folder + 
                                   'Characters\\Nagoriyuki\\Nagoriyuki_Portrait_P2.png', 
                               'Win_Pose_Left': template_img_folder + 
                                   'Characters\\Nagoriyuki\\Nagoriyuki_Win_Pose_Left.png', 
                               'Win_Pose_Right': template_img_folder + 
                                   'Characters\\Nagoriyuki\\Nagoriyuki_Win_Pose_Right.png'
                                }, 
                   'img_objs': {}
                  }
potemkin_templ_imgs = {'Name': 'Potemkin', 
                       'Min_Portrait_Match': 0.2, 
                       'Min_Win_Pose_Match': 0.3, 
                       'img_paths': {
                                   '1P_Portrait': template_img_folder + 
                                       'Characters\\Potemkin\\Potemkin_Portrait_P1.png', 
                                   '2P_Portrait': template_img_folder + 
                                       'Characters\\Potemkin\\Potemkin_Portrait_P2.png', 
                                   'Win_Pose_Left': template_img_folder + 
                                       'Characters\\Potemkin\\Potemkin_Win_Pose_Left.png', 
                                   'Win_Pose_Right': template_img_folder + 
                                       'Characters\\Potemkin\\Potemkin_Win_Pose_Right.png'
                                    }, 
                       'img_objs': {}
                      }
ramlethal_templ_imgs = {'Name': 'Ramlethal', 
                        'Min_Portrait_Match': 0.2, 
                        'Min_Win_Pose_Match': 0.3, 
                        'img_paths': {
                                    '1P_Portrait': template_img_folder + 
                                        'Characters\\Ramlethal\\Ramlethal_Portrait_P1.png', 
                                    '2P_Portrait': template_img_folder + 
                                        'Characters\\Ramlethal\\Ramlethal_Portrait_P2.png', 
                                    'Win_Pose_Left': template_img_folder + 
                                        'Characters\\Ramlethal\\Ramlethal_Win_Pose_Left.png', 
                                    'Win_Pose_Right': template_img_folder + 
                                        'Characters\\Ramlethal\\Ramlethal_Win_Pose_Right.png'
                                     }, 
                        'img_objs': {}
                       }
sol_templ_imgs = {'Name': 'Sol', 
                  'Min_Portrait_Match': 0.24, 
                  'Min_Win_Pose_Match': 0.3, 
                  'img_paths': {
                              '1P_Portrait': template_img_folder + 
                                  'Characters\\Sol\\Sol_Portrait_P1.png', 
                              '2P_Portrait': template_img_folder + 
                                  'Characters\\Sol\\Sol_Portrait_P2.png', 
                              'Win_Pose_Left': template_img_folder + 
                                  'Characters\\Sol\\Sol_Win_Pose_Left.png', 
                              'Win_Pose_Right': template_img_folder + 
                                  'Characters\\Sol\\Sol_Win_Pose_Right.png'
                               }, 
                  'img_objs': {}
                 }
zato_templ_imgs = {'Name': 'Zato', 
                   'Min_Portrait_Match': 0.2, 
                   'Min_Win_Pose_Match': 0.3, 
                   'img_paths': {
                               '1P_Portrait': template_img_folder + 
                                   'Characters\\Zato\\Zato_Portrait_P1.png', 
                               '2P_Portrait': template_img_folder + 
                                   'Characters\\Zato\\Zato_Portrait_P2.png', 
                               'Win_Pose_Left': template_img_folder + 
                                   'Characters\\Zato\\Zato_Win_Pose_Left.png', 
                               'Win_Pose_Right': template_img_folder + 
                                   'Characters\\Zato\\Zato_Win_Pose_Right.png'
                                }, 
                   'img_objs': {}
                  }
round_starter_templ_imgs = {'Name': 'Starter', 
                            'Min_Round_Match': 0.50, 
                            'Min_Number_Match': 0.24, 
                            'Min_Lets_Rock_Match': 0.6, 
                            'img_paths': {
                                        #'Round_1': template_img_folder + 
                                        #    'Round_Starters\\Duel_1.png', 
                                        #'Round_2': template_img_folder + 
                                        #    'Round_Starters\\Duel_2.png', 
                                        #'Round_3': template_img_folder + 
                                        #    'Round_Starters\\Duel_3.png', 
                                        #'Round_Final': template_img_folder + 
                                        #    'Round_Starters\\Duel_Final.png', 
                                        'Duel': template_img_folder + 
                                            'Round_Starters\\Duel_Only.png',
                                        'Number_1': template_img_folder + 
                                            'Round_Starters\\Round_1.png',
                                        'Number_2': template_img_folder + 
                                            'Round_Starters\\Round_2.png',
                                        'Number_3': template_img_folder + 
                                            'Round_Starters\\Round_3.png',
                                        'Number_Final': template_img_folder + 
                                            'Round_Starters\\Round_Final.png',
                                        'Lets_Rock': template_img_folder + 
                                            'Round_Starters\\Lets_Rock.png'
                                        }, 
                            'img_objs': {}
                           }
round_ender_templ_imgs = {'Name': 'Ender', 
                          'Min_Slash_Match': 0.5, 
                          'Min_Double_KO_Match': 0.4, 
                          'Min_Draw_Match': 0.4, 
                          'Min_Perfect_Match': 0.45,
                          'Min_Times_Up_Match': 0.45,
                          'Min_Win_Match': 0.63, 
                          'img_paths': {
                                      'Slash': template_img_folder + 
                                          'Round_Enders\\Slash.png', 
                                      'Double_KO': template_img_folder + 
                                          'Round_Enders\\Double_KO.png', 
                                      'Draw': template_img_folder + 
                                          'Round_Enders\\Draw.png', 
                                      'Perfect': template_img_folder + 
                                          'Round_Enders\\Perfect.png', 
                                      'Times_Up': template_img_folder + 
                                          'Round_Enders\\Times_Up.png', 
                                      '1P_Win': template_img_folder + 
                                          'Round_Enders\\1P_Only.png', 
                                      '2P_Win': template_img_folder + 
                                          'Round_Enders\\2P_Only.png'
                                      }, 
                          'img_objs': {}
                         }
game_ui_templ_imgs = {'Name': 'Game_UI', 
                      'Min_Round_Score_Delta': 0.01,
                      'Min_Round_Score': 0.2,
                      'img_paths': {
                                  '1P_No_Round_Lost': template_img_folder + 
                                      'Round_Score\\P1_No_round_Lost.png',
                                  '1P_Round_Lost': template_img_folder + 
                                      'Round_Score\\P1_round_Lost.png',
                                  '2P_No_Round_Lost': template_img_folder + 
                                      'Round_Score\\P2_No_round_Lost.png',
                                  '2P_Round_Lost': template_img_folder + 
                                      'Round_Score\\P2_round_Lost.png'
                                  }, 
                      'img_objs': {}
                     }

templ_img_min_val_mappings = {'1P_Portrait': 'Min_Portrait_Match', 
                              '2P_Portrait': 'Min_Portrait_Match',
                              'Win_Pose_Left': 'Min_Win_Pose_Match', 
                              'Win_Pose_Right': 'Min_Win_Pose_Match',
                              'Round_1': 'Min_Round_Match', 
                              'Round_2': 'Min_Round_Match', 
                              'Round_3': 'Min_Round_Match', 
                              'Round_Final': 'Min_Round_Match',
                              'Duel': 'Min_Round_Match',
                              'Number_1': 'Min_Number_Match', 
                              'Number_2': 'Min_Number_Match', 
                              'Number_3': 'Min_Number_Match', 
                              'Number_Final': 'Min_Number_Match',
                              'Lets_Rock': 'Min_Lets_Rock_Match',
                              'Slash': 'Min_Slash_Match',
                              'Double_KO': 'Min_Double_KO_Match',
                              'Draw': 'Min_Draw_Match',
                              'Perfect': 'Min_Perfect_Match',
                              'Times_Up': 'Min_Times_Up_Match',
                              '1P_Win': 'Min_Win_Match', 
                              '2P_Win': 'Min_Win_Match',
                              '1P_No_Round_Lost': 'Min_Round_Score', 
                              '1P_Round_Lost': 'Min_Round_Score', 
                              '2P_No_Round_Lost': 'Min_Round_Score', 
                              '2P_Round_Lost': 'Min_Round_Score'
                              }

templ_img_dicts_ls = [anji_templ_imgs, axl_templ_imgs, baiken_templ_imgs, 
					  chipp_templ_imgs, faust_templ_imgs, giovanna_templ_imgs, 
                      goldlewis_templ_imgs, happy_templ_imgs, ino_templ_imgs, 
					  jacko_templ_imgs, ky_templ_imgs, leo_templ_imgs, may_templ_imgs, 
					  millia_templ_imgs, nago_templ_imgs, potemkin_templ_imgs, 
					  ramlethal_templ_imgs, sol_templ_imgs, zato_templ_imgs, 
					  round_starter_templ_imgs, round_ender_templ_imgs, 
					  game_ui_templ_imgs
                      ]