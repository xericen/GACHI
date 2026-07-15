import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "signal_meetings"
        indexes = (
            (("signal_id",), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    signal_id = pw.CharField(max_length=32, unique=True, index=True)
    owner_user_id = pw.CharField(max_length=32, index=True)
    responder_user_id = pw.CharField(max_length=32, index=True)
    title = pw.CharField(max_length=100, default="")
    location_label = pw.CharField(max_length=100, default="")
    status = pw.CharField(max_length=16, default="active", index=True)
    ends_at = pw.DateTimeField(index=True)
    created_at = pw.DateTimeField(index=True)
    updated_at = pw.DateTimeField(index=True)
