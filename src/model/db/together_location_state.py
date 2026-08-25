import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "together_location_states"
        indexes = (
            (("meeting_id", "user_id"), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    meeting_id = pw.CharField(max_length=32, index=True)
    user_id = pw.CharField(max_length=32, index=True)
    lat = pw.DoubleField()
    lng = pw.DoubleField()
    accuracy = pw.DoubleField(default=0)
    created_at = pw.DateTimeField(index=True)
    updated_at = pw.DateTimeField(index=True)
