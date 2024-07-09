from ray.tune import Tuner
from utils import process
from pathlib import Path
from glob import glob
import os
import copy 
from ray import tune
from ray.tune.search.bayesopt import BayesOptSearch

class custom_Tuner(Tuner):
    
    def __init__(self,config,tune_config=None):
        self.config=config
        tune_config_cp=copy.deepcopy(tune_config)

        if 'ressources' in tune_config.keys():
            tune_config_cp.pop('ressources') ##there is no ressource argument in TuneConfig
        else:
            tune_config['ressources']={}
        tune_config_cp['search_alg']=BayesOptSearch(utility_kwargs={"kappa":2.5},metric="profit", mode="max")

        self.stock_list=[]
        for stock_name in self.config['Stocks']['tickers']:
            self.stock_list.append(process.Stocks(stock_name,**self.config))

        self.tuner_config=tune.TuneConfig(**tune_config_cp)
        self.__results=None
        trainable_with_resources=tune.with_resources(self.run_simulation, tune_config['ressources'])
        trainable_with_parameters=tune.with_parameters(trainable_with_resources, data=self.stock_list)
        super().__init__(trainable_with_parameters, param_space=self.config,tune_config=self.tuner_config) 

    def __call__(self):
       self.__results = self.fit()
       return self.__results
    
  

    def get_best_run(self):
        best_score=self.results.get_best_result(metric="profit", mode="max").metrics['profit']
        best_config=self.results.get_best_result(metric="profit", mode="max").config

        result_grid=self.results.get_dataframe(filter_metric="profit", filter_mode="max")
        dir_path=self.create_new_folder('run')
        self.create_csv_table(result_grid,dir_path)
        
        ##save chart for each stocks with best config
        for stock in self.stock_list:
            trader=process.Trader(**best_config)
            peaks=trader.indicators.get_all_peaks(stock)
            signals,divergence_plot=trader.compute_signals(stock)
            filtered_peaks=trader.indicators.filter_peaks_from_signal(peaks,signals['RSI'])
            merged_signals,signal_plot=trader.merge_signals(stock(),signals)
            trader.display_chart(stock(),
                                 format='all',
                                 peaks=filtered_peaks,
                                 signals=merged_signals,
                                 indicators=trader.indicators,
                                 divergence=divergence_plot,
                                 save_path=dir_path,
                                 save_name=stock.name+'.png',
                                 signal_plot=signal_plot)
        return best_config,best_score
    
    def create_new_folder(self,name,base_dir='./runs/'):
        dir_path=Path(base_dir+name)
        l1=glob(base_dir+'*/')
        if len(l1)!=0:
            dir_path=Path(os.path.join(dir_path.parent, dir_path.name+'_'+str(len(l1))))
        dir_path.mkdir(parents=True)
        return dir_path

    def create_csv_table(self,result_grid,dir_path):
        relevant_columns = [
            "profit","date",
        ]
        relevant_columns=relevant_columns+[i for i in result_grid.columns if 'config' in i]
        # Save the DataFrame to a CSV file
        result_grid[relevant_columns].to_csv(os.path.join(dir_path,'table.csv'), index=False)
   

    @property
    def results(self):
        if self.__results is None:
            self()
        return self.__results
        
    @staticmethod
    def run_simulation(config,data):
        final_result={}
        profit_list=[]
        for stock in data:
            trader=process.Trader(**config)
            indicators=trader.compute_indicators(stock)
            peaks=trader.indicators.get_all_peaks(stock)
            signals,divergence_plot=trader.compute_signals(stock)
            merged_signals,_=trader.merge_signals(stock(),signals)
            trader.buy_at_signals(stock,merged_signals,volume={'buy':config['Trader']['buy'],'sell':config['Trader']['sell']})
            profit=trader.compute_profit()
            profit_list.append(profit)
            trader.print_history()
        
            final_result[stock.name]={"profit": profit,"peaks":peaks,"signals":merged_signals,"indicators":indicators,"divergence_plot":divergence_plot}
        
        final_result['profit']=sum(profit_list)/len(profit_list)
        return final_result
