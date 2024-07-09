## Context

This repository can be used to simulate stock market transactions thanks to signals obtained from technical indicators.

## Basic Usage
### Stock analysis

To compute the signals for different indicators you can use the **main.py** file.

Make sure to modify the **config.yaml** file first to select the stock you want to analyze and to specify the values of your hyperparameter.

### Hyperparameter search

This repository is based on [raytune library](https://docs.ray.io/en/latest/tune/index.html) to do hyperparameter search. Be sure to define your searching space first and pass it to the **Custom_Tuner class**. 

Check the file **tune.py** to see an example of hyperparameter tuning.

## Adding new indicators

You can add new indicators by simply creating a python file inside the [resource folder](utils/ressources/). It is important that the name of the new class matches the name of the indicator specified inside the [config file](config.yaml).<br>
Also, make sure that this class contains a **call()** function with the indicator logic. <br> Finally, don't forget to specify what type of indicator it is (ie. *oscillator*, *bands*, ...) or you might encounter issues when plotting the stock and its corresponding signals.

## Installation

1. To install this framework, you'll have to install TA-LIB library first by following their [documentation](https://ta-lib.org/).

2. Then, you can install the python dependencies by using :

        pip install -r requirements.txt


## Troubleshooting 

If you are on Windows, you might not be able to retrieve the results from the hyperparameters search. This issue is not related to this framework but rather with the raytune library that creates folders with too many characters. To avoid this issue, you can [enable the LongPath feature from Windows](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=powershell).

Check this [related issue](https://discuss.ray.io/t/tune-run-ignores-loggers-none-and-fails-on-tbxlogger/927/7).

## Dependencies and license
This project is licensed under the MIT License.

This project relies on other frameworks that may have other license restrictions such as:
- [TA-Lib](https://github.com/TA-Lib/ta-lib)
- [mplfinance](https://github.com/matplotlib/mplfinance?tab=License-1-ov-file#readme)
- [Raytune](https://github.com/TA-Lib/ta-lib)
- [BayesianOptimization](https://github.com/bayesian-optimization/BayesianOptimization)