from xgboost import XGBRegressor

import pandas as pd
from sklearn.model_selection import train_test_split
from data_pipeline import create_X_Y_df

def train_and_save_model(from_station:str, to_station:str):
    df_X, df_y = create_X_Y_df(from_station, to_station)

    model = XGBRegressor(enable_categorical=True, tree_method="hist")

    
