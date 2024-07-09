import numpy as np
import pandas as pd
import copy
from scipy.signal import find_peaks
import importlib


class indicators():

    def __init__(self,distance,prominence,indicators):
        self.indicators=[]
        self.distance=distance
        self.prominence=prominence
        self.data=None
        for indicator_name,args in indicators.items():
            indicator_module=importlib.import_module('utils.ressources.'+indicator_name)
            indicator_class=getattr(indicator_module, indicator_name)  ##access to class name
            indicator_class=indicator_class(**args)
            self.indicators.append(indicator_class)
        self.signals=[]
    
    def apply_to_whole_chart(self,stock) ->dict:  ##return dict composed of indicator and value
        result_list=[]
      
       
        ##compute indicators for the whole chart
        for indicator in self.indicators:
            indicator_val=indicator(stock()) 
            result_list.append(indicator_val)

        indicators_name=[d.__class__.__name__ for d in self.indicators]
        self.data=dict(zip(indicators_name,result_list))
        return self.data
    
    
    
    def find_spikes(self,stock_OG)->tuple[pd.DataFrame,pd.DataFrame]:  ##return df with index composed of nan values and stock price values
        ##find higher peaks
       
        stock=copy.deepcopy(stock_OG)
        peaks_idx=find_peaks(stock['Close'],distance=self.distance,prominence=self.prominence)[0]
        #stock.index.isin(stock.iloc[peaks_idx].index)   
        stock[~stock.index.isin(stock.iloc[peaks_idx].index)]=np.nan
        higher_peaks=stock['Close']

        ##find lower peaks
        stock=copy.deepcopy(stock_OG)
        peaks_idx=find_peaks(-1*stock['Close'],distance=self.distance,prominence=self.prominence)[0]
        #stock.index.isin(stock.iloc[peaks_idx].index)   
        stock[~stock.index.isin(stock.iloc[peaks_idx].index)]=np.nan
        lower_peaks=stock['Close']
    
        ##ajouter la dernière valeur en tant que pic
        if sum(1 for x in stock_OG.iloc[-(self.distance+1):]['Close'].diff() if x >0) > sum(1 for x in stock_OG.iloc[-(self.distance+1):]['Close'].diff() if x <0):
            higher_peaks.iloc[-1]=stock_OG['Close'].iloc[-1]
        else:
            lower_peaks.iloc[-1]=stock_OG['Close'].iloc[-1]


        return higher_peaks,lower_peaks
       
    def find_corresponding_peak(self,peaks:pd.Series,oscillator_val:pd.Series)-> pd.Series:
        copy_val=copy.deepcopy(peaks)
        oscillator_values=copy.deepcopy(oscillator_val)
        mask=pd.notna(copy_val)
        oscillator_values[~mask]=np.nan

        return oscillator_values
     


    def get_all_peaks(self,stock)->list[dict]: 
        high_stock_peaks,low_stock_peaks=self.find_spikes(stock())
        stock_peaks={'high':high_stock_peaks,'low':low_stock_peaks}
        peaks_list=[stock_peaks]
        for indicator in [i for i in self.indicators if i.type=='oscillator']:
            indicator_name=indicator.__class__.__name__
            oscilattor_val=indicator(stock())[indicator_name]
            oscillator_peaks={'high':self.find_corresponding_peak(high_stock_peaks,oscilattor_val),
                              'low':self.find_corresponding_peak(low_stock_peaks,oscilattor_val)}
            peaks_list.append(oscillator_peaks)
        return peaks_list
    
    def filter_peaks_from_signal(self,peaks:list[dict],signal:pd.DataFrame)->list[dict]:
        filtered_peaks=copy.deepcopy(peaks)
        signal_cp=copy.deepcopy(signal)
        signal_cp=signal_cp['buy'].combine_first(signal_cp['sell'])
        for peak in filtered_peaks:
            mask=pd.notna(signal_cp)
            for val in peak.values():
                val[~mask]=np.nan
        return filtered_peaks

    def compute_divergence(self,stock:pd.DataFrame,oscillator_val:pd.Series) -> tuple[pd.DataFrame,list[pd.Series]]: ##signals
        high_stock_peaks,low_stock_peaks=self.find_spikes(stock)
        stock_peaks={'high':high_stock_peaks,'low':low_stock_peaks}

        signals={'buy':[],'sell':[]}
     
        bars={'stock':[],'oscillator':[]}
        for peak in stock_peaks.values():

            ##compute sign of derivative
            copy_val=copy.deepcopy(stock['Close'])
            mask=pd.notna(peak)
            ##... for stock
            diff=-copy_val[mask].diff(-1)
            diff[:]=np.where(diff>0,1,-1)   ##mask of 1 and -1
            copy_val[mask]=diff
            copy_val[~mask]=np.nan
            sign_stock=copy_val.ffill()

            ##... for oscillator 
            oscillator_values=copy.deepcopy(oscillator_val)
            diff=-oscillator_values[mask].diff(-1)
            diff[:]=np.where(diff>0,1,-1)   ##mask of 1 and -1
            oscillator_values[mask]=diff
            oscillator_values[~mask]=np.nan
            sign_oscillator=oscillator_values.ffill()
            
            ##Computing diff between sings
           

            diff_sign=sign_stock.sub(sign_oscillator,axis=0)


            mask=pd.notna(peak)
            shifted = diff_sign.shift(1)

            peak_index=diff_sign[mask]
            peak_index_minus_one=shifted[mask]
            l1=[]
            l2=[]
            for idx in (peak_index.index):
                if (peak_index.loc[idx] in [-2,0,2]) and (peak_index_minus_one.loc[idx] in [-2,2]):
                    if peak_index_minus_one.loc[idx]==-2:
                        ##buy signal
                        l1.append(idx)
                    elif peak_index_minus_one.loc[idx]==2:
                        ##sell signal
                        l2.append(idx)

            buy_signals=copy.deepcopy(stock['Close'])
            mask = ~buy_signals.index.isin(l1)
            buy_signals.loc[mask] = np.nan
            signals['buy'].append(buy_signals)

            sell_signals=copy.deepcopy(stock['Close'])
            #sell_signals.loc[l2]=np.nan
            mask = ~sell_signals.index.isin(l2)
            sell_signals.loc[mask] = np.nan
            signals['sell'].append(sell_signals)

           
            ##compute divergence bars
            ##stock
            stock_cp=copy.deepcopy(stock['Close'])
            stock_cp=peak.interpolate(method='linear')
            mask=diff_sign.isin([2,-2])    
            stock_cp[~mask]=np.nan
            bars['stock'].append(stock_cp)
           

            ##oscillator
            copy_val=copy.deepcopy(peak)
            mask=pd.notna(copy_val)
            oscillator_values=copy.deepcopy(oscillator_val)
            oscillator_values[~mask]=np.nan
            stock_cp=oscillator_values.interpolate(method='linear')
            mask=diff_sign.isin([2,-2])
            stock_cp[~mask]=np.nan
            bars['oscillator'].append(stock_cp)
         
           
        ##concatenating buy and sells signals
       
        for key,signal in signals.items():
            combined=signal[0]
            for i in range(1,len(signal)):
                combined=combined.combine_first(signal[i])
            signals[key]=combined

        signals_df=pd.DataFrame(index=list(stock.index))
        signals_df= signals_df.assign(buy=signals['buy'])
        signals_df= signals_df.assign(sell=signals['sell'])
        return signals_df,bars   
    

    def compute_difference(self,stock:pd.DataFrame,indicator_val:pd.DataFrame) -> pd.DataFrame: ##signals
        signals={'buy':[],'sell':[]}

        ##sell signal
        stock_cp=copy.deepcopy(stock['Close'])
        high_diff=indicator_val['upper_band']-stock_cp
        shifted=high_diff.shift(1)
        #buy_mask=high_diff[(high_diff >= 0) & (shifted < 0)]
        sell_mask=(high_diff >= 0) & (shifted < 0)
        stock_cp[~sell_mask]=np.nan
        signals['sell'].append(stock_cp)
        
        ##sell signal
        stock_cp=copy.deepcopy(stock['Close'])
        low_diff=indicator_val['lower_band']-stock_cp
        shifted=low_diff.shift(1)
        buy_mask=(low_diff <= 0) & (shifted > 0)
        stock_cp[~buy_mask]=np.nan
        signals['buy'].append(stock_cp)
        
        for key,signal in signals.items():
            combined=signal[0]
            for i in range(1,len(signal)):
                combined=combined.combine_first(signal[i])
            signals[key]=combined

        signals_df=pd.DataFrame(index=list(stock.index))
        signals_df= signals_df.assign(buy=signals['buy'])
        signals_df= signals_df.assign(sell=signals['sell'])
        return signals_df   


