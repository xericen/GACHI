import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "mobile_device"

    id = pw.CharField(max_length=32, primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    device_token = pw.CharField(max_length=512, unique=True)
    platform = pw.CharField(max_length=16, default="ios", index=True)
    app_version = pw.CharField(max_length=32, default="")
    locale = pw.CharField(max_length=32, default="ko-KR")
    enabled = pw.BooleanField(default=True, index=True)
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField(index=True)
