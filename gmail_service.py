from googleapiclient.discovery import build
from collections import defaultdict
from auth import get_credentials
import re
from email.utils import parseaddr

def get_gmail_service():
    creds = get_credentials()
    return build('gmail', 'v1', credentials=creds)

def extract_from(headers):
    for h in headers:
        if h['name'].lower() == 'from':
            return h['value']
    return "unknown"

def normalize_sender(sender):
    # use parseaddr to robustly extract the email address
    name, email_addr = parseaddr(sender or "")
    if email_addr:
        return email_addr.lower()
    # fallback: strip and lowercase the raw value
    return (sender or "").strip().lower()

def count_messages_for_sender(sender):
    """Return the number of messages matching `from:sender` across the account."""
    service = get_gmail_service()
    email_addr = normalize_sender(sender)
    if not email_addr:
        return 0
    messages = list_all_messages(service, query=f'from:{email_addr}')
    return len(messages)

def get_sender_counts(max_messages=1000):
    service = get_gmail_service()
    counts = defaultdict(int)

    # request all messages across the account (including labels)
    messages = list_all_messages(service, query='in:anywhere')

    for msg in messages[:max_messages]:
        full = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From']
        ).execute()

        headers = full['payload']['headers']
        sender = normalize_sender(extract_from(headers))
        counts[sender] += 1

    return dict(counts)

def list_all_messages(service, query=None):
    messages = []
    request = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=500,
        includeSpamTrash=True
    )

    while request:
        response = request.execute()
        messages.extend(response.get("messages", []))
        request = service.users().messages().list_next(request, response)

    return messages



def delete_by_sender(sender: str):
    service = get_gmail_service()

    messages = list_all_messages(service, query=f"from:{sender}")

    if not messages:
        return 0

    message_ids = [m["id"] for m in messages]

    if not message_ids:
        return 0  # No hay mensajes para eliminar

    service.users().messages().batchDelete(
        userId="me",
        body={"ids": message_ids}
    ).execute()

    return len(message_ids)


# def delete_by_sender(sender):
#     service = get_gmail_service()
#     query = f'from:{sender}'

#     response = service.users().messages().list(
#         userId='me',
#         q=query
#     ).execute()

#     ids = [m['id'] for m in response.get('messages', [])]

#     if ids:
#         service.users().messages().batchDelete(
#             userId='me',
#             body={'ids': ids}
#         ).execute()
