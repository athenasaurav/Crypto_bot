import websocket, json, pprint, talib, numpy
from binance.client import Client
from binance.enums import *
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
import pandas as pd
import json
from scipy.signal import argrelextrema
import numpy as np
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open("crypto")
sheet = sheet.get_worksheet(2) # Open the spreadhseet
data = pd.DataFrame(sheet.get_all_records())
SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@kline_30m"
closes = []
highs = []
lows = []

in_position = False
client = Client('your_api_key', 'your_api_key')

def order(side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global closes, highs, closes, in_position
    
    print('received message')
    json_message = json.loads(message)
    pprint.pprint(json_message)

    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']
    high = candle['h']
    low = candle['l']

    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        highs.append(float(high))
        lows.append(float(low))
        np_closes = numpy.array(closes)
        np_highs = numpy.array(highs)
        np_low = numpy.array(lows)
        numpyArray = np.array(np_highs,np_lows, np_closes)
        panda_df = pd.DataFrame(data = numpyArray,  
                        index = ["high", "low", "close"],  
                        columns = ["Column_1", 
                                   "Column_2", "Column_3"]) 
        local_max = argrelextrema(panda_df['high'], np.greater)[0]
        local_min = argrelextrema(panda_df['low'], np.less)[0]
        print(local_max)
        print(local_min)
        highs = panda_df.iloc[local_max,:]
        lows = panda_df.iloc[local_min,:]
        import matplotlib.pyplot as plt
        fig = plt.figure(figsize=[20,14])
        highslows = pd.concat([highs,lows])
        panda_df['high'].plot()
        panda_df['low'].plot()
        plt.scatter(highslows.index,highslows)


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
