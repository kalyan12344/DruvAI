
#lc/contact_tools.py
import json
from typing import Optional, List

from langchain.tools import tool
from pydantic import BaseModel, Field
# Import the new service getter
from core.google_auth import get_people_service

# --- Pydantic Model for Tool Input ---

class ContactInput(BaseModel):
    """Input model for the find_contact_info tool."""
    name: str = Field(description="The full name of the person to look up in Google Contacts.")

# --- The New Contact Lookup Tool (using Google People API) ---

@tool("find_contact_info", args_schema=ContactInput)
def find_contact_info(name: str) -> dict:
    """
    Looks up contact information for a person by searching the user's Google Contacts.
    Returns a dictionary with the contact's details or an error if not found.
    """
    print(f"--- TOOL: Running find_contact_info for: {name} ---")
    
    try:
        # Get the authenticated Google People API service
        service = get_people_service()

        # Search for the person in the user's connections
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=10,
            personFields='names,emailAddresses,phoneNumbers',
            # Note: The Google People API does not support direct search by name query.
            # It returns a list of contacts that we must search through.
            # For larger contact lists, this would need optimization/caching.
        ).execute()
        
        connections = results.get('connections', [])
        
        # Normalize the search name
        search_name_lower = name.lower()

        for person in connections:
            names = person.get('names', [])
            if not names:
                continue
            
            # Check if any of the person's names match the search query
            for name_field in names:
                display_name = name_field.get('displayName', '').lower()
                if search_name_lower in display_name:
                    print(f"--- Found matching contact: {name_field.get('displayName')} ---")
                    
                    # Extract the primary details
                    email = person.get('emailAddresses', [{}])[0].get('value', 'Not Available')
                    phone = person.get('phoneNumbers', [{}])[0].get('value', 'Not Available')
                    
                    return {
                        "name": name_field.get('displayName'),
                        "email": email,
                        "phone": phone,
                    }

        # If no match was found after checking all contacts
        print(f"--- Contact not found for: {name} ---")
        return {
            "error": "Contact not found.",
            "details": f"I could not find a contact matching '{name}' in your Google Contacts."
        }
    
    except Exception as e:
        print(f"--- An error occurred with the Google People API: {e} ---")
        return {
            "error": "API Error",
            "details": f"An error occurred while trying to access Google Contacts: {str(e)}"
        }
