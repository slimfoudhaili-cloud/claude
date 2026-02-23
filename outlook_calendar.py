"""
Outlook Calendar - Microsoft Graph API integration
Requires: pip install msal requests
"""

import json
import os
import webbrowser
from datetime import datetime, timedelta, timezone

import msal
import requests

# ─── Configuration ────────────────────────────────────────────────────────────
# To get these values:
# 1. Go to https://portal.azure.com
# 2. Azure Active Directory > App registrations > New registration
# 3. Add redirect URI: http://localhost (for device flow, not needed)
# 4. API permissions > Add > Microsoft Graph > Delegated > Calendars.ReadWrite
CLIENT_ID = os.environ.get("AZURE_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
TENANT_ID = os.environ.get("AZURE_TENANT_ID", "common")  # "common" for personal accounts

SCOPES = ["Calendars.ReadWrite", "User.Read"]
GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_CACHE_FILE = ".outlook_token_cache.json"

# ─── Authentication ────────────────────────────────────────────────────────────

def get_token_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_FILE):
        cache.deserialize(open(TOKEN_CACHE_FILE).read())
    return cache


def save_token_cache(cache: msal.SerializableTokenCache):
    if cache.has_state_changed:
        with open(TOKEN_CACHE_FILE, "w") as f:
            f.write(cache.serialize())


def get_access_token() -> str:
    cache = get_token_cache()
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        token_cache=cache,
    )

    # Try silent authentication first (uses cached token)
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            save_token_cache(cache)
            return result["access_token"]

    # Interactive: device code flow (works in terminal)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError("Could not initiate device flow")

    print("\n" + "=" * 60)
    print("AUTHENTICATION REQUIRED")
    print("=" * 60)
    print(f"1. Open: {flow['verification_uri']}")
    print(f"2. Enter code: {flow['user_code']}")
    print("=" * 60 + "\n")
    webbrowser.open(flow["verification_uri"])

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise RuntimeError(f"Authentication failed: {result.get('error_description')}")

    save_token_cache(cache)
    return result["access_token"]


def graph_get(token: str, endpoint: str, params: dict = None) -> dict:
    resp = requests.get(
        f"{GRAPH_BASE}{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
    )
    resp.raise_for_status()
    return resp.json()


def graph_post(token: str, endpoint: str, body: dict) -> dict:
    resp = requests.post(
        f"{GRAPH_BASE}{endpoint}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body,
    )
    resp.raise_for_status()
    return resp.json()


# ─── Calendar features ─────────────────────────────────────────────────────────

def list_events(token: str, days: int = 7):
    """List upcoming calendar events for the next N days."""
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)

    params = {
        "$orderby": "start/dateTime",
        "$top": 20,
        "startDateTime": now.isoformat(),
        "endDateTime": end.isoformat(),
    }

    data = graph_get(token, "/me/calendarView", params=params)
    events = data.get("value", [])

    if not events:
        print(f"No events in the next {days} days.")
        return

    print(f"\n{'=' * 60}")
    print(f"  UPCOMING EVENTS (next {days} days)")
    print(f"{'=' * 60}")
    for ev in events:
        start_raw = ev["start"]["dateTime"]
        start_dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
        local_dt = start_dt.astimezone()
        print(f"\n  [{local_dt.strftime('%a %d %b %H:%M')}]  {ev['subject']}")
        if ev.get("location", {}).get("displayName"):
            print(f"   Location: {ev['location']['displayName']}")
        if ev.get("bodyPreview"):
            preview = ev["bodyPreview"][:100].replace("\n", " ")
            print(f"   Note    : {preview}...")
    print()


def create_event(token: str):
    """Interactively create a new calendar event."""
    print("\n--- Create a new event ---")
    subject = input("Title: ").strip()
    date_str = input("Date (YYYY-MM-DD): ").strip()
    start_time = input("Start time (HH:MM): ").strip()
    end_time = input("End time   (HH:MM): ").strip()
    location = input("Location (optional): ").strip()
    notes = input("Notes (optional): ").strip()

    start_iso = f"{date_str}T{start_time}:00"
    end_iso = f"{date_str}T{end_time}:00"

    # Detect local timezone offset
    tz_offset = datetime.now(timezone.utc).astimezone().strftime("%z")
    tz_str = f"UTC{tz_offset[:3]}:{tz_offset[3:]}"

    body = {
        "subject": subject,
        "start": {"dateTime": start_iso, "timeZone": tz_str},
        "end":   {"dateTime": end_iso,   "timeZone": tz_str},
    }
    if location:
        body["location"] = {"displayName": location}
    if notes:
        body["body"] = {"contentType": "text", "content": notes}

    event = graph_post(token, "/me/events", body)
    print(f"\nEvent created: {event['subject']} (id: {event['id'][:20]}...)")


def show_profile(token: str):
    """Display the authenticated user's profile."""
    profile = graph_get(token, "/me")
    print(f"\nConnected as: {profile.get('displayName')} <{profile.get('mail') or profile.get('userPrincipalName')}>")


# ─── Main menu ─────────────────────────────────────────────────────────────────

def main():
    if CLIENT_ID == "YOUR_CLIENT_ID_HERE":
        print("ERROR: Set your Azure CLIENT_ID in the script or via environment variable:")
        print("  export AZURE_CLIENT_ID=your-client-id")
        print("\nSee README.md for setup instructions.")
        return

    print("Connecting to Microsoft account...")
    token = get_access_token()
    show_profile(token)

    while True:
        print("\nWhat do you want to do?")
        print("  1. View upcoming events (7 days)")
        print("  2. View upcoming events (30 days)")
        print("  3. Create a new event")
        print("  0. Quit")
        choice = input("\nChoice: ").strip()

        if choice == "1":
            list_events(token, days=7)
        elif choice == "2":
            list_events(token, days=30)
        elif choice == "3":
            create_event(token)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
