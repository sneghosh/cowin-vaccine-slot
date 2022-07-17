"""
Created on Sat May 15 10:13:27 2021

@author: Snehashish Ghosh
@email: snehashish.ghosh@gmail.com
"""

import datetime
import json
import requests
import pandas as pd
from copy import deepcopy
from fake_useragent import UserAgent
from playsound import playsound
import time
import sys
import telegram_send #https://medium.com/@robertbracco1/how-to-write-a-telegram-bot-to-send-messages-with-python-bcdf45d0a580

#https://api.telegram.org/bot1667468398:AAFWSvsnEeGCZYPcNryBK_z2ApaYMPhwJ38/getUpdates
group_chat_id=-1001297757596




# browser_header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
# browser_header = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; ONEPLUS A6000) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.99 Mobile Safari/537.36'}

def filter_column(df, col, value):
    df_temp = deepcopy(df.loc[df[col] == value, :])
    return df_temp

manualexit=0
while True:
    # code goes here
    #time.sleep(4)
    if manualexit==1:
        print("Manually Exited.......")
        break
    print(" ------ START ---------")
    temp_user_agent = UserAgent()
    browser_header = {'User-Agent': temp_user_agent.random}
    
    # Enter the district that you want to search
    #DIST_ID = 725  #KOLKATA  725
    #DIST_ID = 730 #North 24 Parganas
    #DIST_ID = 735 #South 24 Parganas,735
    #DIST_ID = 720 #Hoogly,720
    #DIST_ID = 719 #East Bardhaman,719
    #DIST_ID = 721 #Howrah,721
    #DIST_ID = 718 #Diamond,721
    
    distlist = ["725", "730", "735","720","721"]
    distlist = ["725"]
    
    # How many days data you want to search
    numdays=1
    base = datetime.datetime.today()
    date_list = [base + datetime.timedelta(days=x) for x in range(numdays)]
    date_str = [x.strftime("%d-%m-%Y") for x in date_list]
    
    #Which age group you want to search
    age_inp=18
    #age_inp=45
 
    final_df = None
    no_slot=0
    for INP_DATE in date_str:
        for INP_DIST in distlist:
            #print("Date:"+ INP_DATE + " District: "+ INP_DIST)
            URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(INP_DIST, INP_DATE)
            response = requests.get(URL, headers=browser_header)
            if (response.ok) and ('centers' in json.loads(response.text)):
                resp_json = json.loads(response.text)['centers']
                if resp_json is not None:
                    df = pd.DataFrame(resp_json)
                    if len(df):
                        df = df.explode("sessions")
                        df['min_age_limit'] = df.sessions.apply(lambda x: x['min_age_limit'])
                        df['vaccine'] = df.sessions.apply(lambda x: x['vaccine'])
                        df['available_capacity'] = df.sessions.apply(lambda x: x['available_capacity'])
                        df['date'] = df.sessions.apply(lambda x: x['date'])
                        df['available_capacity_dose1'] = df.sessions.apply(lambda x: x['available_capacity_dose1'])
                        df['available_capacity_dose2'] = df.sessions.apply(lambda x: x['available_capacity_dose2'])
                        df = df[["date", "available_capacity", "vaccine", "min_age_limit", "pincode", "name", "state_name", "district_name", "block_name", "fee_type","available_capacity_dose1","available_capacity_dose2"]]
                        final_df = None
                        if final_df is not None:
                            final_df = pd.concat([final_df, df])
                        else:
                            final_df = deepcopy(df)
                
                
                try:
                    now=datetime.datetime.now()
                    now.isoformat() 
                    final_df_age = filter_column(final_df, "min_age_limit", age_inp)
                    final_df_available = final_df_age[final_df_age.available_capacity_dose2>0]

                    index = final_df_available.index
                    number_of_rows = len(index)
                    
                    ignore_avl_cnt=1
                    ignore_avl_dose1_cnt=0
                    count=0
                    while count<number_of_rows:
                        avlslot18=final_df_available.iloc[count,1]
                        avldose1slot18=final_df_available.iloc[count,10]
                        avldose2slot18=final_df_available.iloc[count,11]
                        
                        if  ( (avlslot18 > ignore_avl_cnt 
                             or avldose1slot18 > ignore_avl_dose1_cnt) 
                             and (avlslot18 > avldose2slot18)) :
                            available_slot=final_df_available.iloc[count,1]
                            pincode=final_df_available.iloc[count,4]
                            hospital=final_df_available.iloc[count,5]
                            msg=str(count+1) + ". Pincoce= " + str(pincode) + " " + str(available_slot) + " SLOT Available at " + hospital + " at " + str(now)
                            print(msg)
                            telegram_send.send(messages=[msg])
                            base_url = 'https://api.telegram.org/bot1667468398:AAFWSvsnEeGCZYPcNryBK_z2ApaYMPhwJ38/sendMessage?chat_id=-1001297757596&text="{}"'.format(msg) 
                            requests.get(base_url) 
                            count=count+1
                            playsound('cowin.mp3',block = False)
                        else:
                            count=count+1
                            no_slot=1
                            
                    if (number_of_rows==0 or no_slot==1):
                        msg=" District: "+ INP_DIST + " No SLOT Available at "+ str(now)
                        print(msg)
                        #telegram_send.send(messages=[msg])
                        #base_url = 'https://api.telegram.org/bot1667468398:AAFWSvsnEeGCZYPcNryBK_z2ApaYMPhwJ38/sendMessage?chat_id=-1001297757596&text="{}"'.format(msg) 
                        #requests.get(base_url) 
                        print(" ------------------------")
                            
                    time.sleep(4)   
                    
                except (KeyboardInterrupt):
                    print ('Interrupted')
                    manualexit=1
                    break
                    sys.exit(0)
                except (RuntimeError, TypeError, NameError, OSError):
                    pass
                except:
                    print("Unexpected error:", sys.exc_info()[0])
                    pass
                
                                
            else:
                print("No rows in the data Extracted from the API")
    

