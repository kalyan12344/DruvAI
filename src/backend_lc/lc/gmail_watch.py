# lc/gmail_watch.py

# Make sure your google_auth file is accessible. Adjust the import if needed.
from core.google_auth import get_gmail_service

def start_watching_gmail():
    """
    Sends a one-time request to the Gmail API to start watching the user's inbox
    and sending notifications to your configured Pub/Sub topic.
    """
    try:
        service = get_gmail_service()
        
        # --- IMPORTANT: EDIT THIS LINE ---
        # Replace this with the full "Topic name" from your Google Cloud Pub/Sub page.
        # It looks like: projects/your-gcp-project-id/topics/your-topic-id
        topic_name = "projects/deft-axon-455818-t8/topics/gmail-druv-webhook"
        
        # This is the request body that tells Google what to watch.
        request_body = {
            "labelIds": ["INBOX"],  # Only watch the main inbox
            "topicName": topic_name
        }
        
        print("Sending watch() request to Google to start receiving notifications...")
        # This is the official API call
        response = service.users().watch(userId='me', body=request_body).execute()
        
        print("\n✅ Success! Google is now configured to send notifications.")
        print("Your webhook is active until the expiration date.")
        print(f"Response: {response}")

    except Exception as e:
        print(f"❌ An error occurred while setting up the watch request: {e}")
        print("\nPlease ensure you have enabled the Cloud Pub/Sub API and set the correct topic name.")

if __name__ == '__main__':
    print("--- Gmail Webhook Setup ---")
    print("Ensure your FastAPI server and ngrok tunnel are both running in separate terminals before you continue.")
    input("Press Enter to continue once your server and ngrok are ready...")
    
    start_watching_gmail()  