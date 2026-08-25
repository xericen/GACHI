import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "companion_message"

    id = pw.CharField(max_length=32, primary_key=True)
    post_id = pw.CharField(max_length=64, index=True)
    sender_user_id = pw.CharField(max_length=32, index=True)
    text = pw.TextField()
    created = pw.DateTimeField(index=True)
