"""Critical-signal email alerts via Resend.

Standalone, notify-only. monitor.py detects stage-relevant signals and calls
send_stage_alert() once per run. This module owns ALL Resend/HTTP logic; it
never changes any curated field or stage. A failed send is swallowed — the
daily pipeline must never crash on a notification error.

Test in isolation (no pipeline): uv run --env-file .env python alerts.py
"""

import os

import requests

RESEND_URL = "https://api.resend.com/emails"


def send_stage_alert(flagged_items: list) -> None:
    """Email a single digest of signals that may warrant re-classification.

    Sends ONLY to ALERT_TO_EMAIL (from env) — never to any address derived from
    article content. Returns silently on empty input, missing config, or any
    request failure; never raises.
    """
    if not flagged_items:
        return

    api_key = os.environ.get("RESEND_API_KEY")
    from_email = os.environ.get("ALERT_FROM_EMAIL")
    to_email = os.environ.get("ALERT_TO_EMAIL")
    if not (api_key and from_email and to_email):
        print("Alert skipped: RESEND_API_KEY / ALERT_FROM_EMAIL / ALERT_TO_EMAIL not all set.")
        return

    n = len(flagged_items)
    subject = f"[AI Adoption] {n} institution(s) may warrant re-classification"
    html = _build_html(flagged_items)

    try:
        resp = requests.post(
            RESEND_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": html,
            },
            timeout=30,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        status = getattr(e.response, "status_code", None)
        detail = f" (HTTP {status})" if status else ""
        print(f"Alert email failed{detail}; continuing.")
        return

    print(f"Alert email sent: {n} flagged signal(s).")


def _build_html(flagged_items: list) -> str:
    blocks = []
    for item in flagged_items:
        name = item.get("institution") or item.get("institution_normalized", "Unknown")
        stage = item.get("current_stage", "")
        headline = item.get("headline", "")
        reason = item.get("stage_relevant_reason", "")
        url = item.get("url", "")
        blocks.append(
            f"<li style='margin-bottom:16px'>"
            f"<strong>{name}</strong> &mdash; current stage: <code>{stage}</code><br>"
            f"{headline}<br>"
            f"<em>Why flagged:</em> {reason}<br>"
            f"<a href='{url}'>{url}</a>"
            f"</li>"
        )
    return (
        "<p>The following public signals may indicate a material change in an "
        "institution's AI-adoption stage:</p>"
        f"<ul>{''.join(blocks)}</ul>"
        "<p>Review and run /judge-ai-adoption-phase on each before changing any stage.</p>"
    )


if __name__ == "__main__":
    # Isolated test of the email path — no pipeline, one dummy flagged item.
    send_stage_alert([
        {
            "institution": "CalSTRS",
            "institution_normalized": "CalSTRS",
            "current_stage": "piloting",
            "headline": "CalSTRS moves AI manager-selection system into firm-wide production",
            "stage_relevant_reason": "Describes a firm-wide production rollout, not a single pilot.",
            "url": "https://example.com/calstrs-ai-production",
        }
    ])
