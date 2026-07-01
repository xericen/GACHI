import { OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    public query: string = '';
    public filterSheetOpen: boolean = false;
    public activeHomeFilterKey: string = 'location';
    public filterDraft: any = {
        companion: '',
        schedule: '',
        location: ''
    };
    public authEntryVisible: boolean = false;
    public authMode: string = 'login';
    public authSubmitting: boolean = false;
    public authServerError: string = '';
    public authForm: any = {
        email: '',
        password: '',
        passwordConfirm: '',
        nickname: ''
    };
    public authErrors: any = {};
    public featuredCourses: any[] = [];
    public featuredCoursesLoading: boolean = true;
    public themeSections: any[] = [];
    public themeSectionsLoading: boolean = true;
    public activeThemeKey: string = 'sight';
    public activePlaceRegion: string = '';
    public homeContentTab: string = 'feed';

    public flowSteps: any[] = [
        { icon: 'fa-wand-magic-sparkles', label: 'AI 일정', text: '취향, 예산, 동행 조건으로 여행 계획 생성' },
        { icon: 'fa-pen-to-square', label: '코스 제작', text: '장소, 사진, 설명을 묶어 여행 코스 공유' },
        { icon: 'fa-location-crosshairs', label: '위치 공유', text: '지도에서 친구 위치와 여행 경로 확인' },
        { icon: 'fa-user-group', label: '동행 모집', text: '코스 기반 신청, 수락 후 1:1 채팅' },
        { icon: 'fa-star', label: '후기 작성', text: '여행 완료 후 기록과 리뷰 공유' }
    ];

    public latestCourses: any[] = [
        { title: '익선동 한옥 골목 맛집 투어', location: '서울 종로', summary: '식사, 디저트, 사진 스폿을 짧게 연결', icon: 'fa-utensils' },
        { title: '강릉 커피 거리 당일치기', location: '강릉 안목', summary: '바다 전망 카페와 중앙시장 간식 루트', icon: 'fa-cookie-bite' },
        { title: '전주 한옥마을 1박2일 미식 루트', location: '전주 완산', summary: '한옥 숙소와 야간 산책을 담은 코스', icon: 'fa-landmark' }
    ];

    public companionPosts: any[] = [
        { title: '성수 감성 데이트 루트 동행', route: '성수 감성 데이트 루트', location: '서울 성수', date: '7.12 토', capacity: 2, applicants: 3 },
        { title: '부산 해운대 1박 코스 함께 가요', route: '해운대 바다 1박2일 코스', location: '부산 해운대', date: '7.18 금', capacity: 4, applicants: 5 }
    ];

    public reviewPosts: any[] = [
        { title: 'AI가 잡아준 성수 반나절 코스', course: '성수 감성 데이트 루트', rating: '4.8', summary: '동선이 짧아서 카페 대기 시간이 있어도 일정이 무너지지 않았어요.' },
        { title: '위치 공유 덕분에 해운대에서 안 헤맸어요', course: '해운대 바다 1박2일 코스', rating: '4.9', summary: '친구 위치가 바로 보여서 각자 움직이다 다시 만나기 편했습니다.' }
    ];

    public placeRegionTabs: any[] = [
        { label: '전체', value: '' },
        { label: '서울', value: '서울' },
        { label: '부산', value: '부산' },
        { label: '제주', value: '제주' },
        { label: '강릉', value: '강릉' },
        { label: '속초', value: '속초' },
        { label: '전주', value: '전주' },
        { label: '여수', value: '여수' },
        { label: '경주', value: '경주' },
        { label: '대전', value: '대전' },
        { label: '인천', value: '인천' },
        { label: '가평', value: '가평' }
    ];

    public tabs: any[] = [
        { key: 'home', label: '홈', icon: 'fa-house' },
        { key: 'chat', label: 'AI 채팅', icon: 'fa-comments' },
        { key: 'map', label: '지도', icon: 'fa-map-location-dot' },
        { key: 'saved', label: '저장', icon: 'fa-bookmark' },
        { key: 'my', label: '마이', icon: 'fa-user' }
    ];

    public filterTabs: any[] = [
        { key: 'location', label: '어디로', icon: 'fa-location-dot' },
        { key: 'schedule', label: '언제', icon: 'fa-calendar-days' },
        { key: 'companion', label: '누구랑', icon: 'fa-user-group' }
    ];

    public companionOptions: any[] = [
        { label: '연인', value: '연인' },
        { label: '친구', value: '친구' },
        { label: '가족', value: '가족' },
        { label: '혼자', value: '혼자' }
    ];

    public weekdays: string[] = ['일', '월', '화', '수', '목', '금', '토'];
    public calendarMonthLabel: string = '';
    public calendarDays: any[] = [];
    public scheduleRange: any = { start: '', end: '' };
    public draftScheduleRange: any = { start: '', end: '' };
    public todayKey: string = '';
    public selectedLocationRegion: string = '서울';

    public locationGroups: any[] = [
        {
            name: '서울',
            areas: [
                { label: '전체', value: '서울' },
                { label: '성수', value: '성수' },
                { label: '종로', value: '종로' },
                { label: '익선동', value: '익선동' },
                { label: '한강', value: '한강' },
                { label: '홍대', value: '홍대' }
            ]
        },
        {
            name: '경기',
            areas: [
                { label: '전체', value: '경기' },
                { label: '수원', value: '수원' },
                { label: '가평', value: '가평' },
                { label: '양평', value: '양평' },
                { label: '파주', value: '파주' },
                { label: '용인', value: '용인' },
                { label: '고양', value: '고양' }
            ]
        },
        {
            name: '인천',
            areas: [
                { label: '전체', value: '인천' },
                { label: '송도', value: '송도' },
                { label: '월미도', value: '월미도' },
                { label: '강화', value: '강화' },
                { label: '영종', value: '영종' }
            ]
        },
        {
            name: '강원',
            areas: [
                { label: '전체', value: '강원' },
                { label: '강릉', value: '강릉' },
                { label: '속초', value: '속초' },
                { label: '춘천', value: '춘천' },
                { label: '양양', value: '양양' },
                { label: '평창', value: '평창' }
            ]
        },
        {
            name: '충청',
            areas: [
                { label: '전체', value: '충청' },
                { label: '대전', value: '대전' },
                { label: '세종', value: '세종' },
                { label: '천안', value: '천안' },
                { label: '아산', value: '아산' },
                { label: '공주', value: '공주' },
                { label: '부여', value: '부여' },
                { label: '태안', value: '태안' }
            ]
        },
        {
            name: '전라',
            areas: [
                { label: '전체', value: '전라' },
                { label: '전주', value: '전주' },
                { label: '군산', value: '군산' },
                { label: '목포', value: '목포' },
                { label: '여수', value: '여수' },
                { label: '순천', value: '순천' }
            ]
        },
        {
            name: '경상',
            areas: [
                { label: '전체', value: '경상' },
                { label: '대구', value: '대구' },
                { label: '경주', value: '경주' },
                { label: '포항', value: '포항' },
                { label: '안동', value: '안동' },
                { label: '통영', value: '통영' },
                { label: '거제', value: '거제' }
            ]
        },
        {
            name: '부산',
            areas: [
                { label: '전체', value: '부산' },
                { label: '해운대', value: '해운대' },
                { label: '광안리', value: '광안리' },
                { label: '영도', value: '영도' },
                { label: '서면', value: '서면' }
            ]
        },
        {
            name: '제주',
            areas: [
                { label: '전체', value: '제주' },
                { label: '애월', value: '애월' },
                { label: '협재', value: '협재' },
                { label: '서귀포', value: '서귀포' },
                { label: '성산', value: '성산' },
                { label: '중문', value: '중문' }
            ]
        }
    ];

    private calendarMonth: Date = new Date();
    private scheduleDragStartKey: string = '';
    private schedulePointerActive: boolean = false;
    private ignoreNextScheduleClick: boolean = false;

    constructor(public service: Service) { }

    public async ngOnInit() {
        this.prepareCalendar();
        await this.service.init();
        this.authEntryVisible = false;
        await this.loadPopularCourses();
        await this.loadThemeSections();
        await this.service.render();
    }

    public async loadPopularCourses() {
        this.featuredCoursesLoading = true;
        await this.service.render();
        try {
            let response = await fetch('/api/courses/popular?limit=4', { method: 'GET' });
            let payload = await response.json();
            let data = payload && payload.data ? payload.data : payload;
            this.featuredCourses = this.captureSafeCourses((data && data.rows) || []);
            await this.loadSavedPopularCourses();
        } catch (e) {
            this.featuredCourses = [];
        }
        this.featuredCoursesLoading = false;
    }

    public async loadThemeSections() {
        this.themeSectionsLoading = true;
        try {
            let params = new URLSearchParams();
            params.set('limit', '6');
            if (this.activePlaceRegion) params.set('location', this.activePlaceRegion);
            let response = await fetch(`/api/places/themes?${params.toString()}`, { method: 'GET' });
            let payload = await response.json();
            let data = payload && payload.data ? payload.data : payload;
            this.themeSections = this.captureSafeThemeSections((data && data.rows) || []);
            if (!this.themeSections.some((theme: any) => theme.key === this.activeThemeKey)) {
                this.activeThemeKey = this.themeSections.length > 0 ? this.themeSections[0].key : '';
            }
        } catch (e) {
            this.themeSections = [];
            this.activeThemeKey = '';
        }
        this.themeSectionsLoading = false;
    }

    private captureSafeImage(url: string) {
        let raw = String(url || '').trim();
        if (!raw) return '';
        if (raw.indexOf('data:') === 0 || raw.indexOf('blob:') === 0) return raw;

        try {
            let parsed = new URL(raw, window.location.origin);
            if (parsed.origin === window.location.origin) return `${parsed.pathname}${parsed.search}${parsed.hash}`;
            if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return '';
            return parsed.href;
        } catch (e) {
            return raw;
        }
    }

    private isExternalImage(url: string) {
        let raw = String(url || '').trim();
        if (!raw || raw.indexOf('data:') === 0 || raw.indexOf('blob:') === 0 || raw.charAt(0) === '/') return false;
        try {
            let parsed = new URL(raw, window.location.origin);
            return (parsed.protocol === 'http:' || parsed.protocol === 'https:') && parsed.origin !== window.location.origin;
        } catch (e) {
            return false;
        }
    }

    private isEmbeddedContext() {
        if (typeof window === 'undefined') return false;
        try {
            return window.parent !== window;
        } catch (e) {
            return true;
        }
    }

    private captureSafeCourses(rows: any[]) {
        let useFallback = this.isEmbeddedContext();
        return (rows || []).map((course: any) => {
            let item = { ...course };
            if (item.cover_image) {
                item.original_cover_image = item.original_cover_image || item.cover_image;
                if (useFallback && this.isExternalImage(item.cover_image)) item.image_broken = true;
                else item.cover_image = this.captureSafeImage(item.cover_image);
            }
            if (item.image) {
                item.original_image = item.original_image || item.image;
                if (useFallback && this.isExternalImage(item.image)) item.image_broken = true;
                else item.image = this.captureSafeImage(item.image);
            }
            return item;
        });
    }

    private captureSafeThemeSections(sections: any[]) {
        let useFallback = this.isEmbeddedContext();
        return (sections || []).map((theme: any) => ({
            ...theme,
            places: (theme.places || []).map((place: any) => {
                let item = { ...place };
                if (item.image) {
                    item.original_image = item.original_image || item.image;
                    if (useFallback && this.isExternalImage(item.image)) item.image_broken = true;
                    else item.image = this.captureSafeImage(item.image);
                }
                return item;
            })
        }));
    }

    public async selectPlaceRegion(region: any) {
        let value = region && region.value ? region.value : '';
        if (value === this.activePlaceRegion) return;
        this.activePlaceRegion = value;
        await this.loadThemeSections();
        await this.service.render();
    }

    public activePlaceRegionLabel() {
        let region = this.placeRegionTabs.find((item: any) => item.value === this.activePlaceRegion);
        return region ? region.label : '추천 지역';
    }

    public async selectTheme(theme: any) {
        this.activeThemeKey = theme && theme.key ? theme.key : '';
        await this.service.render();
    }

    public async setHomeContentTab(tab: string) {
        this.homeContentTab = tab;
        await this.service.render();
    }

    public activeTheme() {
        return this.themeSections.find((theme: any) => theme.key === this.activeThemeKey) || this.themeSections[0] || null;
    }

    public activeThemePlaces() {
        let theme = this.activeTheme();
        return theme && theme.places ? theme.places : [];
    }

    public activeThemeCountLabel() {
        if (this.themeSectionsLoading) return '불러오는 중';
        let theme = this.activeTheme();
        if (!theme) return '0개';
        return `${theme.count || 0}개`;
    }

    public themePlaceMeta(place: any) {
        return [place.area, place.category].filter((item: string) => !!item).join(' · ');
    }

    public themePlaceRating(place: any) {
        if (place.rating === null || typeof place.rating === 'undefined' || place.rating === '') return '';
        let value = Number(place.rating);
        if (Number.isNaN(value)) return String(place.rating);
        return value.toFixed(1);
    }

    public markThemeImageBroken(place: any) {
        place.image_broken = true;
    }

    public markCourseImageBroken(course: any) {
        if (!course) return;
        course.image_broken = true;
    }

    public openThemePlace(place: any) {
        if (!place) return;
        let area = String(place.area || '').trim();
        let keyword = String(place.theme_keyword || place.theme_label || place.category || '여행').trim();
        let name = String(place.name || '').trim();
        let prompt = [area, keyword, name ? `${name} 포함` : '', '코스 추천'].filter((item: string) => !!item).join(' ');
        let location = this.locationValueFromArea(area);
        let params = new URLSearchParams();
        params.set('tab', 'chat');
        params.set('prompt', prompt);
        if (location) params.set('location', location);
        if (keyword) params.set('keyword', keyword);

        this.setSessionValue('tour-on-chat-prompt', prompt);
        this.setSessionValue('tour-on-access-state', JSON.stringify({
            activeTab: 'chat',
            selectedFilters: {
                companion: '',
                schedule: '',
                location
            },
            selectedKeyword: keyword,
            query: '',
            scheduleRange: { start: '', end: '' }
        }));
        this.service.href(`/access?${params.toString()}`);
    }

    public async loadSavedPopularCourses() {
        if (!this.isLoggedIn() || this.featuredCourses.length === 0) return;
        try {
            const { code, data } = await wiz.call('saved_courses', {});
            if (code === 200) this.applySavedPopularCourseIds(data && data.course_ids ? data.course_ids : []);
        } catch (e) { }
    }

    public async togglePopularLike(course: any, event?: Event) {
        if (event) event.stopPropagation();
        if (!this.isLoggedIn()) {
            this.authMode = 'login';
            this.authEntryVisible = true;
            await this.service.render();
            return;
        }

        let previousSaved = !!course.saved;
        let previousCount = Number(course.like_count || course.saved_count || 0);
        let nextSaved = !previousSaved;
        course.saved = nextSaved;
        course.like_count = Math.max(0, previousCount + (nextSaved ? 1 : -1));
        course.saved_count = course.like_count;
        await this.service.render();

        try {
            const { code, data } = await wiz.call('save_course', {
                course_id: course.id,
                saved: nextSaved ? 'true' : 'false',
                title: course.title,
                location: course.region || course.location || '',
                summary: course.description || course.summary || '',
                duration: this.courseDuration(course),
                rating: course.rating || '',
                icon: this.courseIcon(course),
                tone: this.courseTone(course)
            });
            if (code === 200) {
                this.applySavedPopularCourseIds(data && data.course_ids ? data.course_ids : []);
                return;
            }
        } catch (e) { }

        course.saved = previousSaved;
        course.like_count = previousCount;
        course.saved_count = previousCount;
        await this.service.render();
    }

    private applySavedPopularCourseIds(ids: string[]) {
        this.featuredCourses.forEach((course: any) => {
            course.saved = ids.indexOf(course.id) > -1;
        });
    }

    public courseDuration(course: any) {
        if (course.duration) return course.duration;
        if (course.duration_type === 'hours') return `${course.duration_value || 4}시간`;
        return course.duration_value || '1박 2일';
    }

    public courseIcon(course: any) {
        let category = String(course.category || '').toLowerCase();
        if (category.indexOf('바다') >= 0) return 'fa-water';
        if (category.indexOf('숙소') >= 0) return 'fa-bed';
        if (category.indexOf('액티비티') >= 0) return 'fa-person-hiking';
        if (category.indexOf('맛') >= 0) return 'fa-utensils';
        if (category.indexOf('드라이브') >= 0) return 'fa-car-side';
        return 'fa-mug-saucer';
    }

    public courseTone(course: any) {
        let category = String(course.category || '').toLowerCase();
        if (category.indexOf('바다') >= 0) return 'tone-blue';
        if (category.indexOf('숙소') >= 0) return 'tone-sun';
        if (category.indexOf('드라이브') >= 0 || category.indexOf('액티비티') >= 0) return 'tone-green';
        return 'tone-rose';
    }

    public courseRating(course: any) {
        if (course.rating === null || typeof course.rating === 'undefined' || course.rating === '') return '-';
        let value = Number(course.rating);
        if (Number.isNaN(value)) return course.rating;
        return value.toFixed(1);
    }

    public isLoggedIn() {
        return !!(this.service.auth && this.service.auth.isLoggedIn && this.service.auth.isLoggedIn());
    }

    public async switchAuthMode(mode: string) {
        this.authMode = mode;
        this.authServerError = '';
        this.authErrors = {};
        await this.service.render();
    }

    public async continueAsGuest() {
        this.authEntryVisible = false;
        this.setSessionFlag('tour-on-auth-entry-dismissed');
        await this.service.render();
    }

    public async submitAuth() {
        if (!this.validateAuthForm()) {
            await this.service.render();
            return;
        }

        this.authSubmitting = true;
        this.authServerError = '';
        await this.service.render();

        let payload: any = {
            email: String(this.authForm.email || '').trim(),
            password: this.authForm.password
        };
        if (this.authMode === 'register') {
            payload.name = String(this.authForm.nickname || '').trim();
            payload.password_confirm = this.authForm.passwordConfirm;
        }

        const { code, data } = await this.requestAuth(payload);
        if (code === 200) {
            let session = data && data.session ? data.session : {};
            this.service.auth.setLocalSession(session, data && data.token ? data.token : '');
            if (session.role === 'admin') {
                this.service.href('/admin/dashboard');
                return;
            }
            this.authEntryVisible = false;
            this.setSessionFlag('tour-on-auth-entry-dismissed');
            this.resetAuthForm();
            await this.loadSavedPopularCourses();
        } else {
            this.authServerError = this.responseMessage(data, this.authMode === 'register' ? '회원가입에 실패했습니다.' : '로그인에 실패했습니다.');
        }

        this.authSubmitting = false;
        await this.service.render();
    }

    public authTitle() {
        return this.authMode === 'register' ? '회원가입' : '로그인';
    }

    public authSubmitLabel() {
        if (this.authSubmitting) return '처리 중';
        return this.authMode === 'register' ? '가입하기' : '로그인';
    }

    private async requestAuth(payload: any) {
        let endpoint = this.authMode === 'register' ? '/auth/signup' : '/auth/login';
        let result: any = await this.service.request.post(endpoint, payload);
        if (result && typeof result.code !== 'undefined') return result;
        return await wiz.call(this.authMode === 'register' ? 'register' : 'login', payload);
    }

    private validateAuthForm() {
        let errors: any = {};
        let email = String(this.authForm.email || '').trim();
        let password = String(this.authForm.password || '');
        let passwordConfirm = String(this.authForm.passwordConfirm || '');
        let nickname = String(this.authForm.nickname || '').trim();
        let isAdminLogin = this.authMode === 'login' && email === 'admin';
        let isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

        if (!email) {
            errors.email = '이메일을 입력해주세요.';
        } else if (!isAdminLogin && !isEmail) {
            errors.email = '올바른 이메일 형식으로 입력해주세요.';
        }
        if (!password) {
            errors.password = '비밀번호를 입력해주세요.';
        }
        if (this.authMode === 'register') {
            if (!isEmail) errors.email = '올바른 이메일 형식으로 입력해주세요.';
            if (!nickname) errors.nickname = '닉네임을 입력해주세요.';
            if (password.length < 6) errors.password = '비밀번호는 6자 이상 입력해주세요.';
            if (password !== passwordConfirm) errors.passwordConfirm = '비밀번호가 일치하지 않습니다.';
        }

        this.authErrors = errors;
        this.authServerError = '';
        return Object.keys(errors).length === 0;
    }

    private resetAuthForm() {
        this.authForm = {
            email: '',
            password: '',
            passwordConfirm: '',
            nickname: ''
        };
        this.authErrors = {};
        this.authServerError = '';
    }

    private responseMessage(data: any, fallback: string) {
        if (typeof data === 'string' && data) return data;
        if (data && data.message) return data.message;
        return fallback;
    }

    public async setQuery(value: string) {
        this.query = value;
        await this.service.render();
    }

    public startAiPlan() {
        let prompt = String(this.query || '').trim() || '이번 주말 예산에 맞는 여행 일정 만들어줘';
        this.setSessionValue('tour-on-chat-prompt', prompt);
        this.service.href(`/access?tab=chat&prompt=${encodeURIComponent(prompt)}`);
    }

    public createCourse() {
        this.service.href('/access?tab=home&compose=course');
    }

    public openZenlyMap() {
        this.service.href('/access?tab=map&mapMode=zenly');
    }

    public selectTab(tab: any) {
        if (tab.key === 'home') return;
        this.service.href(`/access?tab=${encodeURIComponent(tab.key)}`);
    }

    public goLogin() {
        this.service.href('/login');
    }

    public search() {
        let prompt = String(this.query || '').trim();
        if (!prompt) return;

        this.setSessionValue('tour-on-chat-prompt', prompt);
        this.service.href(`/access?tab=chat&prompt=${encodeURIComponent(prompt)}`);
    }

    public async openFilterSheet() {
        this.filterSheetOpen = true;
        this.activeHomeFilterKey = this.filterDraft.location ? 'schedule' : 'location';
        this.syncLocationRegion();
        this.syncCalendarToSchedule();
        await this.service.render();
    }

    public async closeFilterSheet() {
        this.filterSheetOpen = false;
        this.schedulePointerActive = false;
        await this.service.render();
    }

    public async selectHomeFilterTab(key: string) {
        this.activeHomeFilterKey = key;
        if (key === 'location') this.syncLocationRegion();
        if (key === 'schedule') this.buildCalendar();
        await this.service.render();
    }

    public activeFilterTitle() {
        let tab = this.filterTabs.find((item: any) => item.key === this.activeHomeFilterKey);
        return tab ? tab.label : '필터';
    }

    public selectedFilterLabel(key: string) {
        if (key === 'location') return this.filterDraft.location || '지역';
        if (key === 'schedule') return this.filterDraft.schedule || '날짜';
        if (key === 'companion') return this.filterDraft.companion || '동행';
        return '';
    }

    public async resetFilters() {
        this.filterDraft = {
            companion: '',
            schedule: '',
            location: ''
        };
        this.scheduleRange = { start: '', end: '' };
        this.draftScheduleRange = { start: '', end: '' };
        this.selectedLocationRegion = this.locationGroups[0].name;
        this.calendarMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
        this.buildCalendar();
        await this.service.render();
    }

    public async selectFilterValue(key: string, value: string) {
        this.filterDraft[key] = this.filterDraft[key] === value ? '' : value;
        await this.service.render();
    }

    public isFilterSelected(key: string, value: string) {
        return this.filterDraft[key] === value;
    }

    public hasSelectedFilter() {
        return Object.keys(this.filterDraft).some((key: string) => !!this.filterDraft[key]);
    }

    public activeLocationAreas() {
        let group = this.locationGroups.find((item: any) => item.name === this.selectedLocationRegion);
        return group ? group.areas : [];
    }

    public async selectLocationRegion(region: any) {
        this.selectedLocationRegion = region.name;
        await this.service.render();
    }

    public async selectLocationArea(area: any) {
        this.filterDraft.location = this.filterDraft.location === area.value ? '' : area.value;
        await this.service.render();
    }

    public isLocationAreaSelected(area: any) {
        return this.filterDraft.location === area.value;
    }

    public async changeCalendarMonth(direction: number) {
        this.calendarMonth = new Date(this.calendarMonth.getFullYear(), this.calendarMonth.getMonth() + direction, 1);
        this.buildCalendar();
        await this.service.render();
    }

    public async startScheduleDrag(day: any, event: any) {
        if (event) event.preventDefault();
        this.schedulePointerActive = true;
        this.scheduleDragStartKey = day.key;
        this.setDraftScheduleRange(day.key, day.key);
        await this.service.render();
    }

    public async previewSchedulePointer(event: any) {
        if (!this.schedulePointerActive) return;
        if (event) event.preventDefault();
        let key = this.dateKeyFromPointer(event);
        if (!key) return;
        let next = this.normalizeDateRange(this.scheduleDragStartKey, key);
        if (next.start === this.draftScheduleRange.start && next.end === this.draftScheduleRange.end) return;
        this.draftScheduleRange = next;
        await this.service.render();
    }

    public async finishSchedulePointer(event: any) {
        if (!this.schedulePointerActive) return;
        if (event) event.preventDefault();
        let key = this.dateKeyFromPointer(event) || this.draftScheduleRange.end || this.scheduleDragStartKey;
        this.schedulePointerActive = false;
        this.ignoreNextScheduleClick = true;
        this.setDraftScheduleRange(this.scheduleDragStartKey, key);
        this.applyScheduleRange(this.draftScheduleRange.start, this.draftScheduleRange.end);
        await this.service.render();
    }

    public async cancelScheduleDrag() {
        this.schedulePointerActive = false;
        this.draftScheduleRange = { start: '', end: '' };
        await this.service.render();
    }

    public async selectScheduleDay(day: any) {
        if (this.ignoreNextScheduleClick) {
            this.ignoreNextScheduleClick = false;
            return;
        }

        this.applyScheduleRange(day.key, day.key);
        await this.service.render();
    }

    public async clearSchedule() {
        this.scheduleRange = { start: '', end: '' };
        this.draftScheduleRange = { start: '', end: '' };
        this.filterDraft.schedule = '';
        await this.service.render();
    }

    public isScheduleDayInRange(day: any) {
        let range = this.visibleScheduleRange();
        if (!range.start || !range.end) return false;
        return day.key >= range.start && day.key <= range.end;
    }

    public isScheduleRangeStart(day: any) {
        let range = this.visibleScheduleRange();
        return !!range.start && day.key === range.start;
    }

    public isScheduleRangeEnd(day: any) {
        let range = this.visibleScheduleRange();
        return !!range.end && day.key === range.end;
    }

    public isScheduleDaySelected(day: any) {
        return this.isScheduleRangeStart(day) && this.isScheduleRangeEnd(day);
    }

    public applyFilters() {
        if (!this.hasSelectedFilter()) {
            this.filterSheetOpen = false;
            this.service.render();
            return;
        }

        let params = new URLSearchParams();
        params.set('tab', 'home');
        Object.keys(this.filterDraft).forEach((key: string) => {
            if (this.filterDraft[key]) params.set(key, this.filterDraft[key]);
        });
        if (this.scheduleRange.start && this.scheduleRange.end) {
            params.set('scheduleStart', this.scheduleRange.start);
            params.set('scheduleEnd', this.scheduleRange.end);
        }

        this.setSessionValue('tour-on-access-state', JSON.stringify({
            activeTab: 'home',
            selectedFilters: { ...this.filterDraft },
            selectedKeyword: '',
            query: '',
            scheduleRange: { ...this.scheduleRange }
        }));

        this.service.href(`/access?${params.toString()}`);
    }

    private prepareCalendar() {
        let today = new Date();
        this.todayKey = this.toDateKey(today);
        this.calendarMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        this.buildCalendar();
    }

    private buildCalendar() {
        let year = this.calendarMonth.getFullYear();
        let month = this.calendarMonth.getMonth();
        let firstDate = new Date(year, month, 1);
        let startDate = new Date(year, month, 1 - firstDate.getDay());
        let days = [];

        this.calendarMonthLabel = `${year}년 ${month + 1}월`;

        for (let weekIndex = 0; weekIndex < 6; weekIndex++) {
            for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
                let date = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate() + (weekIndex * 7) + dayIndex);
                let key = this.toDateKey(date);
                days.push({
                    key,
                    label: date.getDate(),
                    inMonth: date.getMonth() === month,
                    isToday: key === this.todayKey,
                    ariaLabel: `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`
                });
            }
        }

        this.calendarDays = days;
    }

    private setDraftScheduleRange(startKey: string, endKey: string) {
        this.draftScheduleRange = this.normalizeDateRange(startKey, endKey);
    }

    private applyScheduleRange(startKey: string, endKey: string) {
        let range = this.normalizeDateRange(startKey, endKey);
        let isSameRange = this.scheduleRange.start === range.start && this.scheduleRange.end === range.end;

        if (isSameRange) {
            this.scheduleRange = { start: '', end: '' };
            this.draftScheduleRange = { start: '', end: '' };
            this.filterDraft.schedule = '';
            return;
        }

        this.scheduleRange = range;
        this.draftScheduleRange = range;
        this.filterDraft.schedule = this.formatScheduleRangeLabel(range.start, range.end);
    }

    private visibleScheduleRange() {
        if (this.schedulePointerActive && this.draftScheduleRange.start) return this.draftScheduleRange;
        return this.scheduleRange;
    }

    private normalizeDateRange(startKey: string, endKey: string) {
        if (!startKey || !endKey) return { start: '', end: '' };
        if (startKey <= endKey) return { start: startKey, end: endKey };
        return { start: endKey, end: startKey };
    }

    private formatScheduleRangeLabel(startKey: string, endKey: string) {
        let startLabel = this.formatDateLabel(startKey);
        if (startKey === endKey) return startLabel;
        return `${startLabel}-${this.formatDateLabel(endKey)}`;
    }

    private formatDateLabel(key: string) {
        let date = this.fromDateKey(key);
        return `${date.getMonth() + 1}.${date.getDate()}`;
    }

    private toDateKey(date: Date) {
        let year = date.getFullYear();
        let month = String(date.getMonth() + 1).padStart(2, '0');
        let day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    private fromDateKey(key: string) {
        let parts = key.split('-').map((part: string) => Number(part));
        return new Date(parts[0], parts[1] - 1, parts[2]);
    }

    private syncLocationRegion() {
        let location = this.filterDraft.location || '';
        if (!location) {
            this.selectedLocationRegion = this.locationGroups[0].name;
            return;
        }

        let region = this.getRegionForLocation(location);
        this.selectedLocationRegion = region || this.locationGroups[0].name;
    }

    private getRegionForLocation(location: string) {
        for (let group of this.locationGroups) {
            if (group.name === location) return group.name;
            if (group.areas.some((area: any) => area.value === location)) return group.name;
        }
        return '';
    }

    private locationValueFromArea(area: string) {
        let value = String(area || '').trim();
        if (!value) return '';
        if (this.getRegionForLocation(value)) return value;

        let parts = value.split(/\s+/).filter((item: string) => !!item);
        for (let index = parts.length - 1; index >= 0; index--) {
            if (this.getRegionForLocation(parts[index])) return parts[index];
        }
        return parts[0] || value;
    }

    private syncCalendarToSchedule() {
        if (!this.scheduleRange.start) {
            this.buildCalendar();
            return;
        }
        let date = this.fromDateKey(this.scheduleRange.start);
        this.calendarMonth = new Date(date.getFullYear(), date.getMonth(), 1);
        this.buildCalendar();
    }

    private dateKeyFromPointer(event: any) {
        if (!event || typeof document === 'undefined') return '';
        let element: any = document.elementFromPoint(event.clientX, event.clientY);
        while (element && element !== document.body) {
            if (element.getAttribute) {
                let key = element.getAttribute('data-date-key');
                if (key) return key;
            }
            element = element.parentElement;
        }
        return '';
    }

    private setSessionValue(key: string, value: string) {
        if (typeof window === 'undefined' || !window.sessionStorage) return;
        try {
            window.sessionStorage.setItem(key, value);
        } catch (e) { }
    }

    private setSessionFlag(key: string) {
        this.setSessionValue(key, '1');
    }

    private readSessionFlag(key: string) {
        if (typeof window === 'undefined' || !window.sessionStorage) return false;
        try {
            return window.sessionStorage.getItem(key) === '1';
        } catch (e) {
            return false;
        }
    }
}
