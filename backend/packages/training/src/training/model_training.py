import os
from datetime import date
from xgboost import XGBRegressor

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from data_pipeline import create_X_Y_df

def train_and_save_model(from_station:str, to_station:str, start_date:date, end_date:date, test_start_date:date, test_end_date:date):
    x_train, y_train = create_X_Y_df(from_station, to_station, start_date, end_date)
    
    model = XGBRegressor()

    model.fit(x_train, y_train)

    x_test, y_test = create_X_Y_df(from_station, to_station, test_start_date, test_end_date)

    y_pred = model.predict(x_test)
    print("MSE:", mean_squared_error(y_test, y_pred))
    
    root_dir = os.environ.get("ROOT_DIR", ".")
    model.get_booster().save_model(f"{root_dir}/models/{from_station}_{to_station}_xgb_model.json")

def load_model(from_station:str, to_station:str) -> XGBRegressor:
    root_dir = os.environ.get("ROOT_DIR", ".")
    model = XGBRegressor()
    model.load_model(f"{root_dir}/models/{from_station}_{to_station}_xgb_model.json")
    return model

if __name__ == "__main__":

    print("Starting model training")
    train_and_save_model("Bergshamra", "Kungshamra", date(2024,6,15), date(2024,6,17), date(2024,6,18), date(2024,6,18))
    # dfx, dfy = create_X_Y_df("Bergshamra", "Kungshamra", date(2024,6,15), date(2024,6,16))
    # print(dfx.dtypes)
    # print(dfx.head())
    # dfx.to_csv("tmp.csv")
