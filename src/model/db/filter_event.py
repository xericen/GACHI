import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "filter_event"

    id = pw.CharField(max_length=32, primary_key=True)
    user_id = pw.CharField(max_length=32, default="", index=True)
    filter_key = pw.CharField(max_length=40, index=True)
    filter_value = pw.CharField(max_length=120, index=True)
    created = pw.DateTimeField(index=True)
