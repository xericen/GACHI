import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "user_daily_activity"
        indexes = (
            (("user_id", "activity_date"), True),
        )

    id = pw.CharField(max_length=64, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    activity_date = pw.DateField(index=True)
    first_seen = pw.DateTimeField(index=True)
    last_seen = pw.DateTimeField(index=True)
    login_count = pw.IntegerField(default=0)
    visit_count = pw.IntegerField(default=0)
