import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHAT_TEMPLATE = PROJECT_ROOT / "src/app/page.access/view.pug"
CHAT_STYLES = PROJECT_ROOT / "src/app/page.access/view.scss"


class AiChatLayoutTests(unittest.TestCase):
    def test_composer_is_outside_the_message_scroller(self):
        lines = CHAT_TEMPLATE.read_text(encoding="utf-8").splitlines()
        layout_index = next(
            index for index, line in enumerate(lines)
            if 'div(class="ai-planner-layout"' in line
        )
        layout_indent = len(lines[layout_index]) - len(lines[layout_index].lstrip(" "))

        next_sibling = next(
            line for line in lines[layout_index + 1:]
            if line.strip() and len(line) - len(line.lstrip(" ")) <= layout_indent
        )

        self.assertEqual(
            len(next_sibling) - len(next_sibling.lstrip(" ")),
            layout_indent,
        )
        self.assertIn('form(class="composer ai-planner-composer"', next_sibling)

    def test_final_layout_rules_keep_only_messages_scrollable(self):
        styles = CHAT_STYLES.read_text(encoding="utf-8")
        final_rules = styles.split(
            "/* Bound the complete AI chat height chain so the message area can actually scroll. */",
            1,
        )[1]

        self.assertIn("flex: 1 1 0 !important;", final_rules)
        self.assertIn("overflow-y: auto !important;", final_rules)
        self.assertIn("position: relative !important;", final_rules)
        self.assertNotIn("position: sticky !important;", final_rules)

    def test_course_preview_can_close_and_reopen_without_losing_the_course(self):
        template = CHAT_TEMPLATE.read_text(encoding="utf-8")
        component = (PROJECT_ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")

        self.assertIn('(click)="closePlannerCoursePreview()"', template)
        self.assertIn('(click)="openPlannerCoursePreview()"', template)
        self.assertIn("public plannerCourseVisible: boolean = false;", component)
        self.assertIn("this.plannerCourseVisible = false;", component)
        self.assertIn("this.plannerCourseVisible = true;", component)

    def test_travel_condition_chips_scroll_horizontally_without_wrapping(self):
        template = CHAT_TEMPLATE.read_text(encoding="utf-8")
        styles = CHAT_STYLES.read_text(encoding="utf-8")
        component = (PROJECT_ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")
        chips = styles.split(".ai-travel-state-chips {", 1)[1]
        chips = chips.split("}", 1)[0]
        chip_item = styles.split(".ai-travel-state-chips span {", 1)[1]
        chip_item = chip_item.split("}", 1)[0]

        self.assertIn("flex-wrap: nowrap;", chips)
        self.assertIn("overflow-x: auto;", chips)
        self.assertIn("touch-action: pan-x;", chips)
        self.assertIn("-webkit-overflow-scrolling: touch;", chips)
        self.assertIn("flex: 0 0 auto;", chip_item)
        self.assertIn("white-space: nowrap;", chip_item)
        self.assertIn('(pointerdown)="startTravelConditionDrag($event)"', template)
        self.assertIn('(pointermove)="moveTravelConditionDrag($event)"', template)
        self.assertIn("public startTravelConditionDrag(event: any)", component)
        self.assertIn("target.scrollLeft = this.travelConditionDragScrollLeft - delta;", component)

    def test_planner_choices_follow_the_server_stage_and_keep_confirmation_separate(self):
        template = CHAT_TEMPLATE.read_text(encoding="utf-8")
        styles = CHAT_STYLES.read_text(encoding="utf-8")
        component = (PROJECT_ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")

        self.assertIn("plannerSuggestedReplies", component)
        self.assertIn("Array.isArray(payload.suggested_replies)", component)
        self.assertIn("후보·동선 확인 중", component)
        self.assertIn("this.plannerStage = 'checking_feasibility';", component)
        self.assertIn('(click)="editPlannerConditions()"', template)
        self.assertIn('(click)="selectPlannerSuggestedReply(reply)"', template)
        self.assertIn("코스 만들기", template)
        self.assertIn("조건 수정", template)
        self.assertIn("overflow-x: auto;", styles.split(".ai-planner-suggested-replies {", 1)[1].split("}", 1)[0])

    def test_new_chat_uses_compact_input_guides_and_then_server_replies(self):
        template = CHAT_TEMPLATE.read_text(encoding="utf-8")
        styles = CHAT_STYLES.read_text(encoding="utf-8")
        component = (PROJECT_ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")

        composer_index = template.index('form(class="composer ai-planner-composer"')
        quick_index = template.index('nav(class="ai-planner-quick-start"', composer_index)
        input_index = template.index('textarea(data-testid="chat-input"', quick_index)
        quick_styles = styles.split(".ai-planner-frame .ai-planner-quick-start {", 1)[1].split("}", 1)[0]

        self.assertLess(composer_index, quick_index)
        self.assertLess(quick_index, input_index)
        self.assertIn('*ngIf="plannerComposerQuickReplies().length"', template)
        self.assertIn('(click)="selectPlannerComposerQuickReply(reply)"', template)
        for label in ["어디로", "누구와", "언제", "여행 스타일"]:
            self.assertIn(label, component)
        for icon in ["fa-location-arrow", "fa-user-group", "fa-calendar-days", "fa-wand-magic-sparkles"]:
            self.assertIn(icon, component)
        for fixed_value in ["{ label: '제주도'", "{ label: '이번 주말에'", "{ label: '차 없이'"]:
            self.assertNotIn(fixed_value, component)
        self.assertIn("!hasUserMessage", component)
        self.assertIn("if (this.plannerSuggestedReplies.length) return this.plannerSuggestedReplies;", component)
        self.assertIn("this.draft = inputPrefix;", component)
        self.assertIn("input.focus()", component)
        self.assertIn("overflow-x: auto;", quick_styles)
        self.assertIn("touch-action: pan-x;", quick_styles)
        self.assertIn("flex: 0 0 auto;", quick_styles)
        self.assertIn("min-height: 27px;", styles.split(".ai-planner-frame .ai-planner-quick-start button {", 1)[1].split("}", 1)[0])
        self.assertIn('[class.initial-guide]="!!reply.inputPrefix"', template)
        self.assertIn('class="fa-solid quick-start-icon"', template)
        initial_style = styles.split(".ai-planner-frame .ai-planner-quick-start button.initial-guide {", 1)[1].split("}", 1)[0]
        self.assertIn("border-radius: 10px;", initial_style)
        self.assertIn("box-shadow:", initial_style)

    def test_chat_header_uses_text_without_brand_logo(self):
        template = CHAT_TEMPLATE.read_text(encoding="utf-8")
        styles = CHAT_STYLES.read_text(encoding="utf-8")
        header_start = template.index('div(class="ai-planner-card-head")')
        header_end = template.index('button(type="button", class="chat-history-backdrop"', header_start)
        header = template[header_start:header_end]
        final_header_rule = styles.rsplit(".ai-planner-frame .ai-planner-card-head {", 1)[1].split("}", 1)[0]

        self.assertIn("strong GACHI AI", header)
        self.assertNotIn('class="ai-chat-logo"', header)
        self.assertNotIn("gachi-logo.png", header)
        self.assertIn("grid-template-columns: 34px minmax(0, 1fr) 34px !important;", final_header_rule)

    def test_chat_archive_has_owner_scoped_delete_action(self):
        template = CHAT_TEMPLATE.read_text(encoding="utf-8")
        component = (PROJECT_ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")
        api = (PROJECT_ROOT / "src/app/page.access/api.py").read_text(encoding="utf-8")

        self.assertIn('(click)="requestDeleteChatThread(thread)"', template)
        self.assertIn('(click)="deleteChatThread(thread)"', template)
        self.assertIn("public chatDeleteConfirmThreadId: string = '';", component)
        self.assertNotIn("window.confirm('이 AI 채팅을 삭제할까요?", component)
        self.assertIn("wiz.call('chat_thread_delete'", component)
        self.assertIn("def chat_thread_delete():", api)
        self.assertIn("ai_chat.delete_thread(user_id, thread_id)", api)

    def test_chat_request_has_bounded_wait_without_duplicate_context_loader(self):
        template = CHAT_TEMPLATE.read_text(encoding="utf-8")
        component = (PROJECT_ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")

        self.assertNotIn("대화 내용을 실시간 코스 준비에 반영하고 있어요", template)
        self.assertIn("{ timeout: 45000 }", component)
        self.assertNotIn("AI 연결이 불안정해요", component)

    def test_course_confirmation_is_idempotent_and_starts_a_new_chat_after_save(self):
        template = CHAT_TEMPLATE.read_text(encoding="utf-8")
        component = (PROJECT_ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")

        self.assertIn('[disabled]="plannerCourseConfirming"', template)
        self.assertIn("if (this.plannerCourseConfirming) return;", component)
        self.assertIn("`planner-course-${threadId}`.slice(0, 64)", component)
        self.assertIn("Number(createResponse.code || 0) !== 200", component)
        save_index = component.index("createResponse = await wiz.call('create_builder_course'")
        archive_index = component.index("await this.loadChatThreads(false);", save_index)
        new_chat_index = component.index("await this.startNewChat();", archive_index)
        self.assertLess(save_index, archive_index)
        self.assertLess(archive_index, new_chat_index)

    def test_itinerary_time_card_contains_long_schedule_labels(self):
        template = CHAT_TEMPLATE.read_text(encoding="utf-8")
        styles = CHAT_STYLES.read_text(encoding="utf-8")
        final_rules = styles.split(
            "/* Keep itinerary labels and times contained in the left timeline card. */",
            1,
        )[1]

        self.assertEqual(template.count('span(class="route-time-copy")'), 2)
        self.assertIn("grid-template-columns: 64px minmax(0, 1fr) !important;", final_rules)
        self.assertIn("width: 64px !important;", final_rules)
        self.assertIn("height: 44px !important;", final_rules)
        self.assertIn("min-height: 44px !important;", final_rules)
        self.assertIn(".ai-planner-frame .route-stop-rail", final_rules)
        self.assertIn("align-items: stretch !important;", final_rules)
        self.assertIn("justify-self: center;", final_rules)
        self.assertIn("margin: 0 auto !important;", final_rules)
        self.assertIn("transform: none !important;", final_rules)
        self.assertIn(".route-time > .route-time-copy", final_rules)
        self.assertIn("position: absolute;", final_rules)
        self.assertIn("inset: 0;", final_rules)
        self.assertIn("flex-direction: column;", final_rules)
        self.assertIn("align-items: center !important;", final_rules)
        self.assertIn("justify-content: center !important;", final_rules)
        self.assertIn("gap: 2px;", final_rules)
        self.assertIn("padding: 5px 3px !important;", final_rules)
        self.assertGreaterEqual(final_rules.count("margin: 0 !important;"), 2)
        self.assertIn("overflow: hidden !important;", final_rules)
        self.assertIn("white-space: nowrap !important;", final_rules)
        self.assertIn("word-break: keep-all;", final_rules)


if __name__ == "__main__":
    unittest.main()
