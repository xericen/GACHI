import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "course_checkins"
        indexes = (
            (("user_id", "course_id", "place_id"), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    course_id = pw.CharField(max_length=64, index=True)
    place_id = pw.CharField(max_length=64, index=True)
    method = pw.CharField(max_length=16, default="manual", index=True)
    lat = pw.CharField(max_length=40, default="")
    lng = pw.CharField(max_length=40, default="")
    checked_at = pw.DateTimeField(index=True)
