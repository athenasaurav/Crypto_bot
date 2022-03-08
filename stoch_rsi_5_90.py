import websocket, json, pprint, talib, numpy
from binance.client import Client
from binance.enums import *
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
import pandas as pd
import json
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open("crypto")
sheet = sheet.get_worksheet(3) 
data = pd.DataFrame(sheet.get_all_records())

SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m"

RSI_PERIOD = 3
RSI_OVERBOUGHT = 65
RSI_OVERSOLD = 35
STOCH_PERIOD = 3
STOCH_OVERBOUGHT = 90
STOCH_OVERSOLD = 5
TRADE_SYMBOL = 'BTCUSDT'

closes = []
highs = []
lows = []
in_position = False

client = Client('your_api_key', 'your_api_secret')
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
    global closes, in_position
    
    ##print('received message')
    json_message = json.loads(message)
    ##pprint.pprint(json_message)

    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']
    high = candle['h']
    low = candle['l']
    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        highs.append(float(high))
        #print(highs)
        lows.append(float(low))
        #print(lows)
        ##print("closes")
        print(closes)
        latest_close = closes[-1]
        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            np_highs = numpy.array(highs)
            np_lows = numpy.array(lows)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print(type(rsi))
            print(rsi)
            ##print("all rsis calculated so far")
            ##print(rsi)
            last_rsi = rsi[-1]
            
            fastk, fastd = talib.STOCHRSI(rsi, 3, 3, 3, 0)
            # print("all rsis calculated so far")
            # print(fastd)
            last_stoch_rsi_k = fastd[-1]
            last_stoch_rsi_d = fastk[-1]
            print("the current stoch fask k rsi is {}".format(last_stoch_rsi_k))
            print("the current stoch fask d rsi is {}".format(last_stoch_rsi_d))
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            ##print("all rsis calculated so far")
            ##print(rsi)
            last_rsi = rsi[-1]
            print("the current rsi is {}".format(last_rsi))
            if last_stoch_rsi_d > STOCH_OVERBOUGHT:
                print("Stoch rsi sell triggered.")
                if last_rsi > RSI_OVERBOUGHT:
                    print("RSI and Stoch rsi both Oversold")
                    if in_position:
                        order = client.order_market_sell(
                            symbol='BTCUSDT',
                            quantity='0.001')
                        print(order)
                        last_rsi = str(last_rsi)
                        last_stoch_rsi = str(last_stoch_rsi)
                        price = str(order['fills'][0]['price'])
                        commission= str(order['fills'][0]['commission'])
                        qty= str(order['fills'][0]['qty'])
                        date = datetime.date.today()
                        time = datetime.datetime.now()
                        date = str(date)
                        hour = time.hour
                        hour = str(hour)
                        minu = time.minute
                        minu = str(minu)
                        time_1 = str(hour) + str(minu)
                        to_save = [date, hour, minu]
                        sheet.insert_row(to_save, 2)
                        sheet.update_cell(2,4, last_rsi)
                        sheet.update_cell(2,5, "${}".format(price))
                        sheet.update_cell(2,6, "${}".format(last_stoch_rsi))
                        sheet.update_cell(2,7, "Sell")
                        in_position = False
                    else:
                        print("Overbought but both rsi triggered. Cant Bid no money in account.")
                else:
                    print("It is overbought, but we don't own any. Nothing to do.")
            if last_stoch_rsi_d < STOCH_OVERSOLD:
                print("Stoch RSI triggered for buying")                    
                if last_rsi < RSI_OVERSOLD:
                    print("stoch Rsi and RSI bot oversold and its time to buy.")
                    if in_position:
                        print("It is oversold, but you already own it, nothing to do.")
                    else:
                        order = client.order_market_buy(
                            symbol='BTCUSDT',
                            quantity='0.001')
                        print(order)
                        print("Oversold! Buy! Buy! Buy!")
                        # put binance buy order logic here
                        last_rsi = str(last_rsi)
                        last_stoch_rsi = str(last_stoch_rsi)
                        price = str(order['fills'][0]['price'])
                        commission= str(order['fills'][0]['commission'])
                        date = datetime.date.today()
                        time = datetime.datetime.now()
                        date = str(date)
                        hour = time.hour
                        hour = str(hour)
                        minu = time.minute
                        minu = str(minu)
                        time_1 = str(hour) + str(minu)
                        to_save = [date, hour, minu]
                        sheet.insert_row(to_save, 2)
                        sheet.update_cell(2,4, last_rsi)
                        sheet.update_cell(2,5, "${}".format(price))
                        sheet.update_cell(2,6, "${}".format(last_stoch_rsi))
                        sheet.update_cell(2,7, "Buy")
                        in_position = True

                
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
