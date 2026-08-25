# =============================================================================
# 프로젝트 루트 Struct (Composite Struct / Singleton)
# =============================================================================
# 호출 예시:
#   struct = wiz.model("struct")
#   struct.user.list()                    # 프로젝트 고유 User Sub-Struct
#   struct.user.authenticate(email, pw)   # 사용자 인증
#   struct.post.post.search()             # portal/post 패키지 Struct → Post Sub-Struct
# =============================================================================

class Struct:
    def __init__(self):
        self.orm = wiz.model("portal/season/orm")
        self.session = wiz.model("portal/season/session").use()

        # 프로젝트 고유 Sub-Struct 클래스 로드
        self._User = wiz.model("struct/user")
        self._Admin = wiz.model("struct/admin")
        self._Course = wiz.model("struct/course")
        self._Place = wiz.model("struct/place")
        self._Zenly = wiz.model("struct/zenly")
        self._Mobile = wiz.model("struct/mobile")

        # 패키지 Struct 캐시
        self._packages = {}

        # 앱 프로세스당 한 번만 테이블을 확인한다. 요청·소켓마다 전체 스키마를
        # 재확인하면 다중 서버 환경에서 불필요한 DB 연결이 급증한다.
        marker = "gachi_struct_tables_initialized"
        if not getattr(wiz.server.app, marker, False):
            self._init_tables()
            setattr(wiz.server.app, marker, True)

    def _init_tables(self):
        """DB 테이블이 없으면 자동 생성"""
        tables = [
            "user",
            "saved_course",
            "place",
            "course",
            "course_place",
            "course_checkin",
            "course_like",
            "chat_thread",
            "community_post",
            "companion_application",
            "companion_message",
            "companion_message_receipt",
            "companion_chat_event",
            "community_comment",
            "community_reaction",
            "featured_course",
            "filter_event",
            "notice",
            "app_setting",
            "place_presence_log",
            "signal",
            "signal_response",
            "signal_report",
            "signal_meeting",
            "signal_meeting_message",
            "mobile_device",
            "mobile_push_job",
        ]
        self._schema_tables = tables
        for name in tables:
            db = None
            try:
                db = self.orm.use(name)
                db.orm.create_table(safe=True)
            except Exception:
                pass
            finally:
                try:
                    database = db.orm._meta.database if db is not None else None
                    if database is not None and not database.is_closed():
                        database.close()
                except Exception:
                    pass
        try:
            self.admin.ensure_schema()
        except Exception:
            pass
        finally:
            self._close_schema_connections()

    def _close_schema_connections(self):
        for name in getattr(self, "_schema_tables", []):
            try:
                db = self.orm.use(name)
                database = db.orm._meta.database
                if not database.is_closed():
                    database.close()
            except Exception:
                pass

    def db(self, name):
        """ORM Wrapper 반환 (src/model/db/{name}.py)"""
        return self.orm.use(name)

    @property
    def user(self):
        """User Sub-Struct 접근 (호출마다 새 인스턴스)"""
        return self._User(self)

    @property
    def admin(self):
        """Admin Sub-Struct 접근"""
        return self._Admin(self)

    @property
    def course(self):
        """Course Sub-Struct 접근"""
        return self._Course(self)

    @property
    def place(self):
        """Place Sub-Struct 접근"""
        return self._Place(self)

    @property
    def zenly(self):
        """Zenly presence/signal Sub-Struct 접근"""
        return self._Zenly(self)

    @property
    def mobile(self):
        """모바일 디바이스 등록 Sub-Struct 접근"""
        return self._Mobile(self)

    def __getattr__(self, name):
        """알 수 없는 속성 → 패키지 Struct 동적 로드"""
        if name.startswith('_'):
            raise AttributeError(name)
        if name not in self._packages:
            try:
                self._packages[name] = wiz.model(f"portal/{name}/struct")
            except Exception:
                raise AttributeError(f"Package '{name}' not found")
        return self._packages[name]

Model = Struct()
