import json

# Global websocket reference
_global_websocket = None


def set_global_websocket(ws):
    """Set the global websocket instance."""
    global _global_websocket
    _global_websocket = ws


def broadcast_to_all(server, data, except_origin = False):
    """Broadcast data to all servers except the origin."""
    if _global_websocket:
        print(data)
        _global_websocket.send(json.dumps({"event": "send command", "args": [data, 'list']}))
