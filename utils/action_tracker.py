"""
Action Tracker - Records all actions during execution for test script generation.
"""
from typing import List, Dict, Any
from datetime import datetime
import json

class ActionTracker:
    """Tracks all browser actions for test script generation."""
    
    def __init__(self):
        self.actions: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start tracking actions."""
        self.start_time = datetime.now()
        self.actions = []
    
    def stop(self):
        """Stop tracking actions."""
        self.end_time = datetime.now()
    
    def add_action(self, action_type: str, **kwargs):
        """Add an action to the tracker."""
        action = {
            "type": action_type,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.actions.append(action)
    
    def add_navigation(self, url: str):
        """Track navigation action."""
        self.add_action("navigate", url=url)
    
    def add_click(self, selector: str, element_type: str = "element"):
        """Track click action."""
        self.add_action("click", selector=selector, element_type=element_type)
    
    def add_fill(self, selector: str, text: str):
        """Track fill input action."""
        self.add_action("fill", selector=selector, text=text)
    
    def add_press(self, selector: str, key: str):
        """Track key press action."""
        self.add_action("press", selector=selector, key=key)
    
    def add_wait(self, wait_type: str, timeout: int = None, selector: str = None):
        """Track wait action."""
        self.add_action("wait", wait_type=wait_type, timeout=timeout, selector=selector)
    
    def add_sleep(self, seconds: float):
        """Track sleep action."""
        self.add_action("sleep", seconds=seconds)
    
    def get_actions(self) -> List[Dict[str, Any]]:
        """Get all tracked actions."""
        return self.actions
    
    def export_json(self, filepath: str):
        """Export actions to JSON file."""
        data = {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "actions": self.actions
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def clear(self):
        """Clear all tracked actions."""
        self.actions = []
        self.start_time = None
        self.end_time = None
