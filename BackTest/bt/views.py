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
                    self.buy(tp=self.data.Close[-1]+self.TP*0.25,sl=self.data.Close[-1]-self.SL*0.25,size=1)
                elif (not self.SMAFilter or self.data.Close[-1]<self.sma[-1]) and self.data.Close[-1]>self.bollinger[2][-1] and self.data.Close[-2]>self.bollinger[2][-2] and (not self.RSIFilter or self.rsi[-1]>self.OB):
                    self.sell(tp=self.data.Close[-1]-self.TP*0.25,sl=self.data.Close[-1]+self.SL*0.25,size=1)


class DK_MA_Cloud(Strategy):
    Fast=1
    Slow=5
    TargetTicks=20
    StopTicks=20
    MinAdx=20
    MaxAdx=40
    StartTime=520
    StopTime=590
    UseSMAFilter=True
    SmaFilterLength=1650
    UseEMAFilter=True
    EmaFilterLength=55

    lastTradeDirection=0

    def init(self):
        self.smaFast=self.I(pandas_ta.sma,pd.Series(self.data.Close),self.Fast)
        self.smaSlowHigh=self.I(pandas_ta.sma,pd.Series(self.data.High),self.Slow)
        self.smaSlowLow=self.I(pandas_ta.sma,pd.Series(self.data.Low),self.Slow)
        self.adx=self.I(pandas_ta.adx,pd.Series(self.data.High),pd.Series(self.data.Low),pd.Series(self.data.Close),14)
        self.smaFilter=self.I(pandas_ta.sma,pd.Series(self.data.Close),self.SmaFilterLength)
        self.emaFilter=self.I(pandas_ta.ema,pd.Series(self.data.Close),self.EmaFilterLength)


    def next(self):

        current=datetime.strptime(str(self.data.index[-1]),'%Y-%m-%d  %H:%M:%S')

        currentTimeInMinutes=current.hour*60+current.minute

        crossAbove=self.smaFast[-1]>self.smaSlowHigh[-1] and self.smaFast[-2]<self.smaSlowHigh[-2]
        crossBelow=self.smaFast[-1]<self.smaSlowLow[-1] and self.smaFast[-2]>self.smaSlowLow[-2]

        isPriceAboveSmaFilter = self.data.Close[-1] > self.smaFilter[-1]
        isPriceAboveEmaFilter = self.data.Close[-1] > self.emaFilter[-1]

        allow_trading= currentTimeInMinutes>=self.StartTime and currentTimeInMinutes<self.StopTime and self.adx[0][-1]>=self.MinAdx and self.adx[0][-1]<=self.MaxAdx

        #logging.info("L: "+str(self.data.index[-1])+"  "+str(crossAbove)+"  "+str(allow_trading)+"  "+str(self.lastTradeDirection != 1)+"  "+str(isPriceAboveSmaFilter)+"  "+str(isPriceAboveEmaFilter))
        #logging.info("S: "+str(self.data.index[-1])+"  "+str(crossBelow)+"  "+str(allow_trading)+"  "+str(self.lastTradeDirection != -1)+"  "+str((not isPriceAboveSmaFilter))+"  "+str((not isPriceAboveEmaFilter)))
        if crossAbove:
            if allow_trading and self.lastTradeDirection != 1 and (not self.UseSMAFilter or isPriceAboveSmaFilter) and (not self.UseEMAFilter or isPriceAboveEmaFilter) and not self.position.is_long:
                self.buy(tp=self.data.Close[-1]+self.TargetTicks*0.25,sl=self.data.Close[-1]-self.StopTicks*0.25,size=1)
                #logging.info("LONG")
            self.lastTradeDirection=1
        elif crossBelow:
            if allow_trading and self.lastTradeDirection != -1 and (not self.UseSMAFilter or not isPriceAboveSmaFilter) and (not self.UseEMAFilter or not isPriceAboveEmaFilter)and not self.position.is_short:
                self.sell(tp=self.data.Close[-1]-self.TargetTicks*0.25,sl=self.data.Close[-1]+self.StopTicks*0.25,size=1)
                #logging.info("SHORT")
            self.lastTradeDirection=-1





def profitPal(request):
    inputs={
        "StartDate":"2024/03/07",
        "EndDate":"2024/06/17",
        "StartTime":"09:40:00",
        "EndTime":"10:50:00",
        "TP":"17",
        "SL":"23",
        "smaFilter":"Yes",
        "SMALength":"1650",
        "bLength":"39",
        "bDev":"2.25",
        "adxLen":"14",
        "minADX":"18",
        "maxADX":"52",
        "atrLen":"14",
        "minATR":"0",
        "maxATR":"100",
        "bMin":"1",
        "bMax":"100",
        "rsiLen":"14",
        "OB":"80",
        "OS":"20",
        "TF":"2min"
    }
    if request.method=='GET' and 'rsiLen' in request.GET:
        Instrument=request.GET['Instrument']
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
        
        df=InstrumentChoice(startDate,endDate,tf,Instrument)

        bt = Backtest(df,ProfitPal,cash=100_000)

        stats=bt.run(
            StartTime=start,StopTime=end,TP=tp,SL=sl,SMAFilter=smaFil,smaLen=smaL,
            bLen=bL,bDev=bD,adxLen=adxL,minADX=adxmin,maxADX=adxmax,atrLen =atrL,minATR=atrmin,maxATR=atrmax,
            minBB=minb,maxBB=maxb,RSIFilter=rsiFil,rsiLen=rsiL,OB=ob,OS=os)

        #bt.plot(filename="profitpal",open_browser=False,resample=tf)
        removed_stats=stats.drop("_equity_curve")
        removed_stats=removed_stats.drop("_trades")

        
        tradesDict=stats.to_dict()["_trades"]

        pointValue=PointValue(Instrument)

        grossProfit=0
        for pnl in tradesDict['PnL']:
            if float(pnl)>0:
                grossProfit+=float(pnl)*pointValue

        consWinners=0
        consLosers=0
        maxWin=0
        maxLoss=0
        for tr in tradesDict['PnL']:
            if float(tr)>0:
                consWinners+=1
                if consLosers>0:
                    maxLoss+=max(maxLoss,consLosers)-maxLoss
                consLosers-=consLosers
            if float(tr)<0:
                consLosers+=1
                if consWinners>0:
                    maxWin+=max(maxWin,consWinners)-maxWin
                consWinners-=consWinners

        maxLoss+=max(maxLoss,consLosers)-maxLoss
        maxWin+=max(maxWin,consWinners)-maxWin

        #print("GROSS: " + str(grossProfit) )
        #print(removed_stats.to_dict().keys())
        #print(removed_stats.to_dict().values())

        keyList=list(removed_stats.to_dict().keys())
        valueList=list(removed_stats.to_dict().values())
        highlighted_key=[]
        highlighted_value=[]


        #Gross Profit
        highlighted_key.append("Gross Profit")
        highlighted_value.append(grossProfit)
        #Net Profit
        highlighted_key.append("Net Profit")
        highlighted_value.append((int(valueList[4])-100_000)*pointValue)
        #Profit Factor
        highlighted_key.append(keyList[24])
        highlighted_value.append(valueList[24])
        #Sharpe Ratio
        highlighted_key.append(keyList[10])
        highlighted_value.append(valueList[10])
        #Trades number
        highlighted_key.append(keyList[17])
        highlighted_value.append(valueList[17])
        #Cons Winners
        highlighted_key.append("Cons Winners")
        highlighted_value.append(maxWin)
        #Cons Losers
        highlighted_key.append("Cons Losers")
        highlighted_value.append(maxLoss)
        #Win Rate
        highlighted_key.append(keyList[18])
        highlighted_value.append(valueList[18])
        #Average Trade
        highlighted_key.append("Avg Trade")
        highlighted_value.append(float(valueList[21])*100*pointValue )



        trades_df=pd.DataFrame(data=tradesDict)

        for idx in range(0,trades_df['Size'].count()):
            if int(trades_df['Size'][idx])>0:
                trades_df['Size'][idx]="Long"
            else:
                trades_df['Size'][idx]="Short"

        return render(request,"bt/profitpal.html",{'trades':trades_df.to_html(),"stats":removed_stats.to_frame().to_html(),"form":request.GET,"hl_keys":highlighted_key,"hl_values":highlighted_value,"inst":Instrument})

    return render(request,"bt/profitpal.html",{"form":inputs})





def dkMACloud(request):
    inputs={
        "StartDate":"2024/03/07",
        "EndDate":"2024/06/17",
        "Fast":"1",
        "Slow":"5",
        "TargetTicks":"20",
        "StopTicks":"20",
        "MinAdx":"20",
        "MaxAdx":"40",
        "StartTime":"09:40:00",
        "EndTime":"10:50:00",
        "UseSMAFilter":"Yes",
        "SmaFilterLength":1650,
        "UseEMAFilter":"Yes",
        "EmaFilterLength":55,
        "TF":"2min"
    }

    if request.method=='GET' and 'Fast' in request.GET:
        Instrument=request.GET['Instrument']
        startDate=request.GET['StartDate']
        endDate=request.GET['EndDate']

        start=request.GET['StartTime']
        end=request.GET['EndTime']
        start=datetime.strptime(start,'%H:%M:%S')
        end=datetime.strptime(end,'%H:%M:%S')
        start=start.hour*60+start.minute-2
        end=end.hour*60+end.minute

        fast=int(request.GET['Fast'])
        slow=int(request.GET['Slow'])
        targetTicks=int(request.GET['TargetTicks'])
        stopTicks=int(request.GET['StopTicks'])
        minAdx=float(request.GET['MinAdx'])
        maxAdx=float(request.GET['MaxAdx'])
        smaFilter=True if 'UseSMAFilter' in request.GET else False
        smaLen=int(request.GET['SmaFilterLength'])
        emaFilter=True if 'UseEMAFilter' in request.GET else False
        emaLen=int(request.GET['EmaFilterLength'])
        tf=request.GET['TF']


        df=InstrumentChoice(startDate,endDate,tf,Instrument)

        print(df.head())

        bt = Backtest(df,DK_MA_Cloud,cash=100_000)

        stats=bt.run(
            StartTime=start,StopTime=end,Fast=fast,Slow=slow,TargetTicks=targetTicks,StopTicks=stopTicks,
            MinAdx=minAdx,MaxAdx=maxAdx,UseSMAFilter=smaFilter,SmaFilterLength=smaLen,UseEMAFilter=emaFilter,
            EmaFilterLength=emaLen
        )

        removed_stats=stats.drop("_equity_curve")
        removed_stats=removed_stats.drop("_trades")

        
        tradesDict=stats.to_dict()["_trades"]

        pointValue=PointValue(Instrument)

        grossProfit=0
        for pnl in tradesDict['PnL']:
            if float(pnl)>0:
                grossProfit+=float(pnl)*pointValue

        consWinners=0
        consLosers=0
        maxWin=0
        maxLoss=0
        for tr in tradesDict['PnL']:
            if float(tr)>0:
                consWinners+=1
                if consLosers>0:
                    maxLoss+=max(maxLoss,consLosers)-maxLoss
                consLosers-=consLosers
            if float(tr)<0:
                consLosers+=1
                if consWinners>0:
                    maxWin+=max(maxWin,consWinners)-maxWin
                consWinners-=consWinners

        maxLoss+=max(maxLoss,consLosers)-maxLoss
        maxWin+=max(maxWin,consWinners)-maxWin

        #print("GROSS: " + str(grossProfit) )
        #print(removed_stats.to_dict().keys())
        #print(removed_stats.to_dict().values())

        keyList=list(removed_stats.to_dict().keys())
        valueList=list(removed_stats.to_dict().values())
        highlighted_key=[]
        highlighted_value=[]


        #Gross Profit
        highlighted_key.append("Gross Profit")
        highlighted_value.append(grossProfit)
        #Net Profit
        highlighted_key.append("Net Profit")
        highlighted_value.append((int(valueList[4])-100_000)*pointValue)
        #Profit Factor
        highlighted_key.append(keyList[24])
        highlighted_value.append(valueList[24])
        #Sharpe Ratio
        highlighted_key.append(keyList[10])
        highlighted_value.append(valueList[10])
        #Trades number
        highlighted_key.append(keyList[17])
        highlighted_value.append(valueList[17])
        #Cons Winners
        highlighted_key.append("Cons Winners")
        highlighted_value.append(maxWin)
        #Cons Losers
        highlighted_key.append("Cons Losers")
        highlighted_value.append(maxLoss)
        #Win Rate
        highlighted_key.append(keyList[18])
        highlighted_value.append(valueList[18])
        #Average Trade
        highlighted_key.append("Avg Trade")
        highlighted_value.append(float(valueList[21])*100*pointValue )



        trades_df=pd.DataFrame(data=tradesDict)

        for idx in range(0,trades_df['Size'].count()):
            if int(trades_df['Size'][idx])>0:
                trades_df['Size'][idx]="Long"
            else:
                trades_df['Size'][idx]="Short"

        return render(request,"bt/dkmacloud.html",{'trades':trades_df.to_html(),"stats":removed_stats.to_frame().to_html(),"form":request.GET,"hl_keys":highlighted_key,"hl_values":highlighted_value,"inst":Instrument})

    return render(request,"bt/dkmacloud.html",{"form":inputs})



def InstrumentChoice(startDate,endDate,tf,choice):
    #ES-0 MES-1 NQ-2 MNQ-3
    data = [pd.read_csv("static/media/ES.csv"),pd.read_csv("static/media/MES.csv"),pd.read_csv("static/media/NQ.csv"),pd.read_csv("static/media/MNQ.csv")]
    data[0]['timestamp']=pd.to_datetime(data[0]['timestamp'])-timedelta(hours=4,minutes=1)
    data[1]['timestamp']=pd.to_datetime(data[1]['timestamp'])-timedelta(hours=4,minutes=1)
    data[2]['timestamp']=pd.to_datetime(data[2]['timestamp'])-timedelta(hours=4,minutes=1)
    data[3]['timestamp']=pd.to_datetime(data[3]['timestamp'])-timedelta(hours=4,minutes=1)
    data[0] = data[0].set_index('timestamp')
    data[1] = data[1].set_index('timestamp')
    data[2] = data[2].set_index('timestamp')
    data[3] = data[3].set_index('timestamp')

    df_ES=data[0].resample(tf).agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last','Volume':'sum'})
    df_ES=df_ES.loc[(startDate+' 00:00:00'):(endDate+' 23:00:00')]
    df_ES=df_ES.dropna()
    df_MES=data[1].resample(tf).agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last','Volume':'sum'})
    df_MES=df_MES.loc[(startDate+' 00:00:00'):(endDate+' 23:00:00')]
    df_MES=df_MES.dropna()
    df_NQ=data[2].resample(tf).agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last','Volume':'sum'})
    df_NQ=df_NQ.loc[(startDate+' 00:00:00'):(endDate+' 23:00:00')]
    df_NQ=df_NQ.dropna()
    df_MNQ=data[3].resample(tf).agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last','Volume':'sum'})
    df_MNQ=df_MNQ.loc[(startDate+' 00:00:00'):(endDate+' 23:00:00')]
    df_MNQ=df_MNQ.dropna()

    if choice=="0":
        return df_ES
    if choice=="1":
        return df_MES
    if choice=="2":
        return df_NQ
    if choice=="3":
        return df_MNQ


def PointValue(choice):
    if choice=="0":
        return 50
    if choice=="1":
        return 5
    if choice=="2":
        return 20
    if choice=="3":
        return 2




def homePage(request):
    
    return render(request,"bt/home.html")


def testing(request):
    html_content = open("profitpal.html")
    return HttpResponse(html_content)