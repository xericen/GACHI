import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "course_collaboration_votes"
        indexes = (
            (("item_id", "user_id"), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    item_id = pw.CharField(max_length=32, index=True)
    user_id = pw.CharField(max_length=32, index=True)
    created = pw.DateTimeField(index=True)
