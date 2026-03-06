from collections import defaultdict
from email.utils import parseaddr

from auth import get_credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

BATCH_DELETE_LIMIT = 1000


def get_gmail_service():
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def extract_from(headers):
    for h in headers:
        if h["name"].lower() == "from":
            return h["value"]
    return "unknown"


def normalize_sender(sender):
    name, email_addr = parseaddr(sender or "")
    if email_addr:
        return email_addr.lower()
    return (sender or "").strip().lower()


def build_period_query(months):
    safe_months = max(1, min(int(months), 6))
    return f"in:anywhere -in:trash -in:spam newer_than:{safe_months}m"


def list_all_messages(service, query=None):
    messages = []
    request = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=500,
        includeSpamTrash=True,
    )

    while request:
        response = request.execute()
        messages.extend(response.get("messages", []))
        request = service.users().messages().list_next(request, response)

    return messages


def count_messages_for_sender(sender):
    service = get_gmail_service()
    email_addr = normalize_sender(sender)
    if not email_addr:
        return 0
    messages = list_all_messages(service, query=f"from:{email_addr}")
    return len(messages)


def get_sender_counts(months=1, max_messages=1000):
    service = get_gmail_service()
    counts = defaultdict(int)

    messages = list_all_messages(service, query=build_period_query(months))

    for msg in messages[:max_messages]:
        full = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From"],
        ).execute()

        headers = full.get("payload", {}).get("headers", [])
        sender = normalize_sender(extract_from(headers))
        if sender:
            counts[sender] += 1

    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def delete_by_sender(sender: str, months=1):
    service = get_gmail_service()

    normalized_sender = normalize_sender(sender)
    if not normalized_sender:
        return {"processed": 0, "deleted": 0, "trashed": 0}

    query = f"from:{normalized_sender} {build_period_query(months)}"
    messages = list_all_messages(service, query=query)

    if not messages:
        return {"processed": 0, "deleted": 0, "trashed": 0}

    message_ids = [m["id"] for m in messages if m.get("id")]
    if not message_ids:
        return {"processed": 0, "deleted": 0, "trashed": 0}

    deleted_count = 0
    trashed_count = 0
    for i in range(0, len(message_ids), BATCH_DELETE_LIMIT):
        chunk = message_ids[i : i + BATCH_DELETE_LIMIT]
        try:
            service.users().messages().batchDelete(
                userId="me",
                body={"ids": chunk},
            ).execute()
            deleted_count += len(chunk)
        except HttpError as exc:
            # Some accounts/scopes reject permanent delete. Fallback to TRASH
            # so deletion action still works with gmail.modify scope.
            if getattr(exc, "status_code", None) == 403 or getattr(exc.resp, "status", None) == 403:
                service.users().messages().batchModify(
                    userId="me",
                    body={
                        "ids": chunk,
                        "addLabelIds": ["TRASH"],
                        "removeLabelIds": [],
                    },
                ).execute()
                trashed_count += len(chunk)
            else:
                raise

    return {
        "processed": len(message_ids),
        "deleted": deleted_count,
        "trashed": trashed_count,
    }
