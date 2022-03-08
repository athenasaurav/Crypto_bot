import websocket, json, pprint, talib, numpy
from binance.client import Client
from binance.enums import *
import numpy as np

client = Client('your_api_key', 'your_api_secret')

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

klines = np.array(client.get_historical_klines("BNBBTC", Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC"))

print(klines)

import pandas as pd
history = pd.DataFrame(klines.reshape(-1,12),dtype=float, columns = ('Open Time',
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

history['timestamp'] = pd.to_datetime(history['Open Time'], unit='ms')
#Remove the Date column
history.drop(['Open','High','Low','Volume', 'Close time','Quote asset volume','Number of trades','Open Time','Taker buy base asset volume','Taker buy quote asset volume','Ignore'], 1, inplace=True)
print(history)
history.drop(['timestamp'], 1, inplace=True)
#A variable for predicting 'n' days out into the future
prediction = predictionory.copy()
def on_message(ws, message):
    
    history = history.iloc[1:]
    
    prediction_days = 30 #n = 30 days

    #Create another column (the target or dependent variable) shifted 'n' units up
    prediction['Prediction'] = prediction[['Close']].shift(-prediction_days)
    #CREATE THE INDEPENDENT DATA SET (X)

    # Convert the dataframe to a numpy array and drop the prediction column
    X = np.array(prediction.drop(['Prediction'],1))

    #Remove the last 'n' rows where 'n' is the prediction_days
    X= X[:len(prediction)-prediction_days]
    print(X)
    #CREATE THE DEPENDENT DATA SET (y) 
    # Convert the dataframe to a numpy array (All of the values including the NaN's) 
    y = np.array(prediction['Prediction'])  
    # Get all of the y values except the last 'n' rows 
    y = y[:-prediction_days] 
    print(y)
    # Split the data into 80% training and 20% testing
    from sklearn.model_selection import train_test_split
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    # Set prediction_days_array equal to the last 30 rows of the original data set from the price column
    prediction_days_array = np.array(prediction.drop(['Prediction'],1))[-prediction_days:]
    print(prediction_days_array)
    from sklearn.svm import SVR
    # Create and train the Support Vector Machine 
    svr_rbf = SVR(kernel='rbf', C=1e3, gamma=0.00001)#Create the model
    svr_rbf.fit(x_train, y_train) #Train the model
    # Testing Model: Score returns the accuracy of the prediction. 
    # The best possible score is 1.0
    svr_rbf_confidence = svr_rbf.score(x_test, y_test)
    print("svr_rbf accuracy: ", svr_rbf_confidence)
    # Print the predicted value
    svm_prediction = svr_rbf.predict(x_test)
    print(svm_prediction)

    print()

    #Print the actual values
    print(y_test)
    # Print the model predictions for the next 'n=30' days
    svm_prediction = svr_rbf.predict(prediction_days_array)
    print(svm_prediction)
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
