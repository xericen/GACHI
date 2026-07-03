import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "featured_course"

    id = pw.CharField(max_length=32, primary_key=True)
    course_id = pw.CharField(max_length=32, index=True)
    display_order = pw.IntegerField(default=0, index=True)
    starts_at = pw.CharField(max_length=20, default="")
    ends_at = pw.CharField(max_length=20, default="")
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField()
