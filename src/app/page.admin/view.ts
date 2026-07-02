import { OnInit } from '@angular/core';
import { Chart, registerables } from 'chart.js';
import { Service } from '@wiz/libs/portal/season/service';

Chart.register(...registerables);

export class Component implements OnInit {
    public section: string = 'dashboard';
    public loading: boolean = false;

    public overview: any = {};
    public signupRange: string = '7d';
    public signups: any[] = [];
    public topCourses: any[] = [];
    public filterUsage: any = {};

    public users: any[] = [];
    public userSearch: any = { search: '', role: '' };
    public userRoles: string[] = ['user', 'admin', 'editor', 'viewer'];

    public places: any[] = [];
    public placeAreaSummary: any = { total: 0, rows: [] };
    public placeAreaDetail: any = { area: '', total: 0, categories: [], districts: [] };
    public selectedPlaceArea: string = '';
    public placeDetailLoading: boolean = false;
    public placeCategories: string[] = [];
    public placeSearch: any = { search: '', category: '', visibility: 'visible' };

    public courses: any[] = [];
    public courseCategories: string[] = [];
    public coursePlaces: any[] = [];
    public courseSearch: any = { search: '', category: '', visibility: 'visible' };
    public manualTags: string[] = ['신규', '인기', '에디터추천'];

    public featured: any[] = [];
    public featuredForm: any = { course_id: '', display_order: 1, starts_at: '', ends_at: '' };
    public courseLookup: string = '';

    public notices: any[] = [];
    public noticeForm: any = { title: '', content: '', starts_at: '', ends_at: '' };
    public termsData: any = { terms: '', privacy: '' };

    public modelSettings: any = {
        provider: 'Google Gemini',
        enabled: true,
        model: '',
        timeout: 30,
        temperature: 0.45,
        max_output_tokens: 900,
        api_key_configured: false,
        status: 'missing_key',
        models: [],
        tools: []
    };
    public modelForm: any = {};

    public editType: string = '';
    public editData: any = {};
    public dragFeaturedIndex: number = -1;

    private signupChart: any = null;

    constructor(public service: Service) { }

    public async ngOnInit() {
        await this.service.init();
        let returnTo = encodeURIComponent('/admin/dashboard');
        if (!this.service.auth.allow(`/login?returnTo=${returnTo}`)) return;
        if (!this.service.auth.allow.role('admin', '/')) return;

        this.section = this.routeSection();
        this.stripTokenParam();
        await this.load();
    }

    public goHome() {
        window.location.href = '/';
    }

    public async setSection(section: string) {
        this.section = section;
        await this.load();
    }

    public openNewCourse() {
        this.service.href('/admin/courses/new');
    }

    public sectionTitle() {
        let labels: any = {
            dashboard: '관리자 대시보드',
            users: '사용자 관리',
            places: '장소 관리',
            courses: '코스 관리',
            curation: '큐레이션',
            models: '모델 관리',
            settings: '시스템 설정'
        };
        return labels[this.section] || labels.dashboard;
    }

    public async load() {
        this.loading = true;
        await this.service.render();

        if (this.section === 'dashboard') await this.loadDashboard();
        if (this.section === 'users') await this.loadUsers();
        if (this.section === 'places') await this.loadPlaces();
        if (this.section === 'courses') await this.loadCourses();
        if (this.section === 'curation') await this.loadCuration();
        if (this.section === 'models') await this.loadModels();
        if (this.section === 'settings') await this.loadSettings();

        this.loading = false;
        await this.service.render();
        this.renderSignupChart();
    }

    public async loadDashboard() {
        let overview = await wiz.call('overview', {});
        if (overview.code === 200) this.overview = overview.data || {};

        let signups = await wiz.call('signups', { range: this.signupRange });
        if (signups.code === 200) this.signups = signups.data || [];

        let top = await wiz.call('top_courses', { limit: 10 });
        if (top.code === 200) this.topCourses = top.data || [];

        let usage = await wiz.call('filter_usage', {});
        if (usage.code === 200) this.filterUsage = usage.data || {};
    }

    public async loadUsers() {
        let result = await wiz.call('users', this.userSearch);
        if (result.code === 200) this.users = (result.data && result.data.rows) || [];
    }

    public async loadPlaces() {
        this.selectedPlaceArea = '';
        this.placeAreaDetail = { area: '', total: 0, categories: [], districts: [] };
        let result = await wiz.call('places', { visibility: this.placeSearch.visibility, summary_only: '1' });
        if (result.code === 200) {
            let rows = (result.data && result.data.rows) || [];
            this.placeAreaSummary = (result.data && result.data.area_summary) || this.summarizePlaceAreas(rows);
            this.places = [];
        }
    }

    public async openPlaceArea(item: any) {
        let area = item && item.area ? item.area : '';
        if (!area) return;
        this.selectedPlaceArea = area;
        this.placeDetailLoading = true;
        this.placeAreaDetail = { area: area, total: 0, categories: [], districts: [] };
        await this.service.render();

        let result = await wiz.call('places', {
            visibility: this.placeSearch.visibility,
            summary_only: '1',
            area: area
        });
        if (result.code === 200) {
            let rows = (result.data && result.data.rows) || [];
            this.placeAreaDetail = (result.data && result.data.area_detail) || this.summarizePlaceAreaDetail(area, rows);
        }
        this.placeDetailLoading = false;
        await this.service.render();
    }

    public closePlaceArea() {
        this.selectedPlaceArea = '';
        this.placeAreaDetail = { area: '', total: 0, categories: [], districts: [] };
    }

    public async loadCourses() {
        let result = await wiz.call('courses', this.courseSearch);
        if (result.code === 200) {
            this.courses = (result.data && result.data.rows) || [];
            this.courseCategories = (result.data && result.data.categories) || [];
            this.coursePlaces = (result.data && result.data.places) || [];
        }
    }

    public async loadCuration() {
        await this.loadCourses();
        let result = await wiz.call('featured', {});
        if (result.code === 200) {
            this.featured = (result.data && result.data.rows) || [];
            this.featuredForm.display_order = this.featured.length + 1;
        }
    }

    public async loadSettings() {
        let notices = await wiz.call('notices', {});
        if (notices.code === 200) this.notices = (notices.data && notices.data.rows) || [];

        let terms = await wiz.call('terms', {});
        if (terms.code === 200) this.termsData = terms.data || { terms: '', privacy: '' };
    }

    public async loadModels() {
        let result = await wiz.call('model_settings', {});
        if (result.code === 404) result = await wiz.call('terms', { scope: 'models' });
        if (result.code !== 200) {
            await this.service.modal.error(this.responseMessage(result.data, 'AI 모델 설정을 불러오지 못했습니다.'));
            return;
        }
        this.modelSettings = result.data || this.modelSettings;
        this.modelForm = this.clone(this.modelSettings);
    }

    public async changeSignupRange(range: string) {
        this.signupRange = range;
        await this.loadDashboard();
        await this.service.render();
        this.renderSignupChart();
    }

    public openPlaceEditor(place: any) {
        this.editType = 'place';
        this.editData = this.clone(place);
    }

    public openCourseEditor(course: any) {
        this.editType = 'course';
        this.editData = this.clone(course);
        if (!Array.isArray(this.editData.place_ids)) this.editData.place_ids = [];
        if (!Array.isArray(this.editData.tags)) this.editData.tags = [];
        if (!this.editData.cover_image) this.editData.cover_image = this.editData.image || '';
        if (!this.editData.duration_type) this.editData.duration_type = 'hours';
        if (!this.editData.duration_value) this.editData.duration_value = this.editData.duration_type === 'hours' ? '4' : '1박 2일';
    }

    public closeEditor() {
        this.editType = '';
        this.editData = {};
    }

    public async saveEditor() {
        let action = this.editType === 'place' ? 'update_place' : 'update_course';
        let result = await wiz.call(action, {
            id: this.editData.id,
            data: JSON.stringify(this.editData)
        });
        if (result.code !== 200) {
            await this.service.modal.error(this.responseMessage(result.data, '저장에 실패했습니다.'));
            return;
        }
        this.closeEditor();
        if (this.section === 'places') await this.loadPlaces();
        if (this.section === 'courses') await this.loadCourses();
        if (this.section === 'curation') await this.loadCuration();
        await this.service.render();
    }

    public async hidePlace(place: any) {
        let ok = await this.confirm(`${place.name} 장소를 숨김 처리하시겠습니까?`, '숨김 처리');
        if (!ok) return;
        await wiz.call('hide_place', { id: place.id });
        await this.loadPlaces();
    }

    public async hideCourse(course: any) {
        let ok = await this.confirm(`${course.title} 코스를 숨김 처리하시겠습니까?`, '숨김 처리');
        if (!ok) return;
        await wiz.call('hide_course', { id: course.id });
        if (this.section === 'curation') await this.loadCuration();
        else await this.loadCourses();
    }

    public async toggleCourseFeatured(course: any) {
        let next = !course.is_featured;
        let result = await wiz.call('toggle_course_featured', {
            id: course.id,
            data: JSON.stringify({ is_featured: next })
        });
        if (result.code !== 200) {
            await this.service.modal.error(this.responseMessage(result.data, '인기 코스 설정 변경에 실패했습니다.'));
            return;
        }
        course.is_featured = next;
        if (this.section === 'curation') await this.loadCuration();
        else await this.loadCourses();
    }

    public async updateUserRole(user: any, role: string) {
        await wiz.call('update_user_role', { id: user.id, role: role });
        await this.loadUsers();
    }

    public canDeleteUser(user: any) {
        let session = this.service.auth && this.service.auth.session ? this.service.auth.session : {};
        if (!user || !user.id) return false;
        if (user.id === session.id) return false;
        if (user.email === 'admin' || user.role === 'admin') return false;
        return true;
    }

    public async deleteUser(user: any) {
        if (!this.canDeleteUser(user)) return;
        let label = user.name || user.email || '사용자';
        let ok = await this.confirm(`${label} 사용자를 삭제하시겠습니까?`, '삭제');
        if (!ok) return;
        let result = await wiz.call('delete_user', { id: user.id });
        if (result.code !== 200) {
            await this.service.modal.error(this.responseMessage(result.data, '사용자 삭제에 실패했습니다.'));
            return;
        }
        await this.loadUsers();
    }

    public async addFeatured() {
        let payload = this.clone(this.featuredForm);
        let result = await wiz.call('add_featured', { data: JSON.stringify(payload) });
        if (result.code !== 200) {
            await this.service.modal.error(this.responseMessage(result.data, '추천 코스 추가에 실패했습니다.'));
            return;
        }
        this.featuredForm = { course_id: '', display_order: this.featured.length + 2, starts_at: '', ends_at: '' };
        await this.loadCuration();
    }

    public async removeFeatured(item: any) {
        let ok = await this.confirm(`${item.course_title || '추천 코스'} 노출을 해제하시겠습니까?`, '해제');
        if (!ok) return;
        await wiz.call('remove_featured', { id: item.id });
        await this.loadCuration();
    }

    public dragStart(index: number) {
        this.dragFeaturedIndex = index;
    }

    public async dropFeatured(index: number) {
        if (this.dragFeaturedIndex < 0 || this.dragFeaturedIndex === index) return;
        let item = this.featured.splice(this.dragFeaturedIndex, 1)[0];
        this.featured.splice(index, 0, item);
        this.dragFeaturedIndex = -1;
        await wiz.call('reorder_featured', { items: JSON.stringify(this.featured) });
        await this.loadCuration();
    }

    public allowDrop(event: any) {
        event.preventDefault();
    }

    public async saveCourseTags(course: any) {
        await wiz.call('update_course_tags', {
            id: course.id,
            tags: JSON.stringify(course.tags || [])
        });
        await this.loadCourses();
    }

    public async saveNotice() {
        let result = await wiz.call('save_notice', { data: JSON.stringify(this.noticeForm) });
        if (result.code !== 200) {
            await this.service.modal.error(this.responseMessage(result.data, '공지 저장에 실패했습니다.'));
            return;
        }
        this.noticeForm = { title: '', content: '', starts_at: '', ends_at: '' };
        await this.loadSettings();
    }

    public async saveTerms() {
        await wiz.call('save_terms', { data: JSON.stringify(this.termsData) });
        await this.service.modal.success('약관이 저장되었습니다.');
        await this.loadSettings();
    }

    public async saveModelSettings() {
        if (this.modelSettings.enabled && !this.modelForm.enabled) {
            let ok = await this.confirm('AI 여행 코스 생성 기능을 중지하시겠습니까?', '중지');
            if (!ok) {
                this.modelForm.enabled = true;
                return;
            }
        }

        let result = await wiz.call('save_model_settings', {
            data: JSON.stringify(this.modelForm)
        });
        if (result.code === 404) {
            result = await wiz.call('save_terms', {
                scope: 'models',
                data: JSON.stringify(this.modelForm)
            });
        }
        if (result.code !== 200) {
            await this.service.modal.error(this.responseMessage(result.data, 'AI 모델 설정 저장에 실패했습니다.'));
            return;
        }
        this.modelSettings = result.data || this.modelSettings;
        this.modelForm = this.clone(this.modelSettings);
        await this.service.modal.success('AI 모델 설정이 저장되었습니다.');
        await this.service.render();
    }

    public toggleEditArray(key: string, value: string) {
        if (!Array.isArray(this.editData[key])) this.editData[key] = [];
        let index = this.editData[key].indexOf(value);
        if (index >= 0) this.editData[key].splice(index, 1);
        else this.editData[key].push(value);
    }

    public toggleCourseTag(course: any, tag: string) {
        if (!Array.isArray(course.tags)) course.tags = [];
        let index = course.tags.indexOf(tag);
        if (index >= 0) course.tags.splice(index, 1);
        else course.tags.push(tag);
    }

    public hasEditValue(key: string, value: string) {
        return Array.isArray(this.editData[key]) && this.editData[key].indexOf(value) >= 0;
    }

    public hasCourseTag(course: any, tag: string) {
        return Array.isArray(course.tags) && course.tags.indexOf(tag) >= 0;
    }

    public featuredCourseOptions() {
        let term = String(this.courseLookup || '').toLowerCase();
        return this.courses.filter((course: any) => {
            if (course.is_hidden) return false;
            if (!term) return true;
            return String(course.title || '').toLowerCase().indexOf(term) >= 0;
        });
    }

    public usageItems(key: string) {
        return (this.filterUsage && this.filterUsage[key]) || [];
    }

    public placeAreaRows() {
        return (this.placeAreaSummary && this.placeAreaSummary.rows) || [];
    }

    public placeAreaDetailRows() {
        return (this.placeAreaDetail && this.placeAreaDetail.districts) || [];
    }

    public placeAreaCategoryRows() {
        return (this.placeAreaDetail && this.placeAreaDetail.categories) || [];
    }

    public summarizePlaceAreas(rows: any[]) {
        let counts: any = {};
        let total = 0;
        for (let row of rows || []) {
            let area = String((row && row.area) || '').trim() || '지역 미지정';
            counts[area] = (counts[area] || 0) + 1;
            total += 1;
        }
        let summaryRows = Object.keys(counts).map((area) => ({ area: area, count: counts[area] }));
        summaryRows.sort((a: any, b: any) => {
            if (b.count !== a.count) return b.count - a.count;
            return a.area.localeCompare(b.area);
        });
        return { total: total, rows: summaryRows };
    }

    public summarizePlaceAreaDetail(area: string, rows: any[]) {
        let categories: any = {};
        let districts: any = {};
        let total = 0;
        for (let row of rows || []) {
            if (String((row && row.area) || '').trim() !== area) continue;
            let category = String((row && row.category) || '').trim() || '기타';
            let district = this.placeDistrictLabel(row);
            total += 1;
            categories[category] = (categories[category] || 0) + 1;
            if (!districts[district]) districts[district] = { area: district, count: 0, categories: {} };
            districts[district].count += 1;
            districts[district].categories[category] = (districts[district].categories[category] || 0) + 1;
        }
        let districtRows = Object.keys(districts).map((name) => {
            let item = districts[name];
            return {
                area: item.area,
                count: item.count,
                categories: this.countRows(item.categories)
            };
        });
        districtRows.sort((a: any, b: any) => {
            if (b.count !== a.count) return b.count - a.count;
            return a.area.localeCompare(b.area);
        });
        return {
            area: area,
            total: total,
            categories: this.countRows(categories),
            districts: districtRows
        };
    }

    public countRows(counts: any) {
        let rows = Object.keys(counts || {}).map((name) => ({ name: name, count: counts[name] }));
        rows.sort((a: any, b: any) => {
            if (b.count !== a.count) return b.count - a.count;
            return a.name.localeCompare(b.name);
        });
        return rows;
    }

    public placeDistrictLabel(row: any) {
        let tokens = String((row && row.address) || '').split(/\s+/);
        for (let token of tokens) {
            token = token.replace(/[(),]/g, '').trim();
            if (!token) continue;
            if (token.indexOf('특별시') >= 0 || token.indexOf('광역시') >= 0 || token.indexOf('특별자치') >= 0 || token.endsWith('도')) continue;
            if (token.endsWith('시') || token.endsWith('군') || token.endsWith('구')) return token;
        }
        return '세부 지역 미지정';
    }

    public statusLabel(hidden: boolean) {
        return hidden ? '숨김' : '노출';
    }

    public courseDuration(course: any) {
        if (course.duration) return course.duration;
        if (course.duration_type === 'hours') return `${course.duration_value || 4}시간`;
        return course.duration_value || '1박 2일';
    }

    public roleClass(role: string) {
        if (role === 'admin') return 'bg-rose-50 text-rose-700 border-rose-200';
        if (role === 'editor') return 'bg-red-50 text-red-700 border-red-200';
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }

    public modelStatusLabel(status: string) {
        if (status === 'ready') return '운영중';
        if (status === 'disabled') return '사용 중지';
        return 'API 키 확인 필요';
    }

    public modelStatusClass(status: string) {
        if (status === 'ready') return 'border-emerald-200 bg-emerald-50 text-emerald-700';
        if (status === 'disabled') return 'border-gray-200 bg-gray-100 text-gray-600';
        return 'border-amber-200 bg-amber-50 text-amber-700';
    }

    private routeSection() {
        let section = (location.pathname.split('/')[2] || 'dashboard').replace(/\/$/, '');
        if (section === 'place-management') return 'places';
        if (section === 'course-management') return 'courses';
        if (['dashboard', 'users', 'places', 'courses', 'curation', 'models', 'settings'].indexOf(section) >= 0) return section;
        return 'dashboard';
    }

    private stripTokenParam() {
        if (typeof window === 'undefined' || !window.history || !window.location) return;
        let params = new URLSearchParams(window.location.search || '');
        if (!params.has('token')) return;
        params.delete('token');
        let query = params.toString();
        let next = `${window.location.pathname}${query ? '?' + query : ''}${window.location.hash || ''}`;
        window.history.replaceState({}, '', next);
    }

    private renderSignupChart() {
        if (this.section !== 'dashboard') return;
        setTimeout(() => {
            let canvas: any = document.getElementById('adminSignupChart');
            if (!canvas) return;
            if (this.signupChart) this.signupChart.destroy();
            this.signupChart = new Chart(canvas, {
                type: 'line',
                data: {
                    labels: this.signups.map((row: any) => row.date.slice(5)),
                    datasets: [{
                        label: '가입자',
                        data: this.signups.map((row: any) => row.count),
                        borderColor: '#ef3b4d',
                        backgroundColor: 'rgba(239, 59, 77, 0.12)',
                        fill: true,
                        tension: 0.35
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { display: false } },
                        y: { beginAtZero: true, ticks: { precision: 0 } }
                    }
                }
            });
        }, 0);
    }

    private clone(value: any) {
        return JSON.parse(JSON.stringify(value || {}));
    }

    private async confirm(message: string, action: string) {
        return await this.service.modal.show({
            title: '확인 필요',
            message: message,
            action: action,
            actionBtn: 'error',
            status: 'error'
        });
    }

    private responseMessage(data: any, fallback: string) {
        if (typeof data === 'string' && data) return data;
        if (data && data.message) return data.message;
        return fallback;
    }
}
