import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "course_collaboration_items"
        indexes = (
            (("course_id", "created"), False),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    course_id = pw.CharField(max_length=32, index=True)
    user_id = pw.CharField(max_length=32, index=True)
    author_name = pw.CharField(max_length=80, default="여행자")
    title = pw.CharField(max_length=120)
    detail = pw.TextField(default="")
    status = pw.CharField(max_length=16, default="open", index=True)
    vote_count = pw.IntegerField(default=0)
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField(index=True)
