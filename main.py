from utils import process
import yaml
import copy 

with open('config.yaml','r') as f:
   MAIN_CONFIG=yaml.safe_load(f)




def simulation():
   trader.buy(cad_stock,cad_stock().index[0],1)
   trader.sell(cad_stock,cad_stock().index[4])

   trader.buy(cad_stock,cad_stock().index[6],'max')
   trader.sell(cad_stock,cad_stock().index[8])

   profit= trader.compute_profit()
   trader.print_history()

def EMA(stock):
        stock=copy.deepcopy(stock)
        from talib import abstract
        stock_data=stock.data.rename(columns={"Close": "close"}) ##talib requirement
        EMA_stock=abstract.EMA(stock_data,3)
        stock.data['Close']=EMA_stock
        return stock

if __name__=='__main__':
  

   profit_list=[]
   for stock_name in MAIN_CONFIG['Stocks']['tickers']:
      config=copy.deepcopy(MAIN_CONFIG)
      cad_stock=process.Stocks(stock_name,**MAIN_CONFIG)

      trader=process.Trader(**MAIN_CONFIG)


      peaks=trader.indicators.get_all_peaks(cad_stock)
      
      signals,divergence_plot=trader.compute_signals(cad_stock)
      filtered_peaks=trader.indicators.filter_peaks_from_signal(peaks,signals['RSI'])
      merged_signals,signal_plot=trader.merge_signals(cad_stock(),signals)
      trader.buy_at_signals(cad_stock,merged_signals,volume={'buy':MAIN_CONFIG['Trader']['buy'],
                                                      'sell':MAIN_CONFIG['Trader']['sell']})
      profit=trader.compute_profit()
      
      profit_list.append(profit)
      
      trader.display_chart(cad_stock(),
                           format='all',
                           peaks=filtered_peaks,
                           signals=merged_signals,
                           indicators=trader.indicators,
                           divergence=divergence_plot,
                           save_path='.',
                           save_name='temp.png',
                           signal_plot=signal_plot)
      trader.print_history()
   
   profit=sum(profit_list)
   print(f' profit {profit} ({(1+profit/5000)*100})')
   