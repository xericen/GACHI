import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "signal_reports"
        indexes = (
            (("signal_id", "reporter_user_id"), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    signal_id = pw.CharField(max_length=32, index=True)
    reporter_user_id = pw.CharField(max_length=32, index=True)
    reported_user_id = pw.CharField(max_length=32, index=True)
    reason = pw.CharField(max_length=120, default="")
    created_at = pw.DateTimeField(index=True)
