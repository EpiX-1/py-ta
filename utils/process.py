from copy import deepcopy
from utils import LOGGER 
import yfinance as yf
from typing import Union
import pandas as pd
from utils.indicators import indicators
import copy
from utils.color import color
from utils.graphics import  display
from scipy.stats import norm
from scipy.signal import find_peaks
import numpy as np

class Stocks:

    def __init__(self,name,**kwargs):
        self.name=name
        self.param=copy.deepcopy(kwargs['Stocks'])
        
        if isinstance(self.param['tickers'],list) and len(self.param['tickers'])>1:
            self.param['tickers']=self.name
        
        try:
            self.data=yf.download(**self.param)
        except:
            print('Failing to retrieve data')
      
        
    def __call__(self):
        return self.data

class Trader:

    def __init__(self,**kwargs):
        self.config=kwargs['Trader']
        self.signal_config=kwargs['Signals']
        self.begin_account=self.config['starting_budget']

        self.total_account=deepcopy(self.begin_account)   ##1000 cad
        self.nb_sale=0
        self.nb_buy=0
        self.own_stocks=[]
        self.own_volumes={}   ##{'stock_name':own_volume}
        self.transactions_history=[]
        self.indicators=indicators(self.config['distance'],self.config['prominence'],self.config['indicators'])

    def buy(self,stock,date_buy,volume:Union[int, str]):
        stock_price=stock().at[date_buy,'Close'].item()  
        if volume=='max':
            volume=self.total_account // stock_price
        order=stock_price*volume
        if self.check_remaining_funds(order,date_buy):
            self.nb_buy=self.nb_buy+1

            transaction={'type':'buy',
                         'stock':stock.name,
                         'date':date_buy,
                         'volume':volume,
                         'price_at_transaction_time':stock_price,
                         'money_involved':order,
                         'funds_before_transaction':self.total_account,
                         'funds_after_transaction':self.total_account-order}
            LOGGER.info('BUY',transaction)

            ##create new volume if it's a new stock
            if stock.name not in self.own_volumes:
                self.own_volumes[stock.name]=0

            ##updating own volumes/stocks
            self.own_volumes[stock.name]=self.own_volumes[stock.name]+volume
            self.own_stocks.append(transaction)
            self.add_transaction(transaction)
            self.total_account=self.total_account-order

    def check_remaining_volume(self,stock,volume_order):
        ##verifying that we own enough volume of the stock to sell it 
        if stock.name in [d['stock'] for d in self.own_stocks]:
            if type(volume_order)==str:  ##means max
                return 1
            if self.own_volumes[stock.name]>=volume_order:
                return 1
        return 0

    def add_transaction(self,transaction):
         ##to add transaction to history
        self.transactions_history.append(transaction)

    def sell(self,stock,date_sale,volume):
        ##check transaction
        if self.check_remaining_volume(stock,volume)==0:
            LOGGER.warning(f"Couldn't sell at {color.YELLOW}{date_sale}{color.RESET} because there isn't enough owned volume !")
            return 

        self.nb_sale=self.nb_sale+1

        #retrieve stock from own stock list 
        own_stock = [transaction for transaction in self.own_stocks if transaction['type'] == 'buy' and transaction['stock'] == stock.name]  ##older

       
        stock_to_sell,self.own_stocks,new_volume=self.find_stock_to_sell(own_stock,volume)
        self.own_volumes[stock.name]=new_volume
       

        for selling_stock in stock_to_sell:
            buy_money=selling_stock['money_involved']
            volume_stock=selling_stock['volume']
            sale_price=stock().at[date_sale,'Close'].item() 
            
            money_involved=sale_price*selling_stock['volume']
            transaction={'type':'sell',
                         'stock':stock.name,
                         'date':date_sale,
                         'volume':volume_stock,
                         'price_at_transaction_time':sale_price,
                         'money_involved':money_involved,
                         'date_of_buy':selling_stock['date'],
                         'funds_before_transaction':self.total_account,
                         'funds_after_transaction':self.total_account+money_involved,
                         }
            
            self.add_transaction(transaction)

            money_made=money_involved-buy_money
            
            self.total_account=self.total_account+money_involved
            LOGGER.info('SELL',transaction)
            
            LOGGER.info('TRANSACTION',money_made)   ##custom en vert quand c'est positif ou en rouge sinon
        
    def find_stock_to_sell(self,own_stock_list:list[dict],volume_order:Union[str,int])->tuple[list[dict],list[dict],int]:
        ##find stock to sells from the stock list and return the new own stock list and the stock to sell
        if volume_order=='max':
            stock_to_sell=copy.deepcopy(own_stock_list)
            remaining_stocks=[]
        else:
            remaining_stocks=copy.deepcopy(own_stock_list)
            stock_to_sell=[]
            sum_volume=volume_order
            for idx,stock in enumerate(own_stock_list):
                if sum_volume-stock['volume']<0:
                    new_stock=copy.deepcopy(stock)
                    unsold_volume=stock['volume']-sum_volume 
                  
                    new_stock['volume']=sum_volume
                    stock_to_sell.append(new_stock)

                    ##updating old stock
                    idx_splitted_stock=remaining_stocks.index(stock)
                    remaining_stocks[idx_splitted_stock]['volume']=unsold_volume
                    
                    break
                elif sum_volume-stock['volume']==0:
                    idx=idx+1
                    break
                sum_volume=sum_volume-stock['volume']
            stock_to_sell=own_stock_list[:idx]+stock_to_sell
            remaining_stocks=remaining_stocks[idx:]

        remaining_volume=sum([d['volume'] for d in remaining_stocks])

        return stock_to_sell,remaining_stocks,remaining_volume
    
    def merge_signals(self,stock:pd.DataFrame,signals_OG:dict[pd.DataFrame])->tuple[dict[pd.Series,pd.Series],pd.DataFrame]:
        ##function where we can normalize according to the signals
        signals=copy.deepcopy(signals_OG)
        merged_signals={'buy':[],
                        'sell':[]}
        
        
        std_dev = self.signal_config['std']
        range_gaussian=self.signal_config['range_gaussian']
        if not isinstance(range_gaussian,int):
            range_gaussian=int(range_gaussian)
        
        ##replace signal by gaussians
        for indicator in self.indicators.indicators:
            indicator_name=indicator.__class__.__name__
            ##generating gaussians values
            for operation_name in ['buy','sell']:
                df=signals[indicator_name][operation_name]
                mask = pd.notna(df)
                timestamps=df[mask].index
                df.loc[:]=0
                for idx in [df.index.get_loc(timestamps[i]) for i in range(len(timestamps))]:
                    left_bound=-range_gaussian//2+idx
                    right_bound=range_gaussian//2+(idx)
                    mean=(right_bound+left_bound)//2
                    if left_bound<0:
                        right_bound=right_bound-(left_bound)  ##bug with this cause we are shifting the mean of linespace
                        left_bound=0
                    elif (right_bound+1)>len(df):
                        left_bound=left_bound-((right_bound+1)-len(df))  #bug with this cause we are shifting the mean of linespace
                        right_bound=len(df)-1
                    nb_values=(right_bound-left_bound)+1

                    # if nb_values%2==0:   
                    #     nb_values=nb_values+1
                    x_values = np.linspace(left_bound-mean, right_bound-mean, num=nb_values)  # Adjust range as needed
                    gaussian_values = norm.pdf(x_values, loc=0, scale=std_dev)
                    df.iloc[left_bound:right_bound+1]=df.iloc[left_bound:right_bound+1]+indicator.coefficient*gaussian_values   ##on peut pas faire de l'assignation si on a des pics proches les uns des autres
            
        
            signals[indicator_name]['sell']=-signals[indicator_name]['sell']
            signals[indicator_name]=signals[indicator_name]['buy'].add(signals[indicator_name]['sell'])
        

        ##concat signals from different indicators
        first_key=list(signals.keys())[0]
        indicator_signal=copy.deepcopy(signals[first_key])
        
        for indicator in self.indicators.indicators:
            indicator_name=indicator.__class__.__name__
            if indicator_name==first_key:
                continue
        
            indicator_signal=indicator_signal.add(signals[indicator_name])
    

        ##to get rid of 0 values because it mess with find_peaks
        mask=(indicator_signal==0)
        indicator_signal[mask]=np.nan
        plot_signal=copy.deepcopy(indicator_signal)

        ##find peaks from signals
        distance=self.signal_config['distance']
        height=self.signal_config['height']
        peaks_idx=find_peaks(indicator_signal,distance=distance,height=height)[0] ##only buying peaks
        mask_buy=indicator_signal.index.isin(indicator_signal.iloc[peaks_idx].index)
        peaks_idx=find_peaks(-1*indicator_signal,distance=distance,height=height)[0]
        mask_sell=indicator_signal.index.isin(indicator_signal.iloc[peaks_idx].index)
        final_mask=mask_buy+mask_sell
        indicator_signal[~final_mask]=np.nan

        ##split buy and sell signal according to their sign
        buy_signals=copy.deepcopy(indicator_signal)
        buy_mask=(buy_signals>0)
        buy_signals[~buy_mask]=np.nan
        sell_signals=copy.deepcopy(indicator_signal)
        sell_mask=(sell_signals<0)
        sell_signals[~sell_mask]=np.nan
        ##to update value of signals with value of the stock
        sell_signals[sell_mask]=stock['Close'][sell_mask]
        buy_signals[buy_mask]=stock['Close'][buy_mask]

        merged_signals={'buy':buy_signals,
         'sell':sell_signals}
      
        
        return merged_signals,plot_signal
    
    def buy_at_signals(self,stock,signals_OG:pd.DataFrame,volume:dict[Union[str,int]]):
        #signals=self.merge_signals(stock(),signals_OG)
        signals=copy.deepcopy(signals_OG)
        mask_buy=signals['buy'].notna()
        signals['buy'][mask_buy]=1
                            ##sorting to be sure
        mask_sell=signals['sell'].notna()
     
        signals['sell'][mask_sell]=-1

        operations=pd.concat([signals['buy'][mask_buy],
                   signals['sell'][mask_sell]])
        
        operations=operations.sort_index()
        ##be careful to buy and sell in the order of the chart !

        ##get a series of all actions date and corresponding action : buy=1 and sell=-1
        for date,val in (operations.items()):
            if val==1:
                ##buy 
                self.buy(stock,date,volume=volume['buy'])   ##correct bug when we buy at max
            elif val==-1:
                ##sell
                self.sell(stock,date,volume=volume['sell'])
        ##sell every position to compute profit
        self.sell_all(stock)
       
    def sell_all(self,stock):
        for stock_data in self.own_stocks:
            if stock.name not in [d['stock'] for d in self.own_stocks]:  ##checking update of self.own_stocks in case it has already been updated by the bellow sell command
                break
            stock_name=stock_data['stock']
            date=stock().index[-1]          ##getting last timestamp of the stock
            LOGGER.info(f"Selling remaining position to compute profit : {color.LIGHT_BLUE}{stock_name}{color.RESET}")
            self.sell(stock,date,volume='max')

    def check_remaining_funds(self,order,date):
        if self.total_account<order:
            LOGGER.warning(f"Can't buy at {color.YELLOW}{date}{color.RESET}  because your unsolvable: remaining funds ({self.total_account}) < order ({order})")
            return 0
        elif order==0:
            LOGGER.warning(f"Can't buy at {color.YELLOW}{date}{color.RESET}  because your unsolvable: order_volume={order}")
            return 0
        else:
            return 1


    ## HIGH API commands

    def print_history(self):
        print(self.transactions_history_table)

    def compute_indicators(self,stock):   ##a mettre dans une autre classe ?
        ##raw stock
        return self.indicators.apply_to_whole_chart(stock)
       
    def compute_peaks(self,stock):
        peaks=self.indicators.find_spikes(stock)
        return peaks
    
    def compute_signals(self,stock) ->tuple[dict,dict[pd.Series,pd.Series]]:   
        ##raw stock
        indicators_val=self.compute_indicators(stock)
        result_list={}
        for indicator in self.indicators.indicators:
            indicator_name=indicator.__class__.__name__
            if indicator.type=='oscillator':
                result,divergence_bars=self.indicators.compute_divergence(stock(),indicators_val[indicator_name][indicator_name])
            elif indicator.type=='bands':
                result=self.indicators.compute_difference(stock(),indicators_val[indicator_name])   ##change
            result_list[indicator_name]=result
        return result_list,divergence_bars
    
    def compute_profit(self):
        final_profit=self.total_account-self.begin_account 
        percentage_final_profit=(self.total_account-self.begin_account)/self.begin_account*100

        print('')
        print('')
        LOGGER.info('--------Computing profit---------')
        
        if final_profit>0:
            display_color=color.GREEN
        else:
            display_color=color.RED
        LOGGER.info(f'Profit made: {display_color}{final_profit}{color.RESET} $ ({display_color}{percentage_final_profit}{color.RESET} %) starting with {color.LIGHT_BLUE}{self.begin_account}{color.RESET}')           
        LOGGER.info('---------------------------------')

        return final_profit
    
    @property
    def transactions_history_table(self):
        transaction_table=pd.DataFrame(self.transactions_history)
        if transaction_table.empty:
            return
        transaction_table.set_index('date', inplace=True)

        ##move important columns at the end of the table
        cols_to_move = ['money_involved','funds_before_transaction', 'funds_after_transaction']
        remaining_cols = [col for col in transaction_table.columns if col not in cols_to_move]
        new_col_order = remaining_cols + cols_to_move
        transaction_table = transaction_table[new_col_order]

        return transaction_table
    
    @staticmethod
    def display_chart(*args,**kwargs):
        display(*args,**kwargs)

    
    
    
