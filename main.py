import hmac
import os

import requests
from werkzeug.exceptions import Forbidden, MethodNotAllowed

webhook_secret = os.environ.get("WEBHOOK_SECRET")
telegram_key = os.environ["TELEGRAM_KEY"]
telegram_chat = os.environ["TELEGRAM_CHAT"]


def github_hook(request):
    if request.method != "POST":
        raise MethodNotAllowed()

    if webhook_secret is not None:
        signature = request.headers.get("X-Hub-Signature")
        if signature is None:
            raise Forbidden()

        digest = hmac.new(webhook_secret.encode("utf8"), request.get_data(), "sha1").hexdigest()

        if not hmac.compare_digest("sha1=" + digest, signature):
            raise Forbidden()

    github_event = request.headers.get("X-GitHub-Event")

    if github_event != "push":
        return "OK"

    json_body = request.get_json()

    commits = json_body["commits"]
    if len(commits) == 0:
        return "OK"

    # pusher
    sender = json_body["sender"]
    text = f'<a href="{sender["html_url"]}">{sender["login"]}</a>'

    # how many commits
    if len(commits) == 1:
        text += " pushed to "
    else:
        text += f" pushed {len(commits)} commits to "

    # branch
    branch = json_body["ref"].split("/")[-1]
    repo = json_body["repository"]

    if branch != repo["default_branch"]:
        text += f'branch <a href="{repo["url"]}/tree/{branch}">{branch}</a> on '

    # repo
    text += f'<a href="{repo["url"]}">{repo["full_name"]}</a>'

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
