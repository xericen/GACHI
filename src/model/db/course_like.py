import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "course_likes"
        indexes = (
            (("course_id", "user_id"), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    course_id = pw.CharField(max_length=32, index=True)
    user_id = pw.CharField(max_length=32, null=True, index=True)
    created = pw.DateTimeField(index=True)
