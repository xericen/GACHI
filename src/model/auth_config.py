class AuthConfig:
    MIN_SECRET_LENGTH = 32
    MIN_BOOTSTRAP_PASSWORD_LENGTH = 12

    def _config(self):
        return wiz.config("auth")

    def jwt_secret(self):
        value = str(getattr(self._config(), "jwt_secret", "") or "").strip()
        if len(value) < self.MIN_SECRET_LENGTH or value.startswith("CHANGE_ME"):
            raise ValueError("config/auth.py jwt_secret must be a unique value of at least 32 characters")
        return value.encode("utf-8")

    def bootstrap_admin(self):
        source = getattr(self._config(), "bootstrap_admin", None)
        if source is None or not bool(getattr(source, "enabled", False)):
            return None

        email = str(getattr(source, "email", "") or "").strip()
        password = str(getattr(source, "password", "") or "")
        name = str(getattr(source, "name", "") or "").strip()
        mobile = str(getattr(source, "mobile", "") or "").strip()

        if not email:
            raise ValueError("bootstrap_admin.email is required")
        if len(password) < self.MIN_BOOTSTRAP_PASSWORD_LENGTH:
            raise ValueError("bootstrap_admin.password must be at least 12 characters")

        return dict(
            email=email,
            password=password,
            name=name or email.split("@")[0],
            mobile=mobile,
            role="admin"
        )


Model = AuthConfig()
