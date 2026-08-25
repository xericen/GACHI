import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "signal_meeting_message_receipts"
        indexes = (
            (("message_id", "user_id"), True),
        )

    id = pw.CharField(max_length=64, primary_key=True)
    meeting_id = pw.CharField(max_length=32, index=True)
    message_id = pw.CharField(max_length=32, index=True)
    user_id = pw.CharField(max_length=32, index=True)
    read_at = pw.DateTimeField(index=True)
