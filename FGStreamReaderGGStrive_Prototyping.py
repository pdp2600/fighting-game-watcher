# -*- coding: utf-8 -*-
"""
Created on Sat May 29 18:24:43 2021

@author: PDP2600
"""
import cv2
import numpy as np
import os

wd_path = "D:\\Libraries\\Documents\\Data_Science\\\\Projects\\FGC_Stream_Reader"
os.chdir(wd_path)

anji_mito_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Anji_Mito\\Anji_Mito_Portrait_P1.png',
                           'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Anji_Mito\\Anji_Mito_Portrait_P2.png',
                           'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Anji_Mito\\Anji_Mito_Win_Pose.png',
                           'Name': 'Anji_Mito'
                           }
axl_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Axl\\Axl_Portrait_P1.png', 
                     'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Axl\\Axl_Portrait_P2.png', 
                     'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Axl\\Axl_Win_Pose.png',
                     'Name': 'Axl'
                     }
chipp_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Chipp\\Chipp_Portrait_P1.png', 
                       'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Chipp\\Chipp_Portrait_P2.png', 
                       'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Chipp\\Chipp_Win_Pose.png', 
                       'Name': 'Chipp'
                       }
faust_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Faust\\Faust_Portrait_P1.png', 
                       'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Faust\\Faust_Portrait_P2.png', 
                       'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Faust\\Faust_Win_Pose.png', 
                       'Name': 'Faust'
                       }
giovanna_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Giovanna\\Giovanna_Portrait_P1.png', 
                          'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Giovanna\\Giovanna_Portrait_P2.png', 
                          'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Giovanna\\Giovanna_Win_Pose.png', 
                          'Name': 'Giovanna'
                          }
i_no_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\I-no\\I-no_Portrait_P1.png', 
                      'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\I-no\\I-no_Portrait_P2.png', 
                      'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\I-no\\I-no_Win_Pose.png', 
                      'Name': 'I-no'
                      }
ky_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Ky\\Ky_Portrait_P1.png', 
                    'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Ky\\Ky_Portrait_P2.png', 
                    'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Ky\\Ky_Win_Pose.png', 
                    'Name': 'Ky'
                    }
leo_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Leo\\Leo_Portrait_P1.png', 
                     'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Leo\\Leo_Portrait_P2.png', 
                     'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Leo\\Leo_Win_Pose.png', 
                     'Name': 'Leo'
                     }
may_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\May\\May_Portrait_P1.png', 
                     'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\May\\May_Portrait_P2.png', 
                     'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\May\\May_Win_Pose.png', 
                     'Name': 'May'
                     }
millia_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Millia\\Millia_Portrait_P1.png', 
                        'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Millia\\Millia_Portrait_P2.png', 
                        'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Millia\\Millia_Win_Pose.png', 
                        'Name': 'Millia'
                        }
nagoriyuki_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Nagoriyuki\\Nagoriyuki_Portrait_P1.png', 
                            'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Nagoriyuki\\Nagoriyuki_Portrait_P2.png', 
                            'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Nagoriyuki\\Nagoriyuki_Win_Pose.png', 
                            'Name': 'Nagoriyuki'
                            }
potemkin_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Potemkin\\Potemkin_Portrait_P1.png', 
                          'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Potemkin\\Potemkin_Portrait_P2.png', 
                          'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Potemkin\\Potemkin_Win_Pose.png', 
                          'Name': 'Potemkin'
                          }
ramlethal_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Ramlethal\\Ramlethal_Portrait_P1.png', 
                           'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Ramlethal\\Ramlethal_Portrait_P2.png', 
                           'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Ramlethal\\Ramlethal_Win_Pose.png', 
                           'Name': 'Ramlethal'
                           }
sol_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Sol\\Sol_Portrait_P1.png', 
                     'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Sol\\Sol_Portrait_P2.png', 
                     'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Sol\\Sol_Win_Pose.png', 
                     'Name': 'Sol'
                     }
zato_template_imgs = {'P1_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Zato\\Zato_Portrait_P1.png', 
                      'P2_portrait': 'GGStrive_Template_imgs_v1\\Characters\\Zato\\Zato_Portrait_P2.png', 
                      'Win_Pose': 'GGStrive_Template_imgs_v1\\Characters\\Zato\\Zato_Win_Pose.png', 
                      'Name': 'Zato'
                      }
round_starter_template_imgs = {'Round_1': 'GGStrive_Template_imgs_v1\\Round_Starters\\Duel_1.png', 
                               'Round_2': 'GGStrive_Template_imgs_v1\\Round_Starters\\Duel_2.png', 
                               'Round_3': 'GGStrive_Template_imgs_v1\\Round_Starters\\Duel_3.png', 
                               'Round_Final': 'GGStrive_Template_imgs_v1\\Round_Starters\\Duel_Final.png', 
                               'Lets_Rock': 'GGStrive_Template_imgs_v1\\Round_Starters\\Lets_Rock.png', 
                               'Name': 'Starter'
                               }
round_ender_template_imgs = {'Slash': 'GGStrive_Template_imgs_v1\\Round_Enders\\Slash.png', 
                             'Double_KO': 'GGStrive_Template_imgs_v1\\Round_Enders\\Double_KO.png', 
                             'Draw': 'GGStrive_Template_imgs_v1\\Round_Enders\\Draw.png', 
                             'Perfect': 'GGStrive_Template_imgs_v1\\Round_Enders\\Perfect.png', 
                             'Times_Up': 'GGStrive_Template_imgs_v1\\Round_Enders\\Times_Up.png', 
                             '1P_Win': 'GGStrive_Template_imgs_v1\\Round_Enders\\1P_Win.png', 
                             '2P_Win': 'GGStrive_Template_imgs_v1\\Round_Enders\\2P_Win.png', 
                             'Name': 'Ender'
                             }
"""For getting the the keys to loop through (Name omitted as it's not an img path
& will only be used to prepend the column name):

list(round_starter_template_imgs.keys())[0:len(list(round_starter_template_imgs.keys()))-1]
"""

#img_path = "images\\trex.png"
#image = cv2.imread(img_path)

#Creating a 300 x 300 martix, with 3 layers, the layer emulate colour channels
canvas = np.zeros((300, 300, 3), dtype = "uint8")

