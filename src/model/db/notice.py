import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "notice"

    id = pw.CharField(max_length=32, primary_key=True)
    title = pw.CharField(max_length=200)
    content = pw.TextField(default="")
    starts_at = pw.CharField(max_length=20, default="")
    ends_at = pw.CharField(max_length=20, default="")
    is_active = pw.BooleanField(default=True, index=True)
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField()
