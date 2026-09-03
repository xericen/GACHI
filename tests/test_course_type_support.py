from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACCESS_APP = PROJECT_ROOT / "src" / "app" / "page.access"


def test_course_builder_exposes_travel_and_date_types():
    template = (ACCESS_APP / "view.pug").read_text(encoding="utf-8")

    assert 'setCourseType(\'여행\')' in template
    assert 'setCourseType(\'데이트\')' in template
    assert 'aria-label="코스 유형 선택"' in template
    assert "여행 · 데이트 코스" in template


def test_course_type_is_persisted_and_used_in_tags():
    view = (ACCESS_APP / "view.ts").read_text(encoding="utf-8")
    api = (ACCESS_APP / "api.py").read_text(encoding="utf-8")

    assert "let courseType = String(this.courseDraft.category" in view
    assert "tags: this.uniqueTags([courseType" in view
    assert 'data["category"] = "데이트"' in api
    assert 'data["tags"] = [data["category"]]' in api
