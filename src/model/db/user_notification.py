import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "user_notifications"
        indexes = (
            (("user_id", "created"), False),
            (("user_id", "is_read"), False),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    event_type = pw.CharField(max_length=32, default="general", index=True)
    title = pw.CharField(max_length=100, default="")
    body = pw.CharField(max_length=500, default="")
    deep_link = pw.CharField(max_length=500, default="")
    payload = pw.TextField(default="{}")
    is_read = pw.BooleanField(default=False, index=True)
    created = pw.DateTimeField(index=True)
    read_at = pw.DateTimeField(null=True)
