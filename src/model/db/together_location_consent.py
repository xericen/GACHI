import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "together_location_consents"
        indexes = (
            (("meeting_id", "user_id"), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    meeting_id = pw.CharField(max_length=32, index=True)
    user_id = pw.CharField(max_length=32, index=True)
    status = pw.CharField(max_length=16, default="inactive", index=True)
    share_duration = pw.CharField(max_length=16, default="60")
    expires_at = pw.DateTimeField(index=True)
    home_enabled = pw.BooleanField(default=True)
    stay_enabled = pw.BooleanField(default=True)
    home_lat = pw.DoubleField(null=True)
    home_lng = pw.DoubleField(null=True)
    stay_lat = pw.DoubleField(null=True)
    stay_lng = pw.DoubleField(null=True)
    created_at = pw.DateTimeField(index=True)
    updated_at = pw.DateTimeField(index=True)
