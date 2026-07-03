session = wiz.model("portal/season/session").use()
ai_chat = wiz.model("ai_chat")


def _current_user_id():
    return session.get("id", "")


def send():
    status, payload = ai_chat.send(
        wiz.request.query("prompt", ""),
        wiz.request.query("history", "[]"),
        _current_user_id(),
        wiz.request.query("thread_id", "").strip()
    )
    wiz.response.status(status, **payload)


def threads():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    wiz.response.status(200, threads=ai_chat.threads(user_id))


def thread():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    item = ai_chat.thread(user_id, wiz.request.query("thread_id", "").strip())
    if item is None:
        wiz.response.status(404, message="대화 기록을 찾을 수 없습니다.")
        return

    wiz.response.status(200, thread=item)
