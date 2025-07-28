import json
import os.path
import requests
import os
from dotenv import load_dotenv
from typing import Annotated

from langchain_core.tools import tool
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
#
# # Google Calendar toolkit
# SCOPES = ["https://www.googleapis.com/auth/calendar", "https://mail.google.com/"]
# # Load stored OAuth tokens/credentials from your JSON file.
# # (The method may vary depending on your OAuth flow.)
# with open("credentials.json", "r") as f:
#     creds_data = json.load(f)
# creds = None
# # The file token.json stores the user's access and refresh tokens, and is
# # created automatically when the authorization flow completes for the first
# # time.
# if os.path.exists("token.json"):
#     creds = Credentials.from_authorized_user_file("token.json", SCOPES)
# # If there are no (valid) credentials available, let the user log in.
# if not creds or not creds.valid:
#     if creds and creds.expired and creds.refresh_token:
#       creds.refresh(Request())
#     else:
#         flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
#         creds = flow.run_local_server(port=0)
# # Save the credentials for the next run
# with open("token.json", "w") as token:
#   token.write(creds.to_json())
#
# # Create the service client.
# service = build('calendar', 'v3', credentials=creds)
#
# @tool
# def list_calendar_events(
#     time_min: Annotated[str, "Start time in ISO format (e.g., '2025-02-10T00:00:00Z')."],
#     time_max: Annotated[str, "End time in ISO format (e.g., '2025-02-10T23:59:59Z')."]
# ) -> str:
#     """
#     Retrieve events from the specified Google Calendar within a given time range.
#     """
#     try:
#         # Build or reuse your Google Calendar service client
#         events_result = service.events().list(
#             calendarId="primary",
#             timeMin=time_min,
#             timeMax=time_max,
#             singleEvents=True,
#             orderBy='startTime'
#         ).execute()
#         events = events_result.get('items', [])
#         if not events:
#             return "No events found in the specified time range."
#         # Format each event as "Event Title at [Start Time]"
#         event_list = []
#         # print(events[-1])
#         for event in events:
#             start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
#             end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))
#             title = event.get('summary', 'No Title')
#             event_list.append(f"{title} at {start} to {end} (uid: {event.get('id', 'No UID')}, htmlLink: {event.get('htmlLink', 'No HTML')})")
#         return event_list
#     except Exception as e:
#         return f"Error retrieving events: {e}"
#
# @tool
# def create_calendar_event(
#     title: Annotated[str, "Title of the event."],
#     description: Annotated[str, "Description of the event."],
#     start_time: Annotated[str, "Event start time in ISO format (e.g., '2025-02-10T09:00:00')."],
#     end_time: Annotated[str, "Event end time in ISO format (e.g., '2025-02-10T10:00:00')."],
# ) -> str:
#     """
#     Create (schedule) a new event in the specified Google Calendar.
#     """
#     try:
#         start_time = start_time.replace("Z", "")
#         end_time = end_time.replace("Z", "")
#
#         event_body = {
#             "summary": title,
#             "description": description,
#             "start": {
#                 "dateTime": start_time,
#                 "timeZone": "Asia/Hong_Kong",
#             },
#             "end": {
#                 "dateTime": end_time,
#                 "timeZone": "Asia/Hong_Kong",
#             }
#         }
#         created_event = service.events().insert(calendarId="primary", body=event_body).execute()
#         link = created_event.get("htmlLink", "No link available")
#         uid = created_event.get('id', 'No UID')
#         return f"Event created successfully: {link} (uid: {uid})"
#     except Exception as e:
#         return f"Error creating event: {e}"
#
# @tool
# def update_calendar_event(
#     event_id: Annotated[str, "The unique identifier of the event to update."],
#     title: Annotated[str, "Updated title (optional)."] = None,
#     description: Annotated[str, "Updated description (optional)."] = None,
#     start_time: Annotated[str, "Updated start time in ISO format (optional)."] = None,
#     end_time: Annotated[str, "Updated end time in ISO format (optional)."] = None,
# ) -> str:
#     """
#     Update an existing Google Calendar event. Only the provided fields will be updated.
#     """
#     try:
#         # Retrieve the existing event
#         event = service.events().get(calendarId="primary", eventId=event_id).execute()
#
#         # Update fields only if provided
#         if title:
#             event['summary'] = title
#         if description:
#             event['description'] = description
#         if start_time:
#             start_time = start_time.replace("Z", "")
#             event['start'] = {"dateTime": start_time, "timeZone": "Asia/Hong_Kong"}
#         if end_time:
#             end_time = end_time.replace("Z", "")
#             event['end'] = {"dateTime": end_time, "timeZone": "Asia/Hong_Kong"}
#
#         updated_event = service.events().update(
#             calendarId="primary", eventId=event_id, body=event
#         ).execute()
#         link = updated_event.get("htmlLink", "No link available")
#         return f"Event updated successfully: {link}"
#     except Exception as e:
#         return f"Error updating event: {e}"
#
# # Gmail toolkit
# from langchain_google_community import GmailToolkit
#
# gmail_toolkit = GmailToolkit().get_tools()



# Utilities
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)