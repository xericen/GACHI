import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "course"

    id = pw.CharField(max_length=32, primary_key=True)
    title = pw.CharField(max_length=200, index=True)
    region = pw.CharField(max_length=100, default="", index=True)
    category = pw.CharField(max_length=80, default="", index=True)
    user_id = pw.CharField(max_length=32, default="", index=True)
    companion_type = pw.CharField(max_length=20, default="", index=True)
    description = pw.TextField(default="")
    image = pw.CharField(max_length=500, default="")
    cover_image = pw.CharField(max_length=500, default="")
    duration_type = pw.CharField(max_length=16, default="hours", index=True)
    duration_value = pw.CharField(max_length=50, default="")
    rating = pw.FloatField(null=True)
    is_featured = pw.BooleanField(default=False, index=True)
    is_public = pw.BooleanField(default=True, index=True)
    place_ids = pw.TextField(default="[]")
    tags = pw.TextField(default="[]")
    is_hidden = pw.BooleanField(default=False, index=True)
    display_order = pw.IntegerField(default=0, index=True)
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField()
