import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "companion_chat_event"

    id = pw.AutoField(primary_key=True)
    event_type = pw.CharField(max_length=32, index=True)
    post_id = pw.CharField(max_length=64, index=True)
    actor_user_id = pw.CharField(max_length=32, index=True, default="")
    payload_json = pw.TextField(default="{}")
    created = pw.DateTimeField(index=True)
