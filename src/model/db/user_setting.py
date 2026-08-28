import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "user_setting"

    user_id = pw.CharField(max_length=32, primary_key=True)
    account_json = pw.TextField(default="{}")
    professional_json = pw.TextField(default="{}")
    billing_json = pw.TextField(default="{}")
    resume_json = pw.TextField(default="{}")
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField(index=True)
