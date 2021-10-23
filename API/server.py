import time

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from . import models as models
from .logging import logging
from .database import db

title = "Tempmail API"
description = """
Tempmail API helps you bypass any email verification.</br>
Email: [dropout@fbi.ac](mailto:dropout@fbi.ac)</br>
"""

tags_metadata = [
    {
        "name": "home",
        "description": "Home page, redirects to __/docs__"
    },
    {
        "name": "stats",
        "description": "Shows the api's stats."
    },
    {
        "name": "create",
        "description": "Create a new email address.",
    },
    {
        "name": "latest",
        "description": "Get the latest emails. You are __required__ to first create a account."
    }
]

app = FastAPI(
    title=title,
    description=description,
    version="1.2",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/docs/config.json",
    openapi_tags=tags_metadata
)

@app.on_event("startup")
async def startup_event():
    logging.info("The api has started!")

@app.get("/", tags=["home"])
async def home():
    return RedirectResponse(url="/docs")

@app.get("/api/stats/", tags=["stats"])
async def stats():
    before = time.monotonic()
    db.find_one({"ping": 1})
    ping = round(time.monotonic() - before) * 1000

    result = db.find({})
    
    total_users = 0
    total_emails = 0

    for user in result:
        total_users += 1
        total_emails += len(user["emails"])

    return {
        "database": {
            "ping": ping,
            "total_users": total_users,
            "total_emails": total_emails
        }
    }

@app.post("/api/create/", tags=["create"])
async def create(data: models.create):
    result = db.find_one({
        "username": data.username,
        "domain": data.domain
    })
    if result != None:
        return HTTPException(
            status_code=400,
            detail="That username/domain has been already registered."
        )
    if any(not c.isalnum() for c in data.username):
        return HTTPException(
            status_code=400,
            detail="Invalid username, do not include any special characters."
        )
    
    db.insert_one({
        "username": data.username,
        "password": data.password,
        "domain": data.domain,
        "emails": []
    })

    return {
        "emails": []
    }

@app.get("/api/latest/", tags=["latest"])
async def latest(data: models.latest):
    result = db.find_one({
        "username": data.address.split("@")[0],
        "domain": data.address.split("@")[1],
        "password": data.password
    })
    if result == None:
        return HTTPException(
            status_code=403,
            detail="Invalid username or password."
        )

    if data.from_address == None:
        return {
            "emails": result["emails"]
        }
    else:
        emails = []
        for email in result["emails"]:
            if email["from"] == data.from_address:
                emails.append(email)
        
        return {
            "emails": emails
        }

def run(host = "0.0.0.0", port = 80):
    uvicorn.run(
        app=app,
        host=host,
        port=port,
        log_level="critical"
    )
