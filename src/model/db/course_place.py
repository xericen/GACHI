import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "course_places"
        indexes = (
            (("course_id", "place_id"), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    course_id = pw.CharField(max_length=32, index=True)
    place_id = pw.CharField(max_length=32, index=True)
    order_index = pw.IntegerField(default=1, index=True)
    visit_time = pw.CharField(max_length=20, default="")
    memo = pw.TextField(default="")
    created = pw.DateTimeField(index=True)
