from xgboost import XGBRegressor

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from data_pipeline import create_X_Y_df

def train_and_save_model(from_station:str, to_station:str):
    df_X, df_y = create_X_Y_df(from_station, to_station)

    model = XGBRegressor(enable_categorical=True, tree_method="hist")

    x_train, x_test, y_train, y_test = train_test_split(df_X, df_y, test_size=0.1)

    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    print("RMSE:", mean_squared_error(y_test, y_pred))

    model.save_model(f"./models/{from_station}_{to_station}_xgb_model.json")

def load_model(from_station:str, to_station:str) -> XGBRegressor:
    model = XGBRegressor()
    model.load_model(f"./models/{from_station}_{to_station}_xgb_model.json")
    return model


