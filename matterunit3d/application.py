import asyncio
import json
import aiohttp

from datetime import datetime, timedelta
from . import consts
from .unit3d import unit3d
from .unit3d_dev import unit3d_dev
from .matterbridge import matterbridge


class application:
    def __init__(self, unit3d_cfg, unit3d_dev_cfg, matterbridge_cfg, matterbridge_dev_cfg):
        self.matterbridge = matterbridge(self, **matterbridge_cfg)

        # Production
        self.unit3d = unit3d(self, **unit3d_cfg)

        # Dev
        self.unit3d_dev = unit3d_dev(self, **unit3d_dev_cfg)

        self.services = [self.matterbridge]
        self.running = False

    async def loop(self, service):
        while self.running:
            try:
                await asyncio.wait_for(service.watch(), timeout=30)
            except asyncio.TimeoutError:
                print("Timeout while waiting for watch() function, retrying.")

    async def run(self):
        self.running = True
        async with aiohttp.ClientSession(headers = {"User-Agent": consts.user_agent}) as session:
            self.session = session
            await asyncio.wait([asyncio.create_task(self.loop(service)) for service in self.services])
    
    def shutdown(self):
        self.running = False
    
    async def jsonlines(self, req):
        async for raw in req.content:
            line = raw.decode()
            try:
                json_out = json.loads(line)
            except:
                print("JSON Decode error")
            yield json_out

    def get_message_attributes(self, msg, source):
        if source == "matterbridgeapi":
            username = msg["username"]
            message = msg["text"]

            return username, message
