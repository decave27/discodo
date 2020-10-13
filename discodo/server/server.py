from typing import Coroutine
from sanic import Sanic, response
from sanic.exceptions import abort

from .. import __version__
from ..config import Config
from ..source import AudioData
from ..status import getStatus
from .planner import app as PlannerBlueprint
from .websocket import app as WebsocketBlueprint

app = Sanic(__name__)
# app.include_router(WebsocketBlueprint)
# app.include_router(PlannerBlueprint)


def authorized(func: Coroutine) -> Coroutine:
    def wrapper(request, *args, **kwargs) -> Coroutine:
        if request.headers.get("Authorization") != Config.PASSWORD:
            abort(403, "Password mismatch.")

        return func(*args, **kwargs)

    return wrapper


@app.route("/")
async def index(request) -> response:
    return response.html(f"<h1>Discodo</h1> <h3>{__version__}")


@app.get("/status")
async def status(request) -> response:
    return response.json(getStatus())


@app.get("/getSource")
@authorized
async def getSource(request) -> response:
    Query = "".join(request.args.get("query", [])).strip()
    if not Query:
        abort(400, "Missing parameter query.")

    return response.json(await AudioData.create(Query))
