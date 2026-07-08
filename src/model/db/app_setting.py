import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "app_setting"

    id = pw.CharField(max_length=32, primary_key=True)
    key = pw.CharField(max_length=80, unique=True, index=True)
    value = pw.TextField(default="")
    updated = pw.DateTimeField()
