import json
from channels.generic.websocket import AsyncWebsocketConsumer

class UpdateConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer to handle real-time updates.
    """

    async def connect(self):
        """
        Handle new WebSocket connections. A new connection will be added 
        to the "updates_group".
        """
        
        # Define the room group name. All connected clients will be part of this group.
        self.room_group_name = 'updates_group'
        
        # Add the new connection to the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnections. The connection will be removed
        from the "updates_group".
        """
        
        # Remove the connection from the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Handle messages received from a WebSocket.
        """
        
        # Parse the received data
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Broadcast the message to all members of the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_update',
                'message': message
            }
        )

    async def send_update(self, event):
        """
        Handle "send_update" events by sending the event's message 
        back to the WebSocket.
        """
        
        # Extract message from event
        message = event['message']
        
        # Send the extracted message to the WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
