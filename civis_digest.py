"""Daily Slack digest of open public consultations on Civis (civis.vote).

Fetches the open ("published") consultations from Civis's public GraphQL API
and posts a formatted list to Slack through a webhook.

Environment variables:
  SLACK_WEBHOOK_URL  Slack incoming-webhook URL, or a Workflow Builder webhook
                     URL whose workflow has a text variable named "digest".
  DRY_RUN            If set to "1", print the message instead of posting it.

Uses only the Python standard library.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

API_URL = "https://api.civis.vote/graphql"
CONSULTATION_URL = "https://www.civis.vote/consultations/{id}/read"
LIST_URL = "https://www.civis.vote/consultations/list"
IST = timezone(timedelta(hours=5, minutes=30))

QUERY = """
{
  consultationList(statusFilter: "published", perPage: 100, page: 1,
                   sort: response_deadline, sortDirection: asc) {
    data { id title createdAt responseDeadline department { name } }
    paging { totalItems totalPages }
  }
}
"""


def post_json(url, payload, timeout=30):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "civis-digest/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def fetch_open_consultations():
    body = json.loads(post_json(API_URL, {"query": QUERY}))
    if body.get("errors"):
        raise RuntimeError("Civis API error: " + "; ".join(e.get("message", "?") for e in body["errors"]))
    result = body["data"]["consultationList"]
    return result["data"], result["paging"]["totalItems"]


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fmt_ist(dt):
    local = dt.astimezone(IST)
    hour = local.strftime("%I").lstrip("0")
    return f"{local.strftime('%a')} {local.day} {local.strftime('%b')}, {hour}:{local.strftime('%M %p')}"


def clean(text):
    # Escape characters that Slack mrkdwn treats specially inside link text.
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "¦").strip()


def build_message(items, total, now=None):
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(IST)
    header = f"*Open public consultations on Civis — {today.strftime('%a')} {today.day} {today.strftime('%b %Y')}*"

    if total == 0 or not items:
        return f"{header}\nNo consultations are open on Civis today."

    def line(c):
        deadline = parse_time(c["responseDeadline"])
        dept = clean((c.get("department") or {}).get("name") or "Department not listed")
        new = " · :new:" if now - parse_time(c["createdAt"]) <= timedelta(hours=24) else ""
        title = clean(c["title"])
        return f"• <{CONSULTATION_URL.format(id=c['id'])}|{title}> — {dept} · Deadline: {fmt_ist(deadline)}{new}"

    soon, later = [], []
    for c in items:
        (soon if parse_time(c["responseDeadline"]) - now <= timedelta(hours=48) else later).append(c)

    parts = [header, f"{total} open right now"]
    if soon:
        parts += ["", "*:alarm_clock: Closing within 48 hours*"] + [line(c) for c in soon]
        if later:
            parts += ["", "*All other open consultations*"] + [line(c) for c in later]
    else:
        parts += [""] + [line(c) for c in later]
    if total > len(items):
        parts += ["", f"_Showing the first {len(items)} of {total}. Full list: <{LIST_URL}|civis.vote>_"]
    parts += ["", "_Source: Civis (civis.vote). Automated daily digest._"]
    return "\n".join(parts)


def failure_message(reason):
    return (
        "*Civis digest skipped today* — " + reason
        + f"\nCheck manually: <{LIST_URL}|civis.vote/consultations/list>"
    )


def send(message):
    if os.environ.get("DRY_RUN") == "1":
        print(message)
        return
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        sys.exit("SLACK_WEBHOOK_URL is not set.")
    # "text" is read by incoming webhooks; "digest" by a Workflow Builder webhook.
    post_json(url, {"text": message, "digest": message})


def main():
    try:
        items, total = fetch_open_consultations()
        message = build_message(items, total)
    except Exception as exc:  # report the failure in Slack instead of failing silently
        send(failure_message(f"couldn't fetch the list from Civis ({exc})."))
        raise
    send(message)
    print(f"Sent digest with {total} open consultations.")


if __name__ == "__main__":
    main()
