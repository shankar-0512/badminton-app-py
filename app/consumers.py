import json
from channels.generic.websocket import AsyncWebsocketConsumer

class UpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'updates_group'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Receive message from WebSocket"""
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_update',
                'message': message
            }
        )

    async def send_update(self, event):
        """Receive event message and send it to the WebSocket"""
        message = event['message']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
