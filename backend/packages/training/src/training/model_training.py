import os
from datetime import date
from xgboost import XGBRegressor

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from training.data_pipeline import create_X_Y_df, create_X_Y_df_with_route

def train_and_save_model(from_station:str, to_station:str, start_date:date, end_date:date, test_start_date:date, test_end_date:date):
    x_train, y_train = create_X_Y_df(from_station, to_station, start_date, end_date)
    
    model = XGBRegressor()

    model.fit(x_train, y_train)

    x_test, y_test = create_X_Y_df(from_station, to_station, test_start_date, test_end_date)

    y_pred = model.predict(x_test)
    print("MSE:", mean_squared_error(y_test, y_pred))
    
    root_dir = os.environ.get("ROOT_DIR", ".")
    model.get_booster().save_model(f"{root_dir}/models/{from_station}_{to_station}_xgb_model.json")


def train_and_save_route_model(route_id:str|set[str], start_date:date, end_date:date):
    df_x, df_y = create_X_Y_df_with_route(route_id, start_date, end_date)
    
    x_train, x_test, y_train, y_test = train_test_split(df_x, df_y, test_size=0.1)

    # print(x_train.dtypes)
    # print(x_train.head())
    # print(x_train.max())
    # print(x_train.mean())
    # print(x_train.min())

    model = XGBRegressor()

    model.fit(x_train, y_train)

    #x_test, y_test = create_X_Y_df_with_route(route_id, test_start_date, test_end_date)

    # print(x_test.dtypes)
    # print(x_test.head())
    # print(x_test.max())
    # print(x_test.min())

    y_pred = model.predict(x_test)
    print("MSE:", mean_squared_error(y_test, y_pred))
    
    root_dir = os.environ.get("ROOT_DIR", ".")
    model.get_booster().save_model(f"{root_dir}/models/{route_id}_xgb_model.json")


def load_model(from_station:str, to_station:str) -> XGBRegressor:
    root_dir = os.environ.get("ROOT_DIR", ".")
    model = XGBRegressor()
    model.load_model(f"{root_dir}/models/{from_station}_{to_station}_xgb_model.json")
    return model

def load_route_model(route_id:str) -> XGBRegressor:
    root_dir = os.environ.get("ROOT_DIR", ".")
    model = XGBRegressor()
    model.load_model(f"{root_dir}/models/{route_id}_xgb_model.json")
    return model

if __name__ == "__main__":
    STAM_BUSES_ROUTE_ID = { "1": "9011001000100000", 
                        "2": "9011001000200000",
                        "3": "9011001000300000",
                        "4": "9011001000400000"}

    STAM_BUSES_ROUTE_SET = {    "9011001000100000", 
                                "9011001000200000",
                                "9011001000300000",
                                "9011001000400000"}

    print("Starting model training")
    train_and_save_route_model(STAM_BUSES_ROUTE_SET, date(2026,1,5), date(2026,1,5))
    # train_and_save_model("Bergshamra", "Kungshamra", date(2024,6,15), date(2024,6,17), date(2024,6,18), date(2024,6,18))
    # dfx, dfy = create_X_Y_df("Bergshamra", "Kungshamra", date(2024,6,15), date(2024,6,16))
    # print(dfx.dtypes)
    # print(dfx.head())
    # dfx.to_csv("tmp.csv")
