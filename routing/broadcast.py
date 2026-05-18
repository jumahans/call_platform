from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def broadcast_call_update(user_id: str, call_data: dict):
    """Push live call update to connected dashboard"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"live_calls_{user_id}",
        {
            'type': 'live_call_update',
            'data': call_data
        }
    )


def broadcast_call_to_org(organization_id: str, call_data: dict):
    """Push live call update to all users in an organization"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"live_calls_org_{organization_id}",
        {
            'type': 'live_call_update',
            'data': call_data
        }
    )