import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "chat_thread"

    id = pw.CharField(max_length=32, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    title = pw.CharField(max_length=120, default="")
    messages = pw.TextField(default="[]")
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField(index=True)
