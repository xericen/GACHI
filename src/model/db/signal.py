import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "signals"

    id = pw.CharField(max_length=32, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    place_id = pw.CharField(max_length=64, default="", index=True)
    lat = pw.DecimalField(max_digits=11, decimal_places=7)
    lng = pw.DecimalField(max_digits=11, decimal_places=7)
    message = pw.CharField(max_length=100, default="")
    mood_tags = pw.TextField(default="[]")
    duration_minutes = pw.IntegerField(default=60)
    expires_at = pw.DateTimeField(index=True)
    status = pw.CharField(max_length=16, default="active", index=True)
    matched_response_id = pw.CharField(max_length=32, default="", index=True)
    report_count = pw.IntegerField(default=0)
    created_at = pw.DateTimeField(index=True)
    updated_at = pw.DateTimeField(index=True)
