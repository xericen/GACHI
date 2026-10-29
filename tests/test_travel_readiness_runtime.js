const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const ts = require('typescript');

const source = fs.readFileSync('src/app/page.access/view.ts', 'utf8');
const start = source.indexOf('    public plannerFailureLabel()');
const end = source.indexOf('    public async selectPlannerDestination(', start);
assert(start >= 0 && end > start);
const script = ts.transpile(
    'class Planner { ' + source.slice(start, end) + ' }\nglobalThis.Planner = Planner;',
    { target: ts.ScriptTarget.ES2020 }
);
const context = {};
vm.createContext(context);
vm.runInContext(script, context);

function planner() {
    const instance = new context.Planner();
    instance.plannerTravelState = {};
    instance.plannerStage = 'collecting';
    instance.plannerAction = 'ask_clarification';
    instance.plannerMissingSlots = [];
    instance.plannerFailureStage = '';
    instance.applyPlannerDraft = () => {};
    return instance;
}

const tomorrowOnly = {
    stage: 'ready_to_generate',
    travel_state: { days: 1, start_date: '2026-10-29', end_date: '2026-10-29' },
    missing_slots: [],
    message: '입력 조건을 정리했어요. 코스 만들기를 눌러주세요.',
    suggested_replies: [{ label: '코스 만들기', prompt: '이 조건으로 코스 만들어줘' }]
};
let p = planner();
p.plannerFailureStage = 'travel_conditions';
assert.equal(p.plannerFailureLabel(), '');
p.plannerStage = 'error';
p.plannerAction = 'answer_only';
assert.equal(p.plannerFailureLabel(), '여행 조건을 조금 더 알려주세요.');

p = planner();
p.applyPlannerContract(tomorrowOnly);
assert.equal(p.plannerCanOfferCourse(), false);
assert.equal(p.plannerStage, 'collecting');
assert.equal(p.plannerMissingSlots[0], 'region');
assert(tomorrowOnly.message.includes('어느 지역'));
assert(!tomorrowOnly.message.includes('코스 만들기'));
assert.equal(p.plannerSuggestedReplies.length, 0);

p = planner();
p.applyPlannerContract({
    stage: 'ready_to_generate',
    travel_state: { region: '2026-10-29', destination: '2026-10-29', days: 1, transport: '미정' },
    missing_slots: []
});
assert.equal(p.plannerCanOfferCourse(), false);
assert.equal(p.plannerTravelState.region, '');
assert.equal(p.plannerTravelState.destination, null);

const complete = {
    region: '부산', days: 1, start_date: '2026-10-29', end_date: '2026-10-29',
    start_location: '부산역', transport: '대중교통', arrival_time: '14:00', departure_time: '18:00'
};
p = planner();
p.applyPlannerContract({ stage: 'ready_to_generate', travel_state: complete, missing_slots: [], can_generate: true });
assert.equal(p.plannerCanOfferCourse(), true);

p = planner();
p.applyPlannerContract({
    stage: 'ready_to_generate', travel_state: { ...complete, transport: '미정' }, missing_slots: []
});
assert.equal(p.plannerCanOfferCourse(), false);
assert.equal(p.plannerTravelState.pending_slot, 'transport');

p = planner();
p.applyPlannerContract({
    stage: 'ready_to_generate', travel_state: { ...complete, departure_time: '13:00' }, missing_slots: []
});
assert.equal(p.plannerCanOfferCourse(), false);
assert.equal(p.plannerTravelState.pending_slot, 'time_window');

p = planner();
p.applyPlannerContract({ stage: 'ready_to_generate', travel_state: complete, missing_slots: [], can_generate: false });
assert.equal(p.plannerCanOfferCourse(), false);

const template = fs.readFileSync('src/app/page.access/view.pug', 'utf8');
assert(template.includes('*ngIf="plannerCanOfferCourse()"'));
assert(source.indexOf('this.applyPlannerContract(data);', source.indexOf('private async sendChatPrompt'))
    < source.indexOf('reply.text = data.message', source.indexOf('private async sendChatPrompt')));
assert(!source.includes('어디로, 누구와, 언제 가는지만 말해주면 코스 초안을 바로 잡아드릴게요.'));
console.log('여행 준비 UI 회귀 검사: 날짜만 입력/오래된 준비 응답/스레드 복원/미정 교통/역전 시간 차단, 충분한 조건의 버튼 표시 통과');
