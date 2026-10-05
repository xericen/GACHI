import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "course_travel_review"
        indexes = ((("course_id", "reviewer_id", "target_id"), True),)

    id = pw.CharField(max_length=64, primary_key=True)
    course_id = pw.CharField(max_length=64, index=True)
    reviewer_id = pw.CharField(max_length=32, index=True)
    target_id = pw.CharField(max_length=32, index=True)
    rating = pw.IntegerField()
    comment = pw.TextField()
    evidence_json = pw.TextField(default="{}")
    created = pw.DateTimeField(index=True)
