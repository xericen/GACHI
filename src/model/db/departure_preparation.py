import peewee as pw
orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "departure_preparation"
    id = pw.CharField(max_length=32, primary_key=True)
    scope = pw.CharField(max_length=140, index=True)
    user_id = pw.CharField(max_length=32, index=True)
    data = pw.TextField(default="{}")
    updated = pw.DateTimeField()
