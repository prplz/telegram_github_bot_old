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
    text = "<b>%s</b>" % json_body["pusher"]["name"]

    # how many commits
    if len(commits) == 1:
        text += " pushed to "
    else:
        text += " pushed %d commits to " % len(commits)

    # branch
    branch = json_body["ref"].split("/")[-1]
    if branch != "master":
        text += "branch <b>%s</b> on " % branch

    # repo (link)
    text += '<a href="%s">%s</a>' % (
        json_body["repository"]["url"],
        json_body["repository"]["full_name"],
    )

    # commits
    commits_end = 9 if len(commits) > 10 else len(commits)
    for commit in commits[:commits_end]:
        # only use first line
        message = commit["message"].split("\n")[0]
        text += '\n<a href="%s">%s</a> %s' % (commit["url"], commit["id"][:7], message)
    if commits_end < len(commits):
        text += "\n+%d more" % (len(commits) - commits_end)

    # compare link
    if len(commits) > 1:
        text += '\n<a href="%s">Compare</a>' % json_body["compare"]

    requests.post(
        "https://api.telegram.org/%s/sendMessage" % telegram_key,
        json={
            "chat_id": telegram_chat,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
    )

    return "OK"
