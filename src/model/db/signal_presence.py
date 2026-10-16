import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "signal_presences"

    id = pw.CharField(max_length=32, primary_key=True)
    lat = pw.DoubleField()
    lng = pw.DoubleField()
    accuracy = pw.DoubleField()
    updated_at = pw.DateTimeField(index=True)
