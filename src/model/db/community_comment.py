import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "community_comment"

    id = pw.CharField(max_length=64, primary_key=True)
    post_id = pw.CharField(max_length=64, index=True)
    user_id = pw.CharField(max_length=32, index=True, default="")
    author = pw.CharField(max_length=80, default="")
    body = pw.TextField(default="")
    created = pw.DateTimeField(index=True)
