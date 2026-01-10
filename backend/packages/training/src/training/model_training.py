import os
from datetime import date
from xgboost import XGBRegressor

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from data_pipeline import create_X_Y_df

def train_and_save_model(from_station:str, to_station:str, start_date:date, end_date:date):
    df_X, df_y = create_X_Y_df(from_station, to_station, start_date, end_date)

    print(df_X.dtypes)
    print(df_X.head())
    print(df_y.dtypes)
    print(df_y.head())
    
    model = XGBRegressor()

    x_train, x_test, y_train, y_test = train_test_split(df_X, df_y, test_size=0.1)

    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    print("MSE:", mean_squared_error(y_test, y_pred))
    
    root_dir = os.environ.get("ROOT_DIR", ".")
    model.get_booster().save_model(f"{root_dir}/models/{from_station}_{to_station}_xgb_model.json")

def load_model(from_station:str, to_station:str) -> XGBRegressor:
    root_dir = os.environ.get("ROOT_DIR", ".")
    model = XGBRegressor()
    model.load_model(f"{root_dir}/models/{from_station}_{to_station}_xgb_model.json")
    return model

train_and_save_model("Bergshamra", "Kungshamra", date(2024,6,15), date(2024,6,15))
