# ID2223 Project: Dynamic Bus Times Predictions

## Description
This project's aim is to create individualized models for each sl single digit bus route and dynamically retrain them weekly to provide good predictions of arrival times.

## Data Sources
Our dynamic data sources are the KoDa archived public transport data, and the GTFS-Regional date that provides realtime updates, including vehicle positions.

## Frontend
We have a react based front end availble at id2223.dreamplay.net that displays our predictions and realtime visualization of the bus routes and the currently active buses.

## Backend
Our backend is a python fastapi server that keeps up to date with the realtime data and serves prediction. It also retrains the models weekly. 

## The Models
We chose to use XGBoost regressor models as we believed they would be adequate for the job and would not over complicate the project more than dealing with GTFS data already would.

