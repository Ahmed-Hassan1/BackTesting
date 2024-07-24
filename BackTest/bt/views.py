from django.shortcuts import render, redirect
from django.http import HttpResponse
from pathlib import Path
import os
import numpy as np
import pandas as pd
import pandas_ta
import logging

from backtesting import Backtest, Strategy
from backtesting.lib import resample_apply,crossover

logging.basicConfig(filename='backtesting.log',level=logging.INFO)






class RsiOsci(Strategy):
    def init(self):
        self.rsi=self.I(pandas_ta.rsi,pd.Series(self.data.Close),14)
        self.bollinger=self.I(pandas_ta.bbands,pd.Series(self.data.Close),21,2.4)
        self.sma=self.I(pandas_ta.sma,pd.Series(self.data.Close),1650)
        self.adx=self.I(pandas_ta.adx,pd.Series(self.data.High),pd.Series(self.data.Low),pd.Series(self.data.Close),14)
        self.atr=self.I(pandas_ta.atr,pd.Series(self.data.High),pd.Series(self.data.Low),pd.Series(self.data.Close),14)

    def next(self):
        #((upperBand - lowerBand) / middleBand) * 100 * 100;
        upperBand=self.bollinger[2][-1]
        lowerBand=self.bollinger[0][-1]
        middleBand=self.bollinger[1][-1]
        bollingerBandWidth=((upperBand - lowerBand) / middleBand) * 100 * 100

        

        if bollingerBandWidth >= 1 and bollingerBandWidth<=100 and self.adx[-1]>=0 and self.adx[-1]<=100 and self.atr[-1]>=0 and self.atr[-1]<=100:
            #if self.rsi[-1]<20:
                
            if self.data.Close[-1]>self.sma[-1] and self.data.Close[-1]<lowerBand and (self.rsi[-1]<20 or True):
                #logging.info(str(self.data.index[-1]))
                self.buy(tp=self.data.Close[-1]+19*0.25,sl=self.data.Close[-1]-23*0.25)
            elif self.data.Close<self.sma[-1] and self.data.Close[-1]>upperBand and (self.rsi[-1]>80 or True):
                self.sell(tp=self.data.Close[-1]-19*0.25,sl=self.data.Close[-1]+23*0.25)


def homePage(request):
    data = pd.read_csv("static/media/ES_1min_sample.csv")
    data['timestamp']=pd.to_datetime(data['timestamp'])
    data = data.set_index('timestamp') 
    #df=data.resample('5min').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last','Volume':'sum'})
    #df=df.dropna()

    bt = Backtest(data,RsiOsci,cash=10_000)

    stats=bt.run()
    removed_stats=stats.drop("_equity_curve")
    removed_stats=removed_stats.drop("_trades")

    trades_df=pd.DataFrame(data=stats.to_dict()["_trades"])
    #return render(request,"RsiOsci.html",{'result':1})
    return render(request,"bt/home.html",{'trades':trades_df.to_html(),"stats":removed_stats.to_frame().to_html()})

    #return HttpResponse("1")