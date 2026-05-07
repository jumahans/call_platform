# apps/accounts/broadcast.py

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def send_activity_to_user(user_id: str, activity_data: dict):
    """Send real-time activity notification to specific user"""
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        f"activity_user_{user_id}",
        {
            'type': 'send_activity',
            'data': activity_data
        }
    )


def broadcast_new_call(call_data: dict):
    """Broadcast new call to all connected admin dashboards"""
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        "admin_dashboard",
        {
            'type': 'new_call',
            'data': call_data
        }
    )