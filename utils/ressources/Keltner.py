
import pandas as pd
from talib import abstract


class Keltner():
    def __init__(self,**kwargs):
        self.type='bands'
        for key, value in kwargs.items():
            setattr(self, key, value)
        if not isinstance(self.period,int):
            self.period=int(self.period)

    def __call__(self,stock)->pd.DataFrame:
        
        stock=stock.rename(columns={"Close": "close"}) ##talib requirement
        stock=stock.rename(columns={"High": "high"}) ##talib requirement
        stock=stock.rename(columns={"Low": "low"}) ##talib requirement
        if len(stock.index)<self.period+1:
            return None
        atr = abstract.ATR(stock,self.period)
        ema_stock = abstract.EMA(stock, timeperiod=self.period)
        upper_band=ema_stock+self.alpha*atr
        lower_band=ema_stock-self.alpha*atr
        keltner_bands=pd.concat([upper_band,lower_band], keys=["upper_band", "lower_band"],axis=1)
  
        return keltner_bands