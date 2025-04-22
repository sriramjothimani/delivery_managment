# shared_data.py

_shared_state = {}

def set_shared(key: str, value):
    """Store a value in shared state."""
    _shared_state[key] = value

def get_shared(key: str):
    """Retrieve a value from shared state. Returns None if not found."""
    return _shared_state.get(key)

def clear_shared(key: str):
    """Remove a specific key from shared state."""
    if key in _shared_state:
        del _shared_state[key]

def clear_all_shared():
    """Clear the entire shared state."""
    _shared_state.clear()
