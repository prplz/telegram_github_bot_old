import hmac
import json
import os

import requests
from flask import abort

webhook_secret = bytes(os.environ["WEBHOOK_SECRET"], "utf-8")
telegram_key = os.environ.get("TELEGRAM_KEY")
telegram_chat = os.environ.get("TELEGRAM_CHAT")


def github_hook(request):
    if request.method != "POST":
        return abort(405)

    signature = request.headers.get("X-Hub-Signature")
    if signature is None:
        return abort(403)

    body = request.get_data()
    digest = hmac.new(webhook_secret, body, "sha1").hexdigest()

    if not hmac.compare_digest("sha1=" + digest, signature):
        return abort(403)

    github_event = request.headers.get("X-GitHub-Event")

    if github_event != "push":
        return "OK"

    json_body = json.loads(body.decode("utf-8"))

    commits = json_body["commits"]
    if len(commits) == 0:
        return "OK"

    # pusher
    text = f'<a href="{json_body["sender"]["html_url"]}">{json_body["pusher"]["name"]}</a>'

    # how many commits
    if len(commits) == 1:
        text += " pushed to "
    else:
        text += f" pushed {len(commits)} commits to "

    # branch
    branch = json_body["ref"].split("/")[-1]
    if branch != "master":
        text += f'branch <a href="{json_body["repository"]["url"]}/{branch}">{branch}</a> on '

    # repo (link)
    text += f'<a href="{json_body["repository"]["url"]}">{json_body["repository"]["full_name"]}</a>'

    # commits
    commits_end = 9 if len(commits) > 10 else len(commits)
    for commit in commits[:commits_end]:
        # only use first line
        message = commit["message"].split("\n")[0]
        text += f'\n<a href="{commit["url"]}">{commit["id"][:7]}</a> {message}'
    if commits_end < len(commits):
        text += f"\n+{len(commits) - commits_end} more"

    # compare link
    if len(commits) > 1:
        text += f'\n<a href="{json_body["compare"]}">Compare</a>'

    requests.post(
        f"https://api.telegram.org/{telegram_key}/sendMessage",
        json={
            "chat_id": telegram_chat,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
    )

    return "OK"
