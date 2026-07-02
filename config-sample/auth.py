import season

# Generate a unique value, for example: openssl rand -hex 32
jwt_secret = "CHANGE_ME_WITH_AT_LEAST_32_RANDOM_CHARACTERS"

# Disabled by default. Enable only for the first administrator bootstrap,
# then disable it immediately after the account has been created.
bootstrap_admin = season.util.stdClass(
    enabled=False,
    email="",
    password="",
    name="",
    mobile=""
)
