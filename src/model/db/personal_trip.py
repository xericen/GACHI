import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "personal_trip"
        indexes = (
            (("user_id", "course_id"), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    course_id = pw.CharField(max_length=64, index=True)
    course_source = pw.CharField(max_length=16, default="mine")
    title = pw.CharField(max_length=200, default="")
    location = pw.CharField(max_length=100, default="")
    start_date = pw.CharField(max_length=10, default="", index=True)
    end_date = pw.CharField(max_length=10, default="")
    status = pw.CharField(max_length=16, default="planned", index=True)
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField()
