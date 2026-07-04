import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "community_reaction"

    id = pw.CharField(max_length=64, primary_key=True)
    post_id = pw.CharField(max_length=64, index=True)
    user_key = pw.CharField(max_length=160, index=True)
    reaction_type = pw.CharField(max_length=20, index=True)
    option = pw.CharField(max_length=200, default="")
    created = pw.DateTimeField(index=True)
