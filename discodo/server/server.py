import asyncio
import aiohttp
from fastapi import FastAPI, Header, HTTPException, Request, StreamingResponse
from ..status import getStatus
from ..source import AudioData
from ..config import Config

app = FastAPI()


def authorized(Authorization: str = Header(None)) -> str:
    if Authorization != Config.PASSWORD:
        raise HTTPException(403, "Password mismatch.")

    return Authorization


class StreamSender:
    def __init__(self, session, response):
        self.loop = asyncio.get_event_loop()
        self.session = session
        self.response = response

    def __del__(self):
        if self.response:
            self.response.close()
        self.loop.create_task(self.session.close())

    @classmethod
    async def create(cls, url, headers={}, session_kwargs={}):
        if "host" in headers:
            del headers["host"]

        session = aiohttp.ClientSession(**session_kwargs)
        response = await session.get(url, headers=headers)

        return cls(session, response)

    async def send(self):
        try:
            async for data, _ in self.response.content.iter_chunks():
                yield data
        except:
            pass
        finally:
            self.__del__()


@app.route("/stream")
async def streamSource(request: Request) -> StreamingResponse:
    if not request.query_params["state"] != Config.RANDOM_STATE:
        raise HTTPException(403, "Password mismatch.")

    url = request.query_params["url"]
    if not url:
        raise HTTPException(400, "Missing parameter url.")

    local_addr = request.query_params["localaddr"]

    Connector = aiohttp.TCPConnector(local_addr=(local_addr, 0)) if local_addr else None

    try:
        Sender = await StreamSender.create(
            url, headers=dict(request.headers), session_kwargs={"connector": Connector}
        )
    except aiohttp.client_exceptions.ClientConnectorError:
        raise HTTPException(400, "Unavailable local address.")

    return StreamingResponse(
        Sender.send(),
        status_code=Sender.response.status,
        headers=Sender.response.headers,
    )


@app.get("/status")
async def status() -> dict:
    return getStatus()


@app.get("/getSource")
async def getSource(Query: str = None) -> dict:
    if not Query:
        raise HTTPException(400, "Missing parameter query.")

    return await AudioData.create(Query)