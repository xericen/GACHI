import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "place_presence_log"
        indexes = (
            (("place_id", "hour_bucket"), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    place_id = pw.CharField(max_length=64, index=True)
    region = pw.CharField(max_length=100, default="", index=True)
    hour_bucket = pw.DateTimeField(index=True)
    count = pw.IntegerField(default=0)
    created_at = pw.DateTimeField(index=True)
    updated_at = pw.DateTimeField(index=True)
