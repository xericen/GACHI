import secrets

struct = wiz.model("struct")

def list():
    text = wiz.request.query("text", "")
    role = wiz.request.query("role", "")

    members = struct.user.list(text=text, role=role)

    # 아바타 컬러 추가
    colors = [
        "bg-red-100 text-red-700",
        "bg-pink-100 text-pink-700",
        "bg-green-100 text-green-700",
        "bg-amber-100 text-amber-700",
        "bg-red-100 text-red-700",
        "bg-violet-100 text-violet-700",
    ]
    for i, m in enumerate(members):
        m["avatarColor"] = colors[i % len(colors)]
        m["joined"] = str(m.get("created", ""))[:10]

    wiz.response.status(200, members)

def invite():
    email = wiz.request.query("email", "")
    role = wiz.request.query("role", "viewer")

    if not email:
        wiz.response.status(400, message="이메일을 입력해주세요.")

    existing = struct.user.db.get(email=email)
    if existing:
        wiz.response.status(400, message="이미 등록된 사용자입니다.")

    temporary_password = secrets.token_urlsafe(16)
    struct.user.create(dict(
        email=email,
        password=temporary_password,
        name=email.split("@")[0],
        role=role
    ))

    wiz.response.status(200, dict(temporary_password=temporary_password))

def remove():
    id = wiz.request.query("id", "")
    if not id:
        wiz.response.status(400, message="ID가 필요합니다.")

    struct.user.db.delete(id=id)
    wiz.response.status(200)
