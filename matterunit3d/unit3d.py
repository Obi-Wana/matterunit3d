import json
import posixpath
import traceback
import uuid

from datetime import datetime, timedelta
from .service import service


class unit3d(service):
    def init(self, username, fmt = "{username}: {message}"):
        self.username = username
        self.fmt = fmt
        # Variable to store IDs or timestamps of processed messages
        self.processed_messages = set()
    
    def request(self, method, url):
        url = self.addr + url + self.chatroom_id + "?api_token=" + self.token

        return self.app.session.request(method, url)
    
    def collect_msg_information(self, msg):
        username = msg["username"]
        self.text = msg["text"]
        self.created_at = msg["timestamp"]
        self.msg = (f'[{username}] {self.text}')

        return username, self.msg, self.created_at

    def post(self, url, msg):
        username, self.msg, self.created_at = self.collect_msg_information(msg)
        payload = {
            'username': self.chatroom_id,
            'message': self.msg,
            'chatroom_id': self.chatroom_id,
            'save': 'true',
            'targeted': '0',
            'user_id': '2'
        }

        url = self.addr + url

        return self.app.session.post(url, json = payload)

    async def send(self, msg):
        async with self.post("/api/chats/messages?api_token=" + self.token, msg) as req:
            if req.status >= 400:
                self.logger.error(f"{req.status}\n{await req.text()}")
    
    # Read message in UNIT3D chatbox and pass them to matterbridge.send() (Chatbox -> IRC)
    async def watch(self):
        async with self.request("GET", "/api/chats/messages/") as req:
            async for msg in self.app.jsonlines(req):
                messages = sorted(msg["data"], key=lambda x: x["id"], reverse=True)
                for msg in messages:
                    message_id = msg['id']
                    username = msg["username"]
                    message = msg["message"]
                    created_at = datetime.strptime(msg['created_at'], '%Y-%m-%d %H:%M:%S')

                    

                    if username != self.username and message_id not in self.processed_messages:
                        if created_at < datetime.now() - timedelta(seconds=5):
                            self.processed_messages.add(message_id)
                        else:
                            self.processed_messages.add(message_id)

                            if message != "[]" or message != "":
                                print(f"(Chatbox -> IRC) [{username}] {message}")
                                self.logger.info(f"(Chatbox -> IRC) [{username}] {message}")
                                await self.app.matterbridge.send(message_id, username, message, created_at)
