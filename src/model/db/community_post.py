import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "community_post"

    id = pw.CharField(max_length=64, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True, default="")
    kind = pw.CharField(max_length=20, default="post")
    topic = pw.CharField(max_length=40, index=True, default="recommend")
    title = pw.CharField(max_length=200, default="")
    summary = pw.TextField(default="")
    category = pw.CharField(max_length=60, default="")
    destination = pw.CharField(max_length=120, default="")
    place = pw.CharField(max_length=160, default="")
    photo = pw.TextField(default="")
    photo_name = pw.CharField(max_length=200, default="")
    author = pw.CharField(max_length=80, default="")
    likes = pw.IntegerField(default=0)
    comments = pw.IntegerField(default=0)
    views = pw.IntegerField(default=0)
    votes = pw.IntegerField(default=0)
    tags = pw.TextField(default="[]")
    poll = pw.TextField(default="")
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField(index=True)
