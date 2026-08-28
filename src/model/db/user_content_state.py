import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "user_content_state"
        indexes = (
            (("user_id", "content_type", "content_id"), True),
        )

    id = pw.CharField(max_length=64, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    content_type = pw.CharField(max_length=24, index=True)
    content_id = pw.CharField(max_length=64, index=True)
    state = pw.CharField(max_length=24, default="active", index=True)
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField(index=True)
