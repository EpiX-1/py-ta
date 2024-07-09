from ray import tune
import yaml
from utils.color import color
from utils.tuner import custom_Tuner
import numpy as np

with open('config.yaml','r') as f:
   MAIN_CONFIG=yaml.safe_load(f)



def override_config(config, search_space):
  
    if not isinstance(config, dict) or not isinstance(search_space, dict):
        return search_space

    overridden_config = config.copy()
    for key, value in search_space.items():
        if key in overridden_config and isinstance(overridden_config[key], dict):
            overridden_config[key] = override_config(overridden_config[key], value)
        else:
            overridden_config[key] = value

    return overridden_config

if __name__=='__main__':
   
    search_space = {
    "Trader": {
        "indicators": {
              "RSI":{
                "coefficient":tune.uniform(0.1,10),
                "period":tune.uniform(5,40),
            },
            "Keltner": {
                "alpha": tune.uniform(1,10),  # Modify the range as needed,
                "period": tune.uniform(5,40),
                "coefficient":tune.uniform(0.1,10),
 
            },
          
        },
        'buy':tune.uniform(1,100)
    },
    "Signals":{
        "std":tune.uniform(0.1,50),
        "range_gaussian":tune.uniform(20,250),
    }
}
    import ray
    ray.init(log_to_driver=False)
    filtered_config=override_config(MAIN_CONFIG,search_space)
    tuner=custom_Tuner(filtered_config,tune_config=filtered_config['Tuner'])
  
    best_config,best_score=tuner.get_best_run()
    if best_score<0:
        print(f'Best score {color.RED}{best_score}{color.RESET} obtained for {color.BLUE}{best_config}{color.RESET}')
    else:
         print(f'Best score {color.GREEN}{best_score}{color.RESET} obtained for {color.BLUE}{best_config}{color.RESET}')

