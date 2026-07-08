import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "signal_responses"
        indexes = (
            (("signal_id", "responder_user_id"), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    signal_id = pw.CharField(max_length=32, index=True)
    responder_user_id = pw.CharField(max_length=32, index=True)
    status = pw.CharField(max_length=16, default="pending", index=True)
    chat_thread_id = pw.CharField(max_length=32, default="", index=True)
    created_at = pw.DateTimeField(index=True)
    updated_at = pw.DateTimeField(index=True)
