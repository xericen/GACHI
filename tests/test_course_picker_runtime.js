const fs = require('fs');
const vm = require('vm');
const assert = require('node:assert/strict');
const ts = require('../build/node_modules/typescript');
const source = fs.readFileSync(__dirname + '/../src/app/page.access/view.ts', 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.CommonJS } }).outputText;
const sandbox = { exports: {}, require: () => ({}), window: {}, console };
vm.runInNewContext(compiled, sandbox);
const Component = sandbox.exports.Component;
function setup() {
    const events = [];
    const course = { id: 'saved', source: 'saved', companion_post_ids: ['post'] };
    const component = Object.assign(Object.create(Component.prototype), {
        service: { render: async () => {} },
        mapExecutableCourses: [course], stagedExecutionCourseId: 'saved',
        directChats: [], myTripBusy: false, mapRouteLoading: false, mapCoursePickerOpen: true,
        selectExecutionCourse: async c => events.push(['map', c.id]),
        loadDirectChatRooms: async () => true,
        setTab: async tab => events.push(['tab', tab]),
        setChatContentTab: async tab => events.push(['chat', tab]),
        selectDirectChat: async room => events.push(['room', room.id]),
        openCompanionMode: async mode => events.push(['find', mode]),
        openCompanionCoursePicker: async () => {},
        setCompanionCoursePickerTab: async tab => events.push(['source', tab]),
        companionPickerCourses: () => [course],
        selectCompanionCourse: async c => events.push(['course', c.id]),
    });
    return { component, events };
}
(async () => {
    const solo = setup();
    sandbox.wiz = { call: async (name, args) => {
        assert.equal(name, 'personal_trip');
        assert.equal(args.action, 'save');
        assert.equal(args.course_id, 'saved');
        assert.equal('start_date' in args, false);
        assert.equal('end_date' in args, false);
        return { code: 200, data: { trip: { id: 'trip', course_id: 'saved' } } };
    } };
    await solo.component.chooseTravelMode('solo');
    assert.deepEqual(solo.events, [['map', 'saved']]);
    assert.equal(solo.component.myTripOpen, false);

    const matched = setup();
    matched.component.directChats = [{ id: 'room', category: 'companion', companionPostId: 'post' }];
    await matched.component.chooseTravelMode('companion');
    assert.deepEqual(matched.events, [['tab', 'chat'], ['chat', 'dm'], ['room', 'room']]);

    const unmatched = setup();
    unmatched.component.directChats = [{ id: 'unrelated', category: 'companion', companionPostId: 'other' }];
    await unmatched.component.chooseTravelMode('companion');
    assert.deepEqual(unmatched.events, []);
    assert.equal(unmatched.component.mapCoursePickerOpen, true);
    assert.equal(unmatched.component.companionSearchOffered, true);
    await unmatched.component.confirmCompanionSearch();
    assert.deepEqual(unmatched.events, [['find', 'pretrip'], ['source', 'saved'], ['course', 'saved']]);
    assert.equal(unmatched.component.mapCoursePickerOpen, false);

    const transient = setup();
    let attempts = 0;
    sandbox.wiz = { call: async () => ++attempts === 1 ? { code: 404, data: {} }
        : { code: 200, data: { trip: { id: 'trip', course_id: 'saved' } } } };
    await transient.component.chooseTravelMode('solo');
    assert.equal(attempts, 2);
    assert.deepEqual(transient.events, [['map', 'saved']]);

    const rejected = setup();
    sandbox.wiz = { call: async () => ({ code: 503, data: { message: '저장소 연결 실패' } }) };
    await rejected.component.chooseTravelMode('solo');
    assert.equal(rejected.component.myTripError, '저장소 연결 실패');
    assert.equal(rejected.component.mapCoursePickerOpen, true);
    assert.deepEqual(rejected.events, []);


    const failed = setup();
    failed.component.loadDirectChatRooms = async () => false;
    await failed.component.chooseTravelMode('companion');
    assert.equal(failed.component.mapCoursePickerOpen, true);
    assert.equal(failed.events.length, 0);
    assert.ok(failed.component.myTripError);

    const catalog = setup();
    catalog.component.isLoggedIn = () => true;
    sandbox.wiz = { call: async () => ({ code: 200, data: { courses: [
        { id: 'matched', source: 'companion' }, { id: 'mine', source: 'mine' }, { id: 'saved', source: 'saved' }
    ] } }) };
    await catalog.component.loadMapExecutionCourses(true);
    assert.equal(catalog.component.mapExecutableCourses.map(c => c.id).join(','), 'matched,mine,saved');
    console.log('PASS: solo without dates, matched room, search confirmation, transient route retry, save failure, room failure, all course sources (7 scenarios)');
})().catch(error => { console.error(error); process.exit(1); });
