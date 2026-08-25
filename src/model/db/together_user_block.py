import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "together_user_blocks"
        indexes = (
            (("blocker_user_id", "blocked_user_id"), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    blocker_user_id = pw.CharField(max_length=32, index=True)
    blocked_user_id = pw.CharField(max_length=32, index=True)
    created_at = pw.DateTimeField(index=True)
