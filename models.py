"""
Notification service - complete implementation.

This module contains:
    Notification class: Core data structure
    from_dict function: Validation and creation
    NotificationStore class: In-memory storage
    TeamsForwarder class: Microsoft Teams integration
    notification_store global instance

Simple list-based storage - no database complexity.

Imports:
    datetime: Timestamps and UTC timezone
    os: Environment variable access for webhook URL
    httpx: Async HTTP client for Teams integration
"""

from datetime import datetime, timezone
import os
import httpx


class Notification:
    """
    Core notification model.
    
    Simple, flat structure - no nested complexity or decorators.
    Type determines forwarding behavior: Warning=forward, Info=ignore.
    """
    
    def __init__(self, type, name, description, received_at=None, forwarded=None):
        """Initialize notification with explicit parameters."""
        self.type = type
        self.name = name
        self.description = description
        self.received_at = received_at
        self.forwarded = forwarded
    
    def __repr__(self):
        """String representation for debugging."""
        return (f"Notification(type={self.type!r}, name={self.name!r}, "
                f"description={self.description!r})")
    
    def __eq__(self, other):
        """Equality comparison."""
        if not isinstance(other, Notification):
            return False
        return (self.type == other.type and 
                self.name == other.name and 
                self.description == other.description)
    
    def to_dict(self):
        """Convert notification to dictionary."""
        return {
            'type': self.type,
            'name': self.name,
            'description': self.description,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'forwarded': self.forwarded
        }


class NotificationStore:
    """
    In-memory notification storage.
    Just a list. No fancy data structures.
    """
    
    def __init__(self):
        self._notifications = []
    
    def add(self, notification):
        """
        Store a notification with timestamp.
        
        Args:
            notification: Notification to store
            
        Returns:
            The stored notification with added metadata
        """
        if not isinstance(notification, Notification):
            raise TypeError("Expected Notification object, got dict or other type")
        
        notification.received_at = datetime.now(timezone.utc)
        self._notifications.append(notification)
        return notification
    
    def get_all(self):
        """Get all stored notifications"""
        return self._notifications.copy()
    
    def get_forwarded(self):
        """Get only forwarded notifications"""
        return [n for n in self._notifications if n.forwarded]
    
    def get_ignored(self):
        """Get only ignored notifications"""
        return [n for n in self._notifications if n.forwarded is False]
    
    def clear(self):
        """Clear all notifications (useful for testing)"""
        self._notifications.clear()
    
    def count(self):
        """Get total notification count"""
        return len(self._notifications)


class TeamsForwarder:
    """
    Forwards notifications to Microsoft Teams.
    Straightforward: just POST to webhook URL.
    """
    
    def __init__(self, webhook_url=None):
        """
        Initialize forwarder with webhook URL.
        
        Args:
            webhook_url: Teams webhook URL. If None, reads from 
                        TEAMS_WEBHOOK_URL environment variable.
        """
        self.webhook_url = webhook_url or os.getenv("TEAMS_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError(
                "Teams webhook URL not provided. "
                "Set TEAMS_WEBHOOK_URL environment variable."
                "Logging info notifications to file ./warning.log instead."
            )
    
    async def forward(self, notification):
        """
        Forward notification to Teams.
        
        Args:
            notification: Notification to forward
            
        Returns:
            True if successful, False otherwise
        """
        # Simple Teams message card format
        message = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": notification.name,
            "themeColor": "FF0000",  # Red for warnings
            "title": f"{notification.name}",
            "sections": [{
                "activityTitle": "Warning Notification",
                "facts": [
                    {"name": "Type", "value": notification.type},
                    {"name": "Description", "value": notification.description}
                ]
            }]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    timeout=10.0
                )
                response.raise_for_status()
                return True
        except Exception as e:
            # Log but don't crash - service should continue
            print(f"Failed to forward to Teams: {e}")
            return False
    
    def should_forward(self, notification):
        """
        Determine if notification should be forwarded.
        
        Simple rule: Only forward "Warning" types.
        No special cases, no complex logic.
        
        Args:
            notification: Notification to check
            
        Returns:
            True if should forward, False otherwise
        """
        return notification.type == "Warning"


def from_dict(data):
    """
    Create notification from dictionary.
    Expects capitalized field names: Type, Name, Description.
    """
    notification_type = data.get('Type', None)
    name = data.get('Name', None)
    description = data.get('Description', None)
    
    if not notification_type:
        raise ValueError("Missing required field: Type")
    if notification_type not in ['Warning', 'Info']:
        raise ValueError(f"Invalid type: {notification_type}. Must be 'Warning' or 'Info'")
    if not name:
        raise ValueError("Missing required field: Name")
    if not description:
        raise ValueError("Missing required field: Description")
    
    return Notification(
        type=notification_type,
        name=name,
        description=description
    )

# Global singleton instances is used to share state between modules
# Second time models.py is imported: Python returns cached instance No new creation!
notification_store = NotificationStore()