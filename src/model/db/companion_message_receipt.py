import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "companion_message_receipt"
        indexes = (
            (("message_id", "user_id"), True),
        )

    id = pw.CharField(max_length=64, primary_key=True)
    post_id = pw.CharField(max_length=64, index=True)
    message_id = pw.CharField(max_length=32, index=True)
    user_id = pw.CharField(max_length=32, index=True)
    read_at = pw.DateTimeField(index=True)
    created = pw.DateTimeField(index=True)
