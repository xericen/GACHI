import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "mobile_push_jobs"
        indexes = (
            (("status", "available_at"), False),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    device_token = pw.CharField(max_length=512, index=True)
    event_type = pw.CharField(max_length=32, default="general", index=True)
    title = pw.CharField(max_length=100, default="")
    body = pw.CharField(max_length=500, default="")
    deep_link = pw.CharField(max_length=500, default="")
    payload = pw.TextField(default="{}")
    status = pw.CharField(max_length=16, default="queued", index=True)
    attempts = pw.IntegerField(default=0)
    available_at = pw.DateTimeField(index=True)
    last_error = pw.TextField(default="")
    created_at = pw.DateTimeField(index=True)
    updated_at = pw.DateTimeField(index=True)
    sent_at = pw.DateTimeField(null=True)
