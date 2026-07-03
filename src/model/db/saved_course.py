import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "saved_course"

    id = pw.CharField(max_length=32, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    course_id = pw.CharField(max_length=64, index=True)
    title = pw.CharField(max_length=200, default="")
    location = pw.CharField(max_length=100, default="")
    summary = pw.TextField(default="")
    duration = pw.CharField(max_length=50, default="")
    rating = pw.CharField(max_length=20, default="")
    icon = pw.CharField(max_length=50, default="")
    tone = pw.CharField(max_length=50, default="")
    places_json = pw.TextField(default="[]")
    route_json = pw.TextField(default="{}")
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField()
