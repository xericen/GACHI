import os
import season

# Apple Team ID는 Apple Developer > Membership에서 확인하는 10자리 값입니다.
# 운영 환경에서는 파일에 비밀키를 넣지 말고 환경 변수로 주입하세요.
apple_team_id = os.getenv("APPLE_TEAM_ID", "")
apple_app_id_prefix = os.getenv("APPLE_APP_ID_PREFIX", apple_team_id)
apple_bundle_id = os.getenv("APPLE_BUNDLE_ID", "com.wizide.gachi")
