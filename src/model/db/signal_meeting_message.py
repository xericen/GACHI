import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "signal_meeting_messages"

    id = pw.CharField(max_length=32, primary_key=True)
    meeting_id = pw.CharField(max_length=32, index=True)
    sender_user_id = pw.CharField(max_length=32, default="", index=True)
    message = pw.CharField(max_length=100, default="")
    created_at = pw.DateTimeField(index=True)
