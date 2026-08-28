import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "user_activity_event"
        indexes = (
            (("user_id", "event_type", "target_id"), True),
        )

    id = pw.CharField(max_length=64, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    event_type = pw.CharField(max_length=24, index=True)
    target_type = pw.CharField(max_length=24, default="feed")
    target_id = pw.CharField(max_length=64, index=True)
    title = pw.CharField(max_length=200, default="")
    meta_json = pw.TextField(default="{}")
    created = pw.DateTimeField(index=True)
