import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "companion_application"

    id = pw.CharField(max_length=64, primary_key=True)
    post_id = pw.CharField(max_length=64, index=True)
    course_id = pw.CharField(max_length=64, index=True, default="")
    owner_user_id = pw.CharField(max_length=32, index=True, default="")
    applicant_user_id = pw.CharField(max_length=32, index=True)
    applicant_email = pw.CharField(max_length=128, default="")
    applicant_name = pw.CharField(max_length=80, default="")
    applicant_mobile = pw.CharField(max_length=20, default="")
    resume_json = pw.TextField(default="{}")
    identity_verified = pw.BooleanField(default=False)
    consent_version = pw.CharField(max_length=40)
    consent_at = pw.DateTimeField(index=True)
    ip_address = pw.CharField(max_length=64, default="")
    user_agent = pw.TextField(default="")
    status = pw.CharField(max_length=16, index=True, default="pending")
    evidence_hash = pw.CharField(max_length=64)
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField(index=True)
