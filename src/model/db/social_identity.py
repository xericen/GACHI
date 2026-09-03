import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "social_identity"
        indexes = (
            (("provider", "subject_hash"), True),
        )

    id = pw.CharField(max_length=32, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    provider = pw.CharField(max_length=16, index=True)
    subject_hash = pw.CharField(max_length=64)
    email_hash = pw.CharField(max_length=64, default="")
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField()
