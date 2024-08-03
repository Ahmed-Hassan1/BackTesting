from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
import pandas_ta
import logging
from datetime import datetime, timedelta

from backtesting import Backtest, Strategy

logging.basicConfig(filename='backtesting.log',level=logging.INFO)

class ProfitPal(Strategy):
    StartTime=520
    StopTime=590
    TP=17
    SL=23
    SMAFilter=True
    smaLen=1650
    bLen=21
    bDev=2.4
    adxLen=14
    minADX=0
    maxADX=100
    atrLen=14
    minATR=0
    maxATR=100
    minBB=1
    maxBB=100
    RSIFilter=False
    rsiLen=14
    OB=80
    OS=20

    lastTrade=0


    def init(self):
        self.rsi=self.I(pandas_ta.rsi,pd.Series(self.data.Close),self.rsiLen)
        self.bollinger=self.I(pandas_ta.bbands,pd.Series(self.data.Close),self.bLen,self.bDev)
        self.sma=self.I(pandas_ta.sma,pd.Series(self.data.Close),self.smaLen)
        self.adx=self.I(pandas_ta.adx,pd.Series(self.data.High),pd.Series(self.data.Low),pd.Series(self.data.Close),self.adxLen)
        self.atr=self.I(pandas_ta.atr,pd.Series(self.data.High),pd.Series(self.data.Low),pd.Series(self.data.Close),self.atrLen)

    def next(self):
        upperBand=self.bollinger[2][-2]
        lowerBand=self.bollinger[0][-2]
        middleBand=self.bollinger[1][-2]
        bollingerBandWidth=((upperBand - lowerBand) / middleBand) * 100 * 100
        

        current=datetime.strptime(str(self.data.index[-1]),'%Y-%m-%d  %H:%M:%S')

        currentTimeInMinutes=current.hour*60+current.minute
        
        #logging.info(str(self.data.index[-1])+"  "+str(currentTimeInMinutes>=520 and currentTimeInMinutes<590) +"    "+str(currentTimeInMinutes))
        if currentTimeInMinutes>=self.StartTime and currentTimeInMinutes<self.StopTime and not self.position:
            if bollingerBandWidth >= self.minBB and bollingerBandWidth<=self.maxBB and self.adx[0][-1]>=self.minADX and self.adx[0][-1]<=self.maxADX and self.atr[-1]>=self.minATR and self.atr[-1]<=self.maxATR:
                if (not self.SMAFilter or self.data.Close[-1]>self.sma[-1]) and self.data.Close[-1]<self.bollinger[0][-1] and self.data.Close[-2]<self.bollinger[0][-2] and (not self.RSIFilter or self.rsi[-1]<self.OS):
                    self.buy(tp=self.data.Close[-1]+self.TP*0.25,sl=self.data.Close[-1]-self.SL*0.25)
                elif (not self.SMAFilter or self.data.Close[-1]<self.sma[-1]) and self.data.Close[-1]>self.bollinger[2][-1] and self.data.Close[-2]>self.bollinger[2][-2] and (not self.RSIFilter or self.rsi[-1]>self.OB):
                    self.sell(tp=self.data.Close[-1]-self.TP*0.25,sl=self.data.Close[-1]+self.SL*0.25)



def profitPal(request):
    inputs={
        "StartDate":"2024/03/07",
        "EndDate":"2024/06/17",
        "StartTime":"08:40:00",
        "EndTime":"09:50:00",
        "TP":"17",
        "SL":"23",
        "smaFilter":"Yes",
        "SMALength":"1650",
        "bLength":"21",
        "bDev":"2.4",
        "adxLen":"14",
        "minADX":"0",
        "maxADX":"100",
        "atrLen":"14",
        "minATR":"0",
        "maxATR":"100",
        "bMin":"1",
        "bMax":"100",
        "rsiLen":"14",
        "OB":"80",
        "OS":"20",
        "TF":"1min"
    }
    if request.method=='GET' and 'rsiLen' in request.GET:
        startDate=request.GET['StartDate']
        endDate=request.GET['EndDate']
        start=request.GET['StartTime']
        end=request.GET['EndTime']
        start=datetime.strptime(start,'%H:%M:%S')
        end=datetime.strptime(end,'%H:%M:%S')
        start=start.hour*60+start.minute-2
        end=end.hour*60+end.minute

        tp=int(request.GET['TP'])
        sl=int(request.GET['SL'])
        smaFil=True if 'smaFilter' in request.GET else False
        smaL=int(request.GET['SMALength'])
        bL=int(request.GET['bLength'])
        bD=float(request.GET['bDev'])
        adxL=int(request.GET['adxLen'])
        adxmin=float(request.GET['minADX'])
        adxmax=float(request.GET['maxADX'])
        atrL=int(request.GET['atrLen'])
        atrmin=float(request.GET['minATR'])
        atrmax=float(request.GET['maxATR'])
        minb=float(request.GET['bMin'])
        maxb=float(request.GET['bMax'])
        rsiFil=True if 'rsiFilter' in request.GET else False
        rsiL=int(request.GET['rsiLen'])
        ob=float(request.GET['OB'])
        os=float(request.GET['OS'])
        tf=request.GET['TF']
        
        
        
        
    
        # data = pd.read_csv("static/media/ES_1min_sample.csv")
        # data['timestamp']=pd.to_datetime(data['timestamp'])
        data = pd.read_csv("static/media/ES.csv")
        data['timestamp']=pd.to_datetime(data['timestamp'])-timedelta(hours=4,minutes=1)
        data = data.set_index('timestamp')
        df=data.resample(tf).agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last','Volume':'sum'})
        df=df.loc[(startDate+' 00:00:00'):(endDate+' 23:00:00')]
        df=df.dropna()

        bt = Backtest(df,ProfitPal,cash=10_000)

        stats=bt.run(
            StartTime=start,StopTime=end,TP=tp,SL=sl,SMAFilter=smaFil,smaLen=smaL,
            bLen=bL,bDev=bD,adxLen=adxL,minADX=adxmin,maxADX=adxmax,atrLen =atrL,minATR=atrmin,maxATR=atrmax,
            minBB=minb,maxBB=maxb,RSIFilter=rsiFil,rsiLen=rsiL,OB=ob,OS=os)

        #bt.plot(filename="profitpal",open_browser=False,resample=tf)
        removed_stats=stats.drop("_equity_curve")
        removed_stats=removed_stats.drop("_trades")

        trades_df=pd.DataFrame(data=stats.to_dict()["_trades"])

        for idx in range(0,trades_df['Size'].count()):
            if int(trades_df['Size'][idx])>0:
                trades_df['Size'][idx]="Long"
            else:
                trades_df['Size'][idx]="Short"

        return render(request,"bt/profitpal.html",{'trades':trades_df.to_html(),"stats":removed_stats.to_frame().to_html(),"form":request.GET})

    return render(request,"bt/profitpal.html",{"form":inputs})




def homePage(request):
    
    return render(request,"bt/home.html")


def testing(request):
    html_content = open("profitpal.html")
    return HttpResponse(html_content)