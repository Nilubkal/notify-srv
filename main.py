"""
Notification Service - Main FastAPI Application

Simple RESTful service that forwards Warning notifications to Teams.
Keeps Info notifications in memory but doesn't forward them.

Design Philosophy:
- Simple data structures (see models.py)
- No special cases in forwarding logic
- Pragmatic: tries to solve the actual problem without overengineering

Imports:
- fastapi: Web framework (FastAPI, HTTPException, status codes, Request)
- models: Everything (Notification, from_dict, NotificationStore, TeamsForwarder, notification_store)
"""
import uvicorn
from fastapi import FastAPI, HTTPException, status, Request
from datetime import datetime

from models import Notification, from_dict, notification_store, TeamsForwarder


# Initialize Teams forwarder at startup
teams_forwarder = None


# Create FastAPI app
app = FastAPI(
    title="Notification Service",
    description="RESTful service for forwarding notifications to Microsoft Teams",
    version="1.0.0"
)


# Explicit startup/shutdown events
async def startup_event():
    """Run on application startup."""
    global teams_forwarder
    try:
        teams_forwarder = TeamsForwarder()
        print("Teams forwarder initialized")
    except ValueError as e:
        print(f"  Teams forwarder not configured: {e}")
        print("   Service will continue but won't forward to Teams")


async def shutdown_event():
    """Run on application shutdown."""
    print("Shutting down notification service")


# Register events explicitly
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)


# Endpoint functions

async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Notification Service",
        "version": "1.0.0"
    }


async def create_notification(request: Request):
    """
    Create and process a notification (calls NotificationStore.add()).
    
    Maps to NotificationStore method:
        notification_store.add(notification) - Stores with automatic timestamp
    
    Request body (JSON):
        Type (required): "Warning" or "Info"
        Name (required): Notification name/title
        Description (required): Detailed description
    
    Behavior:
        Warning notifications: Stored + Forwarded to Teams
        Info notifications: Stored only (not forwarded)
    
    Example request:
    ```bash
    curl -X POST http://localhost:8000/notifications \\
      -H "Content-Type: application/json" \\
      -d '{
        "Type": "Warning",
        "Name": "Database Error",
        "Description": "Connection timeout"
      }'
    ```
    
    Returns:
        status: "created"
        notification: Created notification with timestamp
        forwarding: Forwarding status (forwarded: true/false, status: reason)
    """
    # Parse JSON body
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Create notification from dictionary
    try:
        notification = from_dict(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Store notification first
    stored_notification = notification_store.add(notification)
    
    # Determine if should forward
    should_forward = (
        teams_forwarder is not None and 
        teams_forwarder.should_forward(notification)
    )
    
    forwarded = False
    forward_status = "not_applicable"
    
    if should_forward:
        # Attempt to forward to Teams
        forwarded = await teams_forwarder.forward(notification)
        stored_notification.forwarded = forwarded
        forward_status = "success" if forwarded else "failed"
    else:
        # Info type - not forwarded by design
        stored_notification.forwarded = False
        forward_status = "skipped_info_type" if notification.type == "Info" else "no_teams_config"
        
        # Log Warning notifications to file when Teams not configured
        if notification.type == "Warning" and teams_forwarder is None:
            try:
                with open("warning.log", "a") as f:
                    timestamp = stored_notification.received_at.strftime("%Y-%m-%d %H:%M:%S")
                    log_entry = f"{timestamp} | {notification.name} | {notification.description}\n"
                    f.write(log_entry)
            except Exception as e:
                print(f"Failed to write to warning.log: {e}")
    
    return {
        "status": "created",
        "notification": {
            "type": notification.type,
            "name": notification.name,
            "description": notification.description,
            "received_at": stored_notification.received_at.isoformat() if stored_notification.received_at else None
        },
        "forwarding": {
            "forwarded": forwarded,
            "status": forward_status
        }
    }


async def list_notifications(filter=None):
    """
    List stored notifications with optional filtering.
    
    **Maps to NotificationStore methods:**
    - No filter → `notification_store.get_all()`
    - filter=forwarded → `notification_store.get_forwarded()`
    - filter=ignored → `notification_store.get_ignored()`
    
    **Query Parameters:**
    - **filter** (optional): Filter type
      - `forwarded` - Only notifications sent to Teams
      - `ignored` - Only notifications NOT sent to Teams (Info type)
      - Omit for all notifications
    
    **Example requests:**
    - `GET /notifications` - All notifications
    - `GET /notifications?filter=forwarded` - Forwarded only
    - `GET /notifications?filter=ignored` - Ignored only
    
    **Returns:**
    - total: Count of notifications returned
    - filter: Applied filter type
    - notifications: Array of notification objects
    """
    if filter == "forwarded":
        notifications = notification_store.get_forwarded()
    elif filter == "ignored":
        notifications = notification_store.get_ignored()
    elif filter is None:
        notifications = notification_store.get_all()
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid filter: {filter}. Use 'forwarded', 'ignored', or omit."
        )
    
    return {
        "total": len(notifications),
        "filter": filter or "all",
        "notifications": [
            {
                "type": n.type,
                "name": n.name,
                "description": n.description,
                "received_at": n.received_at.isoformat() if n.received_at else None,
                "forwarded": n.forwarded
            }
            for n in notifications
        ]
    }


async def get_statistics():
    """
    Get notification statistics (uses NotificationStore.count() and filters).
    
    **Maps to NotificationStore methods:**
    - `notification_store.count()` - Total count
    - `notification_store.get_forwarded()` - Forwarded count
    - `notification_store.get_ignored()` - Ignored count
    
    **Example request:**
    ```bash
    curl http://localhost:8000/stats
    ```
    
    **Returns:**
    - total: Total number of stored notifications
    - forwarded: Number of notifications sent to Teams (Warning type)
    - ignored: Number of notifications NOT sent to Teams (Info type)
    
    **Example response:**
    ```json
    {
      "total": 5,
      "forwarded": 3,
      "ignored": 2
    }
    ```
    """
    all_notifications = notification_store.get_all()
    forwarded = len([n for n in all_notifications if n.forwarded])
    ignored = len([n for n in all_notifications if n.forwarded is False])
    
    return {
        "total": len(all_notifications),
        "forwarded": forwarded,
        "ignored": ignored
    }


async def clear_notifications():
    """
    Clear all stored notifications (calls NotificationStore.clear()).
    
    **Maps to NotificationStore method:**
    - `notification_store.clear()` - Removes all notifications
    
    **Example request:**
    ```bash
    curl -X DELETE http://localhost:8000/notifications
    ```
    
    **Returns:**
    - HTTP 204 No Content (success, no body)
    
    **Use cases:**
    - Reset state between tests
    - Clear production data
    - Maintenance operations
    """
    notification_store.clear()
    return None


# This is what @app.get() and @app.post() do behind the scenes
app.add_api_route(
    path="/",
    endpoint=root,
    methods=["GET"],
    summary="Health check",
    tags=["System"]
)

app.add_api_route(
    path="/notifications",
    endpoint=create_notification,
    methods=["POST"],
    status_code=status.HTTP_201_CREATED,
    summary="Create notification (notification_store.add)",
    tags=["Notifications"],
    description="Creates and stores a notification. Maps to NotificationStore.add() method."
)

app.add_api_route(
    path="/notifications",
    endpoint=list_notifications,
    methods=["GET"],
    summary="List notifications (get_all/get_forwarded/get_ignored)",
    tags=["Notifications"],
    description="Lists notifications with optional filtering. Maps to NotificationStore.get_all(), get_forwarded(), or get_ignored()."
)

app.add_api_route(
    path="/stats",
    endpoint=get_statistics,
    methods=["GET"],
    summary="Get statistics (notification_store.count)",
    tags=["Statistics"],
    description="Returns notification counts. Maps to NotificationStore.count() and filtering methods."
)

app.add_api_route(
    path="/notifications",
    endpoint=clear_notifications,
    methods=["DELETE"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear all notifications (notification_store.clear)",
    tags=["Notifications"],
    description="Deletes all stored notifications. Maps to NotificationStore.clear() method."
)


if __name__ == "__main__":
   
    uvicorn.run(app, host="0.0.0.0", port=8000)