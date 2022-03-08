import websocket, json, pprint, talib, numpy
from binance.client import Client
from binance.enums import *
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from scipy.signal import argrelextrema
import pandas as pd 
from scipy.signal import argrelextrema
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.nonparametric.kernel_regression import KernelReg
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
sheet_client = gspread.authorize(creds)
SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m"
closes = []
highs = []
lows = []
opens = []
in_position = False
client = Client('api_key', 'api_secret')

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
    global closes, highs, lows, in_position
    
    ##print('received message')
    json_message = json.loads(message)
    ##pprint.pprint(json_message)

    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']
    high = candle['h']
    low = candle['l']
    start = candle['o']
    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        highs.append(float(high))
        lows.append(float(low))
        opens.append(float(start))
        date = datetime.date.today()
        time = datetime.datetime.now()
        date = str(date)
        hour = time.hour
        hour = str(hour)
        minu = time.minute
        minu = str(minu)
        time_1 = str(hour) + str(minu)
        to_save = [date, hour, minu]
        data_sheet = sheet_client.open("real_time_data_1m")
        data_sheet= data_sheet.get_worksheet(0)
        real_data = pd.DataFrame(data_sheet.get_all_records())
        data_sheet.insert_row(to_save, 2)
        data_sheet.update_cell(2,4, "{}".format(high))
        data_sheet.update_cell(2,5, "{}".format(low))
        data_sheet.update_cell(2,6, "{}".format(close))
        panda_df = pd.DataFrame(data_sheet.get_all_records())
        panda_df = panda_df.iloc[::-1].reset_index(drop=True)
        pd.set_option("display.max_rows", panda_df.shape[0]+1, "display.max_columns", panda_df.shape[0]+1)
        print(panda_df)
        prices = panda_df.copy()
        prices = prices.reset_index()
        prices = prices['close']
        kr = KernelReg(prices.values, prices.index, var_type='c')
        f = kr.fit([prices.index.values])
        smooth_prices = pd.Series(data=f[0], index=panda_df.index)
        smoothed_local_maxima = argrelextrema(smooth_prices.values, np.greater)[0]
        print(smoothed_local_maxima)
        smoothed_local_minima = argrelextrema(smooth_prices.values, np.less)[0]
        print(smoothed_local_minima)
        price_local_max_dt = []
        for i in smoothed_local_maxima:
            if (i>1) and (i<len(panda_df)):
                price_local_max_dt.append(panda_df['close'].iloc[i-4:i].idxmax())
                if in_position:
                    print("Oversold! Sell! Sell! Sell!")
                    data_sheet.update_cell(2,8, "Sell")
                    in_position = False
                else:
                    print("We have nothing to sell")

        price_local_min_dt = []
        for i in smoothed_local_minima:
            if (i>1) and (i<len(panda_df)):
                price_local_min_dt.append(panda_df['close'].iloc[i-4:i].idxmin())
                if in_position:
                    print("We dont have any money")
                else:
                    print("Oversold! Buy! Buy! Buy!")
                    data_sheet.update_cell(2,7, "Buy")
                    in_position = True
                    
        max_min = pd.concat([panda_df.loc[price_local_min_dt, 'close'], panda_df.loc[price_local_max_dt, 'close']])
        # print("buy prices")
        # print(price_local_min_dt)
        price_local_min_dt = panda_df.iloc[price_local_min_dt,:]
        pd.set_option("display.max_rows", price_local_min_dt.shape[0], "display.max_columns", price_local_min_dt.shape[0])
        print(price_local_min_dt['close'].to_string(index=False))
        # print("sell prices")
        # print(price_local_max_dt)
        price_local_max_dt = panda_df.iloc[price_local_max_dt,:]
        pd.set_option("display.max_rows", price_local_max_dt.shape[0]+1, "display.max_columns", price_local_max_dt.shape[0]+1)
        print(price_local_max_dt['close'].to_string(index=False))
        


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
