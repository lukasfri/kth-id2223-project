from math import sqrt
import os
from datetime import date
from typing import Optional
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


def train_and_save_route_model(route_id:set[str], start_date:date, end_date:date):
    
   
    #x_train, x_test, y_train, y_test = train_test_split(df_x, df_y, test_size=0.1)

    # print(x_train.dtypes)
    # print(x_train.head())
    # print(x_train.max())
    # print(x_train.mean())
    # print(x_train.min())
    for r in route_id:
        model = XGBRegressor()
        
        df_x, df_y = create_X_Y_df_with_route(r, start_date, end_date)
        x_train, x_test, y_train, y_test = train_test_split(df_x, df_y, test_size=0.15)
        print(type(x_train))
        print(type(x_test))
        print(type(y_train))
        print(type(y_test))

        print("Starting training", r)
        model.fit(x_train, y_train)
        # print(x_test.dtypes)
        # print(x_test.head())
        # print(x_test.max())
        # print(x_test.min())

        y_pred = model.predict(x_test)
        print(type(y_pred))
        print("SMSE:", sqrt(mean_squared_error(y_test, y_pred)))


        root_dir = os.environ.get("ROOT_DIR", ".")
        model.get_booster().save_model(f"{root_dir}/models/{r}_xgb_model.json")


    #x_test, y_test = create_X_Y_df_with_route(route_id, test_start_date, test_end_date)

        
        

def load_model(from_station:str, to_station:str, *, model_path: Optional[str] = None) -> XGBRegressor:
    if model_path is None:
        root_dir = os.environ.get("ROOT_DIR", ".")
        model_path = f"{root_dir}/models"
    model = XGBRegressor()
    model.load_model(f"{model_path}/{from_station}_{to_station}_xgb_model.json")
    return model

def load_route_model(route_id: str, *, model_path: Optional[str] = None) -> XGBRegressor:
    if model_path is None:
        root_dir = os.environ.get("ROOT_DIR", ".")
        model_path = f"{root_dir}/models"
    model = XGBRegressor()
    model.load_model(f"{model_path}/{route_id}_xgb_model.json")
    return model

# if __name__ == "__main__":
#     STAM_BUSES_ROUTE_ID = { 1: "9011001000100000", 
#                         2: "9011001000200000",
#                         3: "9011001000300000",
#                         4: "9011001000400000"}
#
#     STAM_BUSES_ROUTE_SET = {    "9011001000100000", 
#                                 "9011001000200000",
#                                 "9011001000300000",
#                                 "9011001000400000"}
#
#     print("Starting model training")
#     #for route_id in STAM_BUSES_ROUTE_SET:
#     #    print("training on route: ", route_id)
#     train_and_save_route_model(STAM_BUSES_ROUTE_SET, date(2026,1,5), date(2026,1,5))
#     # train_and_save_model("Bergshamra", "Kungshamra", date(2024,6,15), date(2024,6,17), date(2024,6,18), date(2024,6,18))
#     # dfx, dfy = create_X_Y_df("Bergshamra", "Kungshamra", date(2024,6,15), date(2024,6,16))
#     # print(dfx.dtypes)
#     # print(dfx.head())
#     # dfx.to_csv("tmp.csv")
