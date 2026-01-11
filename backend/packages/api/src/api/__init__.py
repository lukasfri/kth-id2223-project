import os
import pickle
from datetime import date
from fastapi import FastAPI, HTTPException
import dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from training.common import FeedID, Operator
from training.static_data import StaticData
from training.model_training import train_and_save_model, load_model

dotenv.load_dotenv()

import routes
import vehicles

app = FastAPI(lifespan=vehicles.lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)
app.include_router(vehicles.router)

def main():
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
