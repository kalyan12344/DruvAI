from fastapi import APIRouter, HTTPException
from typing import Optional
import json
# Import the Google People API service getter from the core auth module
from core.google_auth import get_people_service
# Import the specific LangChain tool for the agent to use
from lc.contact_tools import find_contact_info

router = APIRouter()

@router.get("/list")
def list_all_contacts():
    """
    Fetches ALL contacts from the user's Google Contacts by automatically handling pagination.
    """
    try:
        service = get_people_service()
        all_connections = []
        next_page_token = None

        # Loop until there are no more pages of contacts
        while True:
            results = service.people().connections().list(
                resourceName='people/me',
                pageSize=1000, # Fetch in the largest possible batches
                personFields='names,emailAddresses,phoneNumbers',
                sortOrder='FIRST_NAME_ASCENDING',
                pageToken=next_page_token
            ).execute()
            
            connections = results.get('connections', [])
            all_connections.extend(connections)
            
            # Get the token for the next page
            next_page_token = results.get('nextPageToken')
            if not next_page_token:
                break # Exit the loop if there are no more pages

        print(f"--- Fetched a total of {len(all_connections)} contacts ---")
        
        formatted_contacts = []
        for person in all_connections:
            names = person.get('names', [])
            if not names:
                continue # Skip contacts with no name
            
            # Safely get the primary email and phone number
            email = person.get('emailAddresses', [{}])[0].get('value', 'No Email Provided')
            phone = person.get('phoneNumbers', [{}])[0].get('value', 'No Phone Provided')
            
            formatted_contacts.append({
                "name": names[0].get('displayName'),
                "email": email,
                "phone": phone
            })
            
        return formatted_contacts
        
    except Exception as e:
        print(f"--- An error occurred while accessing Google Contacts: {e} ---")
        raise HTTPException(status_code=500, detail=f"An error occurred while accessing Google Contacts: {str(e)}")

@router.get("/search")
def search_for_contact(name: str):
    """
    Searches for a single contact by name using the find_contact_info tool.
    """
    if not name:
        raise HTTPException(status_code=400, detail="A 'name' query parameter is required.")
    
    try:
        # We can still use the tool here as it encapsulates the search logic perfectly.
        contact_details = find_contact_info(name)
        
        if contact_details.get("error"):
            raise HTTPException(status_code=404, detail=contact_details.get("details", "Contact not found."))
            
        return contact_details
        
    except Exception as e:
        # Catch-all for any other unexpected errors during the tool's execution.
        print(f"--- An error occurred in the contact search endpoint: {e} ---")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def get_contacts_connection_status():
    """Gets the connection status for Google Contacts."""
    try:
        with open("db.json", 'r') as f:
            db_data = json.load(f)
        return db_data.get("connected_contacts", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
