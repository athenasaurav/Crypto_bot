import websocket, json, pprint, talib, numpy
from binance.client import Client
from binance.enums import *
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
import pandas as pd
import numpy as np
import json
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open("crypto_vol").sheet1
sheet_1 = client.open("crypto_vol")
sheet_1 = sheet_1.get_worksheet(1) # Open the spreadhseet
data_1 = pd.DataFrame(sheet.get_all_records())
data = pd.DataFrame(sheet_1.get_all_records())

SOCKET = "wss://stream.binance.com:9443/ws/bnbusdt@kline_1m"

closes = []
volumes = []

client = Client('usn8SSHYWylT6PX9DcTaU6P0C3rg5knzAQ5TOEOe4Rn6Vp9pnZc6P9D7BZ0fyhxq', 'PFjTSkC8gN6a0hIH698uOzQvRIZykv6kuGwrw4re78sykUaQApwkdi5rvZ73q78j')

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global closes, in_position, np_aveg, Buy_price, Sell_price, price
    json_message = json.loads(message)
    candle = json_message['k']
    is_candle_closed = candle['x']
    close = candle['c']
    volume = candle['v']
    if is_candle_closed:
        klines = np.array(client.get_historical_klines("BNBUSDT", Client.KLINE_INTERVAL_1MINUTE, "10 min ago UTC"))
        # klines = client.get_klines(symbol = "BNBUSDT", interval = Client.KLINE_INTERVAL_1MINUTE)
        # print(klines)
        df = pd.DataFrame(klines.reshape(-1,12),dtype=float, columns = ('Open Time',
                                                                        'Open',
                                                                        'High',
                                                                        'Low',
                                                                        'Close',
                                                                        'Volume',
                                                                        'Close time',
                                                                        'Quote asset volume',
                                                                        'Number of trades',
                                                                        'Taker buy base asset volume',
                                                                        'Taker buy quote asset volume',
                                                                        'Ignore'))

        df['timestamp'] = pd.to_datetime(df['Open Time'], unit='ms')
        df.drop(['Open','High','Low', 'Close time','Quote asset volume','Number of trades','Open Time','Taker buy base asset volume','Taker buy quote asset volume','Ignore'], 1, inplace=True)
        np_volume = df['Volume'].to_numpy()
        np_aveg = np.average(np_volume)
        np_aveg = int(np_aveg)
        print(np_aveg)
        #sheet data
        orders = client.get_open_orders()
        print(orders)
        if orders:
            print("Limit Sell order in place")
        else:
            print("sheet update True")
            sheet.update_cell(2,1, "'True")
            # sheet.update_cell(2.3, "'no_sell")
            # sheet.update_cell(2,2, float(0))
        Buy_price = sheet.cell(2, 2).value
        Buy_price = int(float(Buy_price))
        # print(Buy_price)
        in_position = sheet.cell(2, 1).value
        in_position = str(in_position)
        limit = sheet.cell(2, 3).value
        limit = str(limit)
        # print(in_position)
        # print(type(in_position))
        print("candle closed at {}".format(close))
        closes.append(float(close))
        print("candle volume at {}".format(volume))
        volumes.append(float(volume))
        # print(closes)
        latest_close = closes[-1]
        latest_close= float(latest_close)
        # print(latest_close)
        # print(type(latest_close))
        prev_latest_close = closes[-2]
        prev_latest_close= float(prev_latest_close)
        # print(prev_latest_close)
        # print(type(prev_latest_close))
        latest_volume = volumes[-1]
        latest_volume= int(float(latest_volume))
        
        if latest_volume > (np_aveg*1.05):
            print("Whale identified. Check price rise or lowered")
            if latest_close > prev_latest_close:
                print("price rising. Check buy position in sheet")
                # print(in_position)
                # print(type(in_position))
                if in_position == 'True':
                    print("Buy")
                    try:
                        print("sending order")
                        order = client.order_market_buy(
                            symbol='BNBUSDT',
                            quantity='0.05')
                        print(order)
                    except Exception as e:
                        print("an exception occured - {}".format(e))
                        return False
                    price = float(order['fills'][0]['price'])
                    # print(price)
                    print("Buy  price is {}".format(price))
                    Sell_price = round((price*1.005), 4)
                    # Sell_price = str(Sell_price)
                    order = client.order_limit_sell(
                        symbol='BNBUSDT',
                        quantity=0.05,
                        price=Sell_price)                    
                    sheet.update_cell(2,2, price)
                    print("Update sheet for position to false")
                    sheet.update_cell(2,1, "'False")
                    sheet.update_cell(2,3, "'limit_sell")
                    print("create limit order for sell")
                    print("limit sell at {}".format(Sell_price))
                    date = datetime.date.today()
                    time = datetime.datetime.now()
                    date = str(date)
                    hour = time.hour
                    hour = str(hour)
                    minu = time.minute
                    minu = str(minu)
                    time_1 = str(hour) + str(minu)
                    to_save = [date, hour, minu]
                    sheet_1.insert_row(to_save, 2)
                    price = str(price)
                    Sell_price = str(Sell_price)
                    sheet_1.update_cell(2,5, price)
                    sheet_1.update_cell(2,7, Sell_price)
                    sheet_1.update_cell(2,9, "PROFITABLE")
                elif in_position == 'False':
                    if limit == 'limit_sell':
                        print('limit sell goin on. nothing to buy nothing to sell')
                    elif limit == 'no_sell':
                        print("update sheet to True")
                        sheet.update_cell(2,1, "'True")
                        print("update limit sell sheet cell to no_sell")
                        sheet.update_cell(2,3, "'no_sell")
            else:
                print("Price dropping")
        

        elif latest_close < (Buy_price*0.97):
            print("Cancel all order")
            print("create Stop loss market order Sell at {} ".format(latest_close))
            orders = client.get_open_orders(symbol='BNBUSDT')
            # print(orders[0]['orderId'])
            order_id = str(orders[0]['orderId'])
            result = client.cancel_order(
                symbol='BNBUSDT',
                orderId=order_id)
            order = client.order_market_sell(
                symbol='BNBUSDT',
                quantity=0.05)
            sheet.update_cell(2,1, "'True")
            print("update sheet for position to true")
            

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
