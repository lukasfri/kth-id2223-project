# ID2223 Project: Dynamic Bus Times Predictions

#### Group 1337: Lukas Friman, Georges Tohme

## Description
The aim of this project is to build a complete end-to-end system for predicting bus arrival times for SL’s single-digit bus routes in Stockholm. Instead of relying on one generalized model, we train individualized machine learning models per bus route to better capture route-specific characteristics. A core focus of the project is dynamic learning: models are continuously updated using fresh data and retrained on a weekly schedule to adapt to changes over time.

## Data Sources
Our dynamic data sources are the KoDa archived public transport data, and the GTFS-Regional date that provides realtime updates, including vehicle positions.

The realtime stream allows us to generate predictions continuously and display the current state of routes on the frontend. It also enables the system to produce predictions that reflect current traffic conditions rather than static timetable information.

## Frontend
We have a react based front end availble at id2223.dreamplay.net that displays our predictions and realtime visualization of the bus routes and the currently active buses.

## Backend
Our backend is a python fastapi server that keeps up to date with the realtime data and serves prediction. It also retrains the models weekly. 

## The Models
We use XGBoost Regressor models for arrival time prediction. The primary reasons for choosing XGBoost include:

* strong performance on structured tabular datasets

* robustness to nonlinear relationships (traffic effects, time-of-day patterns, stop-to-stop differences)

* fast training and retraining (important for weekly updates)

* interpretable feature importance for debugging and analysis

Each bus route is assigned its own model, allowing the system to learn route-specific behavior. This avoids the limitations of a single unified model that might average away important route-level differences.
