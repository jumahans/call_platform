import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ActivityConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

        query_string = self.scope.get('query_string', b'').decode()
        token_str = None

        for part in query_string.split('&'):
            if part.startswith('token='):
                token_str = part.split('=', 1)[1]
                break

        if not token_str:
            await self.close(code=4001)
            return

        try:
            token = AccessToken(token_str)
            self.user_id = str(token['user_id'])
        except (InvalidToken, TokenError):
            await self.close(code=4001)
            return

        self.group_name = f"activity_user_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass

    async def send_activity(self, event):
        await self.send(text_data=json.dumps({
            'type': 'activity',
            'data': event['data']
        }))