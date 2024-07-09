import mplfinance as mpf
import matplotlib.pyplot as plt
import numpy as np
from utils import LOGGER
import os
class display:

    def __init__(self,stock,indicators=[],signals={'buy':[],'sell':[]},peaks={},divergence=[],format='raw',save_path=None,save_name=None,signal_plot=None):
        self.added_plots=[] ##dict of pannel
        self.indicators=indicators
        self.signals=signals
        self.peaks=peaks
        self.divergence=divergence
        self.save_path=save_path
        self.save_name=save_name
        self.stock=stock
        self.signal_plot=signal_plot
        self.panel_counter=0

        self.add_indicators()

        if len(divergence)!=0:
            self.add_divergence()

        if len(peaks)!=0:
            self.add_peaks()

        self.add_signal_plot()

        #a réactiver
        ##add arrows corresponding to signals  
        
        if not self.signals['buy'].isnull().all():  
            buy_arrows = mpf.make_addplot(self.signals['buy'], scatter=True,markersize=300,marker=r'$\Uparrow$',color='green')
            self.added_plots.append(buy_arrows)

        if not self.signals['sell'].isnull().all():  
            sell_arrows = mpf.make_addplot(self.signals['sell'], scatter=True,markersize=300,marker=r'$\Downarrow$',color= (0.7, 0, 0))
            self.added_plots.append(sell_arrows)

        self.display_chart(format)

    def display_chart(self,format):
        # Plot the closing price
        if format=='raw':
            mpf.plot(self.stock,type='candle')
        else:
            idx_to_keep=[]
            ##Discard extra plots that are empty
            for i,temp in enumerate(self.added_plots):
                if temp['data'].isnull().all():
                    LOGGER.warning("Couldn't print the plot because there is no data")
                else:
                    idx_to_keep.append(i)
            self.added_plots=[self.added_plots[i] for i in idx_to_keep]
            if self.save_path in [None,False] or self.save_name in [None,False] :
                mpf.plot(self.stock,addplot=self.added_plots,type='candle')
            else:
                #save_config=dict(fname=os.path.join(self.save_path,self.save_name),dpi=200,pad_inches=0.25)
                #mpf.plot(self.stock,addplot=self.added_plots,type='candle',savefig=save_config)
                L_chart_size=self.stock.shape[0]//100*2  if   self.stock.shape[0]//100*2>=8  else 8  ##to display the chart with a good size
                l_chart_size=L_chart_size//2 if   L_chart_size//2>=6  else 6#
                fig1, _ = mpf.plot(self.stock,addplot=self.added_plots,type='candle', figsize =(L_chart_size,l_chart_size),returnfig=True)
                fig1.savefig(os.path.join(self.save_path,self.save_name),dpi=200)

           
    def add_indicators(self):
        
         for indicator in self.indicators.indicators:
             indicator_name=indicator.__class__.__name__
             data=self.indicators.data[indicator_name]
             if indicator.coefficient !=0:    ##if it has no impact on signals no need to plot it
                if indicator.type=='oscillator':
                    self.panel_counter=self.panel_counter+1
                    self.add_oscillators(data,indicator_name,self.panel_counter)
                elif indicator.type=='bands':
                    self.add_bands(data,indicator_name)

    def add_oscillators(self,data,indicator_name,panel_counter):
        #for i,(indicator_name,val) in enumerate(self.indicators.items()):
        oscillator_plot=mpf.make_addplot(data[indicator_name],panel=panel_counter,label=indicator_name)
        self.added_plots.append(oscillator_plot)

    def add_bands(self,data,indicator_name):
        for column in data.columns:
            band_plot=mpf.make_addplot(data[column],panel=0,label=indicator_name,color='blue')
            self.added_plots.append(band_plot)



    def add_divergence(self):
        for i,divergence_list in enumerate(self.divergence.values()):
            ##self.divergence is composed of two df : 'high' and 'low'
            for div in divergence_list:
                bar_plot = mpf.make_addplot(div,color='red',panel=i)
                self.added_plots.append(bar_plot)

    def add_peaks(self):  
        for idx_panel,panel in enumerate(self.peaks):
            for key, values in panel.items():
                ##circles
                peak = mpf.make_addplot(values, scatter=True,markersize=300,edgecolors='green',color='none',panel=idx_panel)
                self.added_plots.append(peak)


    def add_signal_plot(self):
        self.panel_counter=self.panel_counter+1
        peak = mpf.make_addplot(self.signal_plot,panel=self.panel_counter,color='blue',label='signal')
        self.added_plots.append(peak)

    

