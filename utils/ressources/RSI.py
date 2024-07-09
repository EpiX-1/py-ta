import pandas as pd
from talib import abstract

class RSI():
    def __init__(self,**kwargs):
        self.type='oscillator'
        for key, value in kwargs.items():
            setattr(self, key, value)
        if not isinstance(self.period,int):
            self.period=int(self.period)

    def __call__(self,stock)->pd.DataFrame:
        
        stock=stock.rename(columns={"Close": "close"}) ##talib requirement
        if len(stock.index)<self.period+1:
            return None
        rsi = abstract.RSI(stock,self.period)
       # print(rsi.iloc[-1:])
        #rsi=rsi.rename("Close") ##talib requirement
        rsi=pd.DataFrame(rsi,index=stock.index, columns=['RSI'])
        return rsi