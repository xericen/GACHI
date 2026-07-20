import { OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    constructor(public service: Service) {
        this.removeLegacyExampleContent();
    }

    private removeLegacyExampleContent() {
        this.myActivityItems = this.myActivityItems.map((item: any) => ({ ...item, count: 0 }));
        this.myProfileFollowers = [];
        this.myProfileFollowing = [];
        this.myProfilePosts = [];
        this.plannerCompanionCards = [];
        this.communityPosts = [];
        this.companionPosts = [];
        this.reviewPosts = [];
        this.directChats = [];
        this.activeDirectChatId = '';
        this.selectedTogetherCompanionId = '';
        this.togetherCompanions = [];
        this.togetherMeetingPoint = { name: '', time: '', note: '', x: 50, y: 50 };
        this.recommendations = [];
        this.courses = [];
        this.mapSpotMap = { default: [] };
    }

    public activeTab: string = 'home';
    public homeContentTab: string = 'feed';
    public companionMode: string = 'pretrip';
    public chatContentTab: string = 'chat';
    public mapContentTab: string = 'map';
    public savedContentTab: string = 'courses';
    public savedPlaceType: string = 'all';
    public query: string = '';
    public draft: string = '';
    public directDraft: string = '';
    public communitySearchQuery: string = '';
    public courseComposerOpen: boolean = false;
    public courseBuilderMode: string = '';
    public courseBuilderStep: string = 'mode';
    public courseAiMood: string = '';
    public courseComposerPlannerEdit: boolean = false;
    public courseBuilderDayIndex: number = 0;
    public courseBuilderDays: any[] = [];
    public courseAiRebuilding: boolean = false;
    public courseDraftArchiveOpen: boolean = false;
    public courseDraftArchiveSummary: any = null;
    public communityComposerOpen: boolean = false;
    public communityPublishSubmitting: boolean = false;
    public communitySortDropdownOpen: boolean = false;
    public selectedCommunityTopic: string = 'recommend';
    public selectedCommunitySort: string = 'recommended';
    public expandedCommunityPostId: string = '';
    public activeCommunityPost: any = null;
    public communityComments: any[] = [];
    public communityCommentDraft: string = '';
    public communityCommentsLoading: boolean = false;
    public communityArchiveOpen: boolean = false;
    public communityArchivePosts: any[] = [];
    public communityArchiveLoading: boolean = false;
    public communityDeleteSubmittingId: string = '';
    public communityDetailMenuOpen: boolean = false;
    public communityReportSubmittingId: string = '';
    public communityReportedPostIds: string[] = [];
    public courseDraft: any = {
        title: '',
        region: '',
        schedule: '',
        scheduleDate: '',
        scheduleEndDate: '',
        places: '',
        photo: '',
        photoName: '',
        description: '',
        category: '여행',
        companionType: 'friend',
        isPublic: true,
        companionEnabled: false,
        companionDate: '',
        companionTime: '',
        companionCapacity: 2,
        companionCost: '',
        companionBudgetStyle: '',
        companionPace: '',
        companionMood: '',
        companionFlexible: '',
        companionMeetingPoint: '',
        companionSmoking: '',
        companionDrinking: '',
        companionIntro: ''
    };
    public courseDraftSavedAt: string = '';
    public courseBuilderPlaces: any[] = [];
    public coursePlaceSearchQuery: string = '';
    public coursePlaceSearchResults: any[] = [];
    public coursePlaceSearchOpen: boolean = false;
    public coursePlaceSearching: boolean = false;
    public courseRegionSearchOpen: boolean = false;
    public courseBuilderError: string = '';
    public coursePublishModalOpen: boolean = false;
    public coursePublishSubmitting: boolean = false;
    public courseDragIndex: number = -1;
    public courseGoogleReady: boolean = false;
    public courseDateCalendarMonth: Date = new Date();
    private courseDateDragActive: boolean = false;
    private courseDateDragStartKey: string = '';
    private courseBuilderOriginalDays: any[] = [];
    public communityDraft: any = {
        kind: 'post',
        topic: 'recommend',
        title: '',
        body: '',
        hasDestination: true,
        destination: '',
        photo: '',
        photoName: '',
        place: '',
        pollOptions: [],
        pollInput: '',
        tags: [],
        tagInput: ''
    };
    public isChatSending: boolean = false;
    public chatDrawerOpen: boolean = false;
    public chatHistoryLoading: boolean = false;
    public chatThreads: any[] = [];
    public activeChatThreadId: string = '';
    public selectedKeyword: string = '여행';
    public activeFilterKey: string = '';
    public filterOverviewOpen: boolean = false;
    public authModalOpen: boolean = false;
    public authMode: string = 'login';
    public authSubmitting: boolean = false;
    public authServerError: string = '';
    public pendingSaveCourse: any = null;
    public saveHintVisible: boolean = false;
    public saveHintMessage: string = '로그인해야 코스를 저장할 수 있어요.';
    public placeCourses: any[] = [];
    public placeThemeSections: any[] = [];
    public activePlaceThemeKey: string = '';
    public placeCoursesLoading: boolean = false;
    public recentPlaces: any[] = [];
    public savedPlaceFilters: any[] = [
        { key: 'all', label: '전체', icon: 'fa-layer-group' },
        { key: 'cafe', label: '카페', icon: 'fa-mug-saucer' },
        { key: 'stay', label: '숙소', icon: 'fa-bed' },
        { key: 'food', label: '맛집', icon: 'fa-utensils' },
        { key: 'walk', label: '산책', icon: 'fa-person-walking' },
        { key: 'landmark', label: '명소', icon: 'fa-location-dot' },
        { key: 'drive', label: '드라이브', icon: 'fa-car-side' }
    ];
    public myProfileOpen: boolean = false;
    public myProfileTab: string = 'myCourses';
    public myCourseViewMode: string = 'list';
    public myProfileEditOpen: boolean = false;
    public myResumeOpen: boolean = false;
    public myResumePreviewOpen: boolean = false;
    public travelResumeStep: number = 1;
    public travelResumeReturnToSettings: boolean = false;
    public myFeedComposerOpen: boolean = false;
    public myArchiveOpen: boolean = false;
    public myActivityOpen: boolean = false;
    public myFeedDetailOpen: boolean = false;
    public myCourseDetailOpen: boolean = false;
    public newFeedStep: string = 'select';
    public newFeedPhotoIndex: number = 0;
    public profileFeedDetailPhotoIndex: number = 0;
    public profileCourseDetailPhotoIndex: number = 0;
    public profileCourseDetailLoading: boolean = false;
    public selectedMyProfilePost: any = null;
    public selectedMyProfileCourse: any = null;
    public feedComposerReturnCourse: any = null;
    public myProfileEdit: any = {
        photo: '',
        nickname: '',
        region: '',
        intro: ''
    };
    public travelResume: any = {
        schemaVersion: 2,
        photo: '',
        fullName: '',
        age: '',
        gender: '',
        region: '',
        companionUses: 0,
        interests: '',
        smoking: '',
        drinking: '',
        travelExperience: '',
        intro: ''
    };
    public travelIdentity: any = {
        loading: false,
        verifying: false,
        verified: false,
        configured: true,
        name: '',
        age: 0,
        gender: '',
        verifiedAt: '',
        error: ''
    };
    public resumeRegionOptions: string[] = [
        '서울', '경기', '인천', '부산', '대구', '대전', '광주', '울산', '세종',
        '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주'
    ];
    public resumeInterestOptions: string[] = ['바다', '맛집', '전시', '산책', '사진', '카페'];
    public newFeedPost: any = {
        photo: '',
        photos: [],
        courseId: '',
        courseTitle: '',
        title: '',
        location: '',
        tags: '',
        caption: '',
        icon: 'fa-camera',
        tone: 'feed-rose'
    };
    public feedIconOptions: any[] = [
        { value: 'fa-camera', label: '사진' },
        { value: 'fa-mug-saucer', label: '카페' },
        { value: 'fa-water', label: '바다' },
        { value: 'fa-bed', label: '숙소' },
        { value: 'fa-map-location-dot', label: '장소' }
    ];
    public feedToneOptions: any[] = [
        { value: 'feed-rose', label: '레드' },
        { value: 'feed-blue', label: '코랄' },
        { value: 'feed-green', label: '민트' },
        { value: 'feed-sun', label: '옐로우' }
    ];
    public myActivityItems: any[] = [
        { icon: 'fa-heart', label: '좋아요', text: '내가 좋아요를 누른 피드와 코스 반응을 관리해요.', count: 12 },
        { icon: 'fa-comment', label: '댓글', text: '내가 남긴 댓글과 답글 기록을 확인해요.', count: 5 },
        { icon: 'fa-repeat', label: '리포스트', text: '다시 공유했거나 리그램한 피드를 모아봐요.', count: 8 },
        { icon: 'fa-tag', label: '태그', text: '내가 태그된 여행 피드와 장소를 관리해요.', count: 3 }
    ];
    public myProfileFollowers: any[] = [
        { name: '서울 산책러', handle: '@seoul.walk', icon: 'fa-person-walking', note: '성수와 한강 코스를 자주 저장해요.', following: false },
        { name: '부산 바다친구', handle: '@busan.wave', icon: 'fa-water', note: '해운대 1박 코스를 팔로우 중', following: false },
        { name: '감성숙소 큐레이터', handle: '@stay.note', icon: 'fa-bed', note: '숙소 중심 여행 피드를 모아요.', following: false }
    ];
    public myProfileFollowing: any[] = [
        { name: 'GACHI 추천', handle: '@gachi', icon: 'fa-route', note: '인기 여행 코스 공식 피드', following: true },
        { name: '제주 애월 기록', handle: '@aewol.day', icon: 'fa-camera', note: '제주 카페와 해안도로 피드', following: true },
        { name: '당일치기 연구소', handle: '@oneday.trip', icon: 'fa-map-location-dot', note: '주말 짧은 코스 모음', following: true }
    ];
    public myProfilePosts: any[] = [
        {
            id: 'feed-seongsu',
            title: '성수 감성 데이트',
            location: '서울 성수',
            caption: '서울숲 산책과 카페를 천천히 이어 본 코스',
            icon: 'fa-mug-saucer',
            tone: 'feed-rose',
            likes: 128,
            regrams: 8,
            regrammed: true
        },
        {
            id: 'feed-busan',
            title: '해운대 바다 코스',
            location: '부산 해운대',
            caption: '오션 카페에서 시작해 해변길로 마무리',
            icon: 'fa-water',
            tone: 'feed-blue',
            likes: 96,
            regrams: 5,
            regrammed: false
        },
        {
            id: 'feed-jeju',
            title: '애월 감성숙소',
            location: '제주 애월',
            caption: '노을 시간에 맞춰 저장해 둔 스테이 루트',
            icon: 'fa-bed',
            tone: 'feed-green',
            likes: 84,
            regrams: 4,
            regrammed: false
        },
        {
            id: 'feed-iksun',
            title: '익선동 골목 기록',
            location: '서울 종로',
            caption: '한옥 골목, 디저트, 사진 스폿을 묶은 피드',
            icon: 'fa-camera',
            tone: 'feed-sun',
            likes: 73,
            regrams: 6,
            regrammed: true
        }
    ];
    public authForm: any = {
        email: '',
        password: '',
        passwordConfirm: '',
        nickname: ''
    };
    public authErrors: any = {};
    public messages: any[] = [
        {
            role: 'assistant',
            text: '어디로, 누구와, 언제 가는지만 말해주면 코스 초안을 바로 잡아드릴게요.',
            time: '오전 10:30',
            seed: true
        }
    ];
    public suggestions: string[] = [
        '이번 주말 서울 데이트 코스',
        '20만원 예산 제주 1박 코스',
        '혼자 가기 좋은 바다 코스',
        '부모님과 당일치기 코스',
        '덜 걷는 카페 중심 코스',
        '동행 모집까지 가능한 코스'
    ];

    public plannerCourseReady: boolean = false;
    public isPlannerGenerating: boolean = false;
    public plannerTravelState: any = {};
    public plannerStage: string = 'collecting';
    public plannerAction: string = 'ask_clarification';
    public plannerMissingSlots: string[] = [];
    public plannerWarnings: string[] = [];
    public plannerFailureStage: string = '';
    public plannerProgressSteps: string[] = ['여행 조건 정리 중', '장소 검색 중', '동선 계산 중', '일정 구성 중'];
    public plannerGenerationStep: number = 0;
    private plannerProgressTimer: any = null;
    public plannerCourseBaseTitle: string = '내 부산 여행';
    public plannerCourseDayIndex: number = 0;
    public plannerCourseDays: any[] = [];
    public plannerQuality: any = {};
    public plannerTravelerStyle: string = '취향 중심';
    private plannerTouchStartX: number = 0;
    public plannerCourseTitle: string = '내 부산 여행 1일차 코스';
    public plannerCourseRegion: string = '부산 해운대구';
    public plannerCourseSchedule: string = '2박 3일';
    public plannerMapLabel: string = '해운대구 동선';
    public plannerMapExpanded: boolean = false;
    public plannerTotalTime: string = '약 7시간';
    public plannerDistance: string = '약 12.6km';
    public plannerReturnTime: string = '20:20';
    public plannerMapRoutePoints: string = '';
    public plannerMapAreas: any[] = [
        { label: '해운대구', className: 'area-haeundae' },
        { label: '수영구', className: 'area-suyoung' }
    ];
    public plannerStops: any[] = [];
    public plannerRouteSource: string = '기본 동선';
    private plannerGoogleRouteToken: number = 0;
    private plannerRouteSummary: any = {};
    private plannerGoogleRoutePath: any[] = [];
    public plannerCompanionCards: any[] = [
        {
            id: 'planner-mate-busan',
            courseId: '',
            courseConfirmed: false,
            title: '해운대 바다 보고, 밀면 먹을 여행 메이트',
            route: '내 부산 여행 1일차 코스',
            routeStops: ['해운대 해변', '해운대 밀면', '청사포 카페'],
            location: '부산 해운대',
            date: '1박 2일',
            time: '10:00 출발',
            capacity: 4,
            applicants: 3,
            estimatedCost: '1인 약 8만원',
            budgetStyle: 'medium',
            pace: 'balanced',
            moodTags: ['사진', '맛집', '편안한 대화'],
            flexibility: ['카페 순서', '종료 시간'],
            intro: 'AI가 짠 해운대 동선을 같이 걷고 사진도 남길 동행을 찾아요.',
            host: 'GACHI',
            status: 'open',
            saved: false,
            image: '/assets/bg-blue.jpg'
        },
        {
            id: 'planner-mate-cafe',
            courseId: '',
            courseConfirmed: false,
            title: '카페 라소어를 여유롭게 즐길 친구 구해요',
            route: '해운대 카페 중심 코스',
            routeStops: ['해운대 해변', '카페 라소어', '청사포'],
            location: '부산 해운대',
            date: '당일',
            time: '13:00 출발',
            capacity: 3,
            applicants: 1,
            estimatedCost: '1인 약 5만원',
            budgetStyle: 'medium',
            pace: 'slow',
            moodTags: ['카페', '산책', '조용히'],
            flexibility: ['카페 순서'],
            intro: '카페와 바다 산책을 여유롭게 이어갈 분을 찾아요.',
            host: 'GACHI',
            status: 'open',
            saved: false,
            image: '/assets/bg-blue.jpg'
        }
    ];

    public flowSteps: any[] = [
        { icon: 'fa-wand-magic-sparkles', label: 'AI 계획', text: '취향과 예산으로 일정 생성' },
        { icon: 'fa-pen-to-square', label: '코스 제작', text: '장소, 사진, 설명을 묶어 공유' },
        { icon: 'fa-map-location-dot', label: '여행 실행', text: '지도 경로와 친구 위치 확인' },
        { icon: 'fa-user-group', label: '동행 성사', text: '신청 수락 후 1:1 채팅' },
        { icon: 'fa-star', label: '후기 기록', text: '여행 완료 후 리뷰 작성' }
    ];

    public communityTopics: any[] = [
        { key: 'recommend', label: '추천', icon: 'fa-thumbs-up' },
        { key: 'vote', label: '인기 투표', icon: 'fa-square-poll-vertical' },
        { key: 'life', label: '생활정보', icon: 'fa-circle-info' },
        { key: 'question', label: '질문', icon: 'fa-circle-question' },
        { key: 'review', label: '후기', icon: 'fa-star' }
    ];
    public communitySortOptions: any[] = [
        { key: 'recommended', label: '추천' },
        { key: 'latest', label: '최신순' }
    ];

    // 추후 커뮤니티 API 연동 예정: 현재는 UI 확인용 로컬 데이터.
    public communityPosts: any[] = [
        {
            id: 'community-seoul-daytrip',
            kind: 'post',
            topic: 'recommend',
            title: '서울 근교에서 조용했던 당일치기 코스',
            summary: '양평 산책로와 작은 카페를 묶으니 이동 부담이 적고 오후 일정으로 좋았어요.',
            category: '추천',
            destination: '경기 양평',
            place: '두물머리 산책로',
            author: '서울 산책러',
            likes: 128,
            comments: 18,
            votes: 0,
            createdAt: 5,
            createdLabel: '5분 전',
            tags: ['당일치기', '카페', '조용한코스']
        },
        {
            id: 'community-gangneung-family',
            kind: 'post',
            topic: 'recommend',
            title: '부모님과 강릉 가면 편했던 동선',
            summary: '시장, 바다 전망 카페, 짧은 산책로 순서로 잡으니 오래 걷지 않아도 만족도가 높았어요.',
            category: '추천',
            destination: '강원 강릉',
            place: '안목해변, 중앙시장',
            author: '가족여행 메모',
            likes: 88,
            comments: 13,
            votes: 0,
            createdAt: 12,
            createdLabel: '12분 전',
            tags: ['가족', '강릉', '부모님']
        },
        {
            id: 'community-busan-rain-date',
            kind: 'post',
            topic: 'life',
            title: '비 오는 날 부산 실내 데이트 추천',
            summary: '전시, 서점, 오션뷰 카페 순서로 움직이면 날씨 영향이 적었습니다.',
            category: '생활정보',
            destination: '부산 해운대',
            place: '해운대 실내 전시',
            author: '부산 바다친구',
            likes: 94,
            comments: 11,
            votes: 0,
            createdAt: 24,
            createdLabel: '24분 전',
            tags: ['비오는날', '데이트', '실내']
        },
        {
            id: 'community-jeju-cafe-list',
            kind: 'post',
            topic: 'review',
            title: '혼자 제주 갈 때 저장해둘 카페 리스트',
            summary: '애월과 협재 쪽은 오전 방문이 한산했고, 노트북 작업하기 좋은 곳도 있었어요.',
            category: '후기',
            destination: '제주 애월',
            place: '애월 해안 카페',
            author: '제주 애월 기록',
            likes: 76,
            comments: 9,
            votes: 0,
            createdAt: 56,
            createdLabel: '56분 전',
            tags: ['혼행', '카페', '노트북']
        },
        {
            id: 'community-budget-vote',
            kind: 'post',
            topic: 'vote',
            title: '주말 1박 여행 예산 어느 정도가 적당해요?',
            summary: '숙소와 교통비를 포함한 현실적인 예산을 골라주세요.',
            category: '인기 투표',
            destination: '',
            place: '',
            author: 'GACHI',
            likes: 63,
            comments: 7,
            votes: 146,
            createdAt: 78,
            createdLabel: '1시간 전',
            poll: {
                title: '1인 기준 예산',
                options: ['10만원 이하', '10-20만원', '20만원 이상'],
                counts: {
                    '10만원 이하': 28,
                    '10-20만원': 84,
                    '20만원 이상': 34
                }
            },
            tags: ['예산', '1박2일', '투표']
        },
        {
            id: 'community-jejudo-question',
            kind: 'question',
            topic: 'question',
            title: '제주 서쪽 혼자 여행이면 차 없이 가능할까요?',
            summary: '애월, 협재 쪽으로 2박을 잡으려는데 버스만으로 동선이 괜찮은지 궁금합니다.',
            category: '질문',
            destination: '제주 서쪽',
            place: '애월, 협재',
            author: '혼행 준비중',
            likes: 41,
            comments: 14,
            votes: 0,
            createdAt: 118,
            createdLabel: '2시간 전',
            tags: ['제주', '혼행', '대중교통']
        }
    ];

    public companionPosts: any[] = [
        {
            id: 'mate-seongsu',
            courseId: 'course-seongsu-date',
            courseConfirmed: true,
            title: '성수 감성 데이트 루트 동행',
            route: '성수 감성 데이트 루트',
            routeStops: ['서울숲', '성수 전시', '연무장길 카페'],
            location: '서울 성수',
            date: '7.12 토',
            time: '13:00-18:30',
            capacity: 2,
            applicants: 3,
            estimatedCost: '1인 약 4.5만원',
            budgetStyle: 'medium',
            pace: 'slow',
            moodTags: ['차분한 대화', '사진'],
            flexibility: ['카페 순서', '종료 시간 ±1시간'],
            interestTags: ['전시', '카페', '산책'],
            smoking: 'non',
            drinking: 'light',
            verificationRequired: true,
            hostHistory: '동행 5회 · 후기 12개 · 4.9',
            meetingPoint: '서울숲역 3번 출구',
            packingItems: ['편한 신발', '보조배터리', '개인 우산'],
            intro: '전시 보고 카페까지 천천히 걸으며 여행 속도를 맞출 분을 구해요.',
            host: '서울 산책러',
            status: 'open',
            saved: false
        },
        {
            id: 'mate-busan',
            courseId: 'course-busan-haeundae',
            courseConfirmed: true,
            title: '부산 해운대 1박 코스 함께 가요',
            route: '해운대 바다 1박2일 코스',
            routeStops: ['해운대역', '해운대 해변', '청사포', '광안리'],
            location: '부산 해운대',
            date: '7.18 금-7.19 토',
            time: '첫날 15:00 집결',
            capacity: 4,
            applicants: 5,
            estimatedCost: '숙소 제외 1인 약 9만원',
            budgetStyle: 'medium',
            pace: 'balanced',
            moodTags: ['바다', '맛집', '활발한 대화'],
            flexibility: ['저녁 맛집', '둘째 날 종료 시간'],
            interestTags: ['바다', '맛집', '야경'],
            smoking: 'non',
            drinking: 'social',
            verificationRequired: true,
            hostHistory: '부산 여행 8회 · 후기 21개 · 4.8',
            meetingPoint: '해운대역 5번 출구',
            packingItems: ['신분증', '보조배터리', '가벼운 겉옷'],
            intro: '숙소는 각자, 바다 산책과 맛집 코스를 같이 다닐 분을 찾습니다.',
            host: '부산 바다친구',
            status: 'requested',
            saved: true,
            applications: [
                {
                    id: 'application-busan-sample',
                    applicantKey: 'sample-traveler',
                    applicantNickname: '해변 산책러',
                    appliedAt: '방금',
                    status: 'pending',
                    resume: {
                        photo: '',
                        fullName: '김여행',
                        nickname: '해변 산책러',
                        age: 27,
                        gender: '여성',
                        region: '서울 마포',
                        companionUses: 2,
                        interests: '바다, 맛집, 사진',
                        smoking: 'non',
                        drinking: 'social',
                        identityVerified: true,
                        reviewScore: 4.8,
                        availabilityConfirmed: true,
                        travelExperience: '부산과 제주에서 1박 여행 동행 경험이 있고, 숙소는 각자 잡는 방식을 선호합니다.',
                        intro: '사진 찍는 속도를 맞추며 천천히 걷는 여행을 좋아해요.'
                    }
                }
            ]
        },
        {
            id: 'mate-jeju',
            courseId: 'course-jeju-aewol',
            courseConfirmed: true,
            title: '제주 애월 노을 드라이브',
            route: '제주 애월 감성숙소 스테이',
            routeStops: ['애월 카페거리', '한담해변', '협재해변', '노을 숙소'],
            location: '제주 애월',
            date: '8.02 일',
            time: '10:00-20:00',
            capacity: 3,
            applicants: 2,
            estimatedCost: '렌터카 포함 1인 약 12만원',
            budgetStyle: 'high',
            pace: 'slow',
            moodTags: ['사진', '노을', '조용한 대화'],
            flexibility: ['카페 체류 시간', '노을 장소'],
            interestTags: ['드라이브', '카페', '사진'],
            smoking: 'non',
            drinking: 'none',
            verificationRequired: true,
            hostHistory: '제주 여행 6회 · 후기 17개 · 4.9',
            meetingPoint: '제주공항 렌터카 셔틀 승강장',
            packingItems: [
                { label: '운전면허증', done: true },
                { label: '보조배터리', done: false },
                { label: '얇은 겉옷', done: false }
            ],
            intro: '렌터카 이동 예정이고 사진 스폿 위주로 여유롭게 움직여요.',
            host: '제주 애월 기록',
            status: 'matched',
            saved: true
        }
    ];

    public reviewPosts: any[] = [
        {
            id: 'review-seongsu',
            title: 'AI가 잡아준 성수 반나절 코스',
            course: '성수 감성 데이트 루트',
            author: '민지',
            rating: '4.8',
            summary: '동선이 짧아서 카페 대기 시간이 있어도 일정이 무너지지 않았어요.',
            tags: ['AI 일정', '데이트', '서울']
        },
        {
            id: 'review-busan',
            title: '위치 공유 덕분에 해운대에서 안 헤맸어요',
            course: '해운대 바다 1박2일 코스',
            author: '준호',
            rating: '4.9',
            summary: '친구 위치가 바로 보여서 각자 움직이다 다시 만나기 편했습니다.',
            tags: ['같이 지도', '부산', '1박2일']
        },
        {
            id: 'review-jeju',
            title: '동행 성사 후 채팅으로 일정 조율',
            course: '제주 애월 감성숙소 스테이',
            author: '하나',
            rating: '4.7',
            summary: '수락된 사람끼리만 채팅이 열려서 부담 없이 세부 일정을 맞췄어요.',
            tags: ['동행', '제주', '후기']
        }
    ];

    // 동행 성사 후 생성되는 1:1 채팅 UI 확인용 데이터.
    public directChats: any[] = [
        {
            id: 'dm-mate-jeju',
            companionPostId: 'mate-jeju',
            name: '제주 애월 기록',
            handle: '제주 애월 노을 드라이브',
            avatar: '민',
            status: '동행 준비방',
            preview: '렌터카 픽업 시간은 10시로 맞출게요.',
            time: '방금',
            unread: 2,
            category: 'companion',
            muted: false,
            blocked: false,
            messages: [
                { role: 'other', text: '동행 신청 수락했어요. 애월 코스 같이 조율해볼까요?', time: '오후 2:14' },
                { role: 'me', text: '좋아요. 숙소 체크인 전 해안도로 먼저 가면 어떨까요?', time: '오후 2:16' },
                { role: 'other', text: '렌터카 픽업 시간은 10시로 맞출게요.', time: '오후 2:18' }
            ]
        },
        {
            id: 'dm-busan',
            name: '부산 바다친구',
            handle: '해운대 1박 코스',
            avatar: '준',
            status: '동행 성사',
            preview: '해운대역에서 3시에 만나요.',
            time: '1시간',
            unread: 0,
            category: 'companion',
            muted: false,
            blocked: false,
            messages: [
                { role: 'other', text: '신청 수락했습니다. 숙소는 각자 잡는 걸로 괜찮죠?', time: '오후 1:05' },
                { role: 'me', text: '네. 첫날 해운대역에서 만나면 좋겠습니다.', time: '오후 1:10' },
                { role: 'other', text: '해운대역에서 3시에 만나요.', time: '오후 1:12' }
            ]
        }
    ];
    public directChatFilters: any[] = [
        { key: 'all', label: '전체' },
        { key: 'unread', label: '안읽음' },
        { key: 'companion', label: '동행모임' }
    ];
    public directChatFilter: string = 'all';
    public activeDirectChatId: string = 'dm-mate-jeju';
    public directRoomOpen: boolean = false;
    public directActionMenuOpen: boolean = false;

    public keywordTags: string[] = [
        '여행',
        '데이트',
        '1박2일',
        '당일치기',
        '감성숙소',
        '카페',
        '맛집',
        '볼거리',
        '쇼핑'
    ];

    public homeRegionTabs: any[] = [
        { label: '전체', value: '' },
        { label: '서울', value: '서울' },
        { label: '부산', value: '부산' },
        { label: '제주', value: '제주' },
        { label: '강릉', value: '강릉' },
        { label: '속초', value: '속초' },
        { label: '전주', value: '전주' },
        { label: '여수', value: '여수' },
        { label: '경주', value: '경주' },
        { label: '인천', value: '인천' },
        { label: '가평', value: '가평' }
    ];

    public selectedFilters: any = {
        companion: '',
        schedule: '',
        location: ''
    };

    public conditionFilters: any[] = [
        {
            key: 'companion',
            label: '누구랑',
            icon: 'fa-user-group',
            defaultValue: '누구랑',
            options: ['연인', '친구', '가족', '혼자']
        },
        {
            key: 'schedule',
            label: '언제',
            icon: 'fa-calendar-days',
            defaultValue: '날짜'
        },
        {
            key: 'location',
            label: '위치',
            icon: 'fa-location-dot',
            defaultValue: '지역'
        }
    ];

    public weekdays: string[] = ['일', '월', '화', '수', '목', '금', '토'];
    public calendarMonthLabel: string = '';
    public calendarWeeks: any[] = [];
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
    private pinchStartDistance: number = 0;
    private pinchStartZoom: number = 2;
    private googleMap: any = null;
    private googleMapElement: any = null;
    private googleMarkers: any[] = [];
    private googleRouteLine: any = null;
    private googleCompareLine: any = null;
    private googleUserMarker: any = null;
    private googleSearchMarker: any = null;
    private googleSearchCoordinate: any = null;
    private googleDirectionsService: any = null;
    private googleDirectionsRenderer: any = null;
    private googleMapsLoader: any = null;
    private googleRouteToken: number = 0;
    private googleUserCoordinate: any = null;
    private googleCenterOnUser: boolean = false;
    private courseGoogleMap: any = null;
    private courseGoogleMapElement: any = null;
    private courseGoogleMarkers: any[] = [];
    private courseGoogleRouteLine: any = null;
    private plannerGoogleMap: any = null;
    private plannerGoogleMapElement: any = null;
    private plannerGoogleMarkers: any[] = [];
    private plannerGoogleRouteLine: any = null;
    private plannerExpandedGoogleMap: any = null;
    private plannerExpandedGoogleMapElement: any = null;
    private plannerExpandedGoogleMarkers: any[] = [];
    private plannerExpandedGoogleRouteLine: any = null;
    private saveHintTimer: any = null;
    private pendingChatPrompt: string = '';
    private placeCoursesRequestToken: number = 0;
    private placeSearchTimer: any = null;
    private coursePlaceSearchTimer: any = null;
    private savedCourseIds: any[] = [];
    private courseDraftStorageBaseKey: string = 'tour-on-course-draft';
    private courseDraftArchiveChecked: boolean = false;
    private recentPlacesStorageBaseKey: string = 'tour-on-recent-places';
    private travelResumeStorageBaseKey: string = 'tour-on-travel-resume';
    private passIdentityReturnId: string = '';
    private portOneSdkLoader: any = null;
    private myProfileEditStorageBaseKey: string = 'gachi-profile-edit';
    private myCourseViewModeStorageBaseKey: string = 'gachi-my-course-view-mode';
    private communityPostsStorageKey: string = 'gachi-community-posts';
    private communityActorStorageKey: string = 'gachi-community-actor';
    private communityLikeStorageKey: string = 'gachi-community-liked';
    private communityVoteStorageKey: string = 'gachi-community-voted';

    public tabs: any[] = [
        { key: 'home', label: '홈', icon: 'fa-house', iconStyle: 'fa-solid' },
        { key: 'map', label: '지도', icon: 'fa-map-location-dot', iconStyle: 'fa-solid' },
        { key: 'chat', label: '채팅', icon: 'fa-comment-dots', iconStyle: 'fa-regular' },
        { key: 'saved', label: '찜', icon: 'fa-bookmark', iconStyle: 'fa-regular' },
        { key: 'my', label: '마이', icon: 'fa-user', iconStyle: 'fa-regular' }
    ];

    public zenlyLayerTab: string = 'signals';
    public zenlyHeatmapLoading: boolean = false;
    public zenlySignalsLoading: boolean = false;
    public zenlySignalSubmitting: boolean = false;
    public zenlySignalComposerOpen: boolean = false;
    public selectedPresencePlaceId: string = '';
    public selectedZenlySignalId: string = '';
    public selectedZenlyFallbackCard: any = null;
    public zenlyHeatmap: any = {
        region: '성수',
        regionTotal: 0,
        banner: '지금 성수에 0명이 있어요',
        privacy: '개인 식별자 없이 장소별 시간대 집계만 사용합니다.',
        places: []
    };
    public zenlyPresenceHourly: any[] = [];
    public zenlySignals: any[] = [];
    public zenlySignalDurations: any[] = [
        { value: 30, label: '30분' },
        { value: 60, label: '1시간' },
        { value: 180, label: '3시간' }
    ];
    public zenlySignalMoodTags: string[] = ['조용히', '활발하게', '카페', '맛집', '사진', '산책', '전시', '야경'];
    public zenlySignalDraft: any = {
        locationMode: 'current',
        placeQuery: '',
        place: null,
        message: '',
        duration: 60,
        tags: []
    };
    public zenlyPlaceSearchResults: any[] = [];
    public togetherTripStarted: boolean = false;
    public togetherTripEnded: boolean = false;
    public togetherSafetyOpen: boolean = false;
    public togetherInfoFocus: string = 'companions';
    public togetherLocationSharingActive: boolean = false;
    public togetherShareDuration: any = 60;
    public togetherShareStartedAt: number = 0;
    private togetherShareTimer: any = null;
    public togetherMeetingAppointment: any = null;
    public togetherMeetingChatMessages: any[] = [];
    public togetherMeetingChatDraft: string = '';
    public togetherMeetingChatOpen: boolean = false;
    public togetherMeetingChatLoading: boolean = false;
    public togetherMeetingChatSending: boolean = false;
    private togetherMeetingExpiryTimer: any = null;
    private togetherMeetingPollTimer: any = null;
    public selectedTogetherCompanionId: string = 'together-minji';
    public togetherShareDurations: any[] = [
        { value: 30, label: '30분' },
        { value: 60, label: '1시간' },
        { value: 'trip', label: '여행 종료까지' }
    ];
    public togetherPrivateZones: any = {
        home: true,
        stay: true
    };
    public togetherMeetingPoint: any = {
        name: '제주공항 렌터카 셔틀 승강장',
        time: '오전 10:00',
        note: '도착하면 준비방에 알려주세요',
        x: 47,
        y: 57
    };
    public togetherCompanions: any[] = [
        {
            id: 'together-minji',
            name: '민지',
            initial: '민',
            color: '#f97373',
            status: '다음 목적지로 이동 중 · 3분 전',
            x: 58,
            y: 38,
            matched: true,
            mutualConsent: true,
            sharing: true,
            blocked: false,
            reported: false
        },
        {
            id: 'together-junho',
            name: '준호',
            initial: '준',
            color: '#5b8def',
            status: '약속 장소 근처 · 5분 전',
            x: 34,
            y: 64,
            matched: true,
            mutualConsent: false,
            sharing: true,
            blocked: false,
            reported: false
        },
        {
            id: 'together-soyeon',
            name: '소연',
            initial: '소',
            color: '#8b6edb',
            status: '합류 수락을 기다리는 중',
            x: 72,
            y: 61,
            matched: false,
            mutualConsent: false,
            sharing: false,
            blocked: false,
            reported: false
        }
    ];

    public recommendations: any[] = [
        {
            id: 'rec-seongsu',
            title: '성수 감성 데이트 루트',
            location: '서울 성수',
            summary: '전시와 카페, 와인바를 느리게 잇는 코스',
            duration: '4시간',
            rating: '4.8',
            price: '1인 4만원대',
            tone: 'tone-rose',
            icon: 'fa-mug-saucer',
            saved: false,
            tags: ['여행', '연인', '친구', '오늘', '이번주말', '당일치기', '서울', '데이트', '실내']
        },
        {
            id: 'rec-haeundae',
            title: '해운대 바다 1박2일 코스',
            location: '부산 해운대',
            summary: '바다 산책과 루프탑, 숙소 체크인까지 이어지는 루트',
            duration: '1박2일',
            rating: '4.9',
            price: '1인 8만원대',
            tone: 'tone-blue',
            icon: 'fa-water',
            saved: false,
            tags: ['여행', '연인', '친구', '1박2일', '이번주말', '부산', '데이트', '바다']
        },
        {
            id: 'rec-jeju-stay',
            title: '제주 애월 감성숙소 스테이',
            location: '제주 애월',
            summary: '오션뷰 숙소, 해안도로, 로컬 카페를 묶은 여유 코스',
            duration: '1박2일',
            rating: '4.8',
            price: '1인 12만원대',
            tone: 'tone-sun',
            icon: 'fa-bed',
            saved: false,
            tags: ['여행', '연인', '가족', '친구', '1박2일', '제주', '감성숙소', '데이트']
        },
        {
            id: 'rec-taean',
            title: '태안 노을 드라이브 코스',
            location: '충남 태안',
            summary: '해변 드라이브와 노을 명소, 조용한 식당을 잇는 코스',
            duration: '당일치기',
            rating: '4.7',
            price: '1인 5만원대',
            tone: 'tone-green',
            icon: 'fa-car-side',
            saved: false,
            tags: ['여행', '연인', '가족', '당일치기', '1박2일', '충남', '태안', '데이트', '바다']
        }
    ];

    public courses: any[] = [
        {
            id: 'list-iksun',
            title: '익선동 한옥 골목 맛집 투어',
            location: '서울 종로',
            summary: '식사, 디저트, 사진 스폿을 짧게 연결',
            duration: '2시간 30분',
            distance: '2.1km',
            icon: 'fa-utensils',
            saved: false,
            tags: ['여행', '연인', '친구', '가족', '오늘', '이번주말', '서울', '맛집', '데이트', '당일치기']
        },
        {
            id: 'list-gangneung',
            title: '강릉 커피 거리 당일치기',
            location: '강릉 안목',
            summary: '바다 전망 카페와 중앙시장 간식 루트',
            duration: '5시간',
            distance: '6.4km',
            icon: 'fa-cookie-bite',
            saved: false,
            tags: ['여행', '연인', '친구', '가족', '당일치기', '이번주말', '강릉', '바다', '맛집']
        },
        {
            id: 'list-jeonju',
            title: '전주 한옥마을 1박2일 미식 루트',
            location: '전주 완산',
            summary: '한옥 숙소와 시장 간식, 야간 산책을 담은 코스',
            duration: '1박2일',
            distance: '5.7km',
            icon: 'fa-landmark',
            saved: false,
            tags: ['여행', '연인', '친구', '가족', '1박2일', '전주', '전북', '감성숙소', '맛집']
        },
        {
            id: 'list-gyeongju',
            title: '경주 황리단길 감성숙소 코스',
            location: '경주 황남',
            summary: '고분 산책, 감성 숙소, 늦은 저녁 카페까지 연결',
            duration: '1박2일',
            distance: '4.3km',
            icon: 'fa-moon',
            saved: false,
            tags: ['여행', '연인', '친구', '1박2일', '경주', '경북', '감성숙소', '데이트']
        },
        {
            id: 'list-yeosu',
            title: '여수 밤바다 낭만 코스',
            location: '여수 돌산',
            summary: '해상 케이블카와 포차 거리, 야경 산책 루트',
            duration: '1박2일',
            distance: '6.1km',
            icon: 'fa-moon',
            saved: false,
            tags: ['여행', '연인', '친구', '1박2일', '여수', '전남', '데이트', '바다']
        },
        {
            id: 'list-sokcho',
            title: '속초 바다 산책 당일치기',
            location: '속초 청초호',
            summary: '혼자 걷기 좋은 호수길과 시장 먹거리 추천',
            duration: '당일치기',
            distance: '4.8km',
            icon: 'fa-person-walking',
            saved: false,
            tags: ['여행', '혼자', '친구', '오늘', '당일치기', '속초', '강원', '바다', '산책']
        },
        {
            id: 'list-gongju-buyeo',
            title: '공주·부여 역사 드라이브',
            location: '충남 공주',
            summary: '공산성, 백제문화단지, 한적한 카페를 잇는 코스',
            duration: '당일치기',
            distance: '8.2km',
            icon: 'fa-route',
            saved: false,
            tags: ['여행', '가족', '친구', '당일치기', '충남', '공주', '부여', '드라이브']
        },
        {
            id: 'list-tongyeong',
            title: '통영 바다 전망 미식 코스',
            location: '통영 동피랑',
            summary: '벽화마을 산책과 해산물 맛집, 케이블카 전망',
            duration: '당일치기',
            distance: '5.5km',
            icon: 'fa-fish',
            saved: false,
            tags: ['여행', '친구', '가족', '당일치기', '통영', '경남', '바다', '맛집']
        }
    ];

    public mapCategories: any[] = [
        { key: 'cafe', label: '카페', icon: 'fa-mug-saucer' },
        { key: 'food', label: '맛집', icon: 'fa-utensils' },
        { key: 'walk', label: '산책', icon: 'fa-person-walking' },
        { key: 'landmark', label: '명소', icon: 'fa-location-dot' }
    ];

    public activeMapCategories: any = {
        cafe: true,
        food: true,
        walk: true,
        landmark: true
    };

    public mapTravelModes: any[] = [
        { key: 'walk', label: '도보', icon: 'fa-person-walking' },
        { key: 'car', label: '차량', icon: 'fa-car-side' }
    ];

    public moveFilterOptions: any[] = [
        { key: '', label: '전체', icon: 'fa-layer-group' },
        { key: 'walk', label: '도보', icon: 'fa-person-walking' },
        { key: 'car', label: '차량', icon: 'fa-car-side' }
    ];

    public travelMode: string = 'walk';
    public selectedMoveFilter: string = '';
    public selectedMapSpotId: string = '';
    public mapZoom: number = 2;
    public userPosition: any = { x: 82, y: 18 };
    public googleMapReady: boolean = false;
    public googleMapsApiKey: string = '';
    public mapCoursePickerOpen: boolean = false;
    public mapCourseSourceTab: string = 'mine';
    public mapCourseSearchQuery: string = '';
    public stagedExecutionCourseId: string = '';
    public mapCoursesLoading: boolean = false;
    public mapExecutableCourses: any[] = [];
    public activeExecutionCourseId: string = '';
    public executionCourse: any = null;
    public executionPlaces: any[] = [];
    public executionTotalMinutes: number = 0;
    public executionTotalDistanceMeters: number = 0;
    public mapRouteSheetExpanded: boolean = false;
    public mapRouteLoading: boolean = false;
    public mapStartAddress: string = '';
    public mapStartStatus: string = '현재 위치';
    public mapSearchFocused: boolean = false;
    public mapSearchRemoteSuggestions: any[] = [];
    public mapSearchGoogleSuggestions: any[] = [];
    public mapSearchSuggestionLoading: boolean = false;
    public mapGpsDenied: boolean = false;
    private mapStartCoordinate: any = null;
    private executionLiveOrigin: any = null;
    private mapGeoWatchId: any = null;
    private mapSearchTimer: any = null;

    public mapCenters: any = {
        default: { lat: 37.5447, lng: 127.0557, zoom: 15 },
        서울: { lat: 37.5447, lng: 127.0557, zoom: 15 },
        성수: { lat: 37.5447, lng: 127.0557, zoom: 15 },
        종로: { lat: 37.5741, lng: 126.9861, zoom: 15 },
        익선동: { lat: 37.5741, lng: 126.9895, zoom: 16 },
        한강: { lat: 37.5288, lng: 126.9347, zoom: 15 },
        홍대: { lat: 37.5563, lng: 126.9236, zoom: 15 },
        경기: { lat: 37.2869, lng: 127.0117, zoom: 14 },
        수원: { lat: 37.2877, lng: 127.0117, zoom: 15 },
        가평: { lat: 37.8315, lng: 127.5098, zoom: 14 },
        인천: { lat: 37.3925, lng: 126.6349, zoom: 14 },
        송도: { lat: 37.3925, lng: 126.6349, zoom: 15 },
        부산: { lat: 35.1587, lng: 129.1604, zoom: 15 },
        해운대: { lat: 35.1587, lng: 129.1604, zoom: 15 },
        강원: { lat: 37.7711, lng: 128.9476, zoom: 14 },
        강릉: { lat: 37.7711, lng: 128.9476, zoom: 15 },
        속초: { lat: 38.1904, lng: 128.5989, zoom: 15 },
        충청: { lat: 36.4615, lng: 127.1247, zoom: 14 },
        공주: { lat: 36.4615, lng: 127.1247, zoom: 15 },
        태안: { lat: 36.7456, lng: 126.2981, zoom: 14 },
        전라: { lat: 35.8143, lng: 127.1537, zoom: 15 },
        전주: { lat: 35.8143, lng: 127.1537, zoom: 15 },
        여수: { lat: 34.7406, lng: 127.7354, zoom: 14 },
        경상: { lat: 35.8352, lng: 129.2133, zoom: 15 },
        경주: { lat: 35.8352, lng: 129.2133, zoom: 15 },
        통영: { lat: 34.8454, lng: 128.4270, zoom: 15 },
        제주: { lat: 33.4634, lng: 126.3090, zoom: 14 },
        애월: { lat: 33.4634, lng: 126.3090, zoom: 15 }
    };

    public mapSpotMap: any = {
        default: [
            { id: 'default-cafe', order: 1, name: '로컬 카페 거리', kind: '카페', category: 'cafe', icon: 'fa-mug-saucer', x: 27, y: 31, rating: '4.7', hours: '10:00-22:00', description: '창가 좌석과 디저트가 좋은 첫 목적지입니다.', times: { walk: '도보 8분', car: '차량 3분' }, photoClass: 'photo-cafe', visited: false },
            { id: 'default-walk', order: 2, name: '대표 산책로', kind: '산책', category: 'walk', icon: 'fa-person-walking', x: 47, y: 48, rating: '4.6', hours: '상시', description: '짧게 걷기 좋고 중간 휴식 지점이 많습니다.', times: { walk: '도보 12분', car: '차량 5분' }, photoClass: 'photo-walk', visited: false },
            { id: 'default-food', order: 3, name: '저녁 맛집 골목', kind: '맛집', category: 'food', icon: 'fa-utensils', x: 68, y: 63, rating: '4.8', hours: '11:30-21:30', description: '식사 선택지가 몰려 있어 마무리 동선에 적합합니다.', times: { walk: '도보 18분', car: '차량 8분' }, photoClass: 'photo-food', visited: false },
            { id: 'default-landmark', order: 4, name: '전망 포인트', kind: '명소', category: 'landmark', icon: 'fa-camera', x: 39, y: 72, rating: '4.5', hours: '상시', description: '사진을 남기기 좋은 코스의 마지막 지점입니다.', times: { walk: '도보 10분', car: '차량 4분' }, photoClass: 'photo-landmark', visited: false }
        ],
        서울: [
            { id: 'seoul-cafe', order: 1, name: '서울숲 카페거리', kind: '카페', category: 'cafe', icon: 'fa-mug-saucer', x: 26, y: 34, rating: '4.8', hours: '10:00-22:00', description: '성수 골목 초입의 브런치와 커피 스폿입니다.', times: { walk: '도보 7분', car: '차량 3분' }, photoClass: 'photo-cafe', visited: true },
            { id: 'seoul-walk', order: 2, name: '서울숲 산책로', kind: '산책', category: 'walk', icon: 'fa-tree', x: 44, y: 49, rating: '4.7', hours: '05:00-22:00', description: '그늘길과 벤치가 이어지는 코스 중심 지점입니다.', times: { walk: '도보 9분', car: '차량 4분' }, photoClass: 'photo-walk', visited: false },
            { id: 'seoul-food', order: 3, name: '성수 맛집 골목', kind: '맛집', category: 'food', icon: 'fa-utensils', x: 63, y: 61, rating: '4.6', hours: '11:30-21:30', description: '예약 없이 들르기 좋은 식당이 밀집한 구간입니다.', times: { walk: '도보 13분', car: '차량 6분' }, photoClass: 'photo-food', visited: false },
            { id: 'seoul-landmark', order: 4, name: '뚝섬 전망데크', kind: '명소', category: 'landmark', icon: 'fa-camera', x: 76, y: 39, rating: '4.5', hours: '상시', description: '한강 방향으로 열리는 사진 포인트입니다.', times: { walk: '도보 15분', car: '차량 8분' }, photoClass: 'photo-landmark', visited: false }
        ],
        부산: [
            { id: 'busan-cafe', order: 1, name: '해운대 오션 카페', kind: '카페', category: 'cafe', icon: 'fa-mug-saucer', x: 24, y: 38, rating: '4.6', hours: '09:00-22:00', description: '바다를 보며 출발하기 좋은 카페입니다.', times: { walk: '도보 5분', car: '차량 2분' }, photoClass: 'photo-cafe', visited: false },
            { id: 'busan-walk', order: 2, name: '해운대 해변길', kind: '산책', category: 'walk', icon: 'fa-water', x: 47, y: 55, rating: '4.9', hours: '상시', description: '바다 옆으로 길게 걷는 대표 산책 구간입니다.', times: { walk: '도보 8분', car: '차량 4분' }, photoClass: 'photo-walk', visited: false },
            { id: 'busan-food', order: 3, name: '미포 식당가', kind: '맛집', category: 'food', icon: 'fa-fish', x: 68, y: 43, rating: '4.7', hours: '11:00-22:00', description: '해산물과 로컬 식당을 함께 고르기 좋습니다.', times: { walk: '도보 16분', car: '차량 7분' }, photoClass: 'photo-food', visited: false },
            { id: 'busan-landmark', order: 4, name: '달맞이 전망길', kind: '명소', category: 'landmark', icon: 'fa-camera', x: 77, y: 68, rating: '4.8', hours: '상시', description: '노을과 야경을 모두 보기 좋은 언덕길입니다.', times: { walk: '도보 24분', car: '차량 9분' }, photoClass: 'photo-landmark', visited: false }
        ],
        제주: [
            { id: 'jeju-cafe', order: 1, name: '애월 브런치 카페', kind: '카페', category: 'cafe', icon: 'fa-mug-saucer', x: 25, y: 37, rating: '4.7', hours: '09:30-19:00', description: '바다 뷰와 가벼운 식사를 함께 잡는 지점입니다.', times: { walk: '도보 10분', car: '차량 4분' }, photoClass: 'photo-cafe', visited: false },
            { id: 'jeju-walk', order: 2, name: '곽지 해변 산책', kind: '산책', category: 'walk', icon: 'fa-water', x: 48, y: 56, rating: '4.8', hours: '상시', description: '모래사장과 산책길을 짧게 잇는 구간입니다.', times: { walk: '도보 14분', car: '차량 6분' }, photoClass: 'photo-walk', visited: false },
            { id: 'jeju-food', order: 3, name: '로컬 해산물 식당', kind: '맛집', category: 'food', icon: 'fa-utensils', x: 67, y: 65, rating: '4.6', hours: '11:00-20:30', description: '늦은 점심이나 저녁으로 이동하기 좋은 식당입니다.', times: { walk: '도보 22분', car: '차량 8분' }, photoClass: 'photo-food', visited: false },
            { id: 'jeju-landmark', order: 4, name: '애월 해안도로', kind: '명소', category: 'landmark', icon: 'fa-camera', x: 74, y: 34, rating: '4.9', hours: '상시', description: '드라이브와 사진 촬영을 함께 잡는 대표 포인트입니다.', times: { walk: '도보 28분', car: '차량 7분' }, photoClass: 'photo-landmark', visited: false }
        ],
        경기: [
            { id: 'gyeonggi-cafe', order: 1, name: '행궁동 카페', kind: '카페', category: 'cafe', icon: 'fa-mug-saucer', x: 29, y: 34, rating: '4.6', hours: '10:00-21:00', description: '골목 초입에서 쉬어가기 좋은 카페입니다.', times: { walk: '도보 8분', car: '차량 4분' }, photoClass: 'photo-cafe', visited: false },
            { id: 'gyeonggi-walk', order: 2, name: '수원 화성 산책', kind: '산책', category: 'walk', icon: 'fa-person-walking', x: 46, y: 53, rating: '4.8', hours: '상시', description: '성곽을 따라 천천히 도는 대표 산책 코스입니다.', times: { walk: '도보 12분', car: '차량 5분' }, photoClass: 'photo-walk', visited: false },
            { id: 'gyeonggi-food', order: 3, name: '통닭거리 맛집', kind: '맛집', category: 'food', icon: 'fa-utensils', x: 66, y: 66, rating: '4.5', hours: '11:00-22:00', description: '식사 선택지가 많아 동선 마무리에 적합합니다.', times: { walk: '도보 16분', car: '차량 7분' }, photoClass: 'photo-food', visited: false },
            { id: 'gyeonggi-landmark', order: 4, name: '방화수류정', kind: '명소', category: 'landmark', icon: 'fa-camera', x: 75, y: 39, rating: '4.7', hours: '상시', description: '수변과 성곽을 함께 담기 좋은 포인트입니다.', times: { walk: '도보 14분', car: '차량 6분' }, photoClass: 'photo-landmark', visited: false }
        ],
        강원: [
            { id: 'gangwon-cafe', order: 1, name: '안목 커피 거리', kind: '카페', category: 'cafe', icon: 'fa-mug-saucer', x: 27, y: 36, rating: '4.6', hours: '09:00-22:00', description: '바다 앞 커피집을 고르기 좋은 거리입니다.', times: { walk: '도보 8분', car: '차량 3분' }, photoClass: 'photo-cafe', visited: false },
            { id: 'gangwon-walk', order: 2, name: '해변 산책로', kind: '산책', category: 'walk', icon: 'fa-water', x: 48, y: 55, rating: '4.7', hours: '상시', description: '바닷바람을 맞으며 짧게 걷는 구간입니다.', times: { walk: '도보 11분', car: '차량 4분' }, photoClass: 'photo-walk', visited: false },
            { id: 'gangwon-food', order: 3, name: '중앙시장 먹거리', kind: '맛집', category: 'food', icon: 'fa-utensils', x: 68, y: 62, rating: '4.5', hours: '10:00-21:00', description: '간식과 식사를 한 번에 해결하기 좋은 지점입니다.', times: { walk: '도보 20분', car: '차량 12분' }, photoClass: 'photo-food', visited: false },
            { id: 'gangwon-landmark', order: 4, name: '서피비치 포인트', kind: '명소', category: 'landmark', icon: 'fa-camera', x: 76, y: 35, rating: '4.8', hours: '상시', description: '사진과 노을을 함께 담기 좋은 해변 포인트입니다.', times: { walk: '도보 30분', car: '차량 18분' }, photoClass: 'photo-landmark', visited: false }
        ],
        충청: [
            { id: 'chungcheong-cafe', order: 1, name: '공산성 카페', kind: '카페', category: 'cafe', icon: 'fa-mug-saucer', x: 27, y: 35, rating: '4.5', hours: '10:00-20:00', description: '산책 전후로 쉬어가기 좋은 카페입니다.', times: { walk: '도보 8분', car: '차량 4분' }, photoClass: 'photo-cafe', visited: false },
            { id: 'chungcheong-walk', order: 2, name: '공산성 산책길', kind: '산책', category: 'walk', icon: 'fa-person-walking', x: 47, y: 51, rating: '4.8', hours: '09:00-18:00', description: '성곽과 강변을 함께 보는 핵심 구간입니다.', times: { walk: '도보 14분', car: '차량 6분' }, photoClass: 'photo-walk', visited: false },
            { id: 'chungcheong-food', order: 3, name: '로컬 한식 골목', kind: '맛집', category: 'food', icon: 'fa-utensils', x: 66, y: 65, rating: '4.4', hours: '11:00-21:00', description: '가족 식사로 고르기 쉬운 식당이 모여 있습니다.', times: { walk: '도보 18분', car: '차량 8분' }, photoClass: 'photo-food', visited: false },
            { id: 'chungcheong-landmark', order: 4, name: '백제 전망 포인트', kind: '명소', category: 'landmark', icon: 'fa-camera', x: 75, y: 38, rating: '4.6', hours: '상시', description: '역사 코스의 사진 지점으로 쓰기 좋습니다.', times: { walk: '도보 24분', car: '차량 12분' }, photoClass: 'photo-landmark', visited: false }
        ],
        전라: [
            { id: 'jeolla-cafe', order: 1, name: '한옥마을 찻집', kind: '카페', category: 'cafe', icon: 'fa-mug-saucer', x: 26, y: 34, rating: '4.5', hours: '10:00-21:00', description: '한옥 골목 안에서 쉬어가기 좋은 찻집입니다.', times: { walk: '도보 6분', car: '차량 3분' }, photoClass: 'photo-cafe', visited: false },
            { id: 'jeolla-walk', order: 2, name: '전주 한옥마을', kind: '산책', category: 'walk', icon: 'fa-person-walking', x: 47, y: 52, rating: '4.7', hours: '상시', description: '골목과 전통 건물을 함께 둘러보는 구간입니다.', times: { walk: '도보 10분', car: '차량 4분' }, photoClass: 'photo-walk', visited: false },
            { id: 'jeolla-food', order: 3, name: '남부시장 맛집', kind: '맛집', category: 'food', icon: 'fa-utensils', x: 68, y: 64, rating: '4.6', hours: '11:00-22:00', description: '전주식 식사와 간식을 같이 고르기 좋습니다.', times: { walk: '도보 14분', car: '차량 6분' }, photoClass: 'photo-food', visited: false },
            { id: 'jeolla-landmark', order: 4, name: '오목대 전망', kind: '명소', category: 'landmark', icon: 'fa-camera', x: 76, y: 39, rating: '4.6', hours: '상시', description: '한옥 지붕 풍경을 내려다보는 사진 포인트입니다.', times: { walk: '도보 12분', car: '차량 5분' }, photoClass: 'photo-landmark', visited: false }
        ],
        경상: [
            { id: 'gyeongsang-cafe', order: 1, name: '황리단길 카페', kind: '카페', category: 'cafe', icon: 'fa-mug-saucer', x: 27, y: 34, rating: '4.6', hours: '10:00-21:00', description: '고분 산책 전후로 쉬어가기 좋은 지점입니다.', times: { walk: '도보 7분', car: '차량 3분' }, photoClass: 'photo-cafe', visited: false },
            { id: 'gyeongsang-walk', order: 2, name: '대릉원 산책로', kind: '산책', category: 'walk', icon: 'fa-person-walking', x: 46, y: 52, rating: '4.8', hours: '09:00-22:00', description: '고분과 나무길이 이어지는 대표 산책 구간입니다.', times: { walk: '도보 12분', car: '차량 5분' }, photoClass: 'photo-walk', visited: false },
            { id: 'gyeongsang-food', order: 3, name: '로컬 미식 골목', kind: '맛집', category: 'food', icon: 'fa-utensils', x: 67, y: 65, rating: '4.5', hours: '11:00-21:30', description: '저녁 식사로 이어가기 좋은 식당 구간입니다.', times: { walk: '도보 16분', car: '차량 7분' }, photoClass: 'photo-food', visited: false },
            { id: 'gyeongsang-landmark', order: 4, name: '첨성대 야경', kind: '명소', category: 'landmark', icon: 'fa-camera', x: 75, y: 38, rating: '4.7', hours: '상시', description: '해가 진 뒤에도 코스 만족도가 높은 명소입니다.', times: { walk: '도보 18분', car: '차량 8분' }, photoClass: 'photo-landmark', visited: false }
        ]
    };

    public async ngOnInit() {
        try {
            this.googleMapsApiKey = this.resolveGoogleMapsApiKey() || this.googleMapsApiKey;
            this.prepareCalendar();
            this.restoreIncomingState();
            await this.service.init();
            this.loadRecentPlaces();
            this.loadTravelResume();
            this.hydrateCompanionPreparationRooms();
            this.loadMyProfileEdit();
            await this.restorePassIdentityReturn();
            this.loadMyCourseViewMode();
            this.restoreCommunityPostsCache();
            await this.loadCommunityPosts(false);
            if (this.activeTab === 'my' && this.isLoggedIn()) this.myProfileOpen = true;
            if (this.routeLoginForMap()) return;
            if (this.routeRootHomeIfEmptyFilters()) return;
            await this.restoreSavedCourses();
            await this.service.render();
            if (this.activeTab === 'home') this.refreshHomePlacesInBackground();
            if (this.isLoggedIn()) await this.loadChatThreads(false);
            if (this.pendingChatPrompt) {
                let prompt = this.pendingChatPrompt;
                this.pendingChatPrompt = '';
                await this.sendChatPrompt(prompt);
            }
            if (this.activeTab === 'map' && this.mapContentTab === 'map') await this.prepareMapExecution();
            if (this.activeTab === 'map' && this.mapContentTab === 'zenly') await this.loadTogetherMapData(false);
        } catch (e) {
            this.activeTab = 'home';
            this.homeContentTab = 'feed';
            this.filterOverviewOpen = false;
            this.courseComposerOpen = false;
            try { await this.service.render(); } catch (renderError) { }
        }
    }

    public async setTab(tab: string) {
        if (tab === 'zenly' || tab === 'together') {
            tab = 'map';
            this.mapContentTab = 'zenly';
        }
        if (tab === 'map' && !this.isLoggedIn()) {
            this.goMapLogin();
            return;
        }

        this.activeTab = tab;
        if (tab !== 'map') this.togetherMeetingChatOpen = false;
        this.activeFilterKey = '';
        this.filterOverviewOpen = false;
        this.selectedMapSpotId = '';
        this.myProfileOpen = tab === 'my' && this.isLoggedIn();
        this.myProfileEditOpen = false;
        this.myResumeOpen = false;
        this.myResumePreviewOpen = false;
        this.myFeedComposerOpen = false;
        this.myArchiveOpen = false;
        this.myActivityOpen = false;
        this.myFeedDetailOpen = false;
        this.myCourseDetailOpen = false;
        this.profileFeedDetailPhotoIndex = 0;
        this.profileCourseDetailPhotoIndex = 0;
        this.selectedMyProfilePost = null;
        this.selectedMyProfileCourse = null;
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.service.render();
        if (tab === 'home') this.refreshHomePlacesInBackground();
        if (tab === 'chat') await this.loadChatThreads(false);
        if (tab === 'map' && this.mapContentTab === 'map') await this.prepareMapExecution();
        if (tab === 'map' && this.mapContentTab === 'zenly') await this.loadTogetherMapData(false);
    }

    public async selectTab(tab: string) {
        if (tab === 'chat' && ['chat', 'dm'].indexOf(this.chatContentTab) < 0) this.chatContentTab = 'chat';
        await this.setTab(tab);
        if (tab === 'chat') this.resetChatContentScroll();
    }

    public async setHomeContentTab(tab: string) {
        if (['feed', 'courses', 'companion', 'community'].indexOf(tab) < 0) tab = 'feed';
        this.homeContentTab = tab;
        await this.service.render();
        this.resetHomeContentScroll();
    }

    public async setCompanionMode(mode: string) {
        if (['pretrip', 'instant'].indexOf(mode) < 0) return;
        this.companionMode = mode;
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.service.render();
    }

    public async openCompanionMode(mode: string) {
        if (['pretrip', 'instant'].indexOf(mode) < 0) mode = 'pretrip';
        this.activeTab = 'home';
        this.homeContentTab = 'companion';
        this.companionMode = mode;
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.service.render();
        this.resetHomeContentScroll();
    }

    public async openInstantCompanion() {
        await this.setTab('zenly');
        if (this.activeTab !== 'map' || this.mapContentTab !== 'zenly') return;
        if (!this.isTogetherMapActive()) await this.startTogetherTrip();
        if (!this.isTogetherMapActive()) return;
        await this.setZenlyLayerTab('signals');
        if (!this.zenlySignalComposerOpen) await this.openTogetherSignalComposer();
    }

    public async setChatContentTab(tab: string) {
        if (['chat', 'dm'].indexOf(tab) < 0) return;
        let changed = this.chatContentTab !== tab;
        this.chatContentTab = tab;
        if (tab !== 'chat') this.chatDrawerOpen = false;
        if (changed) {
            this.directRoomOpen = false;
            this.directActionMenuOpen = false;
        }
        await this.service.render();
        this.resetChatContentScroll();
    }

    public async setMapContentTab(tab: string) {
        tab = this.normalizeMapContentTab(tab);
        if (!this.isSupportedMapContentTab(tab)) return;
        this.mapContentTab = tab;
        if (tab !== 'zenly') this.togetherMeetingChatOpen = false;
        this.selectedMapSpotId = '';
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.service.render();
        if (tab === 'map') await this.prepareMapExecution();
        if (tab === 'zenly') {
            this.bindZenlyMarkerDelegation();
            await this.loadTogetherMapData(false);
        }
    }

    public togetherConfirmedTrip() {
        if (this.executionCourse) {
            return {
                courseId: this.executionCourse.id || this.activeExecutionCourseId,
                courseConfirmed: true,
                route: this.executionCourse.title || this.executionCourseTitle(),
                title: this.executionCourse.title || this.executionCourseTitle(),
                date: '오늘',
                time: '현재 코스 실행 중',
                meetingPoint: this.togetherMeetingPoint.name,
                routeStops: this.executionPlaces.map((place: any) => place.name)
            };
        }
        return this.companionPosts.find((post: any) => {
            return this.isConfirmedCompanionPost(post) && post.status === 'matched';
        }) || null;
    }

    public hasConfirmedTogetherTrip() {
        return !!this.togetherConfirmedTrip();
    }

    public isTogetherMapActive() {
        return !!this.executionCourse || this.togetherTripStarted || this.hasActiveTogetherMeetingChat();
    }

    public togetherTripTitle() {
        let trip = this.togetherConfirmedTrip();
        if (!trip && this.hasActiveTogetherMeetingChat()) {
            return String(this.togetherMeetingAppointment.title || '주변 즉석 만남');
        }
        return String(trip && (trip.route || trip.title) ? (trip.route || trip.title) : '확정된 여행');
    }

    public togetherTripSchedule() {
        let trip = this.togetherConfirmedTrip();
        let schedule = [trip && trip.date, trip && trip.time].filter((value: any) => !!value).join(' · ');
        if (!schedule && this.hasActiveTogetherMeetingChat()) return this.togetherMeetingRemainingLabel();
        return schedule || '여행 종료 시 자동으로 닫혀요';
    }

    public togetherNextDestination() {
        let next = this.executionPlaces.find((place: any) => place && !place.visited) || this.executionPlaces[0];
        if (next) {
            let eta = next.times && next.times[this.travelMode] ? next.times[this.travelMode] : '도착 시간 계산 중';
            return {
                name: next.name || '다음 목적지',
                eta,
                detail: next.categoryLabel || next.kind || next.location || '코스 목적지'
            };
        }
        let trip = this.togetherConfirmedTrip();
        let stops = this.companionRouteStops(trip);
        return {
            name: stops[1] || stops[0] || '다음 목적지 확인 중',
            eta: '약 18분 뒤',
            detail: stops.length > 1 ? `${stops[0]}에서 이동` : '준비방 코스 기준'
        };
    }

    public async loadTogetherMapData(showLoading: boolean = false) {
        this.zenlyLayerTab = 'signals';
        if (!this.isTogetherMapActive()) {
            await this.loadTogetherMeeting(false, false);
            if (this.hasActiveTogetherMeetingChat()) {
                this.togetherTripStarted = true;
                this.togetherTripEnded = false;
            } else {
                this.zenlySignals = [];
                this.selectedZenlySignalId = '';
                return;
            }
        }
        await this.loadZenlySignals(showLoading);
        await this.loadTogetherMeeting(false, false);
        this.bindZenlyMarkerDelegation();
        await this.service.render();
    }

    public async startTogetherTrip() {
        if (!this.hasConfirmedTogetherTrip()) {
            await this.showSaveHint('확정된 동행 여행이 있어야 같이 지도를 열 수 있어요.');
            return;
        }
        this.togetherTripStarted = true;
        this.togetherTripEnded = false;
        this.togetherLocationSharingActive = false;
        this.togetherShareStartedAt = 0;
        this.clearTogetherShareTimer();
        this.togetherInfoFocus = 'companions';
        this.zenlyLayerTab = 'signals';
        this.activateTogetherTripMeeting();
        await this.loadTogetherMapData(false);
        await this.service.render();
        await this.showSaveHint('같이 지도가 열렸어요. 정확한 위치는 공유 시간을 고른 뒤 공개돼요.');
    }

    public async setTogetherInfoFocus(focus: string, event?: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        if (['companions', 'route', 'meeting', 'signals'].indexOf(focus) < 0) return;
        this.togetherMeetingChatOpen = false;
        this.togetherInfoFocus = focus;
        if (focus === 'signals') this.zenlyLayerTab = 'signals';
        await this.service.render();
    }

    public async openTogetherSafety(event?: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        this.zenlySignalComposerOpen = false;
        this.togetherMeetingChatOpen = false;
        this.togetherSafetyOpen = true;
        await this.service.render();
    }

    public async closeTogetherSafety() {
        this.togetherSafetyOpen = false;
        await this.service.render();
    }

    public async closeTogetherOverlays() {
        this.togetherSafetyOpen = false;
        this.zenlySignalComposerOpen = false;
        this.togetherMeetingChatOpen = false;
        await this.service.render();
    }

    public async setTogetherShareDuration(duration: any) {
        if ([30, 60, 'trip'].indexOf(duration) < 0) return;
        this.togetherShareDuration = duration;
        if (this.togetherLocationSharingActive) this.scheduleTogetherShareExpiry();
        await this.service.render();
    }

    public async startTogetherLocationShare() {
        if (!this.isTogetherMapActive()) {
            await this.showSaveHint('여행을 시작한 뒤 위치를 공유할 수 있어요.');
            return;
        }
        this.togetherLocationSharingActive = true;
        this.togetherShareStartedAt = Date.now();
        this.scheduleTogetherShareExpiry();
        this.togetherSafetyOpen = false;
        await this.service.render();
        await this.showSaveHint(`${this.togetherShareStatusLabel()} · 집과 숙소 주변은 계속 숨겨요.`);
    }

    public togetherShareStatusLabel() {
        if (!this.togetherLocationSharingActive) return '공유 꺼짐';
        if (this.togetherShareDuration === 'trip') return '여행 종료까지 공개 중';
        if (Number(this.togetherShareDuration) === 30) return '30분 공개 중';
        return '1시간 공개 중';
    }

    public async endTogetherLocationShare() {
        this.togetherLocationSharingActive = false;
        this.togetherShareStartedAt = 0;
        this.clearTogetherShareTimer();
        this.togetherSafetyOpen = false;
        await this.service.render();
        await this.showSaveHint('위치 공유를 종료했어요. 동행자에게는 대략적인 위치만 보여요.');
    }

    public async toggleTogetherPrivateZone(key: string) {
        if (['home', 'stay'].indexOf(key) < 0) return;
        this.togetherPrivateZones[key] = !this.togetherPrivateZones[key];
        await this.service.render();
    }

    public togetherVisibleCompanions() {
        return this.togetherCompanions.filter((companion: any) => companion && !companion.blocked);
    }

    public selectedTogetherCompanion() {
        let visible = this.togetherVisibleCompanions();
        return visible.find((companion: any) => companion.id === this.selectedTogetherCompanionId) || visible[0] || null;
    }

    public isTogetherCompanionSelected(companion: any) {
        return !!companion && companion.id === this.selectedTogetherCompanionId;
    }

    public canShowTogetherPreciseLocation(companion: any) {
        return !!companion
            && this.togetherLocationSharingActive
            && companion.matched === true
            && companion.mutualConsent === true
            && companion.sharing === true
            && !companion.blocked;
    }

    public togetherCompanionPrecisionLabel(companion: any) {
        if (this.canShowTogetherPreciseLocation(companion)) return '실시간 위치 · 상호 수락';
        if (companion && companion.matched) return '약 500m 범위 · 정확한 위치 잠김';
        return '약 1km 범위 · 수락 전';
    }

    public async selectTogetherCompanion(companion: any, event?: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        if (!companion || companion.blocked) return;
        this.selectedTogetherCompanionId = companion.id;
        this.togetherInfoFocus = 'companions';
        this.selectedZenlySignalId = '';
        await this.service.render();
    }

    public async blockTogetherCompanion(companion: any, event?: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        if (!companion) return;
        companion.blocked = true;
        let next = this.togetherVisibleCompanions()[0];
        this.selectedTogetherCompanionId = next ? next.id : '';
        await this.service.render();
        await this.showSaveHint(`${companion.name}님을 차단했어요. 위치와 신호가 더 이상 보이지 않아요.`);
    }

    public async reportTogetherCompanion(companion: any, event?: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        if (!companion) return;
        companion.reported = true;
        await this.service.render();
        await this.showSaveHint(`${companion.name}님에 대한 신고를 접수했어요.`);
    }

    public async openTogetherMeetingChat(event?: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        if (!this.hasActiveTogetherMeetingChat()) {
            await this.showSaveHint('진행 중인 약속이 생기면 약속 채팅이 열려요.');
            return;
        }
        this.togetherInfoFocus = 'meeting';
        this.togetherSafetyOpen = false;
        this.zenlySignalComposerOpen = false;
        this.togetherMeetingChatOpen = true;
        await this.refreshTogetherMeetingMessages(false);
        await this.service.render();
        this.scrollTogetherMeetingChat();
    }

    public async closeTogetherMeetingChat(event?: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        this.togetherMeetingChatOpen = false;
        await this.service.render();
    }

    public hasActiveTogetherMeetingChat() {
        let meeting = this.togetherMeetingAppointment;
        if (!meeting || meeting.active === false || meeting.status !== 'active') return false;
        let endsAt = Number(meeting.endsAtEpoch || 0);
        return !endsAt || endsAt > Date.now();
    }

    public togetherMeetingRemainingLabel() {
        if (!this.hasActiveTogetherMeetingChat()) return '종료됨';
        let endsAt = Number(this.togetherMeetingAppointment && this.togetherMeetingAppointment.endsAtEpoch || 0);
        if (!endsAt) return '약속 진행 중';
        let minutes = Math.max(1, Math.ceil((endsAt - Date.now()) / 60000));
        if (minutes < 60) return `${minutes}분 남음`;
        let hours = Math.floor(minutes / 60);
        let rest = minutes % 60;
        return rest ? `${hours}시간 ${rest}분 남음` : `${hours}시간 남음`;
    }

    private activateTogetherTripMeeting() {
        let trip = this.togetherConfirmedTrip();
        if (!trip) return;
        this.clearTogetherMeetingState(false);
        let locationLabel = String(trip.meetingPoint || this.togetherMeetingPoint.name || '준비방에서 정한 약속 장소');
        let tripId = String(trip.courseId || trip.id || Date.now());
        this.togetherMeetingPoint = {
            ...this.togetherMeetingPoint,
            name: locationLabel,
            time: String(trip.time || '약속 진행 중'),
            note: '약속 채팅은 약속이 끝나면 자동으로 사라져요.'
        };
        this.togetherMeetingAppointment = {
            id: `trip-${tripId}`,
            signalId: '',
            title: String(trip.route || trip.title || '여행 약속'),
            locationLabel,
            peerName: '동행자',
            status: 'active',
            active: true,
            serverBacked: false,
            endsAtEpoch: Date.now() + (3 * 60 * 60 * 1000)
        };
        this.togetherMeetingChatMessages = [{
            id: `trip-system-${tripId}`,
            role: 'system',
            senderName: '안내',
            text: '약속 채팅이 열렸어요. 이 대화는 약속이 끝나면 자동으로 사라져요.',
            timeLabel: '방금'
        }];
        this.scheduleTogetherMeetingExpiry();
    }

    private applyTogetherMeetingPayload(meeting: any, messages: any[] = []) {
        if (!meeting || meeting.status !== 'active') {
            if (this.togetherMeetingAppointment && this.togetherMeetingAppointment.serverBacked) {
                this.clearTogetherMeetingState(true);
            }
            return;
        }
        this.clearTogetherMeetingTimers();
        this.togetherMeetingAppointment = {
            ...meeting,
            active: true,
            serverBacked: true,
            endsAtEpoch: Number(meeting.endsAtEpoch || 0)
        };
        this.togetherMeetingChatMessages = Array.isArray(messages) ? messages.map((message: any, index: number) => ({
            id: message.id || `meeting-message-${index}`,
            role: ['me', 'other', 'system'].indexOf(message.role) > -1 ? message.role : 'other',
            senderName: message.senderName || (message.role === 'me' ? '나' : '동행자'),
            text: String(message.text || ''),
            timeLabel: message.timeLabel || '방금'
        })) : [];
        this.togetherMeetingPoint = {
            ...this.togetherMeetingPoint,
            name: meeting.locationLabel || '서로 정한 약속 장소',
            time: '약속 진행 중',
            note: `${meeting.peerName || '동행자'}님과 · ${this.togetherMeetingRemainingLabel()}`
        };
        this.scheduleTogetherMeetingExpiry();
        this.scheduleTogetherMeetingPoll();
    }

    public async loadTogetherMeeting(showLoading: boolean = false, shouldRender: boolean = true) {
        if (!this.isLoggedIn()) return;
        if (showLoading) {
            this.togetherMeetingChatLoading = true;
            if (shouldRender) await this.service.render();
        }
        try {
            const response: any = await wiz.call('zenly_meeting_active', {});
            if (response && response.code === 200 && response.data) {
                if (response.data.meeting) {
                    this.applyTogetherMeetingPayload(response.data.meeting, response.data.messages || []);
                } else if (this.togetherMeetingAppointment && this.togetherMeetingAppointment.serverBacked) {
                    this.clearTogetherMeetingState(true);
                }
            }
        } catch (e) { }
        this.togetherMeetingChatLoading = false;
        if (shouldRender) await this.service.render();
    }

    public async refreshTogetherMeetingMessages(shouldRender: boolean = true) {
        let meeting = this.togetherMeetingAppointment;
        if (!meeting || !meeting.serverBacked || !meeting.id || !this.isLoggedIn()) return;
        try {
            const response: any = await wiz.call('zenly_meeting_messages', { meeting_id: meeting.id });
            if (response && response.code === 200 && response.data && response.data.meeting) {
                this.applyTogetherMeetingPayload(response.data.meeting, response.data.messages || []);
            } else if (response && [404, 410].indexOf(Number(response.code)) > -1) {
                this.clearTogetherMeetingState(true);
            }
        } catch (e) { }
        if (shouldRender) {
            await this.service.render();
            this.scrollTogetherMeetingChat();
        }
    }

    public async sendTogetherMeetingMessage(event?: any) {
        if (event && event.preventDefault) event.preventDefault();
        if (event && event.stopPropagation) event.stopPropagation();
        let text = String(this.togetherMeetingChatDraft || '').trim().slice(0, 80);
        if (!text || !this.hasActiveTogetherMeetingChat() || this.togetherMeetingChatSending) return;
        let meeting = this.togetherMeetingAppointment;
        this.togetherMeetingChatSending = true;
        if (meeting.serverBacked) {
            try {
                const response: any = await wiz.call('zenly_meeting_message_send', {
                    meeting_id: meeting.id,
                    message: text
                });
                if (response && response.code === 200 && response.data && response.data.meeting) {
                    this.togetherMeetingChatDraft = '';
                    this.applyTogetherMeetingPayload(response.data.meeting, response.data.messages || []);
                } else if (response && [404, 410].indexOf(Number(response.code)) > -1) {
                    this.clearTogetherMeetingState(true);
                    await this.showSaveHint('약속이 끝나 채팅도 닫혔어요.');
                } else {
                    await this.showSaveHint(this.responseMessage(response && response.data, '메시지를 보내지 못했어요.'));
                }
            } catch (e) {
                await this.showSaveHint('메시지를 보내지 못했어요.');
            }
        } else {
            this.togetherMeetingChatMessages = [...this.togetherMeetingChatMessages, {
                id: `local-meeting-${Date.now()}`,
                role: 'me',
                senderName: '나',
                text,
                timeLabel: this.currentChatTimeLabel()
            }];
            this.togetherMeetingChatDraft = '';
        }
        this.togetherMeetingChatSending = false;
        await this.service.render();
        this.scrollTogetherMeetingChat();
    }

    public async endTogetherMeeting(event?: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        if (!this.togetherMeetingAppointment) return;
        await this.closeTogetherMeeting(true);
        await this.service.render();
        await this.showSaveHint('약속을 종료해 약속 채팅도 함께 사라졌어요.');
    }

    private async closeTogetherMeeting(notifyServer: boolean = true) {
        let meeting = this.togetherMeetingAppointment;
        if (notifyServer && meeting && meeting.serverBacked && meeting.id && this.isLoggedIn()) {
            try {
                await wiz.call('zenly_meeting_end', { meeting_id: meeting.id });
            } catch (e) { }
        }
        this.clearTogetherMeetingState(true);
    }

    private clearTogetherMeetingState(markEnded: boolean = true) {
        this.clearTogetherMeetingTimers();
        this.togetherMeetingAppointment = null;
        this.togetherMeetingChatMessages = [];
        this.togetherMeetingChatDraft = '';
        this.togetherMeetingChatOpen = false;
        this.togetherMeetingChatLoading = false;
        this.togetherMeetingChatSending = false;
        if (markEnded) {
            this.togetherMeetingPoint = {
                ...this.togetherMeetingPoint,
                time: '종료됨',
                note: '약속 채팅이 자동으로 닫혔어요.'
            };
        }
    }

    private scheduleTogetherMeetingExpiry() {
        if (this.togetherMeetingExpiryTimer && typeof window !== 'undefined') {
            window.clearTimeout(this.togetherMeetingExpiryTimer);
        }
        this.togetherMeetingExpiryTimer = null;
        if (!this.hasActiveTogetherMeetingChat() || typeof window === 'undefined') return;
        let endsAt = Number(this.togetherMeetingAppointment.endsAtEpoch || 0);
        if (!endsAt) return;
        let delay = Math.max(0, endsAt - Date.now());
        this.togetherMeetingExpiryTimer = window.setTimeout(async () => {
            this.togetherMeetingExpiryTimer = null;
            this.clearTogetherMeetingState(true);
            try {
                await this.service.render();
                await this.showSaveHint('약속이 끝나 약속 채팅이 자동으로 사라졌어요.');
            } catch (e) { }
        }, delay);
    }

    private scheduleTogetherMeetingPoll() {
        if (this.togetherMeetingPollTimer && typeof window !== 'undefined') {
            window.clearTimeout(this.togetherMeetingPollTimer);
        }
        this.togetherMeetingPollTimer = null;
        if (!this.hasActiveTogetherMeetingChat()
            || !this.togetherMeetingAppointment.serverBacked
            || typeof window === 'undefined') return;
        this.togetherMeetingPollTimer = window.setTimeout(async () => {
            this.togetherMeetingPollTimer = null;
            await this.refreshTogetherMeetingMessages(this.togetherMeetingChatOpen);
            if (this.hasActiveTogetherMeetingChat()) this.scheduleTogetherMeetingPoll();
        }, 7000);
    }

    private clearTogetherMeetingTimers() {
        if (typeof window !== 'undefined') {
            if (this.togetherMeetingExpiryTimer) window.clearTimeout(this.togetherMeetingExpiryTimer);
            if (this.togetherMeetingPollTimer) window.clearTimeout(this.togetherMeetingPollTimer);
        }
        this.togetherMeetingExpiryTimer = null;
        this.togetherMeetingPollTimer = null;
    }

    private scrollTogetherMeetingChat() {
        if (typeof window === 'undefined' || typeof document === 'undefined') return;
        window.setTimeout(() => {
            let list: any = document.querySelector('.access-shell .together-meeting-chat-list');
            if (list) list.scrollTop = list.scrollHeight;
        }, 0);
    }

    public togetherSignalRadius(signal: any) {
        let fuzzy = Number(signal && signal.fuzzyRadius ? signal.fuzzyRadius : 500);
        if (!isFinite(fuzzy) || fuzzy <= 0) fuzzy = 500;
        return Math.max(58, Math.min(108, Math.round(fuzzy / 7)));
    }

    public async selectTogetherSignal(signal: any, event?: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        this.togetherMeetingChatOpen = false;
        this.togetherInfoFocus = 'signals';
        await this.selectZenlySignal(signal, event);
    }

    public async openTogetherSignalComposer(event?: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        if (!this.isTogetherMapActive()) {
            await this.showSaveHint('여행을 시작한 뒤 주변 합류 신호를 보낼 수 있어요.');
            return;
        }
        this.togetherInfoFocus = 'signals';
        this.zenlyLayerTab = 'signals';
        this.togetherSafetyOpen = false;
        this.togetherMeetingChatOpen = false;
        if (!this.zenlySignalComposerOpen) await this.toggleZenlySignalComposer();
    }

    public async useTogetherSignalExample(message: string) {
        this.zenlySignalDraft.message = String(message || '').slice(0, 50);
        await this.service.render();
    }

    public async endTogetherTrip() {
        this.togetherLocationSharingActive = false;
        this.togetherShareStartedAt = 0;
        this.clearTogetherShareTimer();
        this.togetherTripStarted = false;
        this.togetherTripEnded = true;
        this.togetherSafetyOpen = false;
        this.zenlySignalComposerOpen = false;
        this.selectedZenlySignalId = '';
        this.zenlySignals = [];
        if (this.executionCourse) {
            await this.endExecutionCourse();
        } else {
            await this.closeTogetherMeeting(true);
        }
        await this.service.render();
        await this.showSaveHint('여행을 종료했어요. 위치 공유와 약속 채팅이 모두 자동으로 닫혔어요.');
    }

    private scheduleTogetherShareExpiry() {
        this.clearTogetherShareTimer();
        if (!this.togetherLocationSharingActive || this.togetherShareDuration === 'trip' || typeof window === 'undefined') return;
        let minutes = Number(this.togetherShareDuration);
        if (!isFinite(minutes) || minutes <= 0) return;
        this.togetherShareTimer = window.setTimeout(async () => {
            this.togetherShareTimer = null;
            this.togetherLocationSharingActive = false;
            this.togetherShareStartedAt = 0;
            try {
                await this.service.render();
                await this.showSaveHint('선택한 공개 시간이 끝나 위치 공유가 자동으로 해제됐어요.');
            } catch (e) { }
        }, minutes * 60 * 1000);
    }

    private clearTogetherShareTimer() {
        if (this.togetherShareTimer && typeof window !== 'undefined') {
            window.clearTimeout(this.togetherShareTimer);
        }
        this.togetherShareTimer = null;
    }

    public activeDirectChat() {
        return this.directChats.find((chat: any) => chat.id === this.activeDirectChatId) || this.directChats[0] || { messages: [] };
    }

    public filteredDirectChats() {
        return this.directChats.filter((chat: any) => this.directChatMatchesFilter(chat, this.directChatFilter));
    }

    public directChatFilterCount(key: string) {
        return this.directChats.filter((chat: any) => this.directChatMatchesFilter(chat, key)).length;
    }

    public async setDirectChatFilter(key: string) {
        if (!this.directChatFilters.some((filter: any) => filter.key === key)) return;
        this.directChatFilter = key;
        this.directRoomOpen = false;
        this.directActionMenuOpen = false;
        await this.service.render();
    }

    public async selectDirectChat(chat: any) {
        if (!chat) return;
        this.activeDirectChatId = chat.id;
        chat.unread = 0;
        this.directRoomOpen = true;
        this.directActionMenuOpen = false;
        await this.service.render();
        this.resetChatContentScroll();
    }

    public async closeDirectChatRoom() {
        this.directRoomOpen = false;
        this.directActionMenuOpen = false;
        this.directDraft = '';
        await this.service.render();
    }

    public async toggleDirectActionMenu() {
        this.directActionMenuOpen = !this.directActionMenuOpen;
        await this.service.render();
    }

    public directMuteActionLabel(chat: any) {
        return chat && chat.muted ? '알람 켜기' : '알람 끄기';
    }

    public directBlockActionLabel(chat: any) {
        return chat && chat.blocked ? '차단 해제' : '상대방 차단';
    }

    public async handleDirectChatAction(action: string) {
        let chat = this.activeDirectChat();
        if (!chat || !chat.id) return;

        this.directActionMenuOpen = false;

        if (action === 'block') {
            chat.blocked = !chat.blocked;
            await this.showSaveHint(chat.blocked ? `${chat.name}님을 차단했어요.` : `${chat.name}님 차단을 해제했어요.`);
            return;
        }

        if (action === 'report') {
            await this.showSaveHint(`${chat.name}님 신고 접수를 준비했어요.`);
            return;
        }

        if (action === 'fraud') {
            await this.showSaveHint('사기 이력이 조회되지 않았어요.');
            return;
        }

        if (action === 'mute') {
            chat.muted = !chat.muted;
            await this.showSaveHint(chat.muted ? '채팅방 알림을 껐어요.' : '채팅방 알림을 켰어요.');
            return;
        }

        if (action === 'leave') {
            let name = chat.name || '1:1';
            this.directChats = this.directChats.filter((item: any) => item.id !== chat.id);
            this.activeDirectChatId = this.directChats.length > 0 ? this.directChats[0].id : '';
            this.directRoomOpen = false;
            this.directDraft = '';
            await this.showSaveHint(`${name} 채팅방에서 나왔어요.`);
        }
    }

    public canSendDirectMessage() {
        let chat = this.activeDirectChat();
        return !!(chat && chat.id && !chat.blocked) && String(this.directDraft || '').trim().length > 0;
    }

    public async sendDirectMessage() {
        let text = String(this.directDraft || '').trim();
        if (!text) return;

        if (!this.isLoggedIn()) {
            await this.openAuthModal('login');
            return;
        }

        let chat = this.activeDirectChat();
        if (chat.blocked) {
            await this.showSaveHint('차단한 상대에게는 메시지를 보낼 수 없어요.');
            return;
        }
        if (!chat.messages) chat.messages = [];
        chat.messages.push({ role: 'me', text, time: '방금' });
        chat.preview = text;
        chat.time = '방금';
        chat.unread = 0;
        this.directDraft = '';
        await this.service.render();
        this.scrollDirectMessages();
    }

    public handleDirectComposerFocus() {
        this.scrollDirectMessages();
    }

    public async startDirectChat() {
        if (!this.isLoggedIn()) {
            await this.openAuthModal('login');
            return;
        }

        await this.showSaveHint('1:1 채팅은 동행 신청이 수락된 사용자끼리만 열립니다.');
    }

    public async setCommunityTopic(topic: string) {
        if (!this.communityTopics.some((item: any) => item.key === topic)) return;
        this.selectedCommunityTopic = topic;
        this.communitySortDropdownOpen = false;
        await this.service.render();
        this.resetChatContentScroll();
    }

    public async toggleCommunitySortDropdown() {
        this.communitySortDropdownOpen = !this.communitySortDropdownOpen;
        await this.service.render();
    }

    public async setCommunitySort(sort: string) {
        if (!this.communitySortOptions.some((item: any) => item.key === sort)) return;
        this.selectedCommunitySort = sort;
        if (sort === 'recommended') this.selectedCommunityTopic = 'recommend';
        this.communitySortDropdownOpen = false;
        await this.service.render();
    }

    public communitySortLabel() {
        let option = this.communitySortOptions.find((item: any) => item.key === this.selectedCommunitySort);
        return option ? option.label : '추천';
    }

    public communityFilterTopics() {
        return this.communityTopics.filter((topic: any) => topic.key !== 'recommend');
    }

    public communityTopicLabel() {
        if (this.selectedCommunityTopic === 'recommend') return this.communitySortLabel();
        let topic = this.communityTopics.find((item: any) => item.key === this.selectedCommunityTopic);
        return topic ? topic.label : '추천';
    }

    public filteredCommunityPosts() {
        let posts = this.communityPosts.filter((post: any) => {
            if (!this.selectedCommunityTopic) return true;
            if (this.selectedCommunityTopic === 'recommend') return true;
            return post.topic === this.selectedCommunityTopic;
        });
        let search = String(this.communitySearchQuery || '').trim().toLowerCase();
        if (search) {
            posts = posts.filter((post: any) => this.communityPostSearchText(post).indexOf(search) > -1);
        }

        return [...posts].sort((a: any, b: any) => {
            if (this.selectedCommunitySort === 'latest') {
                return Number(a.createdAt || 0) - Number(b.createdAt || 0);
            }
            let aScore = Number(a.likes || 0) + Number(a.comments || 0) * 3 + Number(a.votes || 0);
            let bScore = Number(b.likes || 0) + Number(b.comments || 0) * 3 + Number(b.votes || 0);
            return bScore - aScore;
        });
    }

    public async handleCommunitySearchInput() {
        this.expandedCommunityPostId = '';
        await this.service.render();
    }

    public async clearCommunitySearch() {
        this.communitySearchQuery = '';
        this.expandedCommunityPostId = '';
        await this.service.render();
    }

    private communityPostSearchText(post: any) {
        return [
            post && post.title,
            post && post.summary,
            post && post.category,
            post && post.author,
            post && post.destination,
            post && post.place,
            ...(post && Array.isArray(post.tags) ? post.tags : [])
        ].map((value: any) => String(value || '').toLowerCase()).join(' ');
    }

    private async loadCommunityPosts(showLoading: boolean = false) {
        try {
            const { code, data } = await this.requestCommunityPosts();
            if (code !== 200) {
                let cached = this.readCommunityPostsCache();
                if (cached.length > 0) this.communityPosts = this.mergeCommunityPosts(cached);
                if (showLoading) await this.service.render();
                return false;
            }
            let posts = data && Array.isArray(data.posts) ? data.posts : [];
            this.communityPosts = this.mergeCommunityPosts(posts);
            this.persistCommunityPostsCache();
            if (showLoading) await this.service.render();
            return true;
        } catch (e) { }
        return false;
    }

    private async requestCommunityPosts() {
        try {
            let response: any = await wiz.call('saved_courses', {
                community_action: 'list',
                actor_key: this.communityActorKey()
            });
            if (response && response.code === 200) return response;
        } catch (e) { }
        return { code: 500, data: { posts: [] } };
    }

    private mergeCommunityPosts(posts: any[] = []) {
        let seen: any = {};
        return [...posts, ...this.communityPosts].filter((post: any) => {
            let id = String(post && post.id ? post.id : '');
            if (!id || seen[id]) return false;
            seen[id] = true;
            return true;
        });
    }

    private applyCommunityPostUpdate(post: any) {
        if (!post || !post.id) return null;
        this.communityPosts = this.mergeCommunityPosts([post]);
        if (this.activeCommunityPost && this.activeCommunityPost.id === post.id) {
            this.activeCommunityPost = post;
        }
        this.persistCommunityPostsCache();
        return post;
    }

    private async saveCommunityPost(post: any) {
        if (!post || !post.id) return { post: null, remote: false };
        let payload = JSON.stringify(post);
        try {
            let response: any = await wiz.call('save_course', {
                community_action: 'post',
                actor_key: this.communityActorKey(),
                post: payload
            });
            if (!response || response.code !== 200) {
                response = await wiz.call('save_community_post', { post: payload });
            }
            if (response && response.code === 200 && response.data && response.data.post) {
                this.applyCommunityPostUpdate(response.data.post);
                return { post: response.data.post, remote: true };
            }
        } catch (e) { }
        this.applyCommunityPostUpdate(post);
        return { post, remote: false };
    }

    private async requestCommunityPostAction(action: string, post: any, data: any = {}) {
        let postId = String(post && post.id ? post.id : '');
        if (!postId) return { code: 400, data: {} };
        try {
            let response: any = await wiz.call('save_course', {
                community_action: action,
                post_id: postId,
                actor_key: this.communityActorKey(),
                ...data
            });
            if (response && response.code === 200) return response;
        } catch (e) { }
        return { code: 500, data: {} };
    }

    private async loadCommunityComments(post: any, showLoading: boolean = true) {
        if (!post || !post.id) {
            this.communityComments = [];
            return;
        }
        this.communityCommentsLoading = true;
        if (showLoading) await this.service.render();
        try {
            let response: any = await wiz.call('saved_courses', {
                community_action: 'comments',
                post_id: post.id
            });
            if (response && response.code === 200 && response.data && Array.isArray(response.data.comments)) {
                this.communityComments = response.data.comments;
            } else {
                this.communityComments = [];
            }
        } catch (e) {
            this.communityComments = [];
        }
        this.communityCommentsLoading = false;
        if (showLoading) await this.service.render();
    }

    private async requestMyCommunityPosts() {
        try {
            let response: any = await wiz.call('saved_courses', {
                community_action: 'mine',
                actor_key: this.communityActorKey()
            });
            if (response && response.code === 200) return response;
        } catch (e) { }
        return { code: 500, data: { posts: [] } };
    }

    public async openCommunityArchive() {
        this.communityArchiveOpen = true;
        await this.loadCommunityArchivePosts(true);
    }

    public async closeCommunityArchive() {
        if (this.communityDeleteSubmittingId) return;
        this.communityArchiveOpen = false;
        await this.service.render();
    }

    public async loadCommunityArchivePosts(showLoading: boolean = true) {
        this.communityArchiveLoading = true;
        if (showLoading) await this.service.render();
        let response = await this.requestMyCommunityPosts();
        let posts = response && response.code === 200 && response.data && Array.isArray(response.data.posts)
            ? response.data.posts
            : [];
        this.communityArchivePosts = posts;
        posts.forEach((post: any) => this.applyCommunityPostUpdate(post));
        this.communityArchiveLoading = false;
        if (showLoading) await this.service.render();
    }

    public isOwnCommunityPost(post: any) {
        if (!post || !post.id) return false;
        if (post.owned) return true;
        return this.communityArchivePosts.some((item: any) => item && item.id === post.id);
    }

    public async openArchivedCommunityPost(post: any) {
        if (!post || !post.id) return;
        this.communityArchiveOpen = false;
        this.activeTab = 'home';
        this.homeContentTab = 'community';
        this.applyCommunityPostUpdate(post);
        await this.openCommunityPost(post);
    }

    public async deleteCommunityPost(event: any, post: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        if (!post || !post.id || this.communityDeleteSubmittingId) return;
        this.communityDetailMenuOpen = false;
        if (typeof window !== 'undefined' && !window.confirm('이 게시글을 삭제할까요? 삭제한 글은 복구할 수 없습니다.')) return;
        this.communityDeleteSubmittingId = post.id;
        await this.service.render();
        let response = await this.requestCommunityPostAction('delete', post);
        if (response && response.code === 200) {
            this.communityPosts = this.communityPosts.filter((item: any) => item && item.id !== post.id);
            this.communityArchivePosts = this.communityArchivePosts.filter((item: any) => item && item.id !== post.id);
            if (this.activeCommunityPost && this.activeCommunityPost.id === post.id) {
                this.activeCommunityPost = null;
                this.communityComments = [];
                this.communityCommentDraft = '';
            }
            this.persistCommunityPostsCache();
            await this.showSaveHint('내가 쓴 글을 삭제했어요.');
        } else {
            let message = response && response.data && response.data.message
                ? response.data.message
                : '내가 쓴 글만 삭제할 수 있어요.';
            await this.showSaveHint(message);
        }
        this.communityDeleteSubmittingId = '';
        await this.service.render();
    }

    public async toggleCommunityDetailMenu(event?: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        this.communityDetailMenuOpen = !this.communityDetailMenuOpen;
        await this.service.render();
    }

    public hasReportedCommunityPost(post: any) {
        return !!post && this.communityReportedPostIds.indexOf(String(post.id || '')) >= 0;
    }

    public async reportCommunityPost(event: any, post: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        if (!post || !post.id || this.isOwnCommunityPost(post) || this.communityReportSubmittingId) return;
        this.communityDetailMenuOpen = false;
        if (this.hasReportedCommunityPost(post)) {
            await this.showSaveHint('이미 신고한 게시글이에요.');
            return;
        }
        if (typeof window !== 'undefined' && !window.confirm('부적절하거나 문제가 있는 게시글로 신고할까요?')) return;

        this.communityReportSubmittingId = post.id;
        await this.service.render();
        let response = await this.requestCommunityPostAction('report', post, { reason: '부적절한 내용' });
        if (response && response.code === 200) {
            if (this.communityReportedPostIds.indexOf(post.id) < 0) this.communityReportedPostIds.push(post.id);
            let already = !!(response.data && response.data.already);
            await this.showSaveHint(already ? '이미 신고한 게시글이에요.' : '신고가 접수되었어요. 운영팀이 확인할게요.');
        } else {
            await this.showSaveHint('신고를 접수하지 못했어요. 잠시 후 다시 시도해주세요.');
        }
        this.communityReportSubmittingId = '';
        await this.service.render();
    }

    private restoreCommunityPostsCache() {
        let cached = this.readCommunityPostsCache();
        if (cached.length > 0) this.communityPosts = this.mergeCommunityPosts(cached);
    }

    private readCommunityPostsCache() {
        if (typeof window === 'undefined' || !window.localStorage) return [];
        try {
            let raw = window.localStorage.getItem(this.communityPostsStorageKey) || '[]';
            let posts = JSON.parse(raw);
            return Array.isArray(posts) ? posts : [];
        } catch (e) { }
        return [];
    }

    private persistCommunityPostsCache(posts: any[] = this.communityPosts) {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            let cached = posts
                .filter((post: any) => this.shouldPersistCommunityPost(post))
                .slice(0, 50);
            window.localStorage.setItem(this.communityPostsStorageKey, JSON.stringify(cached));
        } catch (e) { }
    }

    private shouldPersistCommunityPost(post: any) {
        let id = String(post && post.id ? post.id : '');
        return id.indexOf('community-draft-') === 0 || id.indexOf('community-user-') === 0 || id.indexOf('community-db-') === 0;
    }

    private communityActorKey() {
        if (typeof window === 'undefined' || !window.localStorage) return 'server-render';
        try {
            let current = window.localStorage.getItem(this.communityActorStorageKey);
            if (current) return current;
            let next = `actor-${Date.now()}-${Math.random().toString(16).slice(2)}`;
            window.localStorage.setItem(this.communityActorStorageKey, next);
            return next;
        } catch (e) { }
        return 'volatile-actor';
    }

    private readCommunityActionMap(storageKey: string) {
        if (typeof window === 'undefined' || !window.localStorage) return {};
        try {
            let raw = window.localStorage.getItem(storageKey) || '{}';
            let value = JSON.parse(raw);
            return value && typeof value === 'object' ? value : {};
        } catch (e) { }
        return {};
    }

    private writeCommunityActionMap(storageKey: string, value: any) {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            window.localStorage.setItem(storageKey, JSON.stringify(value || {}));
        } catch (e) { }
    }

    public hasLikedCommunityPost(post: any) {
        let id = String(post && post.id ? post.id : '');
        if (!id) return false;
        return !!this.readCommunityActionMap(this.communityLikeStorageKey)[id];
    }

    private markCommunityPostLiked(post: any) {
        let id = String(post && post.id ? post.id : '');
        if (!id) return;
        let map = this.readCommunityActionMap(this.communityLikeStorageKey);
        map[id] = true;
        this.writeCommunityActionMap(this.communityLikeStorageKey, map);
    }

    public hasVotedCommunityPoll(post: any) {
        let id = String(post && post.id ? post.id : '');
        if (!id) return false;
        return !!this.readCommunityActionMap(this.communityVoteStorageKey)[id];
    }

    public communityPollOptionSelected(post: any, option: string) {
        let id = String(post && post.id ? post.id : '');
        if (!id) return false;
        return this.readCommunityActionMap(this.communityVoteStorageKey)[id] === option;
    }

    private markCommunityPollVoted(post: any, option: string) {
        let id = String(post && post.id ? post.id : '');
        if (!id) return;
        let map = this.readCommunityActionMap(this.communityVoteStorageKey);
        map[id] = option;
        this.writeCommunityActionMap(this.communityVoteStorageKey, map);
    }

    public communityPostLocationLabel(post: any) {
        if (!post) return '';
        return [post.destination, post.place]
            .map((value: any) => String(value || '').trim())
            .filter((value: string) => !!value)
            .join(' · ');
    }

    public communityPostViews(post: any) {
        if (!post) return 0;
        return Math.max(0, Number(post.views || 0));
    }

    public isCommunityPostExpanded(post: any) {
        return !!post && this.expandedCommunityPostId === post.id;
    }

    public communityPostCanExpand(post: any) {
        if (!post) return false;
        return !!post.poll || !!post.photo || String(post.title || '').length > 18 || String(post.summary || '').length > 38;
    }

    public async openCommunityPost(post: any, commentMode: boolean = false) {
        if (!post || !post.id) return;
        this.communityDetailMenuOpen = false;
        this.activeCommunityPost = post;
        this.expandedCommunityPostId = '';
        post.views = Number(post.views || 0) + 1;
        this.applyCommunityPostUpdate(post);
        let response = await this.requestCommunityPostAction('view', post);
        if (response && response.code === 200 && response.data && response.data.post) {
            this.applyCommunityPostUpdate(response.data.post);
        } else if (String(post.id || '').indexOf('community-draft-') === 0) {
            await this.saveCommunityPost(post);
        }
        if (commentMode) this.communityCommentDraft = this.communityCommentDraft || '';
        await this.loadCommunityComments(this.activeCommunityPost, false);
        await this.service.render();
    }

    public async closeCommunityPost() {
        this.communityDetailMenuOpen = false;
        this.activeCommunityPost = null;
        this.communityComments = [];
        this.communityCommentDraft = '';
        await this.service.render();
    }

    public async toggleCommunityPost(post: any) {
        await this.openCommunityPost(post);
    }

    public async handleCommunityPostKeydown(event: any, post: any) {
        let key = event ? String(event.key || event.code || '') : '';
        if (key !== 'Enter' && key !== ' ' && key !== 'Spacebar') return;
        if (event.preventDefault) event.preventDefault();
        await this.openCommunityPost(post);
    }

    public async likeCommunityPost(event: any, post: any) {
        if (event && event.stopPropagation) event.stopPropagation();
        if (!post || !post.id) return;
        if (this.hasLikedCommunityPost(post)) {
            await this.showSaveHint('좋아요는 한 번만 누를 수 있어요.');
            return;
        }
        this.markCommunityPostLiked(post);
        post.likes = Number(post.likes || 0) + 1;
        this.applyCommunityPostUpdate(post);
        await this.service.render();
        let response = await this.requestCommunityPostAction('like', post);
        if (response && response.code === 200 && response.data && response.data.post) {
            this.applyCommunityPostUpdate(response.data.post);
            if (response.data.already) await this.showSaveHint('이미 좋아요를 눌렀어요.');
        } else if (String(post.id || '').indexOf('community-draft-') === 0) {
            await this.saveCommunityPost(post);
        }
        await this.service.render();
    }

    public async submitCommunityComment() {
        let post = this.activeCommunityPost;
        let body = String(this.communityCommentDraft || '').trim();
        if (!post || !post.id) return;
        if (!body) {
            await this.showSaveHint('댓글을 입력해주세요.');
            return;
        }
        let localComment = {
            id: `community-comment-${Date.now()}`,
            postId: post.id,
            author: this.myDisplayName(),
            body,
            createdAt: 0,
            createdLabel: '방금'
        };
        this.communityCommentDraft = '';
        this.communityComments = [...this.communityComments, localComment];
        post.comments = Number(post.comments || 0) + 1;
        this.applyCommunityPostUpdate(post);
        await this.service.render();

        let response = await this.requestCommunityPostAction('comment', post, {
            body,
            author: this.myDisplayName()
        });
        if (response && response.code === 200 && response.data) {
            if (response.data.post) this.applyCommunityPostUpdate(response.data.post);
            if (response.data.comment) {
                this.communityComments = [
                    ...this.communityComments.filter((comment: any) => comment.id !== localComment.id),
                    response.data.comment
                ];
            }
        } else {
            await this.showSaveHint('서버 연결이 불안정해 댓글을 기기에 먼저 표시했어요.');
        }
        await this.service.render();
    }

    public async writeCommunityPost() {
        await this.openCommunityComposer('post');
    }

    public async confirmPlannerCourse() {
        let allStops = this.plannerAllStops();
        if (!this.plannerCourseReady || allStops.length === 0) {
            await this.showSaveHint('먼저 채팅으로 여행 조건을 알려주세요.');
            return;
        }

        let savedCourse = this.plannerCourseToSavedCard(allStops);
        this.courses = [
            savedCourse,
            ...this.courses.filter((course: any) => course && course.id !== savedCourse.id)
        ];
        this.recommendations = [
            savedCourse,
            ...this.recommendations.filter((course: any) => course && course.id !== savedCourse.id)
        ];
        this.savedCourseIds = this.uniqueTags([savedCourse.id, ...this.savedCourseIds]);
        this.plannerCompanionCards = this.plannerCompanionCards.map((card: any) => ({
            ...card,
            courseId: savedCourse.id,
            courseConfirmed: true,
            route: savedCourse.title,
            location: savedCourse.location || this.plannerCourseRegion,
            routeStops: allStops.map((stop: any) => stop && stop.name ? stop.name : '').filter((name: string) => !!name)
        }));

        this.courseDraft = {
            ...this.courseDraft,
            title: savedCourse.title,
            region: this.plannerCourseRegion,
            schedule: this.plannerCourseSchedule,
            places: this.plannerCoursePlacesText(),
            photo: allStops[0] && allStops[0].image ? allStops[0].image : '/assets/places/haeundae-beach.jpg',
            photoName: 'AI 플래너 코스',
            description: `AI 대화를 기반으로 만든 ${this.plannerCourseRegion} 코스입니다.`,
            category: '여행',
            companionEnabled: true,
            companionDate: '일정 협의',
            companionTime: '10:00 출발',
            companionCapacity: 4,
            companionCost: '1인 약 8만원',
            companionBudgetStyle: 'medium',
            companionPace: 'balanced',
            companionMood: '사진, 맛집, 편안한 대화',
            companionFlexible: '카페 순서, 종료 시간',
            companionMeetingPoint: `${this.plannerCourseRegion} 첫 장소`,
            companionSmoking: 'non',
            companionDrinking: 'light',
            companionIntro: `AI가 만든 ${this.plannerCourseRegion} 코스를 함께 걸을 동행을 모집합니다.`
        };

        if (this.isLoggedIn()) {
            try {
                let routePayload = this.plannerCourseRoutePayload(allStops);
                await wiz.call('save_course', {
                    course_id: savedCourse.id,
                    title: savedCourse.title,
                    location: savedCourse.location,
                    summary: savedCourse.summary,
                    duration: savedCourse.duration,
                    rating: savedCourse.rating || '',
                    icon: savedCourse.icon || '',
                    tone: savedCourse.tone || '',
                    places_json: JSON.stringify(routePayload.places),
                    route_json: JSON.stringify(routePayload.route),
                    saved: 'true'
                });
            } catch (e) { }
        }

        await this.service.render();
        await this.showSaveHint('코스를 확정해 저장했어요. 이제 이 코스로 동행을 연결할 수 있어요.');
    }

    public isPlannerCourseConfirmed() {
        return this.plannerCompanionCards.length > 0
            && this.plannerCompanionCards.every((card: any) => !!card.courseId && card.courseConfirmed === true);
    }

    public plannerCompanionStatus(card: any) {
        if (!card || card.courseConfirmed !== true) return '코스 확정 후 모집을 확인할 수 있어요';
        return `모집중 신청 ${card && card.applicants ? card.applicants : 0}/${card && card.capacity ? card.capacity : 1}명`;
    }

    public refreshPlannerPreviewFromPrompt(prompt: string) {
        // 실제 장소 검색 도구 결과가 없으면 임의 코스를 만들지 않습니다.
        this.resetPlannerPreview();
        return;

        let text = String(prompt || '').toLowerCase();

        if (!this.plannerCourseReady) {
            this.plannerCourseBaseTitle = text.indexOf('바다') > -1 ? '내 부산 바다 여행' : '내 부산 여행';
        } else if (text.indexOf('바다') > -1) {
            this.plannerCourseBaseTitle = '내 부산 바다 여행';
        }
        this.plannerCourseRegion = '부산 해운대구';
        if (text.indexOf('2박') > -1) this.plannerCourseSchedule = '2박 3일';
        if (text.indexOf('1박') > -1) this.plannerCourseSchedule = '1박 2일';
        if (text.indexOf('당일') > -1) this.plannerCourseSchedule = '당일';
        if (text.indexOf('야경') > -1 || text.indexOf('저녁') > -1) {
            this.plannerMapLabel = '해운대구-수영구 동선';
        } else if (!this.plannerCourseReady) {
            this.plannerMapLabel = '해운대구 동선';
        }

        let nextStops = this.plannerCourseReady ? this.plannerStops.map((stop: any) => ({ ...stop })) : [];
        let templates = this.busanPlannerStopTemplates();
        let shouldFillDefault = !this.plannerCourseReady && !this.promptHasPlannerKeyword(text);

        if (shouldFillDefault || text.indexOf('바다') > -1 || text.indexOf('해변') > -1 || text.indexOf('부산') > -1) {
            this.ensurePlannerStop(nextStops, templates.beach);
            this.ensurePlannerStop(nextStops, templates.coast);
        }
        if (shouldFillDefault || text.indexOf('맛집') > -1 || text.indexOf('점심') > -1 || text.indexOf('먹') > -1 || text.indexOf('식사') > -1) {
            this.ensurePlannerStop(nextStops, templates.food);
        }
        if (shouldFillDefault || text.indexOf('카페') > -1 || text.indexOf('디저트') > -1 || text.indexOf('감성') > -1) {
            this.ensurePlannerStop(nextStops, templates.cafe);
        }
        if (text.indexOf('야경') > -1 || text.indexOf('저녁') > -1 || text.indexOf('밤') > -1 || text.indexOf('night') > -1) {
            this.ensurePlannerStop(nextStops, templates.night);
        }

        if (nextStops.length === 0) {
            this.ensurePlannerStop(nextStops, templates.beach);
            this.ensurePlannerStop(nextStops, templates.food);
            this.ensurePlannerStop(nextStops, templates.cafe);
        }

        let previousDay = this.plannerCourseDayIndex;
        this.plannerCourseDays = this.buildPlannerCourseDays(this.normalizePlannerStops(nextStops));
        this.applyPlannerCourseDay(Math.min(previousDay, this.plannerCourseDays.length - 1));
        this.plannerCourseReady = true;
        this.refreshPlannerRouteWithGoogle();

        let regionKey = String(this.plannerCourseRegion || 'travel').replace(/\s+/g, '-');
        this.plannerCompanionCards = [
            {
                id: `planner-mate-${regionKey}-primary`,
                courseId: '',
                courseConfirmed: false,
                title: `${this.plannerCourseRegion} 코스 같이 걸을 동행을 찾아요`,
                route: this.plannerCourseTitle,
                routeStops: this.plannerStops.map((stop: any) => stop.name),
                location: this.plannerCourseRegion,
                date: this.plannerCourseSchedule,
                time: '10:00 출발',
                capacity: 4,
                applicants: 3,
                estimatedCost: '1인 약 8만원',
                budgetStyle: 'medium',
                pace: 'balanced',
                moodTags: ['사진', '맛집', '편안한 대화'],
                flexibility: ['카페 순서', '종료 시간'],
                intro: 'AI가 짠 동선을 따라 사진과 맛집을 함께 즐길 동행을 찾아요.',
                host: 'GACHI',
                status: 'open',
                saved: false,
                image: this.plannerStops[0] && this.plannerStops[0].image ? this.plannerStops[0].image : '/assets/places/haeundae-beach.jpg'
            },
            {
                id: `planner-mate-${regionKey}-slow`,
                courseId: '',
                courseConfirmed: false,
                title: '여유롭게 쉬어가는 여행 메이트 구해요',
                route: this.plannerCourseTitle,
                routeStops: this.plannerStops.map((stop: any) => stop.name),
                location: this.plannerCourseRegion,
                date: this.plannerCourseSchedule,
                time: '13:00 출발',
                capacity: 3,
                applicants: 1,
                estimatedCost: '1인 약 6만원',
                budgetStyle: 'medium',
                pace: 'slow',
                moodTags: ['카페', '산책', '조용히'],
                flexibility: ['장소 체류 시간'],
                intro: '카페와 산책 시간을 넉넉하게 잡고 천천히 이동할 분을 찾아요.',
                host: 'GACHI',
                status: 'open',
                saved: false,
                image: this.plannerStops[this.plannerStops.length - 1] && this.plannerStops[this.plannerStops.length - 1].image ? this.plannerStops[this.plannerStops.length - 1].image : '/assets/places/busan-cafe.jpg'
            }
        ];
    }

    private busanPlannerStopTemplates() {
        return {
            beach: {
                key: 'beach',
                time: '10:00',
                name: '해운대 해변',
                area: '해운대구 우동',
                tag: '바다 산책',
                move: '도보 10분',
                image: '/assets/places/haeundae-beach.jpg',
                icon: 'fa-water',
                lat: 35.1587,
                lng: 129.1604,
                mapLeft: '78%',
                mapTop: '24%'
            },
            food: {
                key: 'food',
                time: '12:30',
                name: '해운대 밀면 점심',
                area: '해운대구 중동',
                tag: '점심 식사',
                move: '도보 10분',
                image: '/assets/places/busan-milmyeon.jpg',
                icon: 'fa-utensils',
                lat: 35.1629,
                lng: 129.1638,
                mapLeft: '64%',
                mapTop: '45%'
            },
            coast: {
                key: 'coast',
                time: '15:00',
                name: '동백섬 해안 산책로',
                area: '해운대구 우동',
                tag: '해안 산책',
                move: '도보 15분',
                image: '/assets/places/dongbaekseom.jpg',
                icon: 'fa-person-walking',
                lat: 35.1537,
                lng: 129.1518,
                mapLeft: '53%',
                mapTop: '61%'
            },
            cafe: {
                key: 'cafe',
                time: '17:00',
                name: '부산 감성 카페',
                area: '해운대구 마린시티',
                tag: '카페 · 디저트',
                move: '차량 18분',
                image: '/assets/places/busan-cafe.jpg',
                icon: 'fa-mug-saucer',
                lat: 35.1554,
                lng: 129.1458,
                mapLeft: '34%',
                mapTop: '68%'
            },
            night: {
                key: 'night',
                time: '19:30',
                name: '광안대교 야경',
                area: '수영구 광안동',
                tag: '야경 감상',
                move: '차량 22분',
                image: '/assets/places/gwangan-night.jpg',
                icon: 'fa-moon',
                lat: 35.1531,
                lng: 129.1187,
                mapLeft: '24%',
                mapTop: '34%'
            }
        };
    }

    private promptHasPlannerKeyword(text: string) {
        return ['바다', '해변', '부산', '맛집', '점심', '먹', '식사', '카페', '디저트', '감성', '야경', '저녁', '밤', 'night']
            .some((keyword: string) => text.indexOf(keyword) > -1);
    }

    private plannerContextCanGenerateCourse(text: string) {
        let context = String(text || '').toLowerCase();
        let regionKeywords = this.courseKnownRegions()
            .reduce((keywords: string[], option: any) => {
                let label = String(option && option.label ? option.label : '').trim().toLowerCase();
                let area = String(option && option.area ? option.area : '').trim().toLowerCase();
                if (label) keywords.push(label);
                area.split(/\s+/).filter((item: string) => item.length >= 2).forEach((item: string) => keywords.push(item));
                return keywords;
            }, [])
            .concat([
                '경주', '춘천', '속초', '양양', '통영', '거제', '포항', '울산', '대전', '광주', '세종',
                '충주', '제천', '안동', '군산', '목포', '순천', '남해', '하동', '평창'
            ]);
        let intentKeywords = [
            '여행', '코스', '일정', '추천', '데이트', '가볼', '관광', '맛집', '카페',
            '당일', '반나절', '1박', '2박', '3박', '동선'
        ];
        let hasRegion = regionKeywords.some((keyword: string) => context.indexOf(keyword) > -1);
        let hasIntent = intentKeywords.some((keyword: string) => context.indexOf(keyword) > -1);
        return hasRegion && hasIntent;
    }

    private plannerPromptExplicitlyRequestsCourse(text: string) {
        let prompt = String(text || '').trim().toLowerCase();
        if (!prompt) return false;
        let courseTarget = '(?:코스|일정|동선|여행 계획|여행계획)';
        let createAction = '(?:만들(?:어|어줘|어 줘|어달라|어 달라)?|짜(?:줘| 줘|달라| 달라)?|계획(?:해줘|해 줘|해달라|해 달라)?|구성(?:해줘|해 줘|해달라|해 달라)?)';
        return new RegExp(`${courseTarget}.{0,16}${createAction}`).test(prompt)
            || new RegExp(`${createAction}.{0,16}${courseTarget}`).test(prompt);
    }

    private plannerConversationCanGenerateCourse(prompt: string) {
        let recentPrompts = this.messages
            .filter((message: any) => message && message.role === 'user' && !message.loading)
            .slice(-6)
            .map((message: any) => String(message.text || '').trim());
        let current = String(prompt || '').trim();
        if (current && recentPrompts.indexOf(current) === -1) recentPrompts.push(current);
        return this.plannerPromptExplicitlyRequestsCourse(current)
            && this.plannerContextCanGenerateCourse(recentPrompts.join(' '));
    }

    private ensurePlannerStop(stops: any[], stop: any) {
        if (!stop || stops.some((item: any) => item.key === stop.key)) return;
        stops.push({ ...stop });
    }

    private normalizePlannerStops(stops: any[]) {
        let order = ['beach', 'food', 'coast', 'cafe', 'night'];
        return stops
            .filter((stop: any) => stop && stop.key)
            .sort((a: any, b: any) => order.indexOf(a.key) - order.indexOf(b.key))
            .map((stop: any, index: number) => ({
                ...stop,
                status: index < 2 ? 'active' : 'upcoming'
            }));
    }

    private buildPlannerCourseDays(dayOneStops: any[]) {
        let firstDay = dayOneStops.length > 0 ? dayOneStops : this.normalizePlannerStops([
            this.busanPlannerStopTemplates().beach,
            this.busanPlannerStopTemplates().food,
            this.busanPlannerStopTemplates().coast,
            this.busanPlannerStopTemplates().cafe
        ]);
        let days = [
            { label: '1일차', stops: firstDay }
        ];

        if (this.plannerCourseSchedule.indexOf('1박') > -1 || this.plannerCourseSchedule.indexOf('2박') > -1) {
            days.push({
                label: '2일차',
                stops: this.normalizePlannerStops(this.busanPlannerDayTwoStops())
            });
        }

        return days;
    }

    private busanPlannerDayTwoStops() {
        return [
            {
                key: 'day2-breakfast',
                time: '09:30',
                name: '숙소 근처 브런치',
                area: '해운대구 중동',
                tag: '아침 식사',
                move: '도보 12분',
                image: '/assets/places/busan-milmyeon.jpg',
                icon: 'fa-utensils',
                lat: 35.1634,
                lng: 129.164,
                mapLeft: '72%',
                mapTop: '28%'
            },
            {
                key: 'day2-blue-line',
                time: '11:30',
                name: '해운대 블루라인파크',
                area: '해운대구 송정동',
                tag: '해안 열차',
                move: '차량 18분',
                image: '/assets/places/dongbaekseom.jpg',
                icon: 'fa-train',
                lat: 35.1612,
                lng: 129.1716,
                mapLeft: '66%',
                mapTop: '48%'
            },
            {
                key: 'day2-cheongsapo',
                time: '14:30',
                name: '청사포 조개구이',
                area: '해운대구 청사포',
                tag: '점심 식사',
                move: '도보 8분',
                image: '/assets/places/haeundae-beach.jpg',
                icon: 'fa-fish',
                lat: 35.16,
                lng: 129.1917,
                mapLeft: '58%',
                mapTop: '66%'
            },
            {
                key: 'day2-haeridan',
                time: '17:00',
                name: '해리단길 카페',
                area: '해운대구 우동',
                tag: '카페 · 쇼핑',
                move: '차량 14분',
                image: '/assets/places/busan-cafe.jpg',
                icon: 'fa-mug-saucer',
                lat: 35.1636,
                lng: 129.1587,
                mapLeft: '36%',
                mapTop: '72%'
            }
        ];
    }

    private applyPlannerCourseDay(index: number) {
        if (!Array.isArray(this.plannerCourseDays) || this.plannerCourseDays.length === 0) {
            this.plannerStops = [];
            this.refreshPlannerStats();
            return;
        }

        this.plannerCourseDayIndex = Math.max(0, Math.min(index, this.plannerCourseDays.length - 1));
        let day = this.plannerCourseDays[this.plannerCourseDayIndex];
        this.plannerStops = ((day && day.stops) || []).map((stop: any) => ({ ...stop }));
        this.plannerGoogleRoutePath = this.plannerStops
            .filter((stop: any) => this.isFiniteNumber(stop.lat) && this.isFiniteNumber(stop.lng))
            .map((stop: any) => ({ lat: Number(stop.lat), lng: Number(stop.lng) }));
        this.plannerCourseTitle = `${this.plannerCourseBaseTitle} ${this.plannerCourseDayIndex + 1}일차 코스`;
        this.refreshPlannerStats();
        if (day && Number(day.totalMoveMinutes || 0) > 0) {
            let visitMinutes = this.plannerStops.reduce((sum: number, stop: any) => sum + Number(stop.durationMinutes || 0), 0);
            this.plannerTotalTime = this.formatPlannerMinutes(Number(day.totalMoveMinutes || 0) + visitMinutes);
        }
        if (day && Number(day.totalDistanceMeters || 0) > 0) {
            this.plannerDistance = this.formatPlannerDistance(Number(day.totalDistanceMeters), false);
        }
        if (day && day.endTime) this.plannerReturnTime = String(day.endTime);
    }

    public plannerActiveDay() {
        return this.plannerCourseDays[this.plannerCourseDayIndex] || {};
    }

    public plannerQualityScore() {
        return Math.max(0, Math.min(100, Number(this.plannerQuality.score || this.plannerActiveDay().qualityScore || 0)));
    }

    public plannerRouteLegs() {
        return Array.isArray(this.plannerRouteSummary && this.plannerRouteSummary.legs)
            ? this.plannerRouteSummary.legs
            : [];
    }

    public plannerStars(value: any) {
        let rating = Math.max(0, Math.min(5, Number(value || 0)));
        return '★★★★★'.slice(0, Math.round(rating)) + '☆☆☆☆☆'.slice(0, 5 - Math.round(rating));
    }

    public plannerReviewLabel(value: any) {
        let count = Math.max(0, Number(value || 0));
        return count > 0 ? `리뷰 ${count.toLocaleString()}개` : '리뷰 정보 없음';
    }

    public plannerCostLabel(value: any) {
        let cost = Math.max(0, Number(value || 0));
        return cost > 0 ? `예상 ${Math.round(cost).toLocaleString()}원` : '무료 또는 현장 확인';
    }

    public hasPlannerMultipleDays() {
        return Array.isArray(this.plannerCourseDays) && this.plannerCourseDays.length > 1;
    }

    public plannerActiveDayLabel() {
        return `${this.plannerCourseDayIndex + 1}일차`;
    }

    public plannerNextDayButtonLabel() {
        if (!this.hasPlannerMultipleDays()) return '';
        let next = (this.plannerCourseDayIndex + 1) % this.plannerCourseDays.length;
        return `${next + 1}일차 코스 보기`;
    }

    public async showNextPlannerDay() {
        if (!this.hasPlannerMultipleDays()) return;
        this.applyPlannerCourseDay((this.plannerCourseDayIndex + 1) % this.plannerCourseDays.length);
        this.refreshPlannerRouteWithGoogle();
        await this.service.render();
    }

    public handlePlannerTouchStart(event: any) {
        let touch = event && event.touches && event.touches[0] ? event.touches[0] : null;
        this.plannerTouchStartX = touch ? Number(touch.clientX || 0) : 0;
    }

    public async handlePlannerTouchEnd(event: any) {
        if (!this.hasPlannerMultipleDays() || !this.plannerTouchStartX) return;
        let touch = event && event.changedTouches && event.changedTouches[0] ? event.changedTouches[0] : null;
        let endX = touch ? Number(touch.clientX || 0) : this.plannerTouchStartX;
        let delta = endX - this.plannerTouchStartX;
        this.plannerTouchStartX = 0;
        if (Math.abs(delta) < 42) return;
        if (delta < 0) {
            await this.showNextPlannerDay();
            return;
        }
        this.applyPlannerCourseDay((this.plannerCourseDayIndex - 1 + this.plannerCourseDays.length) % this.plannerCourseDays.length);
        this.refreshPlannerRouteWithGoogle();
        await this.service.render();
    }

    private refreshPlannerRouteWithGoogle() {
        if (!this.plannerCourseReady || !Array.isArray(this.plannerStops) || this.plannerStops.length < 2) {
            this.schedulePlannerGoogleMapRender();
            return;
        }

        let routeStops = this.plannerStops
            .map((stop: any, index: number) => ({
                stop,
                index,
                position: { lat: Number(stop.lat), lng: Number(stop.lng) }
            }))
            .filter((item: any) => this.isFiniteNumber(item.stop.lat) && this.isFiniteNumber(item.stop.lng));
        this.plannerGoogleRoutePath = routeStops.map((item: any) => item.position);
        this.schedulePlannerGoogleMapRender();
        if (routeStops.length < 2) return;

        let token = ++this.plannerGoogleRouteToken;
        this.plannerRouteSource = 'Google Maps 교통편 확인 중';
        this.loadGoogleMapsScript().then(async (google: any) => {
            if (token !== this.plannerGoogleRouteToken) return;
            let service = this.isGoogleMapsReady(google) ? new google.maps.DirectionsService() : null;
            let resolvedLegs: any[] = [];

            for (let index = 0; index < routeStops.length - 1; index++) {
                if (token !== this.plannerGoogleRouteToken) return;
                let from = routeStops[index];
                let to = routeStops[index + 1];
                let preferredMode = this.plannerRouteTravelModeForLeg(from.stop, to.stop);
                let googleLeg = service
                    ? await this.requestPlannerGoogleLeg(service, google, from.position, to.position, preferredMode)
                    : null;
                resolvedLegs.push(googleLeg
                    ? {
                        ...googleLeg,
                        fromIndex: from.index,
                        toIndex: to.index,
                        from: from.stop,
                        to: to.stop,
                        source: 'google_maps'
                    }
                    : {
                        ...this.estimatedPlannerLeg(from.stop, to.stop, preferredMode),
                        fromIndex: from.index,
                        toIndex: to.index,
                        from: from.stop,
                        to: to.stop,
                        source: 'distance_estimate'
                    });
            }

            if (token !== this.plannerGoogleRouteToken) return;
            this.applyPlannerResolvedLegs(routeStops, resolvedLegs);
            await this.service.render();
            this.schedulePlannerGoogleMapRender();
        }).catch(async () => {
            if (token !== this.plannerGoogleRouteToken) return;
            let estimatedLegs = routeStops.slice(0, -1).map((from: any, index: number) => {
                let to = routeStops[index + 1];
                let mode = this.plannerRouteTravelModeForLeg(from.stop, to.stop);
                return {
                    ...this.estimatedPlannerLeg(from.stop, to.stop, mode),
                    fromIndex: from.index,
                    toIndex: to.index,
                    from: from.stop,
                    to: to.stop,
                    source: 'distance_estimate'
                };
            });
            this.applyPlannerResolvedLegs(routeStops, estimatedLegs);
            await this.service.render();
            this.schedulePlannerGoogleMapRender();
        });
    }

    private async requestPlannerGoogleLeg(service: any, google: any, origin: any, destination: any, mode: string): Promise<any> {
        let request = (routeMode: string) => new Promise((resolve) => {
            service.route({
                origin,
                destination,
                travelMode: google.maps.TravelMode[routeMode],
                provideRouteAlternatives: false
            }, (result: any, status: string) => {
                let route = result && result.routes && result.routes[0] ? result.routes[0] : null;
                let leg = route && route.legs && route.legs[0] ? route.legs[0] : null;
                if (status !== 'OK' || !route || !leg) {
                    resolve(null);
                    return;
                }
                resolve({
                    mode: routeMode,
                    seconds: Number(leg.duration && leg.duration.value ? leg.duration.value : 0),
                    meters: Number(leg.distance && leg.distance.value ? leg.distance.value : 0),
                    durationText: leg.duration && leg.duration.text ? leg.duration.text : '',
                    distanceText: leg.distance && leg.distance.text ? leg.distance.text : '',
                    path: this.plannerPathFromGoogleRoute(route)
                });
            });
        });

        let result: any = await request(mode);
        if (!result && mode !== 'DRIVING') result = await request('DRIVING');
        return result;
    }

    private plannerPathFromGoogleRoute(route: any) {
        return ((route && route.overview_path) || []).map((point: any) => ({
            lat: typeof point.lat === 'function' ? point.lat() : Number(point.lat),
            lng: typeof point.lng === 'function' ? point.lng() : Number(point.lng)
        })).filter((point: any) => this.isFiniteNumber(point.lat) && this.isFiniteNumber(point.lng));
    }

    private estimatedPlannerLeg(from: any, to: any, mode: string) {
        let distance = this.distanceKm(from && from.lat, from && from.lng, to && to.lat, to && to.lng);
        let kilometers = distance === null ? 1 : Math.max(0.1, distance);
        let speed = mode === 'WALKING' ? 4.2 : (mode === 'TRANSIT' ? 18 : 24);
        let overhead = mode === 'WALKING' ? 0 : (mode === 'TRANSIT' ? 8 : 4);
        let minutes = Math.max(2, Math.round((kilometers / speed) * 60 + overhead));
        return {
            mode,
            seconds: minutes * 60,
            meters: Math.round(kilometers * 1000),
            durationText: `${minutes}분`,
            distanceText: this.formatPlannerDistance(kilometers * 1000, false),
            path: [
                { lat: Number(from.lat), lng: Number(from.lng) },
                { lat: Number(to.lat), lng: Number(to.lng) }
            ]
        };
    }

    private applyPlannerResolvedLegs(routeStops: any[], legs: any[]) {
        let totalSeconds = 0;
        let totalMeters = 0;
        let routePath: any[] = [];
        let googleLegCount = 0;

        legs.forEach((leg: any) => {
            let seconds = Math.max(0, Number(leg && leg.seconds ? leg.seconds : 0));
            let meters = Math.max(0, Number(leg && leg.meters ? leg.meters : 0));
            let stop = this.plannerStops[leg.fromIndex];
            totalSeconds += seconds;
            totalMeters += meters;
            if (leg.source === 'google_maps') googleLegCount++;
            if (stop) {
                stop.move = `${this.plannerRouteModeLabel(leg.mode)} ${this.formatPlannerLegDuration(seconds)}`;
                stop.googleDistance = this.formatPlannerDistance(meters, false);
            }
            (leg.path || []).forEach((point: any) => {
                let previous = routePath[routePath.length - 1];
                if (!previous || previous.lat !== point.lat || previous.lng !== point.lng) routePath.push(point);
            });
        });

        let itinerarySeconds = this.applyPlannerArrivalTimes(routeStops, legs);
        if (totalMeters > 0) this.plannerDistance = this.formatPlannerDistance(totalMeters);
        if (itinerarySeconds > 0) this.plannerTotalTime = this.formatPlannerDuration(itinerarySeconds);
        this.plannerGoogleRoutePath = routePath.length > 1
            ? routePath
            : routeStops.map((item: any) => item.position);
        this.plannerRouteSource = googleLegCount === legs.length
            ? 'Google Maps 교통편 기준'
            : (googleLegCount > 0 ? 'Google Maps · 일부 거리 추정' : '거리·교통편 예상');
        this.plannerMapLabel = '실제 장소 동선';
        this.plannerRouteSummary = {
            source: googleLegCount === legs.length ? 'google_maps' : 'mixed_route',
            travel_mode: 'mixed',
            total_seconds: totalSeconds,
            itinerary_seconds: itinerarySeconds,
            total_meters: totalMeters,
            legs: legs.map((leg: any, index: number) => ({
                order: index + 1,
                from: leg.from && leg.from.name ? leg.from.name : '',
                to: leg.to && leg.to.name ? leg.to.name : '',
                mode: String(leg.mode || '').toLowerCase(),
                source: leg.source,
                duration_text: leg.durationText,
                duration_seconds: leg.seconds,
                distance_text: leg.distanceText,
                distance_meters: leg.meters
            }))
        };
        this.syncPlannerActiveDayStops();
    }

    private applyPlannerArrivalTimes(routeStops: any[], legs: any[]) {
        if (!routeStops.length) return 0;
        let startMinutes = this.plannerMinutesFromTime(routeStops[0].stop.time, 10 * 60);
        let currentMinutes = startMinutes;

        routeStops.forEach((item: any, index: number) => {
            if (index > 0 && item.stop.timeLocked) {
                let lockedMinutes = this.plannerMinutesFromTime(item.stop.time, currentMinutes);
                if (lockedMinutes >= currentMinutes) currentMinutes = lockedMinutes;
            }
            item.stop.time = this.timeFromMinutes(currentMinutes);
            if (index >= routeStops.length - 1) return;
            let leg = legs[index] || {};
            let travelMinutes = Math.max(1, Math.round(Number(leg.seconds || 0) / 60));
            currentMinutes = this.roundPlannerMinutes(currentMinutes + this.plannerStopDurationMinutes(item.stop) + travelMinutes);
        });

        let endMinutes = currentMinutes + this.plannerStopDurationMinutes(routeStops[routeStops.length - 1].stop);
        this.plannerReturnTime = this.timeFromMinutes(endMinutes);
        return Math.max(60, (endMinutes - startMinutes) * 60);
    }

    private plannerMinutesFromTime(value: any, fallback: number) {
        let match = String(value || '').match(/^(\d{1,2}):(\d{2})$/);
        if (!match) return fallback;
        return Math.max(0, Math.min(1439, Number(match[1]) * 60 + Number(match[2])));
    }

    private roundPlannerMinutes(value: number) {
        return Math.round(value / 5) * 5;
    }

    private plannerStopDurationMinutes(stop: any) {
        let text = `${stop && stop.name ? stop.name : ''} ${stop && stop.tag ? stop.tag : ''}`;
        if (/숙소|체크인/.test(text)) return 30;
        if (/아침|점심|저녁|식사|맛집|브런치/.test(text)) return 70;
        if (/카페|디저트/.test(text)) return 60;
        if (/열차|레포츠|액티비티/.test(text)) return 90;
        if (/쇼핑/.test(text)) return 75;
        if (/산책|해변|바다|공원|문화|전시|관광/.test(text)) return 90;
        return 75;
    }

    private plannerRouteTravelModeForLeg(from: any, to: any) {
        let move = String(from && from.move ? from.move : '');
        if (/지하철|버스|대중교통|열차/.test(move)) return 'TRANSIT';
        if (/차량|자동차|택시|렌터카/.test(move)) return 'DRIVING';
        if (/도보|걷기/.test(move)) return 'WALKING';
        let distance = this.distanceKm(from && from.lat, from && from.lng, to && to.lat, to && to.lng);
        return distance !== null && distance <= 1.4 ? 'WALKING' : 'TRANSIT';
    }

    private plannerRouteModeLabel(mode: string) {
        if (mode === 'DRIVING') return '차량';
        if (mode === 'TRANSIT') return '대중교통';
        return '도보';
    }

    private syncPlannerActiveDayStops() {
        if (!this.plannerCourseDays[this.plannerCourseDayIndex]) return;
        this.plannerCourseDays[this.plannerCourseDayIndex].stops = this.plannerStops.map((stop: any) => ({ ...stop }));
    }

    public async openPlannerMap() {
        this.plannerMapExpanded = true;
        await this.service.render();
        this.schedulePlannerGoogleMapRender();
    }

    public async closePlannerMap() {
        if (!this.plannerMapExpanded) return;
        this.plannerMapExpanded = false;
        await this.service.render();
    }

    public fitPlannerMap() {
        let google: any = (window as any).google;
        let map = this.plannerExpandedGoogleMap;
        if (!map || !google || !google.maps || typeof google.maps.LatLngBounds !== 'function') return;
        let path = this.plannerGoogleRoutePath.length > 1
            ? this.plannerGoogleRoutePath
            : this.plannerStops.filter((stop: any) => this.isFiniteNumber(stop.lat) && this.isFiniteNumber(stop.lng));
        if (!path.length) return;
        let bounds = new google.maps.LatLngBounds();
        path.forEach((point: any) => bounds.extend({ lat: Number(point.lat), lng: Number(point.lng) }));
        map.fitBounds(bounds, 42);
    }

    private schedulePlannerGoogleMapRender() {
        if (typeof window === 'undefined') return;
        let root: any = window as any;
        let frame = root.requestAnimationFrame || ((callback: any) => setTimeout(callback, 16));
        frame(() => this.renderPlannerGoogleMaps());
    }

    private async renderPlannerGoogleMaps() {
        if (!this.plannerCourseReady || typeof document === 'undefined') return;
        let google = await this.loadGoogleMapsScript();
        if (!this.isGoogleMapsReady(google)) return;
        this.renderPlannerGoogleMapTarget(google, '.planner-google-map', false);
        if (this.plannerMapExpanded) this.renderPlannerGoogleMapTarget(google, '.planner-google-map-expanded', true);
    }

    private renderPlannerGoogleMapTarget(google: any, selector: string, expanded: boolean) {
        let element: any = document.querySelector(`.access-shell ${selector}`);
        if (!element || !element.offsetWidth || !element.offsetHeight) return;
        let mapStops = (this.plannerStops || [])
            .map((stop: any, index: number) => ({ stop, index }))
            .filter((item: any) => this.isFiniteNumber(item.stop.lat) && this.isFiniteNumber(item.stop.lng));
        let points = mapStops.map((item: any) => ({ lat: Number(item.stop.lat), lng: Number(item.stop.lng) }));
        if (!points.length) return;

        let map = expanded ? this.plannerExpandedGoogleMap : this.plannerGoogleMap;
        let mapElement = expanded ? this.plannerExpandedGoogleMapElement : this.plannerGoogleMapElement;
        if (!map || mapElement !== element) {
            map = new google.maps.Map(element, {
                center: points[0],
                zoom: points.length > 1 ? 13 : 15,
                clickableIcons: false,
                disableDefaultUI: true,
                gestureHandling: expanded ? 'greedy' : 'none',
                keyboardShortcuts: expanded,
                zoomControl: expanded,
                streetViewControl: false,
                mapTypeControl: false,
                fullscreenControl: false
            });
            if (expanded) {
                this.plannerExpandedGoogleMap = map;
                this.plannerExpandedGoogleMapElement = element;
            } else {
                this.plannerGoogleMap = map;
                this.plannerGoogleMapElement = element;
            }
        }

        let markers = expanded ? this.plannerExpandedGoogleMarkers : this.plannerGoogleMarkers;
        markers.forEach((marker: any) => marker.setMap(null));
        markers = points.map((position: any, index: number) => {
            let stop = mapStops[index].stop || {};
            let marker = new google.maps.Marker({
                map,
                position,
                title: stop.name || `${mapStops[index].index + 1}번 장소`,
                label: {
                    text: String(mapStops[index].index + 1),
                    color: '#ffffff',
                    fontSize: expanded ? '11px' : '8px',
                    fontWeight: '800'
                },
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: expanded ? 12 : 9,
                    fillColor: '#F20D19',
                    fillOpacity: 1,
                    strokeColor: '#ffffff',
                    strokeWeight: expanded ? 3 : 2
                }
            });
            if (expanded && typeof google.maps.InfoWindow === 'function' && marker.addListener) {
                let next = this.plannerRouteLegs()[index] || {};
                let tooltip = new google.maps.InfoWindow({
                    content: `<div class="planner-map-tooltip"><strong>${this.escapeMapText(stop.name || '')}</strong><small>${this.escapeMapText(stop.timePeriod || stop.time || '')}${next.duration_text ? ` · ${this.escapeMapText(next.duration_text)}` : ''}</small></div>`
                });
                marker.addListener('click', () => tooltip.open({ map, anchor: marker }));
            }
            return marker;
        });
        if (expanded) this.plannerExpandedGoogleMarkers = markers;
        else this.plannerGoogleMarkers = markers;

        let previousLine = expanded ? this.plannerExpandedGoogleRouteLine : this.plannerGoogleRouteLine;
        if (previousLine) previousLine.setMap(null);
        let path = this.plannerGoogleRoutePath.length > 1 ? this.plannerGoogleRoutePath : points;
        let routeLine = new google.maps.Polyline({
            map,
            path,
            strokeColor: '#F20D19',
            strokeOpacity: 0.9,
            strokeWeight: expanded ? 5 : 3,
            geodesic: false
        });
        if (expanded) this.plannerExpandedGoogleRouteLine = routeLine;
        else this.plannerGoogleRouteLine = routeLine;

        let bounds = new google.maps.LatLngBounds();
        path.forEach((point: any) => bounds.extend(point));
        points.forEach((point: any) => bounds.extend(point));
        if (points.length > 1) map.fitBounds(bounds, expanded ? 42 : 10);
        else {
            map.setCenter(points[0]);
            map.setZoom(15);
        }
    }

    private formatPlannerDuration(seconds: any) {
        let minutes = Math.max(1, Math.round(Number(seconds || 0) / 60));
        let hours = Math.floor(minutes / 60);
        let remain = minutes % 60;
        if (hours > 0 && remain > 0) return `약 ${hours}시간 ${remain}분`;
        if (hours > 0) return `약 ${hours}시간`;
        return `약 ${minutes}분`;
    }

    private escapeMapText(value: any) {
        return String(value || '').replace(/[&<>"']/g, (char: string) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        } as any)[char] || char);
    }

    private formatPlannerLegDuration(seconds: any) {
        let minutes = Math.max(1, Math.round(Number(seconds || 0) / 60));
        let hours = Math.floor(minutes / 60);
        let remain = minutes % 60;
        if (hours > 0 && remain > 0) return `${hours}시간 ${remain}분`;
        if (hours > 0) return `${hours}시간`;
        return `${minutes}분`;
    }

    private formatPlannerDistance(meters: any, approximate: boolean = true) {
        let value = Math.max(0, Number(meters || 0));
        let prefix = approximate ? '약 ' : '';
        if (value < 1000) return `${prefix}${Math.round(value)}m`;
        return `${prefix}${(value / 1000).toFixed(1)}km`;
    }

    private plannerAllStops() {
        if (!Array.isArray(this.plannerCourseDays) || this.plannerCourseDays.length === 0) return this.plannerStops || [];
        return this.plannerCourseDays.reduce((items: any[], day: any) => {
            return items.concat(((day && day.stops) || []).map((stop: any) => ({ ...stop, dayLabel: day.label || '' })));
        }, []);
    }

    private plannerCoursePlacesText() {
        if (!Array.isArray(this.plannerCourseDays) || this.plannerCourseDays.length === 0) {
            return (this.plannerStops || []).map((stop: any) => stop.name).join('\n');
        }
        return this.plannerCourseDays.map((day: any) => {
            let stops = ((day && day.stops) || []).map((stop: any) => `${stop.time || ''} ${stop.name}`).join('\n');
            return `${day.label || '일정'}\n${stops}`;
        }).join('\n\n');
    }

    private plannerCourseSaveTitle() {
        if (this.hasPlannerMultipleDays()) return `${this.plannerCourseBaseTitle} ${this.plannerCourseSchedule} 코스`;
        return this.plannerCourseTitle;
    }

    private plannerCourseToSavedCard(stops: any[]) {
        let title = this.plannerCourseSaveTitle();
        let routePayload = this.plannerCourseRoutePayload(stops);
        return {
            id: `planner-course-${Date.now()}`,
            title,
            location: this.plannerCourseRegion,
            summary: `${this.plannerCoursePlacesText().replace(/\n/g, ' · ').slice(0, 90)}${this.plannerCoursePlacesText().length > 90 ? '...' : ''}`,
            duration: this.plannerCourseSchedule,
            distance: this.plannerDistance,
            rating: '4.9',
            price: '',
            tone: 'tone-blue',
            icon: 'fa-route',
            image: stops[0] && stops[0].image ? stops[0].image : '/assets/places/haeundae-beach.jpg',
            saved: true,
            mine: true,
            places: routePayload.places,
            route: routePayload.route,
            tags: this.uniqueTags(['여행', this.plannerCourseRegion, this.plannerCourseSchedule, 'AI플래너', ...stops.map((stop: any) => stop.name)])
        };
    }

    private plannerCourseRoutePayload(stops: any[]) {
        let days = Array.isArray(this.plannerCourseDays) && this.plannerCourseDays.length > 0
            ? this.plannerCourseDays
            : [{ label: '1일차', stops: stops || [] }];
        let places: any[] = [];
        days.forEach((day: any, dayIndex: number) => {
            ((day && day.stops) || []).forEach((stop: any, index: number) => {
                places.push({
                    day: dayIndex + 1,
                    day_label: day && day.label ? day.label : `${dayIndex + 1}일차`,
                    order: index + 1,
                    time: stop.time || '',
                    name: stop.name || '',
                    area: stop.area || '',
                    tag: stop.tag || '',
                    move: stop.move || '',
                    distance: stop.googleDistance || '',
                    image: stop.image || '',
                    lat: this.isFiniteNumber(stop.lat) ? Number(stop.lat) : null,
                    lng: this.isFiniteNumber(stop.lng) ? Number(stop.lng) : null
                });
            });
        });
        return {
            places,
            route: {
                title: this.plannerCourseSaveTitle(),
                region: this.plannerCourseRegion,
                schedule: this.plannerCourseSchedule,
                active_day: this.plannerCourseDayIndex + 1,
                total_time: this.plannerTotalTime,
                total_distance: this.plannerDistance,
                route_source: this.plannerRouteSource,
                map_label: this.plannerMapLabel,
                google: this.plannerRouteSummary || {},
                days: days.map((day: any, index: number) => ({
                    day: index + 1,
                    label: day && day.label ? day.label : `${index + 1}일차`,
                    stop_count: ((day && day.stops) || []).length
                }))
            }
        };
    }

    private refreshPlannerStats() {
        let hasNight = this.plannerStops.some((stop: any) => stop.key === 'night');
        let hasCafe = this.plannerStops.some((stop: any) => stop.key === 'cafe');
        let count = this.plannerStops.length;

        this.plannerTotalTime = hasNight ? '약 9시간 30분' : (hasCafe ? '약 7시간 20분' : '약 5시간 40분');
        this.plannerDistance = hasNight ? '약 18.4km' : (count >= 4 ? '약 12.6km' : '약 8.2km');
        this.plannerReturnTime = hasNight ? '21:00' : (hasCafe ? '20:20' : '18:30');
        this.plannerMapRoutePoints = this.plannerStops
            .map((stop: any) => `${String(stop.mapLeft || '50%').replace('%', '')},${String(stop.mapTop || '50%').replace('%', '')}`)
            .join(' ');
        this.schedulePlannerGoogleMapRender();
    }

    private resetPlannerPreview() {
        this.plannerCourseReady = false;
        this.isPlannerGenerating = false;
        this.plannerCourseBaseTitle = '내 부산 여행';
        this.plannerCourseDayIndex = 0;
        this.plannerCourseDays = [];
        this.plannerQuality = {};
        this.plannerTravelerStyle = '취향 중심';
        this.plannerGoogleRouteToken++;
        this.plannerMapExpanded = false;
        this.plannerGoogleRoutePath = [];
        this.plannerRouteSource = '기본 동선';
        this.plannerRouteSummary = {};
        this.plannerCourseTitle = '내 부산 여행 1일차 코스';
        this.plannerCourseRegion = '부산 해운대구';
        this.plannerCourseSchedule = '2박 3일';
        this.plannerMapLabel = '해운대구 동선';
        this.plannerTotalTime = '약 7시간';
        this.plannerDistance = '약 12.6km';
        this.plannerReturnTime = '20:20';
        this.plannerMapRoutePoints = '';
        this.plannerStops = [];
    }

    private resetPlannerConversationState() {
        this.stopPlannerProgress();
        this.plannerTravelState = {};
        this.plannerStage = 'collecting';
        this.plannerAction = 'ask_clarification';
        this.plannerMissingSlots = [];
        this.plannerWarnings = [];
        this.plannerFailureStage = '';
        this.plannerGenerationStep = 0;
    }

    public plannerTravelSummaryItems() {
        let state = this.plannerTravelState || {};
        let values: string[] = [];
        if (state.region) values.push(String(state.region));
        if (state.days) values.push(Number(state.days) === 1 ? '당일' : `${Number(state.days) - 1}박 ${state.days}일`);
        if (Array.isArray(state.companions) && state.companions.length) values.push(state.companions.join('·'));
        if (state.transport) values.push(String(state.transport));
        if (state.budget) values.push(`예산 ${state.budget}`);
        if (Array.isArray(state.preferences) && state.preferences.length) values.push(state.preferences.join('·'));
        return values;
    }

    public hasPlannerTravelSummary() {
        return this.plannerTravelSummaryItems().length > 0;
    }

    public plannerStageLabel() {
        let labels: any = {
            collecting: '조건 수집 중',
            ready_to_generate: '조건 준비 완료',
            generating: '코스 생성 중',
            draft_ready: '코스 초안 완료',
            revising: '코스 수정 중',
            completed: '코스 확정',
            error: '확인 필요'
        };
        return labels[this.plannerStage] || '조건 수집 중';
    }

    public plannerFailureLabel() {
        let labels: any = {
            travel_conditions: '여행 조건이 아직 부족해요.',
            place_search: '조건에 맞는 장소 검색 결과가 부족해요.',
            directions: '이동 경로를 계산하지 못했어요.',
            response_format: 'AI 응답 형식을 복구하지 못했어요.',
            model_config: 'AI 모델 또는 API 설정을 확인해주세요.',
            revision_target: '수정할 날짜나 장소를 더 구체적으로 알려주세요.'
        };
        return labels[this.plannerFailureStage] || '';
    }

    public async generatePlannerFromSummary() {
        if (this.isChatSending) return;
        await this.sendChatPrompt('이 조건으로 코스 만들어줘');
    }

    private applyPlannerContract(payload: any) {
        payload = payload || {};
        if (payload.travel_state && typeof payload.travel_state === 'object') this.plannerTravelState = payload.travel_state;
        this.plannerStage = String(payload.stage || this.plannerTravelState.conversation_stage || 'collecting');
        this.plannerAction = String(payload.action || 'answer_only');
        this.plannerMissingSlots = Array.isArray(payload.missing_slots) ? payload.missing_slots : [];
        this.plannerWarnings = Array.isArray(payload.warnings) ? payload.warnings : [];
        this.plannerFailureStage = String(payload.failure_stage || '');
        if (Array.isArray(payload.progress_steps) && payload.progress_steps.length) this.plannerProgressSteps = payload.progress_steps;
        if (payload.itinerary_draft && Array.isArray(payload.itinerary_draft.days) && payload.itinerary_draft.days.length) {
            this.applyPlannerDraft(payload.itinerary_draft);
        }
    }

    private applyPlannerDraft(draft: any) {
        let days = Array.isArray(draft.days) ? draft.days : [];
        this.plannerQuality = draft.quality && typeof draft.quality === 'object' ? draft.quality : {};
        this.plannerTravelerStyle = String(draft.traveler_style || '취향 중심');
        this.plannerCourseRegion = String(draft.region || this.plannerTravelState.region || '여행');
        this.plannerCourseSchedule = days.length <= 1 ? '당일' : `${days.length - 1}박 ${days.length}일`;
        this.plannerCourseBaseTitle = String(draft.title || `${this.plannerCourseRegion} 여행`).replace(/\s*코스\s*$/, '');
        this.plannerMapLabel = `${this.plannerCourseRegion} 동선`;
        this.plannerCourseDays = days.map((day: any, dayIndex: number) => {
            let places = Array.isArray(day.places) ? day.places : [];
            let stops = places.map((place: any, index: number) => ({
                key: String(place.place_id || `day-${dayIndex}-${index}`),
                placeId: String(place.place_id || ''),
                time: String(place.time || ''),
                name: String(place.name || ''),
                area: String(place.address || this.plannerCourseRegion),
                tag: String(place.activity || place.category || '여행지'),
                category: String(place.category || ''),
                move: '일정 종료',
                image: String(place.thumbnail || '') || this.defaultPlannerImage(String(place.category || ''), index),
                icon: this.plannerIconForCategory(String(place.category || '')),
                lat: this.toPlannerNumber(place.lat),
                lng: this.toPlannerNumber(place.lng),
                durationMinutes: Number(place.duration_minutes || 0),
                durationLabel: String(place.duration_label || ''),
                timePeriod: String(place.time_period || ''),
                timePeriodIcon: String(place.time_period_icon || 'fa-location-dot'),
                rating: Number(place.rating || 0),
                reviewCount: Number(place.review_count || 0),
                openingStatus: String(place.opening_status || '영업시간 확인 필요'),
                tags: Array.isArray(place.tags) ? place.tags : [],
                representativeMenu: String(place.representative_menu || ''),
                estimatedCost: Number(place.estimated_cost || 0),
                status: index < 2 ? 'active' : 'upcoming',
                mapLeft: '',
                mapTop: ''
            }));
            places.forEach((place: any, index: number) => {
                if (index <= 0 || !stops[index - 1]) return;
                let move = place.move_from_previous || {};
                let minutes = Number(move.duration_minutes || 0);
                stops[index - 1].move = `${this.plannerModeLabel(move.mode || '')} ${minutes > 0 ? `${minutes}분` : '시간 확인 필요'}`;
            });
            stops = this.applyPlannerMapPositions(stops);
            return {
                label: day.label || `${dayIndex + 1}일차`,
                stops,
                totalMoveMinutes: Number(day.total_move_minutes || 0),
                totalDistanceMeters: Number(day.total_distance_meters || 0),
                totalStayMinutes: Number(day.total_stay_minutes || 0),
                expectedCost: Number(day.expected_cost || 0),
                expectedCostLabel: String(day.expected_cost_label || ''),
                expectedMoveTime: String(day.expected_move_time || ''),
                endTime: day.end_time || '',
                theme: String(day.theme || ''),
                todayRecommendation: String(day.today_recommendation || ''),
                recommendationReason: String(day.recommendation_reason || ''),
                caution: String(day.caution || ''),
                weather: String(day.weather || ''),
                description: Array.isArray(day.description) ? day.description : [],
                qualityScore: Number(day.quality_score || 0)
            };
        });
        this.plannerCourseDayIndex = 0;
        this.plannerCourseReady = this.plannerCourseDays.length > 0;
        this.plannerRouteSource = '내부 장소·이동시간 기반';
        this.applyPlannerCourseDay(0);
        this.plannerCompanionCards = [];
        this.refreshPlannerRouteWithGoogle();
    }

    private startPlannerProgress() {
        this.stopPlannerProgress();
        this.plannerGenerationStep = 0;
        if (typeof window === 'undefined') return;
        this.plannerProgressTimer = window.setInterval(() => {
            this.plannerGenerationStep = Math.min(this.plannerGenerationStep + 1, this.plannerProgressSteps.length - 1);
            this.service.render();
        }, 650);
    }

    private stopPlannerProgress() {
        if (this.plannerProgressTimer && typeof window !== 'undefined') window.clearInterval(this.plannerProgressTimer);
        this.plannerProgressTimer = null;
    }

    private formatPlannerMinutes(value: number) {
        let minutes = Math.max(0, Math.round(Number(value || 0)));
        let hours = Math.floor(minutes / 60);
        let remain = minutes % 60;
        return hours > 0 ? `약 ${hours}시간${remain ? ` ${remain}분` : ''}` : `약 ${remain}분`;
    }

    private rebuildPlannerPreviewFromMessages() {
        this.resetPlannerPreview();
    }

    private plannerReplyForPrompt(prompt: string) {
        let text = String(prompt || '');
        if (this.plannerCourseReady && (text.indexOf('야경') > -1 || text.indexOf('저녁') > -1 || text.indexOf('밤') > -1)) {
            return '좋아요! 저녁 야경 스팟까지 반영해서 기존 코스를 업데이트할게요. 잠시만 기다려주세요.';
        }
        return '좋아요! 바다, 맛집, 감성 카페를 중심으로 코스를 만들어볼게요. 잠시만 기다려주세요.';
    }

    private applyPlannerPreviewFromAiPayload(prompt: string, payload: any) {
        let toolLogs = payload && Array.isArray(payload.tool_logs) ? payload.tool_logs : [];
        let stops = this.plannerStopsFromToolLogs(toolLogs);
        if (stops.length < 2) {
            return false;
        }

        this.applyPlannerDirectionsFromToolLogs(stops, toolLogs);
        stops = this.applyPlannerMapPositions(stops).map((stop: any, index: number) => ({
            ...stop,
            status: index < 2 ? 'active' : 'upcoming'
        }));

        this.plannerCourseRegion = this.plannerRegionFromStops(stops, prompt);
        this.plannerCourseSchedule = this.plannerScheduleFromPrompt(prompt);
        this.plannerCourseBaseTitle = `${this.plannerCourseRegion} AI 여행`;
        this.plannerMapLabel = `${this.plannerCourseRegion} 동선`;
        this.plannerCourseDayIndex = 0;
        this.plannerCourseDays = [{ label: '1일차', stops }];
        this.plannerCourseReady = true;
        this.applyPlannerCourseDay(0);
        this.plannerRouteSource = 'AI 실제 장소 검색 기반';
        this.plannerCompanionCards = [];
        this.refreshPlannerRouteWithGoogle();
        return true;
    }

    private plannerStopsFromToolLogs(toolLogs: any[]) {
        let rows: any[] = [];
        let seen: any = {};
        (toolLogs || []).forEach((log: any) => {
            let call = log && log.functionCall ? log.functionCall : {};
            if (call.name !== 'place_search') return;
            let response = log && log.functionResponse ? log.functionResponse : {};
            let results = Array.isArray(response.results) ? response.results : [];
            results.forEach((place: any) => {
                let key = String((place && (place.place_id || place.id || place.name)) || '').trim();
                if (!key || seen[key] || rows.length >= 5) return;
                seen[key] = true;
                rows.push(place);
            });
        });

        return rows.map((place: any, index: number) => {
            let category = this.cleanPlannerText(place.category || '', 40);
            let address = this.cleanPlannerText(place.address || place.area || '', 120);
            return {
                key: this.cleanPlannerText(place.place_id || place.id || place.name, 80) || `ai-place-${index}`,
                placeId: this.cleanPlannerText(place.place_id || place.id || '', 80),
                time: this.plannerTimeForIndex(index),
                name: this.cleanPlannerText(place.name || place.title || '', 80),
                area: this.plannerAreaFromAddress(address),
                tag: this.plannerActivityLabel(category, index),
                move: '이동 확인 중',
                image: this.cleanPlannerText(place.thumbnail || place.image || '', 300) || this.defaultPlannerImage(category, index),
                icon: this.plannerIconForCategory(category),
                lat: this.toPlannerNumber(place.lat || place.latitude),
                lng: this.toPlannerNumber(place.lng || place.longitude),
                mapLeft: '',
                mapTop: ''
            };
        }).filter((stop: any) => !!stop.name);
    }

    private applyPlannerDirectionsFromToolLogs(stops: any[], toolLogs: any[]) {
        let directions = (toolLogs || []).filter((log: any) => {
            return log && log.functionCall && log.functionCall.name === 'directions_lookup';
        });
        directions.forEach((log: any, index: number) => {
            if (index >= stops.length - 1) return;
            let response = log.functionResponse || {};
            let minutes = Number(response.duration_minutes || 0);
            let meters = Number(response.distance_meters || 0);
            let mode = this.plannerModeLabel(response.mode || (log.functionCall.arguments || {}).mode || '');
            stops[index].move = `${mode} ${minutes > 0 ? `${minutes}분` : '시간 확인 필요'}`;
            if (meters > 0) stops[index].googleDistance = this.formatPlannerDistance(meters, false);
        });
    }

    private applyPlannerMapPositions(stops: any[]) {
        let coords = (stops || []).filter((stop: any) => this.isFiniteNumber(stop.lat) && this.isFiniteNumber(stop.lng));
        if (coords.length < 2) {
            return (stops || []).map((stop: any, index: number) => ({
                ...stop,
                ...this.fallbackPlannerMapPosition(index, stops.length)
            }));
        }

        let minLat = Math.min(...coords.map((stop: any) => Number(stop.lat)));
        let maxLat = Math.max(...coords.map((stop: any) => Number(stop.lat)));
        let minLng = Math.min(...coords.map((stop: any) => Number(stop.lng)));
        let maxLng = Math.max(...coords.map((stop: any) => Number(stop.lng)));
        let latSpan = maxLat - minLat || 0.01;
        let lngSpan = maxLng - minLng || 0.01;

        return (stops || []).map((stop: any, index: number) => {
            if (!this.isFiniteNumber(stop.lat) || !this.isFiniteNumber(stop.lng)) {
                return { ...stop, ...this.fallbackPlannerMapPosition(index, stops.length) };
            }
            let left = 18 + ((Number(stop.lng) - minLng) / lngSpan) * 64;
            let top = 18 + (1 - ((Number(stop.lat) - minLat) / latSpan)) * 64;
            return {
                ...stop,
                mapLeft: `${Math.max(12, Math.min(88, left)).toFixed(0)}%`,
                mapTop: `${Math.max(12, Math.min(88, top)).toFixed(0)}%`
            };
        });
    }

    private fallbackPlannerMapPosition(index: number, total: number) {
        let ratio = total > 1 ? index / (total - 1) : 0;
        return {
            mapLeft: `${Math.round(76 - ratio * 52)}%`,
            mapTop: `${Math.round(22 + ratio * 58)}%`
        };
    }

    private generatedPlannerCompanionCards() {
        let first = this.plannerStops[0] || {};
        let last = this.plannerStops[this.plannerStops.length - 1] || first;
        let regionKey = String(this.plannerCourseRegion || 'ai').replace(/\s+/g, '-');
        return [
            {
                id: `planner-mate-${regionKey}-ai`,
                courseId: '',
                courseConfirmed: false,
                title: `${this.plannerCourseRegion} AI 코스 같이 갈 동행을 찾아요`,
                route: this.plannerCourseTitle,
                routeStops: this.plannerStops.map((stop: any) => stop.name),
                location: this.plannerCourseRegion,
                date: this.plannerCourseSchedule,
                time: '10:00 출발',
                capacity: 4,
                applicants: 2,
                estimatedCost: '1인 약 8만원',
                budgetStyle: 'medium',
                pace: 'balanced',
                moodTags: ['사진', '맛집', '편안한 대화'],
                flexibility: ['카페 순서', '종료 시간'],
                intro: '대화로 만든 동선을 함께 다듬고 걸을 동행을 찾아요.',
                host: 'GACHI',
                status: 'open',
                saved: false,
                image: first.image || '/assets/places/haeundae-beach.jpg'
            },
            {
                id: `planner-mate-${regionKey}-slow-ai`,
                courseId: '',
                courseConfirmed: false,
                title: '여유롭게 쉬어가는 여행 메이트 구해요',
                route: this.plannerCourseTitle,
                routeStops: this.plannerStops.map((stop: any) => stop.name),
                location: this.plannerCourseRegion,
                date: this.plannerCourseSchedule,
                time: '13:00 출발',
                capacity: 3,
                applicants: 1,
                estimatedCost: '1인 약 6만원',
                budgetStyle: 'medium',
                pace: 'slow',
                moodTags: ['카페', '산책', '조용히'],
                flexibility: ['장소 체류 시간'],
                intro: '장소마다 충분히 머물며 사진과 식사를 즐길 분을 찾아요.',
                host: 'GACHI',
                status: 'open',
                saved: false,
                image: last.image || '/assets/places/busan-cafe.jpg'
            }
        ];
    }

    private plannerRegionFromStops(stops: any[], prompt: string) {
        let promptText = String(prompt || '');
        let known = this.courseKnownRegions().find((option: any) => {
            let area = String(option && option.area ? option.area : '').trim();
            return area && promptText.indexOf(area.split(' ')[0]) > -1;
        });
        if (known && known.area) return known.area;

        let area = this.cleanPlannerText(stops && stops[0] ? stops[0].area : '', 60);
        if (!area) return 'AI 추천 지역';
        let parts = area.replace(/광역시|특별시|특별자치도|특별자치시/g, '').split(/\s+/).filter((item: string) => !!item);
        return parts.slice(0, 2).join(' ') || area;
    }

    private plannerAreaFromAddress(address: string) {
        let text = this.cleanPlannerText(address, 120);
        if (!text) return '위치 확인 필요';
        return text.split(/\s+/).filter((item: string) => !!item).slice(0, 3).join(' ');
    }

    private plannerScheduleFromPrompt(prompt: string) {
        let text = String(prompt || '');
        if (text.indexOf('2박') > -1) return '2박 3일';
        if (text.indexOf('1박') > -1) return '1박 2일';
        if (text.indexOf('당일') > -1) return '당일';
        if (text.indexOf('반나절') > -1 || text.indexOf('오후') > -1) return '반나절';
        return this.plannerCourseSchedule || '일정 협의';
    }

    private plannerTimeForIndex(index: number) {
        return ['10:00', '12:30', '15:00', '17:00', '19:30'][index] || '시간 협의';
    }

    private plannerActivityLabel(category: string, index: number) {
        let text = String(category || '');
        if (text.indexOf('카페') > -1) return '카페 · 디저트';
        if (text.indexOf('음식') > -1 || text.indexOf('맛집') > -1) return index <= 1 ? '점심 식사' : '저녁 식사';
        if (text.indexOf('숙박') > -1) return '숙소 체크인';
        if (text.indexOf('쇼핑') > -1) return '쇼핑';
        if (text.indexOf('문화') > -1) return '문화 산책';
        if (text.indexOf('레포츠') > -1) return '액티비티';
        return index === 0 ? '여행 시작' : '추천 방문';
    }

    private plannerIconForCategory(category: string) {
        let text = String(category || '');
        if (text.indexOf('카페') > -1) return 'fa-mug-saucer';
        if (text.indexOf('음식') > -1 || text.indexOf('맛집') > -1) return 'fa-utensils';
        if (text.indexOf('숙박') > -1) return 'fa-bed';
        if (text.indexOf('쇼핑') > -1) return 'fa-bag-shopping';
        if (text.indexOf('문화') > -1) return 'fa-landmark';
        if (text.indexOf('레포츠') > -1) return 'fa-person-running';
        return 'fa-location-dot';
    }

    private defaultPlannerImage(category: string, index: number) {
        let text = String(category || '');
        if (text.indexOf('카페') > -1) return '/assets/places/busan-cafe.jpg';
        if (text.indexOf('음식') > -1 || text.indexOf('맛집') > -1) return '/assets/places/busan-milmyeon.jpg';
        if (text.indexOf('야경') > -1) return '/assets/places/gwangan-night.jpg';
        return ['/assets/places/haeundae-beach.jpg', '/assets/places/dongbaekseom.jpg', '/assets/bg-blue.jpg'][index % 3];
    }

    public plannerModeLabel(mode: string) {
        let text = String(mode || '').toLowerCase();
        if (text === 'driving' || text === 'car') return '차량';
        if (text === 'transit') return '대중교통';
        return '도보';
    }

    private toPlannerNumber(value: any) {
        if (value === null || typeof value === 'undefined' || value === '') return null;
        let number = Number(value);
        return isFinite(number) ? number : null;
    }

    private cleanPlannerText(value: any, limit: number = 120) {
        let text = String(value || '').replace(/<[^>]*>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();
        return text.length > limit ? text.slice(0, limit).trim() : text;
    }

    public async openCommunityComposer(kind: string = 'post') {
        let nextTopic = kind === 'question' ? 'question' : this.selectedCommunityTopic;
        if (nextTopic === 'question') nextTopic = 'recommend';
        this.communityDraft = {
            ...this.defaultCommunityDraft(),
            kind: kind === 'question' ? 'question' : 'post',
            topic: kind === 'question' ? 'question' : nextTopic
        };
        this.communityPublishSubmitting = false;
        this.communityComposerOpen = true;
        await this.service.render();
    }

    public async closeCommunityComposer() {
        if (this.communityPublishSubmitting) return;
        this.communityComposerOpen = false;
        await this.service.render();
    }

    public async setCommunityDraftKind(kind: string) {
        this.communityDraft.kind = kind === 'question' ? 'question' : 'post';
        if (this.communityDraft.kind === 'question') this.communityDraft.topic = 'question';
        if (this.communityDraft.kind === 'post') {
            if (this.communityDraft.topic === 'question') this.communityDraft.topic = 'recommend';
            this.communityDraft.pollOptions = [];
            this.communityDraft.pollInput = '';
        }
        await this.service.render();
    }

    public async setCommunityDraftDestination(enabled: boolean) {
        this.communityDraft.hasDestination = enabled;
        if (!enabled) {
            this.communityDraft.destination = '';
            this.communityDraft.place = '';
        }
        await this.service.render();
    }

    public communityDraftTags() {
        return this.normalizeCommunityDraftTags(this.communityDraft ? this.communityDraft.tags : []);
    }

    public async handleCommunityTagKeydown(event: any) {
        let key = event && event.key ? String(event.key) : '';
        if (key !== 'Enter' && key !== ',') return;
        await this.addCommunityTagFromInput(event);
    }

    public async addCommunityTagFromInput(event?: any) {
        if (event && event.preventDefault) event.preventDefault();
        let input = String(this.communityDraft.tagInput || '');
        let nextTags = input
            .split(/[,\s]+/)
            .map((tag: string) => this.normalizeCommunityTag(tag))
            .filter((tag: string) => !!tag);
        if (nextTags.length === 0) return;

        this.communityDraft.tags = this.uniqueTags([
            ...this.communityDraftTags(),
            ...nextTags
        ]);
        this.communityDraft.tagInput = '';
        await this.service.render();
    }

    public async removeCommunityTag(tag: string) {
        let target = this.normalizeCommunityTag(tag);
        this.communityDraft.tags = this.communityDraftTags().filter((item: string) => item !== target);
        await this.service.render();
    }

    public communityDraftPollOptions() {
        return this.normalizeDraftList(this.communityDraft ? this.communityDraft.pollOptions : []);
    }

    public async handleCommunityPollKeydown(event: any) {
        let key = event && event.key ? String(event.key) : '';
        if (key !== 'Enter') return;
        await this.addCommunityPollOption(event);
    }

    public async addCommunityPollOption(event?: any) {
        if (event && event.preventDefault) event.preventDefault();
        let option = String(this.communityDraft.pollInput || '').trim();
        if (!option) return;

        let options = this.communityDraftPollOptions();
        if (options.indexOf(option) < 0) options.push(option);
        this.communityDraft.pollOptions = options;
        this.communityDraft.pollInput = '';
        await this.service.render();
    }

    public async removeCommunityPollOption(option: string) {
        this.communityDraft.pollOptions = this.communityDraftPollOptions().filter((item: string) => item !== option);
        await this.service.render();
    }

    public async handleCommunityPhotoUpload(event: any) {
        let input = event && event.target ? event.target : null;
        let file = input && input.files && input.files[0] ? input.files[0] : null;
        if (!file) return;

        if (file.type && !/^image\//.test(file.type)) {
            await this.showSaveHint('이미지 파일만 등록할 수 있어요.');
            if (input) input.value = '';
            return;
        }

        let reader = new FileReader();
        reader.onload = () => {
            this.communityDraft.photo = String(reader.result || '');
            this.communityDraft.photoName = String(file.name || '첨부 사진');
            this.service.render();
        };
        reader.readAsDataURL(file);
        if (input) input.value = '';
    }

    public async clearCommunityPhoto() {
        this.communityDraft.photo = '';
        this.communityDraft.photoName = '';
        await this.service.render();
    }

    public communityPhotoIsImage(value: any) {
        let source = String(value || '').trim();
        if (!source) return false;
        if (/^data:image\//i.test(source)) return true;
        return /^https?:\/\/.+\.(png|jpe?g|gif|webp|avif)(\?.*)?$/i.test(source);
    }

    public communityPhotoLabel(post: any) {
        if (!post) return '첨부 사진';
        return String(post.photoName || '').trim() || '첨부 사진';
    }

    public async publishCommunityPost() {
        if (this.communityPublishSubmitting) return;
        this.communityPublishSubmitting = true;
        await this.service.render();
        try {
            let title = String(this.communityDraft.title || '').trim();
            let body = String(this.communityDraft.body || '').trim();
            if (!title) {
                await this.showSaveHint('글 제목을 입력해주세요.');
                return;
            }
            if (!body) {
                await this.showSaveHint('본문을 입력해주세요.');
                return;
            }

            let isQuestion = this.communityDraft.kind === 'question';
            let topic = String(this.communityDraft.topic || 'recommend');
            if (isQuestion) topic = 'question';
            if (!isQuestion && topic === 'question') topic = 'recommend';
            let topicMeta = this.communityTopics.find((item: any) => item.key === topic) || this.communityTopics[0];
            let destination = this.communityDraft.hasDestination ? String(this.communityDraft.destination || '').trim() : '';
            let place = this.communityDraft.hasDestination ? String(this.communityDraft.place || '').trim() : '';
            let pollOptions = isQuestion ? this.communityDraftPollOptions() : [];
            let pendingPollOption = String(this.communityDraft.pollInput || '').trim();
            if (isQuestion && pendingPollOption && pollOptions.indexOf(pendingPollOption) < 0) {
                pollOptions = [...pollOptions, pendingPollOption];
            }
            let pendingTags = String(this.communityDraft.tagInput || '')
                .split(/[,\s]+/)
                .map((tag: string) => this.normalizeCommunityTag(tag))
                .filter((tag: string) => !!tag);
            let tags = this.uniqueTags([
                topicMeta.label,
                destination,
                place,
                ...this.communityDraftTags(),
                ...pendingTags
            ]).filter((tag: string) => !!tag);
            let now = Date.now();
            let post: any = {
                id: `community-draft-${now}`,
                kind: isQuestion ? 'question' : 'post',
                topic,
                title,
                summary: body,
                category: isQuestion ? '질문' : topicMeta.label,
                destination,
                place,
                photo: String(this.communityDraft.photo || '').trim(),
                photoName: String(this.communityDraft.photoName || '').trim(),
                author: this.myDisplayName(),
                likes: 0,
                comments: isQuestion ? 1 : 0,
                views: 1,
                votes: 0,
                createdAt: 0,
                createdLabel: '방금',
                tags
            };

            if (pollOptions.length > 0) {
                let counts: any = {};
                pollOptions.forEach((option: string) => counts[option] = 0);
                if (!isQuestion) {
                    post.topic = 'vote';
                    post.category = '인기 투표';
                }
                post.poll = {
                    title: isQuestion ? '질문 투표' : '투표',
                    options: pollOptions,
                    counts
                };
            }

            let saveResult = await this.saveCommunityPost(post);
            if (!saveResult || !saveResult.post) {
                await this.showSaveHint('글 저장에 실패했어요. 다시 시도해주세요.');
                return;
            }
            let savedPost = saveResult.post;
            if (saveResult.remote) await this.loadCommunityPosts(false);
            this.selectedCommunityTopic = 'recommend';
            this.selectedCommunitySort = 'latest';
            this.expandedCommunityPostId = savedPost.id;
            this.communityDraft = this.defaultCommunityDraft();
            this.communityComposerOpen = false;
            await this.showSaveHint(saveResult.remote
                ? (isQuestion ? '질문글이 등록됐어요.' : '커뮤니티 글이 등록됐어요.')
                : '서버 연결이 불안정해 이 기기에 먼저 보관했어요.');
        } finally {
            this.communityPublishSubmitting = false;
            await this.service.render();
        }
    }

    public communityPollPercent(post: any, option: string) {
        if (!post || !post.poll || !post.poll.counts) return 0;
        let total = Number(post.votes || 0);
        if (total <= 0) return 0;
        return Math.round((Number(post.poll.counts[option] || 0) / total) * 100);
    }

    public async voteCommunityPoll(post: any, option: string) {
        if (!post || !post.poll || !option) return;
        if (this.hasVotedCommunityPoll(post)) {
            await this.showSaveHint('투표는 한 번만 할 수 있어요.');
            return;
        }
        this.markCommunityPollVoted(post, option);
        if (!post.poll.counts) post.poll.counts = {};
        post.poll.counts[option] = Number(post.poll.counts[option] || 0) + 1;
        post.votes = Number(post.votes || 0) + 1;
        this.applyCommunityPostUpdate(post);
        await this.service.render();
        let response = await this.requestCommunityPostAction('vote', post, { option });
        if (response && response.code === 200 && response.data) {
            if (response.data.selectedOption) this.markCommunityPollVoted(post, response.data.selectedOption);
            if (response.data.post) this.applyCommunityPostUpdate(response.data.post);
            await this.showSaveHint(response.data.already ? '이미 투표했어요.' : '투표가 반영됐어요.');
        } else if (String(post.id || '').indexOf('community-draft-') === 0) {
            await this.saveCommunityPost(post);
            await this.showSaveHint('투표가 반영됐어요.');
        } else {
            await this.showSaveHint('서버 연결이 불안정해 투표를 기기에 먼저 표시했어요.');
        }
    }

    public async openAiPlanner() {
        this.activeTab = 'chat';
        this.chatContentTab = 'chat';
        this.draft = '';
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.service.render();
    }

    public async openCourseComposer() {
        this.resetCourseComposerDraftState();
        this.activeFilterKey = '';
        this.filterOverviewOpen = false;
        this.courseBuilderMode = 'manual';
        this.courseBuilderStep = 'info';
        this.clearCourseGoogleOverlays();
        this.courseComposerOpen = true;
        await this.service.render();
    }

    public async openPlannerCourseEditor() {
        if (!this.plannerCourseReady || !Array.isArray(this.plannerCourseDays) || this.plannerCourseDays.length === 0) {
            await this.showSaveHint('먼저 AI와 코스를 만들어주세요.');
            return;
        }

        this.resetCourseComposerDraftState();
        this.courseComposerPlannerEdit = true;
        this.courseBuilderMode = 'manual';
        this.courseBuilderStep = 'places';
        this.courseBuilderDayIndex = Math.max(0, Math.min(this.plannerCourseDayIndex, this.plannerCourseDays.length - 1));
        this.courseBuilderDays = this.plannerCourseDays.map((day: any, dayIndex: number) => ({
            label: day && day.label ? day.label : `${dayIndex + 1}일차`,
            places: ((day && day.stops) || []).map((stop: any, index: number) => this.plannerStopToBuilderPlace(stop, dayIndex, index))
        }));
        this.courseBuilderOriginalDays = this.cloneCourseBuilderDays(this.courseBuilderDays);
        this.courseBuilderPlaces = this.cloneCourseBuilderPlaces(this.courseBuilderDays[this.courseBuilderDayIndex].places);
        let allPlaces = this.courseBuilderDays.reduce((items: any[], day: any) => items.concat(day.places || []), []);
        this.courseDraft = {
            ...this.defaultCourseDraft(),
            title: this.plannerCourseBaseTitle || this.plannerCourseTitle,
            region: this.plannerCourseRegion,
            schedule: this.plannerCourseSchedule,
            places: allPlaces.map((place: any) => place.name).join('\n'),
            photo: allPlaces[0] && allPlaces[0].image ? allPlaces[0].image : '',
            photoName: 'AI 플래너 코스',
            description: `AI 대화로 만든 ${this.plannerCourseSchedule} 코스를 수정합니다.`,
            category: '여행',
            companionType: 'friend',
            isPublic: false
        };
        this.activeFilterKey = '';
        this.filterOverviewOpen = false;
        this.coursePublishModalOpen = false;
        this.coursePlaceSearchOpen = false;
        this.courseBuilderError = '';
        this.clearCourseGoogleOverlays();
        this.courseComposerOpen = true;
        await this.service.render();
        this.scheduleCourseMapRender();
    }

    private plannerStopToBuilderPlace(stop: any, dayIndex: number, index: number) {
        return {
            placeId: String(stop && (stop.placeId || stop.key) ? (stop.placeId || stop.key) : `planner-${dayIndex}-${index}`).replace(/^place-/, ''),
            originalKey: stop && stop.key ? stop.key : '',
            name: stop && stop.name ? stop.name : '장소',
            lat: this.safeNumber(stop && stop.lat),
            lng: this.safeNumber(stop && stop.lng),
            order: index + 1,
            visitTime: stop && stop.time ? stop.time : this.plannerTimeForIndex(index),
            memo: stop && stop.tag ? stop.tag : '',
            area: stop && stop.area ? stop.area : '',
            address: stop && stop.address ? stop.address : '',
            category: stop && stop.tag ? stop.tag : '추천 장소',
            image: stop && stop.image ? stop.image : '',
            move: stop && stop.move ? stop.move : '이동 확인 중',
            manualTime: false
        };
    }

    private cloneCourseBuilderPlaces(places: any[]) {
        return (places || []).map((place: any) => ({ ...place }));
    }

    private cloneCourseBuilderDays(days: any[]) {
        return (days || []).map((day: any) => ({
            label: day.label,
            places: this.cloneCourseBuilderPlaces(day.places)
        }));
    }

    public async setCourseBuilderDay(index: number) {
        if (!this.courseComposerPlannerEdit || index < 0 || index >= this.courseBuilderDays.length || index === this.courseBuilderDayIndex) return;
        this.syncCurrentCourseBuilderDay();
        this.courseBuilderDayIndex = index;
        this.courseBuilderPlaces = this.cloneCourseBuilderPlaces(this.courseBuilderDays[index].places);
        this.coursePlaceSearchQuery = '';
        this.coursePlaceSearchResults = [];
        this.coursePlaceSearchOpen = false;
        this.courseBuilderError = '';
        this.clearCourseGoogleOverlays();
        await this.service.render();
        this.scheduleCourseMapRender();
    }

    private syncCurrentCourseBuilderDay() {
        if (!this.courseComposerPlannerEdit || !this.courseBuilderDays[this.courseBuilderDayIndex]) return;
        this.courseBuilderDays[this.courseBuilderDayIndex].places = this.cloneCourseBuilderPlaces(this.courseBuilderPlaces);
    }

    public async closeCourseComposer() {
        this.courseComposerOpen = false;
        this.courseComposerPlannerEdit = false;
        this.courseBuilderDayIndex = 0;
        this.courseBuilderDays = [];
        this.courseBuilderOriginalDays = [];
        this.courseAiRebuilding = false;
        this.courseBuilderMode = '';
        this.courseBuilderStep = 'mode';
        this.coursePublishModalOpen = false;
        this.coursePlaceSearchOpen = false;
        this.clearCourseGoogleOverlays();
        await this.service.render();
    }

    public async openCourseDraftArchive() {
        this.refreshCourseDraftArchiveSummary();
        this.courseDraftArchiveOpen = true;
        this.filterOverviewOpen = false;
        await this.service.render();
    }

    public async closeCourseDraftArchive() {
        this.courseDraftArchiveOpen = false;
        await this.service.render();
    }

    public async loadSavedCourseDraft() {
        if (!this.restoreCourseDraft(true)) {
            this.courseDraftArchiveOpen = false;
            await this.showSaveHint('저장된 코스가 없어요.');
            return;
        }

        this.activeFilterKey = '';
        this.filterOverviewOpen = false;
        this.courseDraftArchiveOpen = false;
        this.courseComposerOpen = true;
        this.coursePublishModalOpen = false;
        this.coursePlaceSearchOpen = false;
        this.courseBuilderError = '';
        this.clearCourseGoogleOverlays();
        await this.service.render();
        if (this.courseBuilderStep === 'places') {
            this.scheduleCourseMapRender();
            if (!this.coursePlaceSearchResults.length) await this.searchCoursePlaces(false);
        }
    }

    public async selectCourseBuilderMode(mode: string) {
        if (mode !== 'manual' && mode !== 'ai') return;
        this.courseBuilderMode = mode;
        this.courseBuilderStep = mode === 'ai' ? 'ai' : 'info';
        this.courseBuilderError = '';
        this.coursePlaceSearchOpen = false;
        this.clearCourseGoogleOverlays();
        await this.service.render();
    }

    public async resetCourseBuilderMode() {
        this.courseBuilderMode = '';
        this.courseBuilderStep = 'mode';
        this.courseBuilderError = '';
        this.coursePlaceSearchOpen = false;
        this.clearCourseGoogleOverlays();
        await this.service.render();
    }

    public courseBuilderStepOneLabel() {
        return this.courseBuilderMode === 'ai' ? 'AI 추천' : '기본 정보';
    }

    public courseDateCalendarMonthLabel() {
        return `${this.courseDateCalendarMonth.getFullYear()}년 ${this.courseDateCalendarMonth.getMonth() + 1}월`;
    }

    public courseDateCalendarDays() {
        let year = this.courseDateCalendarMonth.getFullYear();
        let month = this.courseDateCalendarMonth.getMonth();
        let firstDate = new Date(year, month, 1);
        let startDate = new Date(year, month, 1 - firstDate.getDay());
        let todayKey = this.formatIsoDate(new Date());
        let selectedStart = String(this.courseDraft.scheduleDate || '');
        let selectedEnd = String(this.courseDraft.scheduleEndDate || selectedStart || '');
        let days: any[] = [];
        for (let i = 0; i < 42; i++) {
            let date = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate() + i);
            let key = this.formatIsoDate(date);
            let inRange = !!selectedStart && !!selectedEnd && key >= selectedStart && key <= selectedEnd;
            days.push({
                key,
                label: date.getDate(),
                inMonth: date.getMonth() === month,
                isToday: key === todayKey,
                inRange,
                rangeStart: key === selectedStart,
                rangeEnd: key === selectedEnd,
                selected: key === selectedStart || key === selectedEnd,
                ariaLabel: `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`
            });
        }
        return days;
    }

    public async changeCourseDateMonth(direction: number) {
        this.courseDateCalendarMonth = new Date(this.courseDateCalendarMonth.getFullYear(), this.courseDateCalendarMonth.getMonth() + direction, 1);
        await this.service.render();
    }

    public async setCourseDraftDate(value: string) {
        if (!value) return;
        this.setCourseDraftDateRange(value, value);
        let date = new Date(`${value}T00:00:00`);
        if (!isNaN(date.getTime())) this.courseDateCalendarMonth = new Date(date.getFullYear(), date.getMonth(), 1);
        this.courseBuilderError = '';
        await this.service.render();
    }

    public async startCourseDateDrag(day: any, event: any) {
        if (!day) return;
        if (event && event.preventDefault) event.preventDefault();
        this.courseDateDragActive = true;
        this.courseDateDragStartKey = day.key;
        this.setCourseDraftDateRange(day.key, day.key);
        await this.service.render();
    }

    public async previewCourseDatePointer(event: any) {
        if (!this.courseDateDragActive) return;
        if (event && event.preventDefault) event.preventDefault();
        let key = this.courseDateKeyFromPointer(event);
        if (!key || key === this.courseDraft.scheduleEndDate) return;
        this.setCourseDraftDateRange(this.courseDateDragStartKey || key, key);
        await this.service.render();
    }

    public finishCourseDateDrag() {
        this.courseDateDragActive = false;
        this.courseDateDragStartKey = '';
    }

    public openCourseRegionSearch() {
        this.courseRegionSearchOpen = true;
    }

    public onCourseRegionInput(event: any) {
        if (event && event.target) this.courseDraft.region = event.target.value || '';
        this.courseRegionSearchOpen = true;
    }

    public courseRegionMatches() {
        let query = String(this.courseDraft.region || '').trim().toLowerCase();
        let initials = this.koreanInitials(query);
        let useInitialSearch = this.isKoreanInitialQuery(query);
        let options = this.courseKnownRegions();
        if (!query) return options.slice(0, 6);
        return options.filter((option: any) => {
            let label = String(option.label || '').toLowerCase();
            let area = String(option.area || '').toLowerCase();
            let index = `${label} ${area}`.indexOf(query) > -1;
            let initialIndex = this.koreanInitials(`${option.label} ${option.area}`).indexOf(initials || query) > -1;
            return index || (useInitialSearch && initialIndex);
        }).slice(0, 8);
    }

    public async selectCourseRegionSuggestion(option: any) {
        if (!option) return;
        this.courseDraft.region = option.area || option.label || '';
        this.courseRegionSearchOpen = false;
        this.courseBuilderError = '';
        await this.service.render();
        if (this.courseBuilderStep === 'places') this.scheduleCourseMapRender();
    }

    public async onCourseCoverFile(event: any) {
        let file = event && event.target && event.target.files ? event.target.files[0] : null;
        if (!file || typeof FileReader === 'undefined') return;
        let reader = new FileReader();
        reader.onload = async () => {
            this.courseDraft.photo = String(reader.result || '');
            this.courseDraft.photoName = file.name || '대표 이미지';
            await this.service.render();
        };
        reader.readAsDataURL(file);
    }

    private courseDateKeyFromPointer(event: any) {
        if (!event || typeof document === 'undefined') return '';
        let target = document.elementFromPoint(event.clientX, event.clientY);
        while (target) {
            if (target.getAttribute) {
                let key = target.getAttribute('data-course-date-key');
                if (key) return key;
            }
            target = target.parentElement;
        }
        return '';
    }

    private setCourseDraftDateRange(start: string, end: string) {
        let range = [start, end].sort();
        this.courseDraft.scheduleDate = range[0];
        this.courseDraft.scheduleEndDate = range[1];
        this.courseDraft.schedule = range[0] === range[1]
            ? this.formatCourseDateLabel(range[0])
            : `${this.formatCourseDateLabel(range[0])} - ${this.formatCourseDateLabel(range[1])}`;
    }

    private formatIsoDate(date: Date) {
        let year = date.getFullYear();
        let month = String(date.getMonth() + 1).padStart(2, '0');
        let day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    private formatCourseDateLabel(value: string) {
        let date = new Date(`${value}T00:00:00`);
        if (isNaN(date.getTime())) return value;
        let weekday = ['일', '월', '화', '수', '목', '금', '토'][date.getDay()];
        return `${date.getMonth() + 1}.${date.getDate()} ${weekday}`;
    }

    private koreanInitials(value: string) {
        const initials = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ';
        return String(value || '').split('').map((char: string) => {
            let code = char.charCodeAt(0) - 44032;
            if (code < 0 || code > 11171) return char.toLowerCase();
            return initials[Math.floor(code / 588)] || char;
        }).join('');
    }

    private isKoreanInitialQuery(value: string) {
        return /^[ㄱ-ㅎ]+$/.test(String(value || '').trim());
    }

    private courseKnownRegions() {
        return [
            { label: '수원', area: '경기 수원', lat: 37.2636, lng: 127.0286 },
            { label: '수지', area: '경기 용인 수지', lat: 37.3221, lng: 127.0977 },
            { label: '서울 성수', area: '서울 성동구 성수동', lat: 37.5446, lng: 127.0557 },
            { label: '서울 홍대', area: '서울 마포구', lat: 37.5563, lng: 126.9236 },
            { label: '서울 잠실', area: '서울 송파구', lat: 37.5133, lng: 127.1002 },
            { label: '판교', area: '경기 성남 분당', lat: 37.3947, lng: 127.1112 },
            { label: '부산', area: '부산 해운대', lat: 35.1631, lng: 129.1635 },
            { label: '제주', area: '제주 제주시', lat: 33.4996, lng: 126.5312 },
            { label: '강릉', area: '강원 강릉', lat: 37.7519, lng: 128.8761 },
            { label: '여수', area: '전남 여수', lat: 34.7604, lng: 127.6622 },
            { label: '전주', area: '전북 전주', lat: 35.8242, lng: 127.1480 },
            { label: '인천', area: '인천 송도', lat: 37.3895, lng: 126.6450 },
            { label: '대구', area: '대구 중구', lat: 35.8714, lng: 128.6014 }
        ];
    }

    public courseInfoStepComplete() {
        return !!String(this.courseDraft.title || '').trim()
            && !!String(this.courseDraft.region || '').trim()
            && !!String(this.courseDraft.schedule || '').trim();
    }

    public async setCourseBuilderStep(step: string) {
        if (step === 'info') {
            await this.backToCourseInfo();
            return;
        }
        if (step === 'places' && this.courseBuilderMode === 'ai' && this.courseBuilderPlaces.length === 0) {
            this.courseBuilderError = 'AI 추천 코스를 선택해주세요.';
            await this.service.render();
            return;
        }
        if (step === 'places') await this.continueCourseInfo();
    }

    public async continueCourseInfo() {
        if (!this.courseInfoStepComplete()) {
            this.courseBuilderError = '여행 제목, 지역, 일정을 입력해주세요.';
            await this.service.render();
            return;
        }

        this.ensureCourseDraftMeta();
        this.courseBuilderError = '';
        this.courseBuilderStep = 'places';
        await this.service.render();
        this.scheduleCourseMapRender();
        if (!this.coursePlaceSearchResults.length) await this.searchCoursePlaces(false);
    }

    public async backToCourseInfo() {
        this.courseBuilderStep = this.courseBuilderMode === 'ai' ? 'ai' : 'info';
        this.coursePublishModalOpen = false;
        this.coursePlaceSearchOpen = false;
        this.courseBuilderError = '';
        this.clearCourseGoogleOverlays();
        await this.service.render();
    }

    public courseAiReady() {
        return !!String(this.courseDraft.region || '').trim()
            && !!String(this.courseDraft.schedule || '').trim();
    }

    public courseAiOptions() {
        return [];

        let region = String(this.courseDraft.region || '서울 성수').trim();
        let schedule = String(this.courseDraft.schedule || '반나절').trim();
        let companion = this.companionTypeLabel();
        let mood = String(this.courseAiMood || '취향 맞춤').trim();
        return [
            {
                title: `${region} 감성 산책 코스`,
                summary: `${schedule} · ${companion} · ${mood}`,
                category: '산책',
                places: ['동네 카페', '전시 공간', '산책로']
            },
            {
                title: `${region} 맛집 중심 코스`,
                summary: `${schedule} · 이동 적게 · 식사와 카페 중심`,
                category: '맛집',
                places: ['브런치 맛집', '소품샵', '디저트 카페']
            },
            {
                title: `${region} 여유 코스`,
                summary: `${schedule} · ${companion} · 사진 찍기 좋은 동선`,
                category: '여행',
                places: ['핫플 거리', '편집샵', '야경 스팟']
            }
        ];
    }

    public async applyAiCourseOption(option: any) {
        if (!this.courseAiReady()) {
            this.courseBuilderError = '어디로, 언제 갈지 입력해주세요.';
            await this.service.render();
            return;
        }

        let region = String(this.courseDraft.region || '').trim();
        this.courseBuilderMode = 'ai';
        this.courseDraft.title = option.title || this.courseDraft.title || `${region} AI 추천 코스`;
        this.courseDraft.category = option.category || this.courseDraft.category || '여행';
        this.courseDraft.description = option.summary || this.courseDraft.description || '';
        let rows: any[] = [];
        try {
            let center = this.courseSearchCenter();
            let result = await wiz.call('search_course_places', {
                lat: center.lat,
                lng: center.lng,
                keyword: option.category || '',
                region,
                limit: 3
            });
            if (result.code === 200) rows = (result.data && result.data.rows) || [];
        } catch (e) { }
        rows = rows.filter((place: any) => !!String(place.place_id || place.id || '').replace(/^place-/, ''));

        if (rows.length === 0) {
            this.courseBuilderError = '실제 장소를 찾지 못해 코스를 만들지 않았어요. 직접 장소를 검색해주세요.';
            await this.service.render();
            return;
        }

        this.courseBuilderPlaces = rows.slice(0, 3).map((place: any, index: number) => ({
                placeId: String(place.place_id || place.id || '').replace(/^place-/, ''),
                name: place.name || place.title || '장소',
                lat: this.safeNumber(place.lat || place.latitude),
                lng: this.safeNumber(place.lng || place.longitude),
                order: index + 1,
                visitTime: this.visitTimeForIndex(index),
                memo: '',
                area: place.area || region,
                address: place.address || '',
                category: place.category || option.category || '추천 장소',
                image: place.image || '',
                manualTime: false
            }));
        this.normalizeCourseBuilderOrder(true);
        this.applyCourseDraftFromPlaces();
        this.courseBuilderError = '';
        this.courseBuilderStep = 'places';
        await this.service.render();
        this.scheduleCourseMapRender();
    }

    public async toggleCourseCompanion() {
        this.courseDraft.companionEnabled = !this.courseDraft.companionEnabled;
        await this.service.render();
    }

    public async saveCourseDraft() {
        this.persistCourseDraft();
        await this.showSaveHint('코스 제작 내용을 임시 저장했어요.');
    }

    public hasSavedCourseDraft() {
        this.ensureCourseDraftArchiveSummary();
        return !!this.courseDraftArchiveSummary;
    }

    public savedCourseDraftTitle() {
        this.ensureCourseDraftArchiveSummary();
        let saved = this.courseDraftArchiveSummary;
        let title = saved ? String(saved.title || '').trim() : '';
        if (title) return title;
        let region = saved ? String(saved.region || '').trim() : '';
        return region ? `${region} 새 코스` : '저장된 새 코스';
    }

    public savedCourseDraftMeta() {
        this.ensureCourseDraftArchiveSummary();
        let saved = this.courseDraftArchiveSummary;
        if (!saved) return '임시저장한 코스가 없습니다.';
        let parts = [saved.region, saved.schedule].map((value: any) => String(value || '').trim()).filter((value: string) => !!value);
        if (saved.placeCount > 0) parts.push(`${saved.placeCount}곳`);
        return parts.length ? parts.join(' · ') : '기본 정보 작성 중';
    }

    public savedCourseDraftTime() {
        this.ensureCourseDraftArchiveSummary();
        let saved = this.courseDraftArchiveSummary;
        if (!saved) return '';
        let date = new Date(saved.savedAt);
        if (Number.isNaN(date.getTime())) return '';
        return `${date.getMonth() + 1}.${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
    }

    public async publishCourse() {
        await this.openCoursePublishModal();
    }

    public async openCoursePublishModal() {
        let title = String(this.courseDraft.title || '').trim();
        if (!title) {
            await this.showSaveHint('여행 제목을 입력해주세요.');
            return;
        }
        if (this.courseBuilderPlaces.length === 0) {
            this.courseBuilderStep = 'places';
            await this.showSaveHint('첫 장소를 검색해서 담아보세요.');
            await this.focusCoursePlaceSearch();
            return;
        }

        this.ensureCourseDraftMeta();
        this.coursePublishModalOpen = true;
        await this.service.render();
    }

    public async closeCoursePublishModal() {
        this.coursePublishModalOpen = false;
        await this.service.render();
    }

    public async submitCoursePublish() {
        if (this.coursePublishSubmitting) return;

        let title = String(this.courseDraft.title || '').trim();
        if (!title) {
            this.courseBuilderError = '코스 제목을 입력해주세요.';
            await this.service.render();
            return;
        }
        if (this.courseBuilderPlaces.length === 0) {
            this.courseBuilderError = '코스에 담을 장소를 1개 이상 추가해주세요.';
            await this.service.render();
            return;
        }
        if (this.courseDraft.companionEnabled) {
            let requiredCompanionFields = [
                this.courseDraft.companionDate,
                this.courseDraft.companionTime,
                this.courseDraft.companionCost,
                this.courseDraft.companionPace,
                this.courseDraft.companionMood,
                this.courseDraft.companionFlexible,
                this.courseDraft.companionMeetingPoint
            ];
            if (requiredCompanionFields.some((value: any) => !String(value || '').trim())) {
                this.courseBuilderError = '동행 모집의 날짜·시간·비용·속도·분위기·변경 가능 일정·약속 장소를 모두 입력해주세요.';
                await this.service.render();
                return;
            }
        }

        this.courseBuilderError = '';
        this.coursePublishSubmitting = true;
        await this.service.render();

        let payload = this.courseBuilderPayload();
        let result = await wiz.call('create_builder_course', { data: JSON.stringify(payload) });
        this.coursePublishSubmitting = false;

        if (result.code !== 200) {
            if (result.code === 401) {
                this.coursePublishModalOpen = false;
                await this.openAuthModal('login');
                return;
            }
            this.courseBuilderError = this.responseMessage(result.data, '코스 게시에 실패했습니다.');
            await this.service.render();
            return;
        }

        let row = result.data && result.data.row ? result.data.row : null;
        let course = this.courseRowToCard(row, payload);
        this.courses = [course, ...this.courses.filter((item: any) => item.id !== course.id)];
        this.recommendations = [course, ...this.recommendations.filter((item: any) => item.id !== course.id)];

        if (this.courseDraft.companionEnabled) {
            this.companionPosts = [{
                id: `mate-${course.id}`,
                courseId: course.id,
                courseConfirmed: true,
                title: `${course.title} 동행 모집`,
                route: course.title,
                routeStops: this.courseBuilderPlaces.map((place: any) => place && place.name ? place.name : '').filter((name: string) => !!name),
                location: course.location,
                date: String(this.courseDraft.companionDate || this.courseDraft.schedule || '일정 협의').trim(),
                time: String(this.courseDraft.companionTime || '시간 협의').trim(),
                capacity: Number(this.courseDraft.companionCapacity || 2),
                applicants: 0,
                estimatedCost: String(this.courseDraft.companionCost || '비용 협의').trim(),
                budgetStyle: String(this.courseDraft.companionBudgetStyle || '').trim(),
                pace: String(this.courseDraft.companionPace || '').trim(),
                moodTags: this.splitList(this.courseDraft.companionMood || ''),
                flexibility: this.splitList(this.courseDraft.companionFlexible || ''),
                interestTags: this.uniqueTags([
                    ...this.courseBuilderPlaces.map((place: any) => place && (place.category || place.kind) ? (place.category || place.kind) : ''),
                    ...this.courseDraftPlaces()
                ]).slice(0, 6),
                smoking: String(this.courseDraft.companionSmoking || '').trim(),
                drinking: String(this.courseDraft.companionDrinking || '').trim(),
                verificationRequired: true,
                hostHistory: `동행 ${this.travelResumeCompanionUses()}회 · 후기 확인`,
                meetingPoint: String(this.courseDraft.companionMeetingPoint || '').trim(),
                packingItems: ['신분증', '보조배터리', '개인 준비물'],
                intro: String(this.courseDraft.companionIntro || '함께 여행할 동행을 모집합니다.').trim(),
                host: this.myDisplayName(),
                status: 'open',
                saved: true,
                applications: []
            }, ...this.companionPosts];
        }

        this.courseDraft = this.defaultCourseDraft();
        this.courseBuilderPlaces = [];
        this.coursePlaceSearchQuery = '';
        this.coursePlaceSearchResults = [];
        this.courseDraftSavedAt = '';
        this.courseBuilderMode = '';
        this.courseBuilderStep = 'mode';
        this.courseAiMood = '';
        this.clearCourseDraftStorage();
        this.coursePublishModalOpen = false;
        this.courseComposerOpen = false;
        this.activeTab = 'home';
        this.homeContentTab = 'courses';
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.showSaveHint('코스가 게시됐어요.');
    }

    public async onCoursePlaceSearchInput() {
        this.coursePlaceSearchOpen = true;
        if (this.coursePlaceSearchTimer) clearTimeout(this.coursePlaceSearchTimer);
        this.coursePlaceSearchTimer = setTimeout(() => {
            this.searchCoursePlaces(false);
        }, 220);
        await this.service.render();
    }

    public async openCoursePlaceSearch() {
        this.coursePlaceSearchOpen = true;
        if (!this.coursePlaceSearchResults.length) await this.searchCoursePlaces(false);
        await this.service.render();
    }

    public async searchCoursePlaces(showLoading: boolean = true) {
        if (showLoading) {
            this.coursePlaceSearching = true;
            await this.service.render();
        }
        let center = this.courseSearchCenter();
        const { code, data } = await wiz.call('search_course_places', {
            lat: center.lat,
            lng: center.lng,
            keyword: this.coursePlaceSearchQuery,
            region: this.courseRegionLabel(),
            limit: 8
        });
        this.coursePlaceSearching = false;
        if (code === 200) this.coursePlaceSearchResults = (data && data.rows) || [];
        await this.service.render();
    }

    public async addCoursePlace(place: any) {
        if (!place) return;
        let placeId = String(place.place_id || place.id || '').replace(/^place-/, '');
        if (!placeId || this.courseBuilderPlaces.some((item: any) => item.placeId === placeId)) {
            this.coursePlaceSearchOpen = false;
            await this.service.render();
            return;
        }

        let next = {
            placeId,
            name: place.name || place.title || '장소',
            lat: this.safeNumber(place.lat || place.latitude),
            lng: this.safeNumber(place.lng || place.longitude),
            order: this.courseBuilderPlaces.length + 1,
            visitTime: this.nextCourseVisitTime(),
            memo: '',
            area: place.area || '',
            address: place.address || '',
            category: place.category || '',
            image: place.image || '',
            manualTime: false
        };

        this.courseBuilderPlaces = [...this.courseBuilderPlaces, next];
        this.normalizeCourseBuilderOrder(true);
        this.applyCourseDraftFromPlaces();
        this.coursePlaceSearchOpen = false;
        if (!this.courseDraft.region) this.courseDraft.region = this.courseRegionLabel();
        if (!this.courseDraft.photo && next.image) this.courseDraft.photo = next.image;
        await this.service.render();
        this.scheduleCourseMapRender();
    }

    public async removeCoursePlace(index: number) {
        if (index < 0 || index >= this.courseBuilderPlaces.length) return;
        this.courseBuilderPlaces.splice(index, 1);
        this.normalizeCourseBuilderOrder(true);
        this.applyCourseDraftFromPlaces();
        await this.service.render();
        this.scheduleCourseMapRender();
    }

    public coursePlaceDragStart(index: number) {
        this.courseDragIndex = index;
    }

    public coursePlaceDragOver(event: any) {
        if (event && event.preventDefault) event.preventDefault();
    }

    public async coursePlaceDrop(index: number) {
        if (this.courseDragIndex < 0 || this.courseDragIndex === index) return;
        let item = this.courseBuilderPlaces.splice(this.courseDragIndex, 1)[0];
        this.courseBuilderPlaces.splice(index, 0, item);
        this.courseDragIndex = -1;
        this.normalizeCourseBuilderOrder(true);
        this.applyCourseDraftFromPlaces();
        await this.service.render();
        this.scheduleCourseMapRender();
    }

    public async updateCourseVisitTime(place: any) {
        if (place) place.manualTime = true;
        this.syncCurrentCourseBuilderDay();
        await this.service.render();
    }

    public async updateCoursePlaceMemo() {
        this.applyCourseDraftFromPlaces();
        await this.service.render();
    }

    public async completePlannerCourseEdit() {
        if (!this.courseComposerPlannerEdit || this.courseAiRebuilding) return;
        this.syncCurrentCourseBuilderDay();
        let emptyDay = this.courseBuilderDays.find((day: any) => !Array.isArray(day.places) || day.places.length === 0);
        if (emptyDay) {
            this.courseBuilderError = `${emptyDay.label || '일정'}에 장소를 1개 이상 남겨주세요.`;
            await this.service.render();
            return;
        }

        let originalDays = this.cloneCourseBuilderDays(this.courseBuilderOriginalDays);
        let editedBuilderDays = this.cloneCourseBuilderDays(this.courseBuilderDays);
        let prompt = this.plannerCourseEditPrompt(originalDays, editedBuilderDays);
        let editedPlannerDays = editedBuilderDays.map((day: any, dayIndex: number) => {
            let stops = (day.places || []).map((place: any, index: number) => ({
                key: place.originalKey || place.placeId || `edited-${dayIndex}-${index}`,
                placeId: place.placeId || '',
                time: place.visitTime || this.plannerTimeForIndex(index),
                timeLocked: !!place.manualTime,
                name: place.name || '장소',
                area: place.area || place.address || this.plannerCourseRegion,
                tag: place.memo || place.category || '추천 방문',
                move: '이동 확인 중',
                image: place.image || this.defaultPlannerImage(place.category || '', index),
                icon: this.plannerIconForCategory(place.category || ''),
                lat: this.safeNumber(place.lat),
                lng: this.safeNumber(place.lng),
                mapLeft: '',
                mapTop: ''
            }));
            stops = this.applyPlannerMapPositions(stops).map((stop: any, index: number) => ({
                ...stop,
                status: index < 2 ? 'active' : 'upcoming'
            }));
            return {
                label: day.label || `${dayIndex + 1}일차`,
                stops
            };
        });

        let activeDay = Math.max(0, Math.min(this.courseBuilderDayIndex, editedPlannerDays.length - 1));
        let history = this.messages
            .filter((message: any) => !message.loading && !message.seed)
            .slice(-12)
            .map((message: any) => ({ role: message.role, text: String(message.text || '') }));
        let summary = editedBuilderDays.map((day: any) => `${day.label} ${(day.places || []).length}곳`).join(', ');
        let requestTime = this.currentChatTimeLabel();
        this.messages.push({
            role: 'user',
            text: `코스 수정 완료: ${summary}. 수정한 일정으로 다시 계산해줘.`,
            time: requestTime
        });
        let reply: any = {
            role: 'assistant',
            text: '수정한 장소와 시간을 확인하고 동선과 이동시간을 다시 계산하고 있어요.',
            time: requestTime,
            loading: true
        };
        this.messages.push(reply);

        this.courseAiRebuilding = true;
        this.isPlannerGenerating = true;
        this.isChatSending = true;
        this.plannerCourseBaseTitle = String(this.courseDraft.title || this.plannerCourseBaseTitle || '내 여행').trim();
        this.plannerCourseRegion = String(this.courseDraft.region || this.plannerCourseRegion).trim();
        this.plannerCourseDays = editedPlannerDays;
        this.plannerCourseReady = true;
        this.applyPlannerCourseDay(activeDay);
        this.plannerRouteSource = 'AI 수정 내용 분석 중';

        this.courseComposerOpen = false;
        this.courseComposerPlannerEdit = false;
        this.courseBuilderMode = '';
        this.courseBuilderStep = 'mode';
        this.coursePlaceSearchOpen = false;
        this.clearCourseGoogleOverlays();
        await this.service.render();
        this.refreshPlannerRouteWithGoogle();
        this.scrollToPlannerPreview();

        try {
            let response: any = await wiz.call('chat_send', {
                prompt,
                history: JSON.stringify(history),
                thread_id: this.activeChatThreadId
            });
            let code = Number(response && response.code ? response.code : 0);
            let data = response && response.data ? response.data : response;
            if (code === 200 && data) {
                reply.text = data.reply || '수정한 코스를 기준으로 동선과 시간을 다시 정리했어요.';
                this.activeChatThreadId = data.thread_id || this.activeChatThreadId;
            } else {
                reply.text = this.responseMessage(data || response, '수정한 일정은 반영했고, 지도 이동시간을 기준으로 코스를 다시 계산했어요.');
            }
        } catch (e) {
            reply.text = '수정한 일정은 반영했어요. AI 응답은 지연됐지만 지도 이동시간을 기준으로 코스를 다시 계산했습니다.';
        }

        reply.loading = false;
        this.courseAiRebuilding = false;
        this.isPlannerGenerating = false;
        this.isChatSending = false;
        this.courseBuilderDays = [];
        this.courseBuilderOriginalDays = [];
        this.courseBuilderPlaces = [];
        await this.service.render();
        this.scrollToLatest();
        this.scrollToPlannerPreview();
        await this.showSaveHint('수정한 코스로 다시 만들었어요.');
    }

    private plannerCourseEditPrompt(originalDays: any[], editedDays: any[]) {
        let changes: string[] = [];
        editedDays.forEach((day: any, dayIndex: number) => {
            let original = originalDays[dayIndex] || { places: [] };
            let beforePlaces = (original.places || []).map((place: any) => `${place.visitTime || ''} ${place.name || ''} ${place.memo || ''}`.trim());
            let afterPlaces = (day.places || []).map((place: any) => `${place.visitTime || ''} ${place.name || ''} ${place.memo || ''}`.trim());
            if (beforePlaces.join('|') !== afterPlaces.join('|')) {
                changes.push(`${day.label}: ${beforePlaces.join(' → ') || '없음'} => ${afterPlaces.join(' → ')}`);
            }
        });
        let schedule = editedDays.map((day: any) => {
            let places = (day.places || []).map((place: any) => {
                let coordinate = this.isFiniteNumber(place.lat) && this.isFiniteNumber(place.lng)
                    ? `${Number(place.lat).toFixed(5)},${Number(place.lng).toFixed(5)}`
                    : '좌표 없음';
                return `- ${place.visitTime || '시간 미정'} ${place.name} (${place.area || place.address || '위치 미정'}, ${coordinate}) / ${place.memo || place.category || '활동 미정'}`;
            }).join('\n');
            return `[${day.label}]\n${places}`;
        }).join('\n');
        return [
            '사용자가 기존 AI 여행 코스를 직접 수정했습니다.',
            `변경점: ${changes.join(' / ') || '장소별 세부 정보 확인'}`,
            schedule,
            '사용자가 선택한 장소와 순서를 우선 유지하세요. 변경된 장소 사이의 교통수단과 이동시간을 다시 확인하고, 수동으로 바꾼 방문시간은 가능한 한 유지해서 코스를 짧게 다시 설명해주세요.'
        ].join('\n').slice(0, 1950);
    }

    public async focusCoursePlaceSearch() {
        if (this.courseBuilderStep !== 'places') {
            if (!this.courseBuilderMode) this.courseBuilderMode = 'manual';
            this.courseBuilderStep = 'places';
            await this.service.render();
            this.scheduleCourseMapRender();
        }
        this.coursePlaceSearchOpen = true;
        await this.service.render();
        if (typeof document === 'undefined') return;
        let input: any = document.querySelector('.course-place-search-input');
        if (input && input.focus) input.focus();
    }

    public courseDraftPlaces() {
        if (this.courseBuilderPlaces.length > 0) {
            return this.courseBuilderPlaces.map((place: any) => place.name).slice(0, 8);
        }
        return this.splitList(this.courseDraft.places).slice(0, 8);
    }

    public courseRegionLabel() {
        let counts: any = {};
        this.courseBuilderPlaces.forEach((place: any) => {
            let area = String(place.area || place.address || '').trim();
            if (!area) return;
            let label = area.split(/\s+/).slice(0, 2).join(' ');
            if (!label) return;
            counts[label] = (counts[label] || 0) + 1;
        });
        let best = Object.keys(counts).sort((a: string, b: string) => counts[b] - counts[a])[0];
        return best || String(this.courseDraft.region || this.selectedFilters.location || '서울 성수동').trim();
    }

    public courseWalkBadge() {
        let minutes = this.courseWalkingMinutes();
        if (this.courseBuilderPlaces.length < 2) return '도보 총 0분';
        return `도보 총 ${minutes}분${this.hasFullCourseCoordinates() ? '' : ' 예상'}`;
    }

    public courseSegmentDistanceLabel(index: number) {
        if (index < 0 || index >= this.courseBuilderPlaces.length - 1) return '';
        let prev = this.courseBuilderPlaces[index];
        let next = this.courseBuilderPlaces[index + 1];
        let distance = this.distanceKm(prev.lat, prev.lng, next.lat, next.lng);
        if (distance === null) return `${index + 1} → ${index + 2} · 거리 정보 없음`;
        let distanceLabel = distance < 1
            ? `${Math.max(1, Math.round(distance * 1000))}m`
            : `${distance.toFixed(distance < 10 ? 1 : 0)}km`;
        let minutes = Math.max(2, Math.round((distance / 4.2) * 60));
        return `${index + 1} → ${index + 2} · 약 ${distanceLabel} · 도보 ${minutes}분`;
    }

    public courseTimelineMapSpots() {
        let places = this.courseBuilderPlaces;
        if (places.length === 0) return [];
        let coordinatePlaces = places.filter((place: any) => this.isFiniteNumber(place.lat) && this.isFiniteNumber(place.lng));
        if (coordinatePlaces.length === places.length) {
            let lats = places.map((place: any) => Number(place.lat));
            let lngs = places.map((place: any) => Number(place.lng));
            let minLat = Math.min(...lats);
            let maxLat = Math.max(...lats);
            let minLng = Math.min(...lngs);
            let maxLng = Math.max(...lngs);
            let latRange = Math.max(0.0001, maxLat - minLat);
            let lngRange = Math.max(0.0001, maxLng - minLng);
            return places.map((place: any) => ({
                name: place.name,
                x: places.length === 1 ? 50 : 14 + ((Number(place.lng) - minLng) / lngRange * 72),
                y: places.length === 1 ? 50 : 82 - ((Number(place.lat) - minLat) / latRange * 64)
            }));
        }
        return places.map((place: any, index: number) => this.fallbackCourseDraftSpot(place.name, index, places.length));
    }

    public courseTimelineRoutePoints() {
        return this.courseTimelineMapSpots().map((spot: any) => `${spot.x},${spot.y}`).join(' ');
    }

    public courseDraftMapLabel() {
        return this.courseRegionLabel();
    }

    public courseDraftMapSpots() {
        return this.courseTimelineMapSpots();
    }

    public courseDraftRoutePoints() {
        return this.courseTimelineRoutePoints();
    }

    public companionTypeLabel() {
        let labels: any = { couple: '연인', friend: '친구', solo: '혼자' };
        return labels[this.courseDraft.companionType] || '친구';
    }

    public visibilityLabel() {
        return this.courseDraft.isPublic ? '커뮤니티에 게시' : '나만 보기';
    }

    public async setCourseCompanionType(type: string) {
        if (['couple', 'friend', 'solo'].indexOf(type) < 0) return;
        this.courseDraft.companionType = type;
        await this.service.render();
    }

    public async toggleCourseVisibility() {
        this.courseDraft.isPublic = !this.courseDraft.isPublic;
        await this.service.render();
    }

    private courseBuilderPayload() {
        let region = String(this.courseDraft.region || this.courseRegionLabel() || '국내').trim();
        let title = String(this.courseDraft.title || '').trim();
        let description = String(this.courseDraft.description || '').trim();
        let places = this.courseBuilderPlaces.map((place: any, index: number) => ({
            place_id: place.placeId,
            order_index: index + 1,
            visit_time: place.visitTime || '',
            memo: place.memo || ''
        }));

        return {
            title,
            region,
            category: String(this.courseDraft.category || '여행').trim(),
            description: description || this.courseBuilderPlaces.map((place: any) => place.name).join(', '),
            cover_image: String(this.courseDraft.photo || '').trim(),
            image: String(this.courseDraft.photo || '').trim(),
            duration_type: 'hours',
            duration_value: String(Math.max(1, Math.ceil((this.courseWalkingMinutes() + this.courseBuilderPlaces.length * 55) / 60))),
            companion_type: String(this.courseDraft.companionType || 'friend'),
            is_public: !!this.courseDraft.isPublic,
            is_featured: !!this.courseDraft.isPublic,
            places,
            tags: this.uniqueTags(['여행', region, title, this.companionTypeLabel(), ...this.courseDraftPlaces()])
        };
    }

    private courseRowToCard(row: any, fallback: any) {
        row = row || {};
        fallback = fallback || {};
        let id = row.id || `draft-course-${Date.now()}`;
        let region = row.region || fallback.region || this.courseRegionLabel();
        let duration = row.duration || `${fallback.duration_value || '4'}시간`;
        let places = Array.isArray(row.places) && row.places.length > 0
            ? row.places
            : (Array.isArray(fallback.places) ? fallback.places : []);
        return {
            id,
            title: row.title || fallback.title,
            location: region,
            summary: row.description || fallback.description || '직접 만든 여행 코스입니다.',
            duration,
            distance: this.courseWalkBadge(),
            category: row.category || fallback.category || '여행',
            icon: 'fa-route',
            tone: 'tone-rose',
            image: row.cover_image || row.image || fallback.cover_image || '',
            cover_image: row.cover_image || row.image || fallback.cover_image || '',
            saved: true,
            mine: true,
            places,
            route: row.route || fallback.route || {},
            tags: this.uniqueTags(['여행', region, row.title || fallback.title, duration, ...(row.tags || fallback.tags || [])])
        };
    }

    private ensureCourseDraftMeta() {
        if (!String(this.courseDraft.region || '').trim()) this.courseDraft.region = this.courseRegionLabel();
        if (!String(this.courseDraft.category || '').trim()) this.courseDraft.category = '여행';
        if (!String(this.courseDraft.companionType || '').trim()) this.courseDraft.companionType = 'friend';
        if (typeof this.courseDraft.isPublic === 'undefined') this.courseDraft.isPublic = true;
        if (!String(this.courseDraft.photo || '').trim()) {
            let cover = this.courseBuilderPlaces.find((place: any) => !!place.image);
            if (cover) this.courseDraft.photo = cover.image;
        }
    }

    private normalizeCourseBuilderOrder(recalculateTimes: boolean = false) {
        this.courseBuilderPlaces = this.courseBuilderPlaces.map((place: any, index: number) => {
            place.order = index + 1;
            if (recalculateTimes && !place.manualTime) place.visitTime = this.visitTimeForIndex(index);
            return place;
        });
    }

    private applyCourseDraftFromPlaces() {
        if (this.courseComposerPlannerEdit) {
            this.syncCurrentCourseBuilderDay();
            this.courseDraft.places = this.courseBuilderDays
                .reduce((items: string[], day: any) => items.concat((day.places || []).map((place: any) => place.name)), [])
                .join('\n');
            return;
        }
        this.courseDraft.places = this.courseBuilderPlaces.map((place: any) => place.name).join('\n');
        if (this.courseBuilderPlaces.length > 0) this.courseDraft.region = this.courseRegionLabel();
    }

    private nextCourseVisitTime() {
        return this.visitTimeForIndex(this.courseBuilderPlaces.length);
    }

    private visitTimeForIndex(index: number) {
        let start = 14 * 60;
        if (index > 0) {
            let previous = this.courseBuilderPlaces[index - 1];
            start = this.minutesFromTime(previous && previous.visitTime ? previous.visitTime : this.visitTimeForIndex(index - 1)) + 90;
        }
        return this.timeFromMinutes(start);
    }

    private minutesFromTime(value: string) {
        let parts = String(value || '14:00').split(':');
        let hours = Number(parts[0] || 14);
        let minutes = Number(parts[1] || 0);
        if (!isFinite(hours) || !isFinite(minutes)) return 14 * 60;
        return (hours * 60) + minutes;
    }

    private timeFromMinutes(value: number) {
        value = ((Math.round(value) % 1440) + 1440) % 1440;
        let hours = Math.floor(value / 60);
        let minutes = value % 60;
        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
    }

    private courseWalkingMinutes() {
        let total = 0;
        for (let i = 1; i < this.courseBuilderPlaces.length; i++) {
            let prev = this.courseBuilderPlaces[i - 1];
            let current = this.courseBuilderPlaces[i];
            let distance = this.distanceKm(prev.lat, prev.lng, current.lat, current.lng);
            total += distance === null ? 12 : Math.max(2, Math.round((distance / 4.2) * 60));
        }
        return Math.round(total);
    }

    private hasFullCourseCoordinates() {
        return this.courseBuilderPlaces.every((place: any) => this.isFiniteNumber(place.lat) && this.isFiniteNumber(place.lng));
    }

    private distanceKm(lat1: any, lng1: any, lat2: any, lng2: any) {
        lat1 = this.safeNumber(lat1);
        lng1 = this.safeNumber(lng1);
        lat2 = this.safeNumber(lat2);
        lng2 = this.safeNumber(lng2);
        if ([lat1, lng1, lat2, lng2].some((value: any) => value === null)) return null;
        let radius = 6371;
        let dlat = (lat2 - lat1) * Math.PI / 180;
        let dlng = (lng2 - lng1) * Math.PI / 180;
        let a = Math.sin(dlat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dlng / 2) ** 2;
        return radius * (2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
    }

    private safeNumber(value: any) {
        if (value === null || typeof value === 'undefined' || value === '') return null;
        let number = Number(value);
        return isFinite(number) ? number : null;
    }

    private isFiniteNumber(value: any) {
        return value !== null && typeof value !== 'undefined' && isFinite(Number(value));
    }

    private courseSearchCenter() {
        let first = this.courseBuilderPlaces.find((place: any) => this.isFiniteNumber(place.lat) && this.isFiniteNumber(place.lng));
        if (first) return { lat: first.lat, lng: first.lng };
        let regionCenter = this.courseRegionCenter();
        if (regionCenter) return regionCenter;
        let center = this.currentMapCenter();
        return { lat: center.lat || 37.5446, lng: center.lng || 127.0557 };
    }

    private courseRegionCenter() {
        let region = String(this.courseDraft.region || '').trim();
        if (!region) return null;
        let normalized = region.toLowerCase();
        let initials = this.koreanInitials(normalized);
        let useInitialSearch = this.isKoreanInitialQuery(normalized);
        let match = this.courseKnownRegions().find((option: any) => {
            let label = String(option.label || '').toLowerCase();
            let area = String(option.area || '').toLowerCase();
            return label.indexOf(normalized) > -1
                || area.indexOf(normalized) > -1
                || normalized.indexOf(label) > -1
                || (useInitialSearch && this.koreanInitials(`${option.label} ${option.area}`).indexOf(initials) > -1);
        });
        return match ? { lat: match.lat, lng: match.lng } : null;
    }

    public async requestCompanion(post: any) {
        if (!post) return;
        if (!this.isConfirmedCompanionPost(post)) {
            await this.showSaveHint('확정된 코스가 연결된 모집에만 신청할 수 있어요.');
            return;
        }
        if (!this.isLoggedIn()) {
            await this.openAuthModal('login');
            return;
        }
        if (post.status === 'matched') {
            await this.openCompanionPreparationRoom(post);
            return;
        }
        if (this.currentCompanionApplication(post)) {
            await this.showSaveHint('신청 완료 상태입니다. 작성자 수락을 기다려주세요.');
            return;
        }

        if (!this.hasCompletedTravelResume()) {
            await this.promptTravelResumeCompletion();
            return;
        }

        let application = this.createCompanionApplication(post);
        if (!Array.isArray(post.applications)) post.applications = [];
        post.applications = [
            application,
            ...post.applications.filter((item: any) => item && item.applicantKey !== application.applicantKey)
        ];
        post.status = 'requested';
        post.applicants = Math.max(Number(post.applicants || 0) + 1, post.applications.length);
        await this.showSaveHint('여행 이력서를 제출하고 동행 신청을 보냈어요.');
    }

    public async acceptCompanionApplication(post: any, application?: any) {
        if (!post || post.status !== 'requested') return;
        if (!application && Array.isArray(post.applications)) application = post.applications[0];
        if (application) {
            application.status = 'accepted';
            post.selectedApplicationId = application.id;
            if (Array.isArray(post.applications)) {
                post.applications.forEach((item: any) => {
                    if (item && item.id !== application.id && item.status === 'pending') item.status = 'declined';
                });
            }
        }
        post.status = 'matched';
        await this.openCompanionPreparationRoom(post, application);
        await this.showSaveHint('신청자를 선택하고 동행 준비방을 만들었어요.');
    }

    public async toggleCompanionSave(post: any, event?: any) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        if (!post) return;
        post.saved = !post.saved;
        await this.service.render();
    }

    public companionActionLabel(post: any) {
        if (!post) return '신청';
        if (post.status === 'matched') return '준비방 열기';
        if (this.currentCompanionApplication(post)) return '수락 대기';
        return '이력서로 신청';
    }

    public isCompanionActionDisabled(post: any) {
        return !!this.currentCompanionApplication(post) && post.status !== 'matched';
    }

    public companionStatusLabel(post: any) {
        if (!post) return '';
        if (post.status === 'matched') return '준비방 개설';
        if (post.status === 'requested') return '신청 검토 중';
        return '모집 중';
    }

    public companionApplications(post: any) {
        if (!post || !Array.isArray(post.applications)) return [];
        return post.applications;
    }

    public currentCompanionApplication(post: any) {
        if (!this.isLoggedIn()) return null;
        let applicantKey = this.currentCompanionApplicantKey();
        return this.companionApplications(post).find((application: any) => {
            return application && application.applicantKey === applicantKey && application.status !== 'declined';
        }) || null;
    }

    public companionApplicantCount(post: any) {
        return Math.max(Number(post && post.applicants ? post.applicants : 0), this.companionApplications(post).length);
    }

    public companionApplicationPhoto(application: any) {
        let resume = this.companionApplicationResume(application);
        return String(resume.photo || '').trim();
    }

    public companionApplicationName(application: any) {
        let resume = this.companionApplicationResume(application);
        return String(application && application.applicantNickname || resume.nickname || resume.name || '신청자').trim();
    }

    public companionApplicationMeta(application: any) {
        let resume = this.companionApplicationResume(application);
        let uses = this.normalizePositiveNumber(resume.companionUses);
        return [
            String(resume.region || '').trim(),
            `${uses}회 동행`,
            resume.reviewScore ? `후기 ${Number(resume.reviewScore).toFixed(1)}` : ''
        ].filter((item: string) => !!item).join(' · ');
    }

    public companionApplicationIntro(application: any) {
        let resume = this.companionApplicationResume(application);
        return String(resume.intro || '').trim();
    }

    public companionApplicationExperience(application: any) {
        let resume = this.companionApplicationResume(application);
        return String(resume.travelExperience || '').trim();
    }

    public companionApplicationStatusLabel(application: any) {
        if (application && application.status === 'accepted') return '선택됨';
        if (application && application.status === 'declined') return '마감';
        return '검토 중';
    }

    public isConfirmedCompanionPost(post: any) {
        return !!post && !!String(post.courseId || '').trim() && post.courseConfirmed === true;
    }

    public companionRouteStops(post: any) {
        if (!post) return [];
        let stops = Array.isArray(post.routeStops) ? post.routeStops : this.splitList(post.routeStops || '');
        return stops.map((stop: any) => String(stop && stop.name ? stop.name : stop || '').trim()).filter((stop: string) => !!stop);
    }

    public companionRouteText(post: any) {
        let stops = this.companionRouteStops(post);
        return stops.length > 0 ? stops.join(' → ') : String(post && post.route ? post.route : '동선 확인 필요');
    }

    public companionMoodTags(post: any) {
        return this.splitList(post && post.moodTags ? post.moodTags : '').slice(0, 4);
    }

    public companionFlexibility(post: any) {
        return this.splitList(post && post.flexibility ? post.flexibility : '').slice(0, 3);
    }

    public companionCardFacts(post: any) {
        return [
            { icon: 'fa-calendar-day', label: '날짜와 시간', value: [post && post.date, post && post.time].filter((value: any) => !!value).join(' · ') || '일정 협의' },
            { icon: 'fa-won-sign', label: '예상 비용', value: String(post && post.estimatedCost ? post.estimatedCost : '비용 협의') },
            { icon: 'fa-person-walking', label: '여행 속도', value: this.travelPaceLabel(post && post.pace) || '보통' },
            { icon: 'fa-user-group', label: '모집 인원', value: `${Math.max(1, Number(post && post.capacity ? post.capacity : 1))}명 · 신청 ${this.companionApplicantCount(post)}명` }
        ];
    }

    public companionFitCriteria(post: any) {
        let interests = this.splitList(post && post.interestTags ? post.interestTags : '').slice(0, 3).join(' · ');
        return [
            { icon: 'fa-calendar-check', label: '날짜', value: `${post && post.date ? post.date : '협의'} 가능` },
            { icon: 'fa-person-walking', label: '속도', value: this.travelPaceLabel(post && post.pace) || '보통' },
            { icon: 'fa-wallet', label: '예산', value: this.budgetStyleLabel(post && post.budgetStyle) || '협의' },
            { icon: 'fa-location-dot', label: '관심 장소', value: interests || '코스 장소' },
            { icon: 'fa-ban-smoking', label: '흡연 여부·음주 성향', value: `${this.smokingStyleLabel(post && post.smoking)} · ${this.drinkingStyleLabel(post && post.drinking)}` },
            { icon: 'fa-star', label: '이력·후기', value: String(post && post.hostHistory ? post.hostHistory : '후기 확인') },
            { icon: 'fa-shield-halved', label: '본인 인증', value: post && post.verificationRequired ? '인증 완료자만' : '선택' }
        ];
    }

    public companionApplicationFitItems(post: any, application: any) {
        let resume = this.companionApplicationResume(application);
        let postInterests = this.splitList(post && post.interestTags ? post.interestTags : '').map((value: string) => value.toLowerCase());
        let resumeInterests = this.splitList(resume.interests || '').map((value: string) => value.toLowerCase());
        let overlap = resumeInterests.filter((value: string) => {
            return postInterests.some((target: string) => target.indexOf(value) > -1 || value.indexOf(target) > -1);
        });
        let smokingMatched = !post || !post.smoking || String(resume.smoking || '') === String(post.smoking || '');
        let drinkingMatched = !post || !post.drinking || String(resume.drinking || '') === String(post.drinking || '');
        let historyMatched = this.normalizePositiveNumber(resume.companionUses) > 0 || String(resume.travelExperience || '').trim().length > 20;
        return [
            { label: '날짜 겹침', value: resume.availabilityConfirmed === false ? '재확인' : '가능', matched: resume.availabilityConfirmed !== false },
            { label: '관심 장소', value: overlap.length > 0 ? `${overlap.length}곳 겹침` : '겹침 없음', matched: overlap.length > 0 },
            { label: '흡연 여부·음주 성향', value: smokingMatched && drinkingMatched ? '조건 일치' : '조율 필요', matched: smokingMatched && drinkingMatched },
            { label: '여행 이력·후기', value: historyMatched ? `${this.normalizePositiveNumber(resume.companionUses)}회 · ${resume.reviewScore ? Number(resume.reviewScore).toFixed(1) : '후기 확인'}` : '첫 동행', matched: historyMatched },
            { label: '본인 인증', value: resume.identityVerified ? '완료' : '미완료', matched: !!resume.identityVerified }
        ];
    }

    public companionApplicationFitScore(post: any, application: any) {
        let items = this.companionApplicationFitItems(post, application);
        let matched = items.filter((item: any) => item.matched).length;
        return Math.round((matched / Math.max(1, items.length)) * 100);
    }

    public async openCompanionPreparationRoom(post: any, application?: any) {
        if (!post || post.status !== 'matched') return;
        let chat = this.ensureDirectChatForCompanion(post, application);
        if (!chat) return;
        this.activeTab = 'chat';
        this.chatContentTab = 'dm';
        this.activeDirectChatId = chat.id;
        this.directRoomOpen = true;
        this.directActionMenuOpen = false;
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.service.render();
        this.resetChatContentScroll();
    }

    public async toggleCompanionPackingItem(chat: any, item: any) {
        if (!chat || !chat.preparation || !item) return;
        item.done = !item.done;
        await this.service.render();
    }

    public async toggleCompanionPreparationRoom(chat: any) {
        if (!chat || !chat.preparation) return;
        chat.preparation.collapsed = !chat.preparation.collapsed;
        await this.service.render();
        this.scrollDirectMessages();
    }

    public async openCompanionTimedMap() {
        await this.openInstantCompanion();
    }

    public travelPaceLabel(value: any) {
        let labels: any = { slow: '여유롭게', balanced: '보통', fast: '빠르게' };
        return labels[String(value || '')] || '';
    }

    public budgetStyleLabel(value: any) {
        let labels: any = { low: '알뜰형', medium: '균형형', high: '경험 우선' };
        return labels[String(value || '')] || '';
    }

    public smokingStyleLabel(value: any) {
        let labels: any = { non: '비흡연', smoking: '흡연', flexible: '상관없음' };
        return labels[String(value || '')] || '협의';
    }

    public drinkingStyleLabel(value: any) {
        let labels: any = { none: '음주 안 함', light: '가볍게', social: '즐기는 편', flexible: '상관없음' };
        return labels[String(value || '')] || '협의';
    }

    public latestCourses() {
        return this.courses.filter((course: any) => this.matchesCourse(course)).slice(0, 5);
    }

    public savedPlaces() {
        return this.recentPlaces;
    }

    public filteredSavedPlaces() {
        let places = this.savedPlaces();
        if (this.savedPlaceType === 'all') return places;
        return places.filter((place: any) => this.savedPlaceTypeKey(place) === this.savedPlaceType);
    }

    public savedPlaceFilterCount(key: string) {
        if (key === 'all') return this.savedPlaces().length;
        return this.savedPlaces().filter((place: any) => this.savedPlaceTypeKey(place) === key).length;
    }

    public async setSavedPlaceType(key: string) {
        if (!this.savedPlaceFilters.some((filter: any) => filter.key === key)) return;
        this.savedPlaceType = key;
        await this.service.render();
    }

    public activeSavedPlaceTypeLabel() {
        let filter = this.savedPlaceFilters.find((item: any) => item.key === this.savedPlaceType);
        return filter ? filter.label : '전체';
    }

    public savedPlaceEmptyText() {
        if (this.savedPlaceType === 'all') return '저장한 장소가 없습니다.';
        return `저장된 ${this.activeSavedPlaceTypeLabel()} 장소가 없습니다.`;
    }

    public savedPlaceKindLabel(place: any) {
        let filter = this.savedPlaceFilters.find((item: any) => item.key === this.savedPlaceTypeKey(place));
        return filter ? filter.label : (place && place.kind ? place.kind : '장소');
    }

    private savedPlaceTypeKey(place: any) {
        let raw = [
            place && place.category,
            place && place.kind,
            place && place.name,
            place && place.description
        ].join(' ').toLowerCase();

        if (raw.indexOf('cafe') > -1 || raw.indexOf('카페') > -1 || raw.indexOf('커피') > -1) return 'cafe';
        if (raw.indexOf('stay') > -1 || raw.indexOf('hotel') > -1 || raw.indexOf('숙소') > -1 || raw.indexOf('호텔') > -1 || raw.indexOf('스테이') > -1) return 'stay';
        if (raw.indexOf('food') > -1 || raw.indexOf('맛집') > -1 || raw.indexOf('식당') > -1 || raw.indexOf('미식') > -1) return 'food';
        if (raw.indexOf('walk') > -1 || raw.indexOf('산책') > -1 || raw.indexOf('숲') > -1) return 'walk';
        if (raw.indexOf('drive') > -1 || raw.indexOf('드라이브') > -1 || raw.indexOf('도로') > -1) return 'drive';
        return 'landmark';
    }

    private executionCategoryIcon(category: string) {
        let icons: any = {
            cafe: 'fa-mug-saucer',
            food: 'fa-utensils',
            walk: 'fa-person-walking',
            stay: 'fa-bed',
            shopping: 'fa-bag-shopping',
            landmark: 'fa-location-dot',
            drive: 'fa-car-side'
        };
        return icons[category] || 'fa-location-dot';
    }

    private executionPhotoClass(category: string) {
        if (category === 'cafe') return 'photo-cafe';
        if (category === 'food') return 'photo-food';
        if (category === 'walk') return 'photo-walk';
        return 'photo-landmark';
    }

    public savedCompanionPosts() {
        return this.companionPosts.filter((post: any) => {
            return this.isConfirmedCompanionPost(post) && (!!post.saved || post.status === 'matched');
        });
    }

    public async setSavedContentTab(tab: string) {
        if (['courses', 'places', 'companions'].indexOf(tab) < 0) return;
        this.savedContentTab = tab;
        await this.service.render();
    }

    public homeRegionLabel() {
        return this.selectedFilters.location || '모든 지역';
    }

    public isHomeRegionActive(region: any) {
        return this.selectedFilters.location === region.value;
    }

    public async selectHomeRegion(region: any) {
        let value = region && typeof region.value !== 'undefined' ? region.value : '';
        this.selectedFilters.location = value;
        this.activeFilterKey = '';
        this.filterOverviewOpen = false;
        this.syncLocationRegion();
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.loadFilterPlaces();
        await this.service.render();
    }

    public async clearHomeRegionFilter() {
        this.resetHomeFiltersToRoot();
    }

    public resetHomeFiltersToRoot() {
        this.selectedFilters = {
            companion: '',
            schedule: '',
            location: ''
        };
        this.scheduleRange = { start: '', end: '' };
        this.draftScheduleRange = { start: '', end: '' };
        this.query = '';
        this.selectedKeyword = '여행';
        this.activeFilterKey = '';
        this.filterOverviewOpen = false;
        this.travelMode = 'walk';
        this.selectedMoveFilter = '';
        this.placeCourses = [];
        this.placeThemeSections = [];
        this.activePlaceThemeKey = '';
        this.clearStoredAccessState();
        this.service.href('/');
    }

    public filteredCompanionPosts() {
        return this.companionPosts.filter((post: any) => {
            return this.isConfirmedCompanionPost(post) && this.matchesSelectedLocation(post);
        });
    }

    public filteredReviewPosts() {
        return this.reviewPosts.filter((review: any) => this.matchesSelectedLocation(review));
    }

    public async selectSuggestion(value: string) {
        if (this.isChatSending) return;
        this.draft = value;
        await this.send();
    }

    public canSendChat() {
        return !this.isChatSending && String(this.draft || '').trim().length > 0;
    }

    public async send() {
        if (this.isChatSending) return;

        let prompt = String(this.draft || '').trim();
        if (!prompt) return;

        this.draft = '';
        await this.sendChatPrompt(prompt);
    }

    public async handleEnter(event: any) {
        if (event.shiftKey) return;
        event.preventDefault();
        await this.send();
    }

    public formatMessage(value: any) {
        let escaped = String(value || '').replace(/[&<>"']/g, (char: string) => {
            let map: any = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            };
            return map[char] || char;
        });
        return escaped
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }

    public async toggleChatDrawer() {
        this.chatDrawerOpen = !this.chatDrawerOpen;
        if (this.chatDrawerOpen) await this.loadChatThreads(false);
        await this.service.render();
    }

    public async startNewChat() {
        this.activeChatThreadId = '';
        this.draft = '';
        this.messages = [this.defaultChatMessage()];
        this.resetPlannerPreview();
        this.resetPlannerConversationState();
        this.chatDrawerOpen = false;
        await this.service.render();
    }

    public async openChatThread(thread: any) {
        if (!thread || !thread.id || !this.isLoggedIn()) return;

        this.chatHistoryLoading = true;
        await this.service.render();

        const { code, data } = await wiz.call('chat_thread', {
            thread_id: thread.id
        });

        this.chatHistoryLoading = false;
        if (code === 200 && data && data.thread) {
            this.activeChatThreadId = data.thread.id || '';
            this.messages = [
                this.defaultChatMessage(),
                ...(data.thread.messages || [])
            ];
            this.resetPlannerPreview();
            this.applyPlannerContract({
                stage: data.thread.travel_state && data.thread.travel_state.conversation_stage,
                travel_state: data.thread.travel_state || {},
                itinerary_draft: data.thread.itinerary_draft || {},
                missing_slots: [],
                action: 'answer_only',
                warnings: [],
                failure_stage: ''
            });
            this.chatDrawerOpen = false;
            await this.service.render();
            this.scrollToLatest();
            return;
        }

        if (code === 401 && this.service.auth) this.service.auth.clearLocalSession();
        await this.service.render();
    }

    public async toggleKeyword(tag: string) {
        this.selectedKeyword = this.selectedKeyword === tag ? '' : tag;
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.loadFilterPlaces();
        await this.service.render();
    }

    public async openFilterOverview() {
        this.activeFilterKey = '';
        this.filterOverviewOpen = !this.filterOverviewOpen;
        await this.service.render();
    }

    public async closeFilterOverview() {
        this.filterOverviewOpen = false;
        await this.service.render();
    }

    public shouldShowFilterBack(filter: any) {
        return !!filter && ['location', 'companion'].indexOf(filter.key) > -1;
    }

    public async backToFilterOverview() {
        this.activeFilterKey = '';
        this.filterOverviewOpen = true;
        await this.service.render();
    }

    public async openFilterSheetFromOverview(key: string) {
        this.filterOverviewOpen = false;
        this.activeFilterKey = key;
        if (key === 'location') this.syncLocationRegion();
        if (key === 'schedule') this.buildCalendar();
        await this.service.render();
    }

    public async selectMoveFilter(mode: string) {
        if (!this.isSupportedMoveFilter(mode)) return;

        this.selectedMoveFilter = this.selectedMoveFilter === mode && mode ? '' : mode;
        if (this.selectedMoveFilter && this.isSupportedTravelMode(this.selectedMoveFilter)) {
            this.travelMode = this.selectedMoveFilter;
        }

        this.persistAccessState();
        this.replaceAccessUrl();
        await this.loadFilterPlaces();
        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    public async openFilterSheet(key: string) {
        if (this.activeFilterKey === key) {
            this.activeFilterKey = '';
            await this.service.render();
            return;
        }

        this.filterOverviewOpen = false;
        this.activeFilterKey = key;
        if (key === 'location') this.syncLocationRegion();
        if (key === 'schedule') this.buildCalendar();
        await this.service.render();
    }

    public async closeFilterSheet() {
        this.activeFilterKey = '';
        await this.service.render();
    }

    public async selectCondition(key: string, value: string) {
        this.selectedFilters[key] = this.selectedFilters[key] === value ? '' : value;
        this.logFilterEvent(key, this.selectedFilters[key]);
        this.activeFilterKey = '';
        this.filterOverviewOpen = false;
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.loadFilterPlaces();
        await this.service.render();
    }

    public hasActiveFilters() {
        return ['companion', 'schedule', 'location'].some((key: string) => !!this.selectedFilters[key]) || !!this.selectedMoveFilter;
    }

    public async clearAllFilters() {
        if (this.activeTab === 'home') {
            this.resetHomeFiltersToRoot();
            return;
        }

        this.selectedFilters = {
            companion: '',
            schedule: '',
            location: ''
        };
        this.scheduleRange = { start: '', end: '' };
        this.draftScheduleRange = { start: '', end: '' };
        this.activeFilterKey = '';
        this.filterOverviewOpen = false;
        this.travelMode = 'walk';
        this.selectedMoveFilter = '';
        this.placeCourses = [];
        this.placeThemeSections = [];
        this.activePlaceThemeKey = '';
        this.syncLocationRegion();
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.loadFilterPlaces();
        await this.service.render();
    }

    public async clearSearch() {
        this.query = '';
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.loadFilterPlaces();
        await this.service.render();
    }

    public async handleSearchInput() {
        this.persistAccessState();
        this.replaceAccessUrl();
        this.scheduleFilterPlaceLoad();
        await this.service.render();
    }

    public markCourseImageBroken(course: any) {
        if (!course) return;
        course.image_broken = true;
    }

    public async selectPlaceTheme(theme: any) {
        if (!theme || !theme.key) return;
        this.activePlaceThemeKey = theme.key;
        await this.service.render();
    }

    public visiblePlaceThemes() {
        return this.placeThemeSections.filter((theme: any) => this.filteredThemeCourses(theme).length > 0);
    }

    public activePlaceTheme() {
        let themes = this.visiblePlaceThemes();
        if (themes.length === 0) return null;
        return themes.find((theme: any) => theme.key === this.activePlaceThemeKey) || themes[0];
    }

    public isPlaceThemeActive(theme: any) {
        let active = this.activePlaceTheme();
        return !!active && !!theme && active.key === theme.key;
    }

    public themeFilteredCount(theme: any) {
        return this.filteredThemeCourses(theme).length;
    }

    public filteredThemePlaceCourses() {
        let theme = this.activePlaceTheme();
        return theme ? this.filteredThemeCourses(theme) : [];
    }

    public activePlaceThemeCountLabel() {
        if (this.placeCoursesLoading) return '로딩';
        return `${this.filteredThemePlaceCourses().length}개`;
    }

    public async setZenlyLayerTab(tab: string) {
        if (['density', 'signals'].indexOf(tab) < 0) return;
        this.zenlyLayerTab = tab;
        this.selectedPresencePlaceId = '';
        this.selectedZenlySignalId = '';
        this.selectedZenlyFallbackCard = null;
        await this.service.render();
        this.bindZenlyMarkerDelegation();
        if (tab === 'density') await this.loadZenlyHeatmap(false);
        if (tab === 'signals') await this.loadZenlySignals(false);
    }

    public zenlyPresencePlaces() {
        let places = this.zenlyHeatmap && Array.isArray(this.zenlyHeatmap.places) ? this.zenlyHeatmap.places : [];
        return places;
    }

    public selectedPresencePlace() {
        let places = this.zenlyPresencePlaces();
        return places.find((place: any) => place.place_id === this.selectedPresencePlaceId) || places[0] || {};
    }

    public async selectPresencePlace(place: any, event?: any) {
        if (event) event.stopPropagation();
        if (event && ['mousedown', 'touchstart'].indexOf(event.type) > -1 && event.preventDefault) event.preventDefault();
        if (!place) return;
        this.selectedPresencePlaceId = place.place_id;
        this.selectedZenlySignalId = '';
        this.selectedZenlyFallbackCard = {
            id: place.place_id,
            name: place.name || '장소',
            category: place.category || '장소',
            count: Math.max(0, Number(place.count || 0))
        };
        await this.service.render();
        this.bindZenlyMarkerDelegation();
        this.loadPresenceHourly(place.place_id, false);
    }

    public presenceBarHeight(count: any) {
        let max = Math.max(1, ...this.zenlyPresenceHourly.map((item: any) => Number(item.count || 0)));
        let value = Math.max(0, Number(count || 0));
        return `${Math.max(12, Math.round((value / max) * 58))}px`;
    }

    public selectedZenlySignal() {
        return this.zenlySignals.find((signal: any) => signal.id === this.selectedZenlySignalId) || this.zenlySignals[0] || {};
    }

    public isZenlyPresenceSelected(place: any) {
        return !!place && !!this.selectedPresencePlaceId && String(this.selectedPresencePlaceId) === String(place.place_id);
    }

    public isZenlySignalSelected(signal: any) {
        return !!signal && !!this.selectedZenlySignalId && String(this.selectedZenlySignalId) === String(signal.id);
    }

    public async selectZenlySignal(signal: any, event?: any) {
        if (event) event.stopPropagation();
        if (event && ['mousedown', 'touchstart'].indexOf(event.type) > -1 && event.preventDefault) event.preventDefault();
        if (!signal) return;
        this.selectedZenlySignalId = signal.id;
        this.selectedPresencePlaceId = '';
        this.selectedZenlyFallbackCard = {
            id: signal.id,
            name: signal.name || signal.message || '동행 신호',
            category: signal.category || '신호',
            count: Math.max(0, Number(signal.count || 0))
        };
        await this.service.render();
        this.bindZenlyMarkerDelegation();
    }

    public async closeZenlyMiniCard(event?: any) {
        let target = event && event.target ? event.target : null;
        if (target && target.closest && target.closest('.zenly-pin-marker, .zenly-summary-bar')) return;
        if (!this.selectedPresencePlaceId && !this.selectedZenlySignalId) return;
        this.selectedPresencePlaceId = '';
        this.selectedZenlySignalId = '';
        this.selectedZenlyFallbackCard = null;
        await this.service.render();
        this.bindZenlyMarkerDelegation();
    }

    public async handleZenlyMapPointer(event: any) {
        let target = event && event.target ? event.target : null;
        let marker = target && target.closest ? target.closest('.zenly-pin-marker') : null;
        if (!marker) return;
        if (event.stopPropagation) event.stopPropagation();
        if (event.preventDefault) event.preventDefault();

        let placeId = marker.getAttribute('data-place-id') || '';
        if (placeId) {
            await this.selectZenlyMarkerFallback(marker, placeId, 'density');
            return;
        }

        let signalId = marker.getAttribute('data-signal-id') || '';
        if (signalId) {
            await this.selectZenlyMarkerFallback(marker, signalId, 'signals');
        }
    }

    private async selectZenlyMarkerFallback(marker: any, id: string, type: string) {
        let card = this.zenlyFallbackCardFromMarker(marker, id, type);
        if (type === 'signals') {
            this.selectedZenlySignalId = id;
            this.selectedPresencePlaceId = '';
        } else {
            this.selectedPresencePlaceId = id;
            this.selectedZenlySignalId = '';
        }
        this.selectedZenlyFallbackCard = card;
        await this.service.render();
        this.bindZenlyMarkerDelegation();
    }

    private zenlyFallbackCardFromMarker(marker: any, id: string, type: string) {
        let label = String(marker && marker.getAttribute ? marker.getAttribute('aria-label') || '' : '').trim();
        let countMatch = label.match(/지금\s*([0-9]+)\s*명/);
        let count = countMatch ? Number(countMatch[1]) : 0;
        let name = label.replace(/\s*지금\s*[0-9]+\s*명.*$/, '').trim();
        if (!name) name = type === 'signals' ? '동행 신호' : '장소';
        return {
            id,
            name,
            category: type === 'signals' ? '신호' : '장소',
            count: Math.max(0, Number(count || 0))
        };
    }

    private bindZenlyMarkerDelegation() {
        if (typeof window === 'undefined' || typeof document === 'undefined') return;
        window.setTimeout(() => {
            let map: any = document.querySelector('.access-shell .zenly-live-map');
            if (!map || map.__gachiZenlyDelegationBound) return;
            map.__gachiZenlyDelegationBound = true;

            let selectFromEvent = (event: any) => {
                let target = event && event.target ? event.target : null;
                let marker = target && target.closest ? target.closest('.zenly-pin-marker') : null;
                if (!marker) return;
                if (event.preventDefault) event.preventDefault();
                if (event.stopPropagation) event.stopPropagation();

                let placeId = marker.getAttribute('data-place-id') || '';
                if (placeId) {
                    this.selectZenlyMarkerFallback(marker, placeId, 'density');
                    return;
                }

                let signalId = marker.getAttribute('data-signal-id') || '';
                if (signalId) {
                    this.selectZenlyMarkerFallback(marker, signalId, 'signals');
                }
            };

            map.addEventListener('click', selectFromEvent, true);
            map.addEventListener('mousedown', selectFromEvent, true);
            map.addEventListener('touchstart', selectFromEvent, { capture: true, passive: false });
        }, 0);
    }

    public zenlySignalMarkers() {
        if (this.zenlySignals && this.zenlySignals.length > 0) {
            return this.zenlySignals.map((signal: any, index: number) => ({
                ...signal,
                id: signal.id || `signal-${index}`,
                name: signal.placeName || signal.locationName || signal.message || '동행 신호',
                category: '신호',
                count: Math.max(1, Number(signal.responseCount || (signal.responses ? signal.responses.length : 0) || 1)),
                displayPosition: signal.displayPosition || this.seedSignalPosition(index)
            }));
        }
        return [];
    }

    public zenlyMarkerLevel(item: any) {
        let count = Math.max(0, Number(item && item.count ? item.count : 0));
        if (count >= 15) return 'high';
        if (count >= 7) return 'medium';
        return 'low';
    }

    public zenlyTotalCount() {
        let total = Math.max(0, Number(this.zenlyHeatmap && this.zenlyHeatmap.regionTotal ? this.zenlyHeatmap.regionTotal : 0));
        if (total > 0) return total;
        return this.zenlyPresencePlaces().reduce((sum: number, place: any) => {
            return sum + Math.max(0, Number(place && place.count ? place.count : 0));
        }, 0);
    }

    public zenlySummaryRegion() {
        let label = this.zenlyRegionLabel();
        if (!label) return '서울';
        if (label.indexOf('서울') > -1 || label.indexOf('성수') > -1) return '서울';
        return label;
    }

    public zenlySummaryText() {
        return `지금 ${this.zenlySummaryRegion()}에 ${this.zenlyTotalCount()}명이 있어요`;
    }

    public zenlySelectedCard() {
        if (this.zenlyLayerTab === 'density' && this.selectedPresencePlaceId) {
            let place = this.zenlyPresencePlaces().find((item: any) => item.place_id === this.selectedPresencePlaceId);
            if (!place && this.selectedZenlyFallbackCard && String(this.selectedZenlyFallbackCard.id) === String(this.selectedPresencePlaceId)) {
                return this.selectedZenlyFallbackCard;
            }
            if (!place) return null;
            return {
                id: place.place_id,
                name: place.name,
                category: place.category || '장소',
                count: Math.max(0, Number(place.count || 0))
            };
        }

        if (this.zenlyLayerTab === 'signals' && this.selectedZenlySignalId) {
            let signal = this.zenlySignalMarkers().find((item: any) => item.id === this.selectedZenlySignalId);
            if (!signal && this.selectedZenlyFallbackCard && String(this.selectedZenlyFallbackCard.id) === String(this.selectedZenlySignalId)) {
                return this.selectedZenlyFallbackCard;
            }
            if (!signal) return null;
            return {
                ...signal,
                id: signal.id,
                name: signal.name || signal.message || '동행 신호',
                category: signal.category || '신호',
                count: Math.max(0, Number(signal.count || 0))
            };
        }

        return null;
    }

    public zenlyCardIcon(card: any) {
        let category = String(card && card.category ? card.category : '').toLowerCase();
        if (category.indexOf('카페') > -1) return 'fa-mug-saucer';
        if (category.indexOf('맛') > -1) return 'fa-utensils';
        if (category.indexOf('산책') > -1) return 'fa-person-walking';
        if (category.indexOf('신호') > -1) return 'fa-paper-plane';
        return 'fa-location-dot';
    }

    public isZenlySignalCard(card: any) {
        return !!card && (card.category === '신호' || !!card.message || !!card.remainingLabel);
    }

    public zenlySignalMeta(signal: any) {
        return [
            signal && signal.rangeLabel ? signal.rangeLabel : '주변',
            signal && signal.remainingLabel ? `${signal.remainingLabel} 남음` : '시간 제한',
            signal && signal.responseStatus === 'pending' ? '관심 보냄' : ''
        ].filter((value: string) => !!value).join(' · ');
    }

    public zenlySignalTags(signal: any) {
        return Array.isArray(signal && signal.moodTags) ? signal.moodTags.slice(0, 6) : [];
    }

    public zenlySignalResponses(signal: any) {
        return Array.isArray(signal && signal.responses) ? signal.responses : [];
    }

    public zenlySignalResponseStatusLabel(response: any) {
        let labels: any = { pending: '검토 중', accepted: '수락됨', declined: '거절됨' };
        return labels[String(response && response.status || '')] || '관심';
    }

    public canRespondZenlySignal(signal: any) {
        return !!signal
            && !signal.owned
            && signal.status !== 'matched'
            && ['pending', 'accepted'].indexOf(String(signal.responseStatus || '')) < 0;
    }

    public async openZenlySummary(event?: any) {
        if (event) event.stopPropagation();
    }

    public async viewZenlyCardCourse(card: any, event?: any) {
        if (event) event.stopPropagation();
        this.query = card && card.name ? card.name : '';
        this.activeTab = 'home';
        this.homeContentTab = 'courses';
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.service.render();
    }

    private seedSignalPosition(index: number) {
        let positions = [
            { x: 34, y: 42 },
            { x: 62, y: 58 },
            { x: 49, y: 74 },
            { x: 72, y: 36 }
        ];
        return positions[index % positions.length];
    }

    public async toggleZenlySignalComposer() {
        if (!this.isLoggedIn()) {
            await this.openAuthModal('login');
            return;
        }
        this.zenlySignalComposerOpen = !this.zenlySignalComposerOpen;
        await this.service.render();
    }

    public async setZenlySignalLocationMode(mode: string) {
        if (['current', 'place'].indexOf(mode) < 0) return;
        this.zenlySignalDraft.locationMode = mode;
        if (mode === 'current') {
            this.zenlySignalDraft.place = null;
            this.zenlyPlaceSearchResults = [];
        } else if (!this.zenlyPlaceSearchResults.length) {
            await this.searchZenlySignalPlaces(false);
        }
        await this.service.render();
    }

    public async setZenlySignalDuration(duration: number) {
        if (!this.zenlySignalDurations.some((item: any) => item.value === duration)) return;
        this.zenlySignalDraft.duration = duration;
        await this.service.render();
    }

    public isZenlySignalTagSelected(tag: string) {
        return this.zenlySignalDraft.tags.indexOf(tag) > -1;
    }

    public async toggleZenlySignalTag(tag: string) {
        let tags = this.zenlySignalDraft.tags || [];
        this.zenlySignalDraft.tags = tags.indexOf(tag) > -1
            ? tags.filter((item: string) => item !== tag)
            : [...tags, tag].slice(0, 6);
        await this.service.render();
    }

    public async onZenlyPlaceSearchInput() {
        await this.searchZenlySignalPlaces(false);
    }

    public async searchZenlySignalPlaces(showLoading: boolean = true) {
        if (showLoading) await this.service.render();
        try {
            let center = this.currentMapCenter();
            const response: any = await wiz.call('search_course_places', {
                lat: center.lat,
                lng: center.lng,
                keyword: this.zenlySignalDraft.placeQuery || '',
                region: this.zenlyRegionLabel(),
                limit: 6
            });
            if (response && response.code === 200) {
                this.zenlyPlaceSearchResults = (response.data && response.data.rows) || [];
            }
        } catch (e) { }
        if (showLoading) await this.service.render();
    }

    public async chooseZenlySignalPlace(place: any) {
        if (!place) return;
        this.zenlySignalDraft.place = place;
        this.zenlySignalDraft.placeQuery = place.name || place.title || '';
        this.zenlyPlaceSearchResults = [];
        await this.service.render();
    }

    public async submitZenlySignal(event?: any) {
        if (event && event.preventDefault) event.preventDefault();
        if (this.zenlySignalSubmitting) return;
        if (!this.isLoggedIn()) {
            await this.openAuthModal('login');
            return;
        }
        if (!this.isTogetherMapActive()) {
            await this.showSaveHint('여행을 시작한 뒤 합류 신호를 보낼 수 있어요.');
            return;
        }
        let message = String(this.zenlySignalDraft.message || '').trim();
        if (!message) {
            await this.showSaveHint('신호 메시지를 입력해주세요.');
            return;
        }
        if (message.length > 50) {
            await this.showSaveHint('합류 신호는 50자 이내로 입력해주세요.');
            return;
        }
        this.zenlySignalSubmitting = true;
        await this.service.render();
        let place = this.zenlySignalDraft.locationMode === 'place' ? this.zenlySignalDraft.place : null;
        let origin = this.mapStartCoordinate || this.executionLiveOrigin || this.currentMapCenter();
        let payload: any = {
            message,
            mood_tags: JSON.stringify(this.zenlySignalDraft.tags || []),
            duration_minutes: this.zenlySignalDraft.duration,
            lat: origin.lat,
            lng: origin.lng
        };
        if (place) {
            payload.place_id = place.place_id || place.id || '';
            payload.lat = place.lat || place.latitude || payload.lat;
            payload.lng = place.lng || place.longitude || payload.lng;
        }
        try {
            const response: any = await wiz.call('zenly_signal_create', payload);
            if (response && response.code === 200 && response.data && response.data.signal) {
                this.zenlySignals = [response.data.signal, ...this.zenlySignals.filter((item: any) => item.id !== response.data.signal.id)];
                this.selectedZenlySignalId = response.data.signal.id;
                this.zenlySignalComposerOpen = false;
                this.zenlySignalDraft.message = '';
                this.zenlySignalDraft.tags = [];
                await this.showSaveHint('신호를 보냈어요.');
            } else {
                await this.showSaveHint(this.responseMessage(response && response.data, '신호를 보내지 못했어요.'));
            }
        } catch (e) {
            await this.showSaveHint('신호를 보내지 못했어요.');
        }
        this.zenlySignalSubmitting = false;
        await this.service.render();
    }

    public async respondZenlySignal(signal: any) {
        if (!signal || !signal.id) return;
        if (!this.isLoggedIn()) {
            await this.openAuthModal('login');
            return;
        }
        try {
            const response: any = await wiz.call('zenly_signal_respond', { signal_id: signal.id });
            if (response && response.code === 200 && response.data && response.data.signal) {
                this.applyZenlySignalUpdate(response.data.signal);
                await this.showSaveHint(response.data.already ? '이미 관심을 표시했어요.' : '관심을 보냈어요.');
            } else {
                await this.showSaveHint(this.responseMessage(response && response.data, '관심 표시를 보내지 못했어요.'));
            }
        } catch (e) {
            await this.showSaveHint('관심 표시를 보내지 못했어요.');
        }
    }

    public async updateZenlySignalResponse(signal: any, response: any, status: string) {
        if (!signal || !response || !signal.id || !response.id) return;
        try {
            const result: any = await wiz.call('zenly_signal_response_update', {
                signal_id: signal.id,
                response_id: response.id,
                status
            });
            if (result && result.code === 200 && result.data) {
                if (result.data.signal) this.applyZenlySignalUpdate(result.data.signal);
                if (status === 'accepted') {
                    if (result.data.meeting) {
                        this.applyTogetherMeetingPayload(result.data.meeting, result.data.messages || []);
                    } else {
                        await this.loadTogetherMeeting(false, false);
                    }
                    this.activeTab = 'map';
                    this.mapContentTab = 'zenly';
                    this.togetherInfoFocus = 'meeting';
                    this.togetherMeetingChatOpen = this.hasActiveTogetherMeetingChat();
                    this.persistAccessState();
                    this.replaceAccessUrl();
                }
                await this.service.render();
                await this.showSaveHint(status === 'accepted' ? '약속과 약속 채팅을 만들었어요.' : '응답을 거절했어요.');
                if (status === 'accepted') this.scrollTogetherMeetingChat();
            } else {
                await this.showSaveHint(this.responseMessage(result && result.data, '응답을 처리하지 못했어요.'));
            }
        } catch (e) {
            await this.showSaveHint('응답을 처리하지 못했어요.');
        }
    }

    public async reportZenlySignal(signal: any) {
        if (!signal || !signal.id) return;
        if (!this.isLoggedIn()) {
            await this.openAuthModal('login');
            return;
        }
        try {
            const response: any = await wiz.call('zenly_signal_report', {
                signal_id: signal.id,
                reason: '부적절한 신호'
            });
            if (response && response.code === 200 && response.data && response.data.signal) {
                this.applyZenlySignalUpdate(response.data.signal);
                await this.showSaveHint('신고가 접수됐어요.');
            } else {
                await this.showSaveHint(this.responseMessage(response && response.data, '신고를 접수하지 못했어요.'));
            }
        } catch (e) {
            await this.showSaveHint('신고를 접수하지 못했어요.');
        }
    }

    public async toggleSave(course: any) {
        if (!this.isLoggedIn()) {
            await this.showSaveHint();
            return;
        }

        await this.persistCourseSave(course, !course.saved);
    }

    public isLoggedIn() {
        return !!(this.service.auth && this.service.auth.isLoggedIn && this.service.auth.isLoggedIn());
    }

    public myDisplayName() {
        let auth = this.service && this.service.auth ? this.service.auth : null;
        let session = auth && auth.session ? auth.session : {};
        let names = [
            session.nickname,
            session.display_name,
            session.displayName,
            session.name,
            session.username
        ];
        for (let value of names) {
            let name = String(value || '').trim();
            if (name) return name;
        }

        let email = String(session.email || '').trim();
        if (email) return email.split('@')[0];

        return '여행자';
    }

    public profileDisplayName() {
        this.ensureMyProfileEditDefaults();
        let nickname = String(this.myProfileEdit.nickname || '').trim();
        let accountName = this.myDisplayName();
        let genericNames = ['여행자', '여행자님'];
        if (nickname && (genericNames.indexOf(nickname) === -1 || accountName === '여행자')) return nickname;
        return accountName;
    }

    public profileIntro() {
        this.ensureMyProfileEditDefaults();
        let intro = String(this.myProfileEdit.intro || '').trim();
        return intro || '내 코스와 여행 팔로우 관계를 한곳에서 확인하고, 인증샷은 각 코스 상세에서 볼 수 있어요.';
    }

    public async openMyProfileEdit() {
        if (!this.isLoggedIn()) {
            this.goLogin();
            return;
        }

        this.ensureMyProfileEditDefaults();
        this.myProfileOpen = true;
        this.resetMyProfileSubscreens();
        this.myProfileEditOpen = true;
        await this.service.render();
    }

    public async closeMyProfileEdit() {
        this.myProfileEditOpen = false;
        await this.service.render();
    }

    public async saveMyProfileEdit() {
        this.ensureMyProfileEditDefaults();
        this.myProfileEdit.nickname = String(this.myProfileEdit.nickname || '').trim();
        this.myProfileEdit.region = String(this.myProfileEdit.region || '').trim();
        this.myProfileEdit.intro = String(this.myProfileEdit.intro || '').trim();
        this.persistMyProfileEdit();
        this.myProfileEditOpen = false;
        await this.showSaveHint('프로필이 저장됐어요.');
    }

    public async handleMyProfilePhotoUpload(event: any) {
        let input = event && event.target ? event.target : null;
        let file = input && input.files && input.files[0] ? input.files[0] : null;
        if (!file) return;

        if (file.type && !/^image\//.test(file.type)) {
            await this.showSaveHint('이미지 파일만 등록할 수 있어요.');
            if (input) input.value = '';
            return;
        }

        let reader = new FileReader();
        reader.onload = () => {
            this.myProfileEdit.photo = String(reader.result || '');
            this.persistMyProfileEdit();
            this.service.render();
        };
        reader.readAsDataURL(file);
        if (input) input.value = '';
    }

    public async openTravelResume(returnToSettings: boolean = false) {
        if (!this.isLoggedIn()) {
            this.goLogin();
            return;
        }

        this.ensureTravelResumeDefaults();
        this.myProfileOpen = true;
        this.resetMyProfileSubscreens();
        this.travelResumeReturnToSettings = !!returnToSettings;
        this.myResumeOpen = true;
        this.myResumePreviewOpen = false;
        this.travelResumeStep = 1;
        this.travelIdentity.loading = true;
        this.travelIdentity.error = '';
        await this.service.render();
        this.resetTravelResumeScroll();
        await this.loadTravelIdentityStatus();
    }

    public async handleTravelResumeBack() {
        if (!this.myResumePreviewOpen && this.travelResumeStep === 2) {
            await this.setTravelResumeStep(1);
            return;
        }
        await this.closeTravelResume();
    }

    public async closeTravelResume() {
        let returnToSettings = this.travelResumeReturnToSettings;
        this.myResumeOpen = false;
        this.myResumePreviewOpen = false;
        this.travelResumeStep = 1;
        this.travelResumeReturnToSettings = false;
        if (returnToSettings) this.myProfileOpen = false;
        await this.service.render();
    }

    public async setTravelResumeStep(step: any) {
        let nextStep = Number(step) === 2 ? 2 : 1;
        if (nextStep === 2 && !(await this.validateTravelResumeStepOne())) return;
        this.travelResumeStep = nextStep;
        this.myResumePreviewOpen = false;
        await this.service.render();
        this.resetTravelResumeScroll();
    }

    public async toggleTravelResumePreview() {
        this.ensureTravelResumeDefaults();
        if (!this.myResumePreviewOpen && !(await this.validateCompleteTravelResume())) return;
        this.myResumePreviewOpen = !this.myResumePreviewOpen;
        await this.service.render();
        this.resetTravelResumeScroll();
    }

    public async saveTravelResume() {
        this.ensureTravelResumeDefaults();
        if (!(await this.validateCompleteTravelResume())) return;
        this.travelResume.fullName = String(this.travelResume.fullName || '').trim();
        this.travelResume.age = this.normalizePositiveNumber(this.travelResume.age);
        this.travelResume.companionUses = this.normalizePositiveNumber(this.travelResume.companionUses);
        this.persistTravelResume();
        await this.showSaveHint('여행 이력서가 저장됐어요.');
    }

    public async handleResumePhotoUpload(event: any) {
        let input = event && event.target ? event.target : null;
        let file = input && input.files && input.files[0] ? input.files[0] : null;
        if (!file) return;

        if (file.type && !/^image\//.test(file.type)) {
            await this.showSaveHint('이미지 파일만 등록할 수 있어요.');
            if (input) input.value = '';
            return;
        }

        if (Number(file.size || 0) > 15 * 1024 * 1024) {
            await this.showSaveHint('15MB 이하 사진을 선택해주세요.');
            if (input) input.value = '';
            return;
        }

        try {
            this.travelResume.photo = await this.prepareTravelResumePhoto(file);
            this.persistTravelResume();
            await this.service.render();
        } catch (e) {
            await this.showSaveHint('사진을 불러오지 못했어요. 다른 사진을 선택해주세요.');
        }
        if (input) input.value = '';
    }

    public travelResumeCompanionUses() {
        let saved = Number(this.travelResume && this.travelResume.companionUses ? this.travelResume.companionUses : 0);
        return Math.max(saved, this.inferredCompanionUseCount());
    }

    public travelResumeCompletion() {
        this.ensureTravelResumeDefaults();
        let checks = [
            this.isTravelResumeIdentityVerified(),
            String(this.travelResume.photo || '').trim().length > 0,
            String(this.travelResume.fullName || '').trim().length > 0,
            this.normalizePositiveNumber(this.travelResume.age) > 0,
            String(this.travelResume.gender || '').trim().length > 0,
            String(this.travelResume.region || '').trim().length > 0,
            String(this.travelResume.smoking || '').trim().length > 0,
            String(this.travelResume.drinking || '').trim().length > 0
        ];
        let done = checks.filter((item: boolean) => item).length;
        return Math.round((done / checks.length) * 100);
    }

    public travelResumeProgressLabel() {
        if (!this.isTravelResumeIdentityVerified()) return '먼저 PASS 본인 인증을 완료해주세요.';
        if (!String(this.travelResume.photo || '').trim()) return '사진 1장만 추가하면 기본 정보가 끝나요.';
        if (!String(this.travelResume.region || '').trim()) return '거주지역만 선택하면 기본 정보가 끝나요.';
        let remaining = [this.travelResume.smoking, this.travelResume.drinking]
            .filter((value: any) => !String(value || '').trim()).length;
        if (remaining > 0) return `${remaining}가지만 선택하면 이력서가 완성돼요.`;
        return '필수 입력을 모두 완료했어요.';
    }

    public resumeValue(value: any, fallback: string) {
        let text = String(value || '').trim();
        return text || fallback;
    }

    public isTravelResumeIdentityVerified() {
        return !!(this.travelIdentity && this.travelIdentity.verified);
    }

    public travelResumeIdentityLabel() {
        return this.isTravelResumeIdentityVerified() ? '본인 인증 완료' : '본인 인증 전';
    }

    public isResumeInterestSelected(value: string) {
        let selected = String(this.travelResume.interests || '')
            .split(',')
            .map((item: string) => item.trim())
            .filter((item: string) => !!item);
        return selected.indexOf(value) > -1;
    }

    public async toggleResumeInterest(value: string) {
        let selected = String(this.travelResume.interests || '')
            .split(',')
            .map((item: string) => item.trim())
            .filter((item: string) => !!item);
        let index = selected.indexOf(value);
        if (index > -1) selected.splice(index, 1);
        else selected.push(value);
        this.travelResume.interests = selected.join(', ');
        this.persistTravelResume();
        await this.service.render();
    }

    public async selectResumePreference(field: string, value: string) {
        if (['smoking', 'drinking'].indexOf(field) === -1) return;
        this.travelResume[field] = value;
        this.persistTravelResume();
        await this.service.render();
    }

    public async setTravelResumeRegion(region: string) {
        this.travelResume.region = String(region || '').trim();
        this.persistTravelResume();
        await this.service.render();
    }

    public canContinueTravelResumeStepOne() {
        return this.isTravelResumeIdentityVerified()
            && !!String(this.travelResume.photo || '').trim()
            && !!String(this.travelResume.fullName || '').trim()
            && this.normalizePositiveNumber(this.travelResume.age) > 0
            && !!String(this.travelResume.gender || '').trim()
            && !!String(this.travelResume.region || '').trim();
    }

    public canSaveTravelResume() {
        return this.canContinueTravelResumeStepOne()
            && !!String(this.travelResume.smoking || '').trim()
            && !!String(this.travelResume.drinking || '').trim();
    }

    public async startPassIdentityVerification() {
        if (!this.isLoggedIn()) {
            this.goLogin();
            return;
        }
        if (this.travelIdentity.verifying) return;

        this.travelIdentity.verifying = true;
        this.travelIdentity.error = '';
        await this.service.render();
        try {
            const startResponse: any = await wiz.call('identity_verification_start', {});
            const startData: any = startResponse && startResponse.data ? startResponse.data : {};
            if (!startResponse || startResponse.code !== 200) {
                this.travelIdentity.configured = startData.configured !== false;
                this.travelIdentity.error = String(startData.message || 'PASS 인증을 시작하지 못했어요.');
                return;
            }

            this.travelIdentity.configured = true;
            const portOne: any = await this.loadPortOneIdentitySdk();
            const redirectUrl = `${window.location.origin}/access?tab=my&identityReturn=1`;
            const result: any = await portOne.requestIdentityVerification({
                storeId: startData.storeId,
                identityVerificationId: startData.identityVerificationId,
                channelKey: startData.channelKey,
                redirectUrl,
                bypass: {
                    inicisUnified: {
                        flgFixedUser: 'N',
                        directAgency: 'PASS'
                    }
                }
            });

            if (result && result.code) {
                this.travelIdentity.error = String(result.message || 'PASS 인증이 취소됐어요.');
                return;
            }
            const completedId = String((result && result.identityVerificationId) || startData.identityVerificationId || '');
            await this.completePassIdentityVerification(completedId);
        } catch (e) {
            this.travelIdentity.error = 'PASS 인증 창을 열지 못했어요. 잠시 후 다시 시도해주세요.';
        } finally {
            this.travelIdentity.verifying = false;
            await this.service.render();
        }
    }

    public async loadTravelIdentityStatus() {
        if (!this.isLoggedIn()) return;
        this.travelIdentity.loading = true;
        this.travelIdentity.error = '';
        try {
            const response: any = await wiz.call('identity_verification_status', {});
            const data: any = response && response.data ? response.data : {};
            if (response && response.code === 200) {
                this.travelIdentity.configured = data.configured !== false;
                this.applyTravelIdentityProfile(data.identity || {});
            } else {
                this.travelIdentity.verified = false;
                this.travelIdentity.error = String(data.message || '본인 인증 상태를 확인하지 못했어요.');
            }
        } catch (e) {
            this.travelIdentity.verified = false;
            this.travelIdentity.error = '본인 인증 상태를 확인하지 못했어요.';
        } finally {
            this.travelIdentity.loading = false;
            await this.service.render();
        }
    }

    private async restorePassIdentityReturn() {
        let identityVerificationId = String(this.passIdentityReturnId || '').trim();
        if (!identityVerificationId || !this.isLoggedIn()) return;

        this.passIdentityReturnId = '';
        this.activeTab = 'my';
        this.myProfileOpen = true;
        this.resetMyProfileSubscreens();
        this.myResumeOpen = true;
        this.travelResumeStep = 1;
        this.travelIdentity.verifying = true;
        this.travelIdentity.error = '';
        let completed = await this.completePassIdentityVerification(identityVerificationId);
        this.travelIdentity.verifying = false;
        if (completed) await this.showSaveHint('PASS 본인 인증이 완료됐어요. 사진만 추가해주세요.');
    }

    private async completePassIdentityVerification(identityVerificationId: string) {
        if (!identityVerificationId) {
            this.travelIdentity.error = '인증 요청 정보를 찾지 못했어요. PASS 인증을 다시 시작해주세요.';
            return false;
        }
        try {
            const response: any = await wiz.call('identity_verification_complete', {
                identity_verification_id: identityVerificationId
            });
            const data: any = response && response.data ? response.data : {};
            if (!response || response.code !== 200) {
                this.travelIdentity.configured = data.configured !== false;
                this.travelIdentity.error = String(data.message || 'PASS 인증 결과를 확인하지 못했어요.');
                return false;
            }
            this.travelIdentity.configured = true;
            this.applyTravelIdentityProfile(data.identity || {});
            this.travelIdentity.error = '';
            return this.isTravelResumeIdentityVerified();
        } catch (e) {
            this.travelIdentity.error = 'PASS 인증 결과를 확인하지 못했어요. 잠시 후 다시 시도해주세요.';
            return false;
        }
    }

    private applyTravelIdentityProfile(profile: any) {
        let verified = !!(profile && profile.verified);
        this.travelIdentity = {
            ...this.travelIdentity,
            verified,
            name: verified ? String(profile.name || '').trim() : '',
            age: verified ? this.normalizePositiveNumber(profile.age) : 0,
            gender: verified ? String(profile.gender || '').trim() : '',
            verifiedAt: verified ? String(profile.verifiedAt || '').trim() : ''
        };
        if (!verified) return;

        this.ensureTravelResumeDefaults();
        this.ensureMyProfileEditDefaults();
        this.travelResume.fullName = this.travelIdentity.name;
        this.travelResume.age = this.travelIdentity.age;
        this.travelResume.gender = this.travelIdentity.gender;
        if (!String(this.travelResume.region || '').trim()) {
            this.travelResume.region = String(this.myProfileEdit.region || '').trim();
        }
        this.persistTravelResume();
    }

    private async validateTravelResumeStepOne() {
        this.ensureTravelResumeDefaults();
        if (!this.isTravelResumeIdentityVerified()) {
            this.travelResumeStep = 1;
            await this.showSaveHint('PASS 본인 인증을 먼저 완료해주세요.');
            return false;
        }
        if (!String(this.travelResume.photo || '').trim()) {
            this.travelResumeStep = 1;
            await this.service.render();
            this.focusTravelResumeRequirement('travelResumePhotoCard');
            await this.showSaveHint('여행 이력서 사진은 필수예요. 사진 1장을 추가해주세요.');
            return false;
        }
        if (
            !String(this.travelResume.fullName || '').trim()
            || this.normalizePositiveNumber(this.travelResume.age) <= 0
            || !String(this.travelResume.gender || '').trim()
        ) {
            this.travelResumeStep = 1;
            await this.showSaveHint('기본 정보를 불러오지 못했어요. PASS 인증을 다시 해주세요.');
            return false;
        }
        if (!String(this.travelResume.region || '').trim()) {
            this.travelResumeStep = 1;
            await this.service.render();
            this.focusTravelResumeRequirement('travelResumeRegion');
            await this.showSaveHint('거주지역을 한 번만 선택해주세요.');
            return false;
        }
        return true;
    }

    private async validateCompleteTravelResume() {
        if (!(await this.validateTravelResumeStepOne())) return false;
        if (!String(this.travelResume.smoking || '').trim() || !String(this.travelResume.drinking || '').trim()) {
            this.travelResumeStep = 2;
            this.myResumePreviewOpen = false;
            await this.service.render();
            this.focusTravelResumeRequirement('travelResumePreferences');
            await this.showSaveHint('흡연 여부와 음주 성향만 선택하면 완료돼요.');
            return false;
        }
        return true;
    }

    private focusTravelResumeRequirement(elementId: string) {
        if (typeof document === 'undefined') return;
        setTimeout(() => {
            let element: any = document.getElementById(elementId);
            if (!element) return;
            if (element.scrollIntoView) element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            if (element.focus) element.focus({ preventScroll: true });
        }, 0);
    }

    private loadPortOneIdentitySdk() {
        if (typeof window === 'undefined' || typeof document === 'undefined') {
            return Promise.reject(new Error('browser only'));
        }
        let portOne = (window as any).PortOne;
        if (portOne && portOne.requestIdentityVerification) return Promise.resolve(portOne);
        if (this.portOneSdkLoader) return this.portOneSdkLoader;

        this.portOneSdkLoader = new Promise((resolve, reject) => {
            let script: any = document.getElementById('portone-v2-browser-sdk');
            let onLoad = () => {
                let loaded = (window as any).PortOne;
                if (loaded && loaded.requestIdentityVerification) resolve(loaded);
                else reject(new Error('PortOne SDK unavailable'));
            };
            let onError = () => reject(new Error('PortOne SDK load failed'));
            if (!script) {
                script = document.createElement('script');
                script.id = 'portone-v2-browser-sdk';
                script.src = 'https://cdn.portone.io/v2/browser-sdk.js';
                script.async = true;
            }
            script.addEventListener('load', onLoad, { once: true });
            script.addEventListener('error', onError, { once: true });
            if (!script.parentNode) document.head.appendChild(script);
        }).catch((error: any) => {
            this.portOneSdkLoader = null;
            throw error;
        });
        return this.portOneSdkLoader;
    }

    private prepareTravelResumePhoto(file: any): Promise<string> {
        return new Promise((resolve, reject) => {
            let reader = new FileReader();
            reader.onerror = () => reject(new Error('read failed'));
            reader.onload = () => {
                let image = new Image();
                image.onerror = () => reject(new Error('image failed'));
                image.onload = () => {
                    let maxSize = 720;
                    let scale = Math.min(1, maxSize / Math.max(image.width || 1, image.height || 1));
                    let width = Math.max(1, Math.round(image.width * scale));
                    let height = Math.max(1, Math.round(image.height * scale));
                    let canvas = document.createElement('canvas');
                    canvas.width = width;
                    canvas.height = height;
                    let context = canvas.getContext('2d');
                    if (!context) {
                        reject(new Error('canvas unavailable'));
                        return;
                    }
                    context.fillStyle = '#ffffff';
                    context.fillRect(0, 0, width, height);
                    context.drawImage(image, 0, 0, width, height);
                    resolve(canvas.toDataURL('image/jpeg', 0.84));
                };
                image.src = String(reader.result || '');
            };
            reader.readAsDataURL(file);
        });
    }

    public recentPlaceTime(place: any) {
        let raw = place && place.viewedAt ? place.viewedAt : '';
        let date = new Date(raw);
        if (!raw || isNaN(date.getTime())) return '방금 전';

        let now = new Date();
        let time = `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
        let today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
        let viewedDay = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();

        if (viewedDay === today) return `오늘 ${time}`;
        if (viewedDay === today - 86400000) return `어제 ${time}`;
        return `${date.getMonth() + 1}.${date.getDate()} ${time}`;
    }

    public async openRecentPlace(place: any) {
        if (!place || !place.id) return;
        if (!this.isLoggedIn()) {
            this.goMapLogin();
            return;
        }

        this.activeTab = 'map';
        this.activeFilterKey = '';
        this.filterOverviewOpen = false;
        if (place.location && place.location !== '국내') {
            this.selectedFilters.location = place.location;
        } else {
            this.selectedFilters.location = '';
        }
        this.syncLocationRegion();
        if (place.category && this.activeMapCategories.hasOwnProperty(place.category)) {
            this.activeMapCategories[place.category] = true;
        }
        this.selectedMapSpotId = place.id;
        this.recordRecentPlace(place);
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    public async clearRecentPlaces() {
        this.recentPlaces = [];
        this.persistRecentPlaces();
        await this.service.render();
    }

    private resetMyProfileSubscreens() {
        this.myProfileEditOpen = false;
        this.myResumeOpen = false;
        this.myResumePreviewOpen = false;
        this.travelResumeStep = 1;
        this.travelResumeReturnToSettings = false;
        this.myFeedComposerOpen = false;
        this.myArchiveOpen = false;
        this.myActivityOpen = false;
        this.myFeedDetailOpen = false;
        this.myCourseDetailOpen = false;
        this.selectedMyProfilePost = null;
        this.selectedMyProfileCourse = null;
        this.feedComposerReturnCourse = null;
        this.profileFeedDetailPhotoIndex = 0;
        this.profileCourseDetailPhotoIndex = 0;
        this.profileCourseDetailLoading = false;
    }

    private resetNewFeedPost() {
        this.newFeedStep = 'select';
        this.newFeedPhotoIndex = 0;
        this.newFeedPost = {
            photo: '',
            photos: [],
            courseId: '',
            courseTitle: '',
            title: '',
            location: '',
            tags: '',
            caption: '',
            icon: 'fa-camera',
            tone: 'feed-rose'
        };
    }

    public async openMyProfile() {
        if (!this.isLoggedIn()) {
            this.goLogin();
            return;
        }

        this.myProfileOpen = true;
        this.myProfileTab = 'myCourses';
        this.resetMyProfileSubscreens();
        await this.service.render();
    }

    public async closeMyProfile() {
        this.myProfileOpen = false;
        this.myProfileTab = 'myCourses';
        this.resetMyProfileSubscreens();
        await this.service.render();
    }

    public isMyProfileMainVisible() {
        return !this.myProfileEditOpen && !this.myResumeOpen && !this.myFeedComposerOpen && !this.myArchiveOpen && !this.myActivityOpen && !this.myFeedDetailOpen && !this.myCourseDetailOpen;
    }

    public async setMyProfileTab(tab: string) {
        if (['myCourses', 'savedCourses', 'following', 'followers'].indexOf(tab) === -1) return;
        this.myProfileTab = tab;
        await this.service.render();
    }

    public async setMyCourseViewMode(mode: string) {
        if (['list', 'grid', 'blog'].indexOf(mode) === -1) return;
        this.myCourseViewMode = mode;
        this.persistMyCourseViewMode();
        await this.service.render();
    }

    public activeMyProfilePosts() {
        return this.myProfilePosts.filter((post: any) => !post.archived);
    }

    public visibleMyProfilePosts() {
        let posts = this.activeMyProfilePosts();
        if (this.myProfileTab === 'regram') {
            return posts.filter((post: any) => post.regrammed);
        }
        return posts;
    }

    public myProfileRegramCount() {
        return this.activeMyProfilePosts().filter((post: any) => post.regrammed).length;
    }

    public myProfileCourses() {
        let courses = this.allCourses();
        let mine = courses.filter((course: any) => {
            if (!course) return false;
            return !!course.mine || !!course.saved || String(course.id || '').indexOf('draft-course-') === 0;
        });
        return (mine.length > 0 ? mine : courses).slice(0, 6);
    }

    public visibleMyProfileCourses() {
        if (this.myProfileTab === 'savedCourses') return this.savedCourses();
        return this.myProfileCourses();
    }

    public myProfileCourseCount() {
        return this.myProfileCourses().length;
    }

    public myProfileSavedCourseCount() {
        return this.savedCourses().length;
    }

    public myProfileCertificationCount() {
        return this.myProfileCourses().reduce((total: number, course: any) => total + this.profileCourseCertificationCount(course), 0);
    }

    public activeMyProfileFollowing() {
        return this.myProfileFollowing.filter((person: any) => person && person.following !== false);
    }

    public myProfileFollowingCount() {
        return this.activeMyProfileFollowing().length;
    }

    public myProfileFollowersCount() {
        return this.myProfileFollowers.length;
    }

    public isProfileFollowing(person: any) {
        if (!person) return false;
        let handle = String(person.handle || '').trim();
        if (handle) {
            return this.myProfileFollowing.some((item: any) => item && item.following !== false && String(item.handle || '').trim() === handle);
        }
        return !!person.following;
    }

    public async toggleProfileFollow(person: any, event?: any) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        if (!person) return;

        let handle = String(person.handle || '').trim();
        let following = this.isProfileFollowing(person);
        if (following) {
            person.following = false;
            this.myProfileFollowing.forEach((item: any) => {
                if (!handle || String(item.handle || '').trim() === handle) item.following = false;
            });
            await this.showSaveHint('팔로잉을 해제했어요.');
            return;
        }

        person.following = true;
        let existing = handle ? this.myProfileFollowing.find((item: any) => String(item.handle || '').trim() === handle) : null;
        if (existing) {
            existing.following = true;
        } else {
            this.myProfileFollowing.push({
                name: person.name,
                handle: person.handle,
                icon: person.icon || 'fa-user',
                note: person.note || '내가 팔로잉하는 여행자',
                following: true
            });
        }
        await this.showSaveHint('팔로우했어요.');
    }

    public profileCourseRegion(course: any) {
        return String((course && course.location) || '지역 미정');
    }

    public profileCourseTitle(course: any) {
        return String((course && course.title) || '여행 코스');
    }

    public profileCourseSummary(course: any) {
        return String((course && course.summary) || '저장한 여행 동선을 확인해보세요.');
    }

    public profileCourseDuration(course: any) {
        return String((course && course.duration) || '소요시간 미정');
    }

    public profileCourseIcon(course: any) {
        return String((course && course.icon) || 'fa-route');
    }

    public profileCourseCategoryLabel(course: any) {
        let explicit = String((course && course.category) || '').trim();
        if (explicit) return explicit;
        let icon = this.profileCourseIcon(course);
        if (icon.indexOf('mug') > -1 || icon.indexOf('coffee') > -1 || icon.indexOf('cookie') > -1) return '카페';
        if (icon.indexOf('water') > -1 || icon.indexOf('fish') > -1) return '바다';
        if (icon.indexOf('bed') > -1) return '숙소';
        if (icon.indexOf('utensils') > -1) return '맛집';
        if (icon.indexOf('walk') > -1 || icon.indexOf('tree') > -1) return '산책';
        if (icon.indexOf('car') > -1) return '드라이브';
        if (icon.indexOf('landmark') > -1 || icon.indexOf('camera') > -1) return '명소';
        return '코스';
    }

    public profileCourseCover(course: any) {
        if (!course) return '';
        if (!course.image_broken) {
            let direct = String(course.cover_image || course.image || '').trim();
            if (direct) return direct;
            let stop = this.profileCourseStops(course).find((item: any) => !!item.image);
            if (stop) return stop.image;
        }
        let shot = this.profileCourseCertShots(course).find((item: any) => !!item.src);
        return shot ? shot.src : '';
    }

    public profileCourseTags(course: any) {
        let tags = Array.isArray(course && course.tags) ? course.tags : [];
        return this.uniqueTags([
            this.profileCourseCategoryLabel(course),
            this.profileCourseRegion(course),
            ...tags
        ]).slice(0, 6);
    }

    public profileCourseDistance(course: any) {
        let route = course && course.route && typeof course.route === 'object' ? course.route : {};
        return String((course && course.distance) || route.total_distance || '').trim();
    }

    public profileCourseStops(course: any) {
        if (!course) return [];
        let route = course.route && typeof course.route === 'object' ? course.route : {};
        let raw: any[] = Array.isArray(course.places) ? course.places : [];
        if (raw.length === 0 && Array.isArray(route.places)) raw = route.places;
        if (raw.length === 0 && Array.isArray(route.days)) {
            raw = route.days.reduce((items: any[], day: any, dayIndex: number) => {
                let stops = day && Array.isArray(day.stops) ? day.stops : [];
                return items.concat(stops.map((stop: any) => ({
                    ...stop,
                    day: stop.day || day.day || dayIndex + 1,
                    day_label: stop.day_label || day.label || `${dayIndex + 1}일차`
                })));
            }, []);
        }

        let defaultDayLabel = String(this.profileCourseDuration(course)).indexOf('박') > -1 ? '1일차' : '오늘의 코스';
        let stops = raw.map((place: any, index: number) => {
            place = place && typeof place === 'object' ? place : {};
            let name = String(place.name || place.title || place.place_name || '').trim();
            if (!name) return null;
            let day = Number(place.day || place.day_index || 0);
            let explicitDayLabel = String(place.day_label || place.dayLabel || (day > 0 ? `${day}일차` : '')).trim();
            let dayLabel = explicitDayLabel || defaultDayLabel;
            return {
                id: place.place_id || place.placeId || place.id || `course-stop-${index}`,
                order: Number(place.order_index || place.order || index + 1),
                name,
                dayLabel,
                time: String(place.visit_time || place.visitTime || place.time || '').trim(),
                category: String(place.category_label || place.tag || place.category || '').trim(),
                address: String(place.area || place.address || place.addr || place.location || '').trim(),
                memo: String(place.memo || place.description || place.overview_summary || place.overview || '').trim(),
                move: String(place.move || place.transport || place.travel_time || place.travelTime || '').trim(),
                distance: String(place.distance || place.distance_text || place.distanceText || '').trim(),
                image: String(place.image || place.first_image || place.firstimage || place.first_image2 || place.thumbnail || '').trim(),
                raw: place,
                dayExplicit: !!explicitDayLabel,
                showDay: false
            };
        }).filter((stop: any) => !!stop);

        let summaryStops = this.profileCourseSummaryStops(course);
        if (stops.length === 0) {
            stops = summaryStops;
        } else if (summaryStops.length > 0) {
            stops = stops.map((stop: any, index: number) => {
                let stopKey = String(stop.name || '').replace(/[^0-9a-zA-Z가-힣]/g, '').toLowerCase();
                let schedule = summaryStops.find((candidate: any) => {
                    let candidateKey = String(candidate.name || '').replace(/[^0-9a-zA-Z가-힣]/g, '').toLowerCase();
                    return stopKey.length >= 2 && candidateKey.length >= 2
                        && (stopKey.indexOf(candidateKey) > -1 || candidateKey.indexOf(stopKey) > -1);
                });
                if (!schedule && summaryStops.length === stops.length) schedule = summaryStops[index];
                if (!schedule) return stop;
                return {
                    ...stop,
                    dayLabel: stop.dayExplicit ? stop.dayLabel : schedule.dayLabel,
                    time: stop.time || schedule.time
                };
            });
        }
        let previousDay = '';
        return stops.map((stop: any) => {
            let showDay = stop.dayLabel !== previousDay;
            previousDay = stop.dayLabel;
            return { ...stop, showDay };
        });
    }

    private profileCourseSummaryStops(course: any) {
        let summary = this.profileCourseSummary(course);
        let parts = summary.split(/\s*(?:→|·|\n)\s*/).filter((part: string) => !!part.trim());
        if (parts.length < 2 && summary.indexOf(',') > -1) {
            parts = summary.split(/\s*,\s*/).filter((part: string) => !!part.trim());
        }
        if (parts.length < 2) return [];

        let dayLabel = String(this.profileCourseDuration(course)).indexOf('박') > -1 ? '1일차' : '오늘의 코스';
        let stops: any[] = [];
        parts.forEach((raw: string, index: number) => {
            let text = String(raw || '').replace(/^[\-–—•]\s*/, '').trim();
            let dayMatch = text.match(/^(\d+일차)\s*(.*)$/);
            if (dayMatch) {
                dayLabel = dayMatch[1];
                text = String(dayMatch[2] || '').replace(/^[:\-–—]\s*/, '').trim();
                if (!text) return;
            }
            let time = '';
            let timeMatch = text.match(/^(\d{1,2}:\d{2})\s*(.*)$/);
            if (timeMatch) {
                time = timeMatch[1];
                text = String(timeMatch[2] || '').trim();
            }
            if (!text) return;
            stops.push({
                id: `summary-stop-${index}`,
                order: stops.length + 1,
                name: text,
                dayLabel,
                time,
                category: '',
                address: '',
                memo: '',
                move: '',
                distance: '',
                image: '',
                showDay: false
            });
        });
        return stops;
    }

    public profileCourseMoveLabel(stop: any) {
        let values = [String((stop && stop.move) || '').trim(), String((stop && stop.distance) || '').trim()]
            .filter((value: string, index: number, items: string[]) => !!value && items.indexOf(value) === index);
        return values.join(' · ') || '다음 장소로 이동';
    }

    public profileCourseStopIcon(stop: any) {
        let text = `${(stop && stop.category) || ''} ${(stop && stop.name) || ''}`;
        if (/카페|커피|디저트/.test(text)) return 'fa-mug-saucer';
        if (/맛집|음식|식당|요리/.test(text)) return 'fa-utensils';
        if (/숙소|호텔|스테이/.test(text)) return 'fa-bed';
        if (/산책|공원|숲|해변/.test(text)) return 'fa-person-walking';
        if (/쇼핑|시장|소품/.test(text)) return 'fa-bag-shopping';
        return 'fa-location-dot';
    }

    public hideCourseBlogImage(event: any) {
        let image = event && event.target ? event.target : null;
        if (image && image.style) image.style.display = 'none';
    }

    public profileCourseSaveCount(course: any) {
        let fixed = Number((course && (course.saves || course.savedCount || course.likes)) || 0);
        if (fixed > 0) return fixed;
        let seed = String((course && (course.id || course.title)) || 'course')
            .split('')
            .reduce((total: number, char: string) => total + char.charCodeAt(0), 0);
        return 42 + (seed % 87);
    }

    public profileCourseCertificationCount(course: any) {
        return this.profileCourseCertShots(course).length;
    }

    public profileCourseCertShots(course: any) {
        let related = this.activeMyProfilePosts()
            .filter((post: any) => this.isPostRelatedToCourse(post, course))
            .reduce((items: any[], post: any) => {
                let photos = Array.isArray(post.photos) && post.photos.length > 0 ? post.photos : (post.photo ? [{ src: post.photo, caption: post.caption || '' }] : []);
                photos.forEach((photo: any) => {
                    let src = String((photo && photo.src) || photo || '').trim();
                    if (!src) return;
                    items.push({
                        src,
                        icon: post.icon || this.profileCourseIcon(course),
                        caption: (photo && photo.caption) || post.caption || this.profileCourseSummary(course),
                        author: post.author || this.myDisplayName(),
                        location: post.location || this.profileCourseRegion(course)
                    });
                });
                return items;
            }, []);

        return related.slice(0, 24);
    }

    public selectedCourseCertShots() {
        return this.profileCourseCertShots(this.selectedMyProfileCourse);
    }

    public selectedCourseCertShot() {
        let shots = this.selectedCourseCertShots();
        if (shots.length === 0) return {};
        let index = Math.min(Math.max(this.profileCourseDetailPhotoIndex, 0), shots.length - 1);
        return shots[index] || {};
    }

    public async openMyCourseDetail(course: any) {
        if (!course) return;
        this.selectedMyProfileCourse = course;
        this.profileCourseDetailPhotoIndex = 0;
        this.profileCourseDetailLoading = true;
        this.myCourseDetailOpen = true;
        this.myResumeOpen = false;
        this.myFeedComposerOpen = false;
        this.myArchiveOpen = false;
        this.myActivityOpen = false;
        this.myFeedDetailOpen = false;
        await this.service.render();
        await Promise.all([
            this.loadProfileCourseDetail(course),
            this.loadProfileCourseStories(course)
        ]);
        if (this.selectedMyProfileCourse && String(this.selectedMyProfileCourse.id || '') === String(course.id || '')) {
            this.profileCourseDetailLoading = false;
            await this.service.render();
        }
    }

    public async closeMyCourseDetail() {
        this.myCourseDetailOpen = false;
        this.profileCourseDetailPhotoIndex = 0;
        this.profileCourseDetailLoading = false;
        this.selectedMyProfileCourse = null;
        await this.service.render();
    }

    private async loadProfileCourseDetail(course: any) {
        let courseId = String((course && course.id) || '').trim();
        if (!courseId) return;
        let detail: any = null;
        try {
            let response = await fetch(`/api/courses/${encodeURIComponent(courseId)}`, { method: 'GET' });
            if (response.ok) {
                let payload = await response.json();
                let data = payload && payload.data ? payload.data : payload;
                detail = data && data.row ? data.row : null;
            }
        } catch (e) { }

        if (!detail && this.isLoggedIn()) {
            try {
                let response: any = await wiz.call('course_execution', { course_id: courseId });
                if (response && response.code === 200 && response.data && response.data.execution) {
                    let execution = response.data.execution;
                    detail = {
                        ...(execution.course || {}),
                        places: Array.isArray(execution.places) ? execution.places : []
                    };
                }
            } catch (e) { }
        }

        if (!detail || !this.selectedMyProfileCourse || String(this.selectedMyProfileCourse.id || '') !== courseId) return;
        let places = Array.isArray(detail.places) && detail.places.length > 0
            ? detail.places
            : (Array.isArray(course.places) ? course.places : []);
        this.selectedMyProfileCourse = {
            ...course,
            ...detail,
            id: courseId,
            location: detail.region || detail.location || course.location || '',
            summary: detail.description || detail.summary || course.summary || '',
            duration: detail.duration || course.duration || '',
            image: detail.cover_image || detail.image || course.image || '',
            cover_image: detail.cover_image || detail.image || course.cover_image || course.image || '',
            places,
            route: detail.route || course.route || {}
        };
    }

    private async loadProfileCourseStories(course: any) {
        let courseId = String((course && course.id) || '').trim();
        if (!courseId) return;
        try {
            let response: any = await wiz.call('saved_courses', {
                community_action: 'course_story',
                course_id: courseId
            });
            if (!response || response.code !== 200 || !response.data || !Array.isArray(response.data.posts)) return;
            let posts = response.data.posts.map((post: any) => this.profileCourseStoryFromApi(post));
            let ids: any = {};
            posts.forEach((post: any) => {
                if (post && post.id) ids[post.id] = true;
            });
            this.myProfilePosts = [
                ...posts,
                ...this.myProfilePosts.filter((post: any) => !ids[post && post.id])
            ];
        } catch (e) { }
    }

    private profileCourseStoryFromApi(post: any) {
        post = post || {};
        let photo = String(post.photo || '').trim();
        let caption = String(post.summary || post.caption || '').trim();
        return {
            id: post.id || `course-story-${Date.now()}`,
            title: post.title || '여행 사진 기록',
            location: post.destination || post.location || '나의 여행',
            caption,
            photo,
            photos: photo ? [{ src: photo, caption }] : [],
            tags: Array.isArray(post.tags) ? post.tags : [],
            icon: 'fa-camera',
            tone: 'feed-rose',
            likes: Number(post.likes || 0),
            regrams: 0,
            regrammed: false,
            archived: false,
            courseId: post.place || post.courseId || '',
            author: post.author || '여행자',
            mine: !!post.owned,
            serverCourseStory: true
        };
    }

    public async openCoursePhotoComposer() {
        if (!this.isLoggedIn()) {
            this.goLogin();
            return;
        }
        let course = this.selectedMyProfileCourse;
        if (!course) return;
        this.feedComposerReturnCourse = course;
        this.resetNewFeedPost();
        this.newFeedPost.courseId = String(course.id || '');
        this.newFeedPost.courseTitle = this.profileCourseTitle(course);
        this.newFeedPost.location = this.profileCourseRegion(course);
        this.myCourseDetailOpen = false;
        this.myFeedComposerOpen = true;
        await this.service.render();
    }

    public async moveCourseCertShot(step: number) {
        let shots = this.selectedCourseCertShots();
        if (shots.length === 0) return;
        this.profileCourseDetailPhotoIndex = Math.min(Math.max(this.profileCourseDetailPhotoIndex + step, 0), shots.length - 1);
        await this.service.render();
    }

    public async selectCourseCertShot(index: number) {
        let shots = this.selectedCourseCertShots();
        if (index < 0 || index >= shots.length) return;
        this.profileCourseDetailPhotoIndex = index;
        await this.service.render();
    }

    private isPostRelatedToCourse(post: any, course: any) {
        if (!post || !course) return false;
        if (post.courseId && course.id && post.courseId === course.id) return true;
        let courseLocation = String(course.location || '').trim();
        let postLocation = String(post.location || '').trim();
        if (courseLocation && postLocation && (courseLocation.indexOf(postLocation) > -1 || postLocation.indexOf(courseLocation) > -1)) return true;

        let courseWords = `${course.title || ''} ${course.location || ''}`.split(/\s+/).filter((word: string) => word.length >= 2);
        let postWords = `${post.title || ''} ${post.location || ''} ${post.caption || ''}`.split(/\s+/).filter((word: string) => word.length >= 2);
        return courseWords.some((word: string) => postWords.indexOf(word) > -1);
    }

    private findProfileCourseForLocation(location: string) {
        let normalized = String(location || '').trim();
        if (!normalized) return null;
        return this.myProfileCourses().find((course: any) => {
            let courseLocation = String((course && course.location) || '').trim();
            return courseLocation && (courseLocation.indexOf(normalized) > -1 || normalized.indexOf(courseLocation) > -1);
        }) || null;
    }

    public async openMyFeedDetail(post: any) {
        if (!post) return;
        this.selectedMyProfilePost = post;
        this.profileFeedDetailPhotoIndex = 0;
        this.myFeedDetailOpen = true;
        this.myResumeOpen = false;
        this.myFeedComposerOpen = false;
        this.myArchiveOpen = false;
        this.myActivityOpen = false;
        await this.service.render();
    }

    public async closeMyFeedDetail() {
        this.myFeedDetailOpen = false;
        this.profileFeedDetailPhotoIndex = 0;
        this.selectedMyProfilePost = null;
        await this.service.render();
    }

    public selectedFeedDetailPhotos() {
        let post = this.selectedMyProfilePost || {};
        if (Array.isArray(post.photos) && post.photos.length > 0) return post.photos;
        if (post.photo) return [{ src: post.photo, caption: post.caption || '' }];
        return [];
    }

    public selectedFeedDetailPhoto() {
        let photos = this.selectedFeedDetailPhotos();
        if (photos.length === 0) return {};
        let index = Math.min(Math.max(this.profileFeedDetailPhotoIndex, 0), photos.length - 1);
        return photos[index] || {};
    }

    public selectedFeedDetailCaption() {
        let photo: any = this.selectedFeedDetailPhoto();
        if (photo.caption) return String(photo.caption);
        let post = this.selectedMyProfilePost || {};
        return String(post.caption || '');
    }

    public selectedFeedDetailTags() {
        let post = this.selectedMyProfilePost || {};
        if (Array.isArray(post.tags)) return post.tags;
        return String(post.tags || '')
            .split(',')
            .map((tag: string) => tag.trim())
            .filter((tag: string) => !!tag);
    }

    public async moveFeedDetailPhoto(step: number) {
        let photos = this.selectedFeedDetailPhotos();
        if (photos.length === 0) return;
        this.profileFeedDetailPhotoIndex = Math.min(Math.max(this.profileFeedDetailPhotoIndex + step, 0), photos.length - 1);
        await this.service.render();
    }

    public async selectFeedDetailPhoto(index: number) {
        let photos = this.selectedFeedDetailPhotos();
        if (index < 0 || index >= photos.length) return;
        this.profileFeedDetailPhotoIndex = index;
        await this.service.render();
    }

    public async toggleProfileRegram(post: any, event?: any) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        if (!post) return;

        post.regrammed = !post.regrammed;
        post.regrams = Math.max(0, Number(post.regrams || 0) + (post.regrammed ? 1 : -1));
        await this.service.render();
    }

    public async openFeedComposer() {
        if (!this.isLoggedIn()) {
            this.goLogin();
            return;
        }

        this.myProfileOpen = true;
        this.resetMyProfileSubscreens();
        this.feedComposerReturnCourse = null;
        this.resetNewFeedPost();
        this.myFeedComposerOpen = true;
        await this.service.render();
    }

    public async closeFeedComposer() {
        let returnCourse = this.feedComposerReturnCourse;
        this.myFeedComposerOpen = false;
        this.feedComposerReturnCourse = null;
        if (returnCourse) {
            this.selectedMyProfileCourse = returnCourse;
            this.myCourseDetailOpen = true;
        }
        await this.service.render();
    }

    public selectedFeedPhotos() {
        return Array.isArray(this.newFeedPost.photos) ? this.newFeedPost.photos : [];
    }

    public currentFeedPhoto() {
        let photos = this.selectedFeedPhotos();
        if (photos.length === 0) return {};
        let index = Math.min(Math.max(this.newFeedPhotoIndex, 0), photos.length - 1);
        return photos[index] || {};
    }

    public currentFeedPhotoCaption() {
        let photo: any = this.currentFeedPhoto();
        return String(photo.caption || '');
    }

    public async setCurrentFeedPhotoCaption(value: any) {
        let photos = this.selectedFeedPhotos();
        if (photos.length === 0) return;
        let index = Math.min(Math.max(this.newFeedPhotoIndex, 0), photos.length - 1);
        photos[index].caption = String(value || '');
    }

    public async selectNewFeedPhoto(index: number) {
        let photos = this.selectedFeedPhotos();
        if (index < 0 || index >= photos.length) return;
        this.newFeedPhotoIndex = index;
        await this.service.render();
    }

    public async moveNewFeedPhoto(step: number) {
        let photos = this.selectedFeedPhotos();
        if (photos.length === 0) return;
        this.newFeedPhotoIndex = Math.min(Math.max(this.newFeedPhotoIndex + step, 0), photos.length - 1);
        await this.service.render();
    }

    public async goFeedCaptionStep() {
        if (this.selectedFeedPhotos().length === 0) {
            await this.showSaveHint('먼저 피드 사진을 선택해주세요.');
            return;
        }

        this.newFeedStep = 'edit';
        this.newFeedPhotoIndex = 0;
        await this.service.render();
    }

    public async backToFeedPhotoSelect() {
        this.newFeedStep = 'select';
        await this.service.render();
    }

    public async removeNewFeedPhoto(index: number, event?: any) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        let photos = this.selectedFeedPhotos();
        if (index < 0 || index >= photos.length) return;
        photos.splice(index, 1);
        this.newFeedPhotoIndex = Math.min(this.newFeedPhotoIndex, Math.max(photos.length - 1, 0));
        if (photos.length === 0) {
            this.newFeedPost.photo = '';
            this.newFeedStep = 'select';
        } else {
            this.newFeedPost.photo = photos[0].src;
        }
        await this.service.render();
    }

    public async handleFeedPhotoUpload(event: any) {
        let input = event && event.target ? event.target : null;
        let files = input && input.files ? Array.prototype.slice.call(input.files) : [];
        if (files.length === 0) return;

        let imageFiles = files.filter((file: any) => file && (!file.type || /^image\//.test(file.type)) && Number(file.size || 0) <= 15 * 1024 * 1024);
        if (imageFiles.length !== files.length) {
            await this.showSaveHint('15MB 이하 이미지 파일만 등록할 수 있어요.');
        }
        if (imageFiles.length === 0) {
            if (input) input.value = '';
            return;
        }

        if (!Array.isArray(this.newFeedPost.photos)) this.newFeedPost.photos = [];
        let available = Math.max(0, 8 - this.newFeedPost.photos.length);
        if (available === 0) {
            await this.showSaveHint('사진은 한 번에 최대 8장까지 올릴 수 있어요.');
            if (input) input.value = '';
            return;
        }
        if (imageFiles.length > available) {
            imageFiles = imageFiles.slice(0, available);
            await this.showSaveHint('사진은 한 번에 최대 8장까지 올릴 수 있어요.');
        }

        let startIndex = this.selectedFeedPhotos().length;
        let failed = 0;
        for (let file of imageFiles) {
            try {
                let src = await this.prepareFeedPhoto(file);
                this.newFeedPost.photos.push({ src, caption: '', name: file.name || '여행 사진' });
                if (!this.newFeedPost.photo) this.newFeedPost.photo = src;
            } catch (e) {
                failed += 1;
            }
        }
        this.newFeedPhotoIndex = Math.min(startIndex, Math.max(0, this.selectedFeedPhotos().length - 1));
        await this.service.render();
        if (failed > 0) await this.showSaveHint(`${failed}장의 사진을 불러오지 못했어요.`);

        if (input) input.value = '';
    }

    private prepareFeedPhoto(file: any): Promise<string> {
        return new Promise((resolve, reject) => {
            let reader = new FileReader();
            reader.onerror = () => reject(new Error('read_failed'));
            reader.onload = () => {
                let image = new Image();
                image.onerror = () => reject(new Error('decode_failed'));
                image.onload = () => {
                    let originalWidth = Math.max(1, Number(image.naturalWidth || image.width || 1));
                    let originalHeight = Math.max(1, Number(image.naturalHeight || image.height || 1));
                    let scale = Math.min(1, 1280 / Math.max(originalWidth, originalHeight));
                    let quality = 0.82;
                    let output = '';
                    for (let attempt = 0; attempt < 10; attempt += 1) {
                        let canvas = document.createElement('canvas');
                        canvas.width = Math.max(1, Math.round(originalWidth * scale));
                        canvas.height = Math.max(1, Math.round(originalHeight * scale));
                        let context = canvas.getContext('2d');
                        if (!context) {
                            reject(new Error('canvas_failed'));
                            return;
                        }
                        context.fillStyle = '#ffffff';
                        context.fillRect(0, 0, canvas.width, canvas.height);
                        context.drawImage(image, 0, 0, canvas.width, canvas.height);
                        output = canvas.toDataURL('image/jpeg', quality);
                        if (output.length <= 48000) break;
                        scale *= 0.82;
                        quality = Math.max(0.46, quality - 0.06);
                    }
                    if (!output || output.length > 62000) {
                        reject(new Error('image_too_large'));
                        return;
                    }
                    resolve(output);
                };
                image.src = String(reader.result || '');
            };
            reader.readAsDataURL(file);
        });
    }

    public async publishFeedPost() {
        let photos = this.selectedFeedPhotos();
        if (photos.length === 0) {
            await this.showSaveHint('피드 사진을 선택해주세요.');
            return;
        }

        let location = String(this.newFeedPost.location || '').trim() || '나의 여행';
        let tags = String(this.newFeedPost.tags || '')
            .split(',')
            .map((tag: string) => tag.trim())
            .filter((tag: string) => !!tag);
        let title = location === '나의 여행' ? '새 여행 피드' : `${location} 여행 피드`;
        let explicitCourseId = String(this.newFeedPost.courseId || '').trim();
        let relatedCourse = explicitCourseId
            ? this.myProfileCourses().find((course: any) => String((course && course.id) || '') === explicitCourseId) || this.feedComposerReturnCourse
            : (this.findProfileCourseForLocation(location) || this.myProfileCourses()[0] || null);
        let courseId = explicitCourseId || String((relatedCourse && relatedCourse.id) || '').trim();
        let createdAt = Date.now();
        let storyPosts = photos.map((photo: any, index: number) => {
            let photoCaption = String((photo && photo.caption) || '').trim() || '새 여행 사진을 공유했어요.';
            return {
                id: `course-story-${createdAt}-${index}`,
                title: this.newFeedPost.courseTitle || title,
                location,
                caption: photoCaption,
                photo: photo.src,
                photos: [{ src: photo.src, caption: photoCaption }],
                photoName: photo.name || `여행 사진 ${index + 1}`,
                tags,
                icon: 'fa-camera',
                tone: 'feed-rose',
                likes: 0,
                regrams: 0,
                regrammed: false,
                archived: false,
                courseId,
                author: this.myDisplayName(),
                mine: true
            };
        });
        this.myProfilePosts = [...storyPosts, ...this.myProfilePosts];
        let failed = 0;
        if (courseId) {
            let results = await Promise.all(storyPosts.map(async (post: any) => {
                try {
                    let response: any = await wiz.call('save_community_post', {
                        post: JSON.stringify({
                            id: post.id,
                            kind: 'course_story',
                            topic: 'travel_log',
                            title: post.title,
                            summary: post.caption,
                            category: 'course_story',
                            destination: post.location,
                            place: post.courseId,
                            photo: post.photo,
                            photoName: post.photoName,
                            author: post.author,
                            tags: post.tags
                        })
                    });
                    return !!(response && response.code === 200);
                } catch (e) {
                    return false;
                }
            }));
            failed = results.filter((saved: boolean) => !saved).length;
        }
        let returnCourse = this.feedComposerReturnCourse;
        this.resetNewFeedPost();
        this.myFeedComposerOpen = false;
        this.feedComposerReturnCourse = null;
        if (returnCourse) {
            this.selectedMyProfileCourse = returnCourse;
            this.profileCourseDetailLoading = false;
            this.myCourseDetailOpen = true;
        } else {
            this.myProfileTab = 'myCourses';
        }
        if (failed > 0) {
            await this.showSaveHint(`${storyPosts.length - failed}장은 저장했고, ${failed}장은 현재 화면에만 남겼어요.`);
        } else {
            await this.showSaveHint('코스에 여행 사진과 글을 올렸어요.');
        }
    }

    public async openMyArchive() {
        if (!this.isLoggedIn()) {
            this.goLogin();
            return;
        }

        this.myProfileOpen = true;
        this.resetMyProfileSubscreens();
        this.myArchiveOpen = true;
        await this.service.render();
    }

    public async closeMyArchive() {
        this.myArchiveOpen = false;
        this.myProfileOpen = false;
        await this.service.render();
    }

    public archivedMyProfilePosts() {
        return this.myProfilePosts.filter((post: any) => !!post.archived);
    }

    public async toggleMyPostArchive(post: any) {
        if (!post) return;
        post.archived = !post.archived;
        await this.showSaveHint(post.archived ? '피드를 보관했어요.' : '피드를 프로필로 되돌렸어요.');
    }

    public async openMyActivity() {
        if (!this.isLoggedIn()) {
            this.goLogin();
            return;
        }

        this.myProfileOpen = true;
        this.resetMyProfileSubscreens();
        this.myActivityOpen = true;
        await this.service.render();
    }

    public async closeMyActivity() {
        this.myActivityOpen = false;
        this.myProfileOpen = false;
        await this.service.render();
    }

    public isAdmin() {
        let auth = this.service && this.service.auth ? this.service.auth : null;
        let session = auth && auth.session ? auth.session : {};
        return session.role === 'admin';
    }

    public goLogin() {
        this.service.href(`/login?returnTo=${encodeURIComponent('/access?tab=my')}`);
    }

    public goAdminDashboard() {
        this.service.href('/admin/dashboard');
    }

    public logout() {
        if (this.service && this.service.auth) this.service.auth.clearLocalSession();
        window.location.href = `/auth/logout?returnTo=${encodeURIComponent('/access?tab=my')}`;
    }

    public goMapLogin() {
        let returnTo = this.mapContentTab === 'zenly' ? '/access?tab=map&mapMode=together' : '/access?tab=map';
        this.service.href(`/login?returnTo=${encodeURIComponent(returnTo)}`);
    }

    public goChatLogin() {
        this.service.href(`/login?returnTo=${encodeURIComponent('/access?tab=chat')}`);
    }

    public async openAuthModal(mode: string = 'login') {
        this.authMode = mode;
        this.authModalOpen = true;
        this.authServerError = '';
        this.authErrors = {};
        await this.service.render();
    }

    public async closeAuthModal() {
        this.authModalOpen = false;
        this.pendingSaveCourse = null;
        this.authServerError = '';
        this.authErrors = {};
        await this.service.render();
    }

    public async switchAuthMode(mode: string) {
        this.authMode = mode;
        this.authServerError = '';
        this.authErrors = {};
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
            this.loadRecentPlaces();
            this.loadMyProfileEdit();
            this.loadMyCourseViewMode();
            if (this.activeTab === 'my') this.myProfileOpen = true;
            if (session.role === 'admin') {
                this.service.href('/admin/dashboard');
                return;
            }
            let course = this.pendingSaveCourse;
            this.pendingSaveCourse = null;
            this.authModalOpen = false;
            this.resetAuthForm();
            if (course) {
                await this.persistCourseSave(course, true);
            } else {
                await this.restoreSavedCourses();
            }
            await this.loadChatThreads(false);
        } else {
            this.authServerError = this.responseMessage(data, this.authMode === 'register' ? '회원가입에 실패했습니다.' : '로그인에 실패했습니다.');
        }

        this.authSubmitting = false;
        await this.service.render();
    }

    public authSubmitLabel() {
        if (this.authSubmitting) return '처리 중';
        return this.authMode === 'register' ? '가입하기' : '로그인';
    }

    public authModalTitle() {
        return this.authMode === 'register' ? '회원가입' : '로그인';
    }

    private async requestAuth(payload: any) {
        let endpoint = this.authMode === 'register' ? '/auth/signup' : '/auth/login';
        let result: any = await this.service.request.post(endpoint, payload);
        if (result && typeof result.code !== 'undefined') return result;
        return await wiz.call(this.authMode === 'register' ? 'register' : 'login', payload);
    }

    private async persistCourseSave(course: any, saved: boolean) {
        let previous = course.saved;
        course.saved = saved;
        await this.service.render();

        const { code, data } = await wiz.call('save_course', {
            course_id: course.id,
            title: course.title,
            location: course.location,
            summary: course.summary,
            duration: course.duration,
            rating: course.rating || '',
            icon: course.icon || '',
            tone: course.tone || '',
            saved: saved ? 'true' : 'false'
        });

        if (code === 200) {
            this.applySavedCourseIds(data && data.course_ids ? data.course_ids : []);
            this.applySavedCourseRows(data && data.courses ? data.courses : []);
            return;
        }

        course.saved = previous;
        if (code === 401 && this.service.auth) this.service.auth.clearLocalSession();
        await this.showSaveHint(this.responseMessage(data, '로그인해야 코스를 저장할 수 있어요.'));
    }

    private async showSaveHint(message: string = '로그인해야 코스를 저장할 수 있어요.') {
        this.saveHintMessage = message;
        this.saveHintVisible = true;
        if (this.saveHintTimer) clearTimeout(this.saveHintTimer);
        if (typeof window !== 'undefined') {
            this.saveHintTimer = window.setTimeout(async () => {
                this.saveHintVisible = false;
                await this.service.render();
            }, 1800);
        }
        await this.service.render();
    }

    private scheduleFilterPlaceLoad() {
        if (this.placeSearchTimer) clearTimeout(this.placeSearchTimer);
        if (typeof window === 'undefined') {
            this.loadFilterPlaces(false);
            return;
        }

        this.placeSearchTimer = window.setTimeout(() => {
            this.loadFilterPlaces();
        }, 260);
    }

    private refreshHomePlacesInBackground() {
        if (this.activeTab !== 'home') return;
        this.loadFilterPlaces(false)
            .then(async () => {
                if (this.activeTab === 'home') await this.service.render();
            })
            .catch(() => { });
    }

    private async loadFilterPlaces(showLoading: boolean = true) {
        let token = ++this.placeCoursesRequestToken;
        if (!this.shouldLoadFilterPlaces()) {
            this.placeCourses = [];
            this.placeThemeSections = [];
            this.activePlaceThemeKey = '';
            this.placeCoursesLoading = false;
            return;
        }

        this.placeCoursesLoading = showLoading;
        if (showLoading) await this.service.render();

        try {
            let params = new URLSearchParams();
            params.set('limit', this.selectedFilters.location ? '48' : '24');
            if (this.selectedFilters.location) params.set('location', this.selectedFilters.location);
            let apiSearch = this.placeApiSearchText();
            if (apiSearch) params.set('search', apiSearch);

            let response = await fetch(`/api/places/themes?${params.toString()}`, { method: 'GET' });
            let payload = await response.json();
            let data = payload && payload.data ? payload.data : payload;
            if (token !== this.placeCoursesRequestToken) return;

            this.placeThemeSections = this.themeSectionsToPlaceSections((data && data.rows) || []);
            this.placeCourses = this.flattenPlaceThemeSections(this.placeThemeSections);
            this.syncActivePlaceTheme();
            this.applySavedCourseIds(this.savedCourseIds);
        } catch (e) {
            if (token === this.placeCoursesRequestToken) {
                this.placeCourses = [];
                this.placeThemeSections = [];
                this.activePlaceThemeKey = '';
            }
        }

        if (token === this.placeCoursesRequestToken) {
            this.placeCoursesLoading = false;
            if (showLoading) await this.service.render();
        }
    }

    private shouldLoadFilterPlaces() {
        if (this.activeTab !== 'home') return false;
        return true;
    }

    private placeApiSearchText() {
        let themeTerms = [
            '여행',
            '데이트',
            '1박2일',
            '당일치기',
            '감성숙소',
            '숙소',
            '카페',
            '맛집',
            '음식점',
            '볼거리',
            '명소',
            '쇼핑',
            '미용',
            '뷰티'
        ];
        return String(this.query || '')
            .trim()
            .split(/\s+/)
            .filter((token: string) => themeTerms.indexOf(token) === -1)
            .join(' ');
    }

    private themeSectionsToPlaceSections(sections: any[] = []) {
        let seen: any = {};
        let rows: any[] = [];
        (sections || []).forEach((section: any, index: number) => {
            let theme: any = {
                key: String((section && section.key) || `theme-${index}`).trim(),
                label: String((section && section.label) || '장소').trim(),
                keyword: String((section && section.keyword) || (section && section.label) || '장소').trim(),
                icon: String((section && section.icon) || '').trim(),
                tone: String((section && section.tone) || '').trim(),
                count: Number((section && section.count) || 0),
                courses: []
            };
            ((section && section.places) || []).forEach((place: any) => {
                if (this.isLegacyExamplePlace(place)) return;
                let id = String((place && (place.id || place.tourapi_id)) || '').trim();
                if (!id || seen[id]) return;
                seen[id] = true;
                theme.courses.push(this.placeToCourse(place, theme));
            });
            if (theme.courses.length > 0) rows.push(theme);
        });
        return rows;
    }

    private isLegacyExamplePlace(place: any) {
        let externalId = String(place && place.tourapi_id || '').trim().toUpperCase();
        let description = String(place && (place.description || place.overview) || '').trim();
        return externalId.indexOf('DUMMY-') === 0 || description.indexOf('[더미]') === 0;
    }

    private flattenPlaceThemeSections(sections: any[] = []) {
        let rows: any[] = [];
        (sections || []).forEach((section: any) => {
            rows = rows.concat((section && section.courses) || []);
        });
        return rows;
    }

    private syncActivePlaceTheme() {
        let themes = this.visiblePlaceThemes();
        if (themes.length === 0) {
            this.activePlaceThemeKey = '';
            return;
        }
        if (!this.activePlaceThemeKey || !themes.some((theme: any) => theme.key === this.activePlaceThemeKey)) {
            this.activePlaceThemeKey = themes[0].key;
        }
    }

    private filteredThemeCourses(theme: any) {
        return ((theme && theme.courses) || []).filter((course: any) => this.matchesCourse(course));
    }

    private placeToCourse(place: any, theme: any) {
        let themeKey = String(place.theme_key || theme.key || '').trim();
        let themeLabel = String(place.theme_label || theme.label || place.category || '장소').trim();
        let themeKeyword = String(place.theme_keyword || theme.keyword || themeLabel).trim();
        let category = String(place.category || themeLabel).trim();
        let location = this.placeLocationLabel(place);
        let summary = String(place.summary || place.address || category || '방문하기 좋은 장소입니다.').trim();
        let tags = this.uniqueTags([
            '여행',
            '데이트',
            '연인',
            '친구',
            '가족',
            '혼자',
            '오늘',
            '이번주말',
            '당일치기',
            '1박2일',
            location,
            themeLabel,
            themeKeyword,
            category,
            place.name,
            place.address,
            summary
        ]);

        return {
            id: `place-${place.id || place.tourapi_id}`,
            source: 'place',
            theme_key: themeKey,
            theme_label: themeLabel,
            theme_keyword: themeKeyword,
            title: place.name || '추천 장소',
            location,
            summary,
            duration: place.usage_time || '방문지',
            distance: category || themeLabel,
            rating: this.placeRatingLabel(place),
            tone: this.placeTone(themeKey),
            icon: place.theme_icon || this.placeIcon(themeKey, category),
            image: place.image || '',
            image_broken: false,
            saved: false,
            tags
        };
    }

    private placeLocationLabel(place: any) {
        let area = String((place && place.area) || '').trim();
        if (area) return area;

        let address = String((place && place.address) || '').trim();
        if (!address) return '부산';

        let tokens = address
            .replace(/특별시|광역시|특별자치도|특별자치시/g, '')
            .split(/\s+/)
            .filter((item: string) => !!item);
        return tokens.slice(0, 2).join(' ') || address;
    }

    private placeRatingLabel(place: any) {
        if (!place || place.rating === null || typeof place.rating === 'undefined' || place.rating === '') return '-';
        let value = Number(place.rating);
        if (Number.isNaN(value)) return String(place.rating);
        return value.toFixed(1);
    }

    private placeTone(themeKey: string) {
        let tones: any = {
            sight: 'tone-blue',
            cafe: 'tone-rose',
            beauty: 'tone-green',
            stay: 'tone-sun',
            food: 'tone-orange',
            shopping: 'tone-slate'
        };
        return tones[themeKey] || 'tone-blue';
    }

    private placeIcon(themeKey: string, category: string) {
        let icons: any = {
            sight: 'fa-location-dot',
            cafe: 'fa-mug-saucer',
            beauty: 'fa-spa',
            stay: 'fa-bed',
            food: 'fa-utensils',
            shopping: 'fa-bag-shopping'
        };
        if (icons[themeKey]) return icons[themeKey];
        if (category.indexOf('음식') > -1) return 'fa-utensils';
        if (category.indexOf('숙') > -1) return 'fa-bed';
        return 'fa-location-dot';
    }

    private uniqueTags(values: any[] = []) {
        let seen: any = {};
        let tags: string[] = [];
        values.forEach((value: any) => {
            let text = String(value || '').trim();
            if (!text) return;
            [text, ...text.replace(/[·,/()]/g, ' ').split(/\s+/)].forEach((item: string) => {
                item = String(item || '').trim();
                if (!item || seen[item]) return;
                seen[item] = true;
                tags.push(item);
            });
        });
        return tags;
    }

    private async restoreSavedCourses() {
        if (!this.isLoggedIn()) return;

        const { code, data } = await wiz.call('saved_courses', {});
        if (code === 200) {
            this.applySavedCourseIds(data && data.course_ids ? data.course_ids : []);
            this.applySavedCourseRows(data && data.courses ? data.courses : []);
            return;
        }

        if (code === 401 && this.service.auth) this.service.auth.clearLocalSession();
    }

    private applySavedCourseIds(ids: any[] = []) {
        this.savedCourseIds = (ids || []).filter((id: any) => !this.isLegacyExampleCourseId(id));
        this.courses = this.courses.filter((course: any) => {
            return !course || !course.serverSavedCourse || this.savedCourseIds.indexOf(course.id) > -1;
        });
        let applySaved = (course: any) => {
            course.saved = this.savedCourseIds.indexOf(course.id) > -1;
        };
        this.allCourses().forEach((course: any) => {
            applySaved(course);
        });
        this.placeThemeSections.forEach((section: any) => {
            ((section && section.courses) || []).forEach((course: any) => applySaved(course));
        });
    }

    private applySavedCourseRows(rows: any[] = []) {
        if (!Array.isArray(rows) || rows.length === 0) return;
        let restored = rows
            .filter((row: any) => !this.isLegacyExampleCourseId(row && row.course_id))
            .map((row: any) => this.savedCourseRowToCourse(row))
            .filter((course: any) => !!course && !!course.id);
        if (restored.length === 0) return;

        let restoredMap: any = {};
        restored.forEach((course: any) => {
            restoredMap[course.id] = course;
        });

        this.courses = [
            ...restored,
            ...this.courses
                .filter((course: any) => course && !restoredMap[course.id])
        ];
        this.recommendations = this.recommendations.map((course: any) => {
            return course && restoredMap[course.id] ? { ...course, saved: true } : course;
        });
    }

    private isLegacyExampleCourseId(value: any) {
        let id = String(value || '').trim().toLowerCase();
        return id.indexOf('rec-') === 0
            || id.indexOf('list-') === 0
            || ['course-seongsu-date', 'course-busan-haeundae', 'course-jeju-aewol'].indexOf(id) > -1;
    }

    private savedCourseRowToCourse(row: any) {
        if (!row || !row.course_id) return null;
        let places = this.parseJsonArray(row.places_json);
        let route = this.parseJsonObject(row.route_json);
        let firstPlace = places.length > 0 ? places[0] : {};
        return {
            id: row.course_id,
            title: row.title || route.title || '저장한 AI 코스',
            location: row.location || route.region || '',
            summary: row.summary || this.savedCoursePlacesSummary(places),
            duration: row.duration || route.schedule || '',
            distance: route.total_distance || '',
            rating: row.rating || '',
            icon: row.icon || 'fa-route',
            tone: row.tone || 'tone-blue',
            image: firstPlace.image || '/assets/places/haeundae-beach.jpg',
            saved: true,
            mine: true,
            serverSavedCourse: true,
            places,
            route,
            tags: this.uniqueTags(['AI플래너', row.location || route.region || '', row.duration || route.schedule || ''])
        };
    }

    private parseJsonArray(value: any) {
        try {
            let parsed = typeof value === 'string' ? JSON.parse(value || '[]') : value;
            return Array.isArray(parsed) ? parsed : [];
        } catch (e) {
            return [];
        }
    }

    private parseJsonObject(value: any) {
        try {
            let parsed = typeof value === 'string' ? JSON.parse(value || '{}') : value;
            return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {};
        } catch (e) {
            return {};
        }
    }

    private savedCoursePlacesSummary(places: any[] = []) {
        return places
            .map((place: any) => `${place.day_label || ''} ${place.time || ''} ${place.name || ''}`.trim())
            .filter((text: string) => !!text)
            .slice(0, 6)
            .join(' · ');
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

    private logFilterEvent(key: string, value: string) {
        if (!value) return;
        wiz.call('log_filter_event', {
            filter_key: key,
            filter_value: value
        });
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
        this.logFilterEvent('schedule', this.selectedFilters.schedule);
        this.activeFilterKey = '';
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.loadFilterPlaces();
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
        this.logFilterEvent('schedule', this.selectedFilters.schedule);
        this.activeFilterKey = '';
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.loadFilterPlaces();
        await this.service.render();
    }

    public async clearSchedule() {
        this.scheduleRange = { start: '', end: '' };
        this.draftScheduleRange = { start: '', end: '' };
        this.selectedFilters.schedule = '';
        this.activeFilterKey = '';
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.loadFilterPlaces();
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

    public activeLocationAreas() {
        let group = this.locationGroups.find((item: any) => item.name === this.selectedLocationRegion);
        return group ? group.areas : [];
    }

    public async selectLocationRegion(region: any) {
        this.selectedLocationRegion = region.name;
        await this.service.render();
    }

    public async selectLocationArea(area: any) {
        this.selectedFilters.location = this.selectedFilters.location === area.value ? '' : area.value;
        this.logFilterEvent('location', this.selectedFilters.location);
        this.activeFilterKey = '';
        this.filterOverviewOpen = false;
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.loadFilterPlaces();
        await this.service.render();
    }

    public isLocationAreaSelected(area: any) {
        return this.selectedFilters.location === area.value;
    }

    public activeFilter() {
        return this.conditionFilters.find((filter: any) => filter.key === this.activeFilterKey);
    }

    public isConditionSelected(key: string) {
        return !!this.selectedFilters[key];
    }

    public getConditionText(filter: any) {
        return this.selectedFilters[filter.key] || filter.defaultValue;
    }

    public getSheetTitle(filter: any) {
        if (filter.key === 'location') return '지역 선택';
        if (filter.key === 'schedule') return '날짜 선택';
        return '누구랑 갈까요?';
    }

    public getPreferenceValue(key: string) {
        return this.selectedFilters[key] || '미선택';
    }

    public getMapLocationLabel() {
        return this.selectedFilters.location || '국내';
    }

    public getLeadText() {
        let location = this.selectedFilters.location;
        let companion = this.getCompanionPhrase(this.selectedFilters.companion);

        if (location && companion) return `${location}에서 ${companion}`;
        if (location) return `${location}에서`;
        if (companion) return `동행 ${companion}`;
        return '오늘의 추천';
    }

    public filteredRecommendations() {
        return [
            ...this.recommendations,
            ...this.placeCourses.slice(0, 8)
        ].filter((course: any) => this.matchesCourse(course));
    }

    public filteredCourses() {
        return [
            ...this.courses,
            ...this.placeCourses
        ].filter((course: any) => this.matchesCourse(course));
    }

    public savedCourses() {
        return this.allCourses().filter((course: any) => course.saved);
    }

    public zenlyRegionLabel() {
        let label = this.selectedFilters.location || (this.executionCourse && this.executionCourse.region) || '성수';
        return String(label || '성수').trim() || '성수';
    }

    public zenlyRegionBanner() {
        return (this.zenlyHeatmap && this.zenlyHeatmap.banner) || `지금 ${this.zenlyRegionLabel()}에 0명이 있어요`;
    }

    public async loadZenlyData(showLoading: boolean = true) {
        await this.loadZenlyHeatmap(showLoading);
        await this.loadZenlySignals(false);
        this.touchZenlyPresence();
        this.bindZenlyMarkerDelegation();
    }

    public async loadZenlyHeatmap(showLoading: boolean = true) {
        this.zenlyHeatmapLoading = !!showLoading;
        if (showLoading) await this.service.render();
        let changed = false;
        try {
            const response: any = await wiz.call('zenly_presence_heatmap', {
                region: this.zenlyRegionLabel(),
                limit: 12
            });
            if (response && response.code === 200 && response.data && response.data.heatmap) {
                this.zenlyHeatmap = response.data.heatmap;
                changed = true;
                if (this.selectedPresencePlaceId) {
                    let selected = this.zenlyPresencePlaces().find((place: any) => place.place_id === this.selectedPresencePlaceId);
                    if (selected && selected.place_id) {
                        await this.loadPresenceHourly(selected.place_id, false);
                    } else {
                        this.selectedPresencePlaceId = '';
                    }
                }
            }
        } catch (e) { }
        this.zenlyHeatmapLoading = false;
        if (showLoading || changed) {
            await this.service.render();
            this.bindZenlyMarkerDelegation();
        }
    }

    public async loadPresenceHourly(placeId: string, showLoading: boolean = true) {
        if (!placeId || String(placeId).indexOf('seed-') === 0) {
            this.zenlyPresenceHourly = this.seedPresenceHourly();
            return;
        }
        try {
            const response: any = await wiz.call('zenly_presence_hourly', {
                place_id: placeId,
                hours: 12
            });
            if (response && response.code === 200 && response.data && response.data.hourly) {
                this.zenlyPresenceHourly = response.data.hourly.buckets || [];
            }
        } catch (e) {
            this.zenlyPresenceHourly = this.seedPresenceHourly();
        }
        if (showLoading) await this.service.render();
    }

    public seedPresenceHourly() {
        let labels = ['09시', '10시', '11시', '12시', '13시', '14시', '15시', '16시', '17시', '18시', '19시', '20시'];
        return labels.map((label: string, index: number) => ({
            label,
            count: [2, 4, 7, 11, 13, 9, 12, 18, 21, 17, 14, 8][index] || 0
        }));
    }

    public async loadZenlySignals(showLoading: boolean = true) {
        this.zenlySignalsLoading = !!showLoading;
        if (showLoading) await this.service.render();
        let origin = this.mapStartCoordinate || this.executionLiveOrigin || this.currentMapCenter();
        let changed = false;
        try {
            const response: any = await wiz.call('zenly_signals_nearby', {
                lat: origin.lat,
                lng: origin.lng,
                radius: 2000
            });
            if (response && response.code === 200 && response.data && Array.isArray(response.data.signals)) {
                this.zenlySignals = response.data.signals;
                changed = true;
                if (this.selectedZenlySignalId && !this.zenlySignals.find((signal: any) => signal.id === this.selectedZenlySignalId)) {
                    this.selectedZenlySignalId = '';
                }
            }
        } catch (e) { }
        this.zenlySignalsLoading = false;
        if (showLoading || changed) {
            await this.service.render();
            this.bindZenlyMarkerDelegation();
        }
    }

    private touchZenlyPresence() {
        if (typeof navigator === 'undefined' || !navigator.geolocation) return;
        navigator.geolocation.getCurrentPosition(
            (position: any) => {
                try {
                    wiz.call('zenly_presence_touch', {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        region: this.zenlyRegionLabel(),
                        radius: 180
                    });
                } catch (e) { }
            },
            () => { },
            { enableHighAccuracy: false, timeout: 2500, maximumAge: 300000 }
        );
    }

    private applyZenlySignalUpdate(signal: any) {
        if (!signal || !signal.id) return;
        this.zenlySignals = [signal, ...this.zenlySignals.filter((item: any) => item.id !== signal.id)];
        this.selectedZenlySignalId = signal.id;
    }

    public async prepareMapExecution() {
        await this.loadMapExecutionCourses(false);
        if (!this.mapStartCoordinate && !this.mapGpsDenied) this.requestMapGpsLocation(false);
        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    public async loadMapExecutionCourses(showLoading: boolean = true) {
        if (!this.isLoggedIn()) return;
        if (this.mapExecutableCourses.length > 0 && !showLoading) return;
        this.mapCoursesLoading = !!showLoading;
        if (showLoading) await this.service.render();
        try {
            const response: any = await wiz.call('course_execution_courses', {});
            const code = response && response.code;
            const data = response && response.data;
            if (code === 200 && data && Array.isArray(data.courses)) {
                this.mapExecutableCourses = data.courses;
                const apiKey = String(data.google_maps_api_key || data.googleMapsApiKey || '').trim();
                if (apiKey) this.googleMapsApiKey = apiKey;
            }
        } catch (e) { }
        this.mapCoursesLoading = false;
        if (showLoading) await this.service.render();
    }

    public async toggleMapCoursePicker() {
        if (this.mapCoursePickerOpen) {
            await this.closeMapCoursePicker();
            return;
        }
        this.mapCoursePickerOpen = true;
        this.stagedExecutionCourseId = this.activeExecutionCourseId || '';
        await this.loadMapExecutionCourses(true);
        await this.service.render();
    }

    public async closeMapCoursePicker() {
        this.mapCoursePickerOpen = false;
        await this.service.render();
    }

    public async setMapCourseSourceTab(tab: string) {
        this.mapCourseSourceTab = tab === 'saved' ? 'saved' : 'mine';
        await this.service.render();
    }

    public filteredMapExecutableCourses() {
        let source = this.mapCourseSourceTab === 'saved' ? 'saved' : 'mine';
        let query = String(this.mapCourseSearchQuery || '').trim().toLowerCase();
        return (this.mapExecutableCourses || []).filter((course: any) => {
            if (String(course && course.source || 'mine') !== source) return false;
            if (!query) return true;
            let text = [
                course.title,
                course.location,
                course.summary,
                course.duration,
            ].join(' ').toLowerCase();
            return text.indexOf(query) > -1;
        });
    }

    public async stageExecutionCourse(course: any) {
        this.stagedExecutionCourseId = String(course && course.id ? course.id : '').trim();
        await this.service.render();
    }

    public isStagedExecutionCourse(course: any) {
        return !!course && String(course.id || '') === this.stagedExecutionCourseId;
    }

    public canStartStagedExecutionCourse() {
        return !!this.stagedExecutionCourseId && this.mapExecutableCourses.some((course: any) => String(course.id || '') === this.stagedExecutionCourseId);
    }

    public async startStagedExecutionCourse() {
        if (!this.canStartStagedExecutionCourse()) return;
        let course = this.mapExecutableCourses.find((item: any) => String(item.id || '') === this.stagedExecutionCourseId);
        await this.selectExecutionCourse(course);
    }

    public courseSourceLabel(course: any) {
        return course && course.source === 'mine' ? '내 코스' : '저장한 코스';
    }

    public courseMetaLabel(course: any) {
        let location = String(course && course.location ? course.location : '지역 미정');
        return `${location} · ${this.courseSourceLabel(course)}`;
    }

    public courseDurationLabel(course: any) {
        let duration = String(course && course.duration ? course.duration : '').trim();
        if (duration) return duration;
        let count = Number(course && course.place_count ? course.place_count : 0);
        let hours = Math.max(1, Math.ceil((count || 2) * 45 / 60));
        return `약 ${hours}시간`;
    }

    public async selectExecutionCourse(course: any) {
        let courseId = String(course && course.id ? course.id : '').trim();
        if (!courseId) return;
        this.activeExecutionCourseId = courseId;
        this.stagedExecutionCourseId = courseId;
        this.mapCoursePickerOpen = false;
        this.mapRouteSheetExpanded = false;
        this.mapRouteLoading = true;
        await this.service.render();
        try {
            const response: any = await wiz.call('course_execution', { course_id: courseId });
            const code = response && response.code;
            const data = response && response.data;
            if (code === 200 && data && data.execution) {
                this.applyExecutionCourse(data.execution);
                this.togetherTripStarted = true;
                this.togetherTripEnded = false;
                this.togetherLocationSharingActive = false;
                this.togetherShareStartedAt = 0;
                this.clearTogetherShareTimer();
                this.activateTogetherTripMeeting();
            }
        } catch (e) { }
        this.mapRouteLoading = false;
        if (this.isTogetherMapActive()) await this.loadTogetherMeeting(false, false);
        await this.service.render();
        this.scheduleGoogleMapRender();
        this.startExecutionGeofence();
    }

    public async endExecutionCourse() {
        await this.closeTogetherMeeting(true);
        this.togetherTripStarted = false;
        this.togetherTripEnded = true;
        this.togetherLocationSharingActive = false;
        this.togetherShareStartedAt = 0;
        this.clearTogetherShareTimer();
        this.togetherSafetyOpen = false;
        this.zenlySignalComposerOpen = false;
        this.activeExecutionCourseId = '';
        this.stagedExecutionCourseId = '';
        this.executionCourse = null;
        this.executionPlaces = [];
        this.executionTotalMinutes = 0;
        this.executionTotalDistanceMeters = 0;
        this.mapRouteSheetExpanded = false;
        this.mapRouteLoading = false;
        this.selectedMapSpotId = '';
        if (this.mapGeoWatchId && typeof navigator !== 'undefined' && navigator.geolocation) {
            try { navigator.geolocation.clearWatch(this.mapGeoWatchId); } catch (e) { }
        }
        this.mapGeoWatchId = null;
        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    public async toggleMapRouteSheet() {
        this.mapRouteSheetExpanded = !this.mapRouteSheetExpanded;
        await this.service.render();
    }

    public mapRouteNextSummary() {
        let spots = this.executionRouteSpots();
        if (!spots || spots.length === 0) return this.executionCourseTitle();
        if (spots.length === 1) return `${spots[0].order}. ${spots[0].name}`;
        return `${spots[0].order}. ${spots[0].name} → ${spots[1].order}. ${spots[1].name}`;
    }

    private applyExecutionCourse(execution: any) {
        this.executionCourse = execution.course || null;
        this.executionPlaces = Array.isArray(execution.places)
            ? execution.places.map((place: any, index: number) => this.normalizeExecutionSpot(place, index))
            : [];
        this.syncExecutionCategories();
        let first = this.executionPlaces.find((spot: any) => this.isFiniteNumber(spot.lat) && this.isFiniteNumber(spot.lng));
        if (first) {
            this.selectedFilters.location = this.executionCourse && this.executionCourse.region ? this.executionCourse.region : first.location;
        }
        this.refreshExecutionSpotProjection();
    }

    private normalizeExecutionSpot(place: any, index: number) {
        let category = place.category_key || this.savedPlaceTypeKey(place);
        let location = place.address || (this.executionCourse && this.executionCourse.region) || '';
        let lat = this.safeNumber(place.lat);
        let lng = this.safeNumber(place.lng);
        let projected = lat !== null && lng !== null ? this.projectMapPosition(lat, lng) : { x: 50, y: 50 };
        return {
            id: place.place_id || `execution-${index + 1}`,
            place_id: place.place_id || `execution-${index + 1}`,
            order: Number(place.order || index + 1),
            name: place.name || '장소',
            kind: place.category_label || place.category || '장소',
            category,
            categoryLabel: place.category_label || place.category || '장소',
            icon: place.icon || this.executionCategoryIcon(category),
            x: projected.x,
            y: projected.y,
            lat,
            lng,
            rating: place.rating || '',
            hours: place.hours || '확인 필요',
            description: place.memo || place.address || '코스에 포함된 장소입니다.',
            times: { walk: '', car: '' },
            photoClass: this.executionPhotoClass(category),
            visited: !!place.checked,
            checked_at: place.checked_at || '',
            checkin_method: place.checkin_method || '',
            location,
            address: place.address || ''
        };
    }

    private syncExecutionCategories() {
        if (this.executionPlaces.length === 0) return;
        let next: any = {};
        this.executionPlaces.forEach((spot: any) => {
            next[spot.category] = typeof this.activeMapCategories[spot.category] === 'boolean'
                ? this.activeMapCategories[spot.category]
                : true;
        });
        this.activeMapCategories = next;
    }

    private refreshExecutionSpotProjection() {
        if (this.executionPlaces.length === 0) return;
        this.executionPlaces = this.executionPlaces.map((spot: any) => {
            if (!this.isFiniteNumber(spot.lat) || !this.isFiniteNumber(spot.lng)) return spot;
            let projected = this.projectMapPosition(Number(spot.lat), Number(spot.lng));
            return {
                ...spot,
                x: projected.x,
                y: projected.y,
            };
        });
    }

    public mapCategoriesForExecution() {
        if (this.executionPlaces.length === 0) return this.mapCategories;
        let seen: any = {};
        return this.executionPlaces
            .filter((spot: any) => {
                if (!spot.category || seen[spot.category]) return false;
                seen[spot.category] = true;
                return true;
            })
            .map((spot: any) => ({
                key: spot.category,
                label: spot.categoryLabel || spot.kind || '장소',
                icon: spot.icon || this.executionCategoryIcon(spot.category),
            }));
    }

    public isMapSpotDimmed(spot: any) {
        if (!this.executionCourse) return false;
        return this.activeMapCategories[spot.category] === false;
    }

    public executionCourseTitle() {
        if (this.executionCourse && this.executionCourse.title) return this.executionCourse.title;
        return '코스를 선택해주세요';
    }

    public mapSummaryLine() {
        let base = this.executionCourse && this.executionCourse.region ? this.executionCourse.region : '국내';
        let minutes = this.executionTotalMinutes > 0 ? `총 ${this.executionTotalMinutes}분` : '시간 계산 중';
        let distance = this.executionTotalDistanceMeters > 0 ? ` · ${this.formatPlannerDistance(this.executionTotalDistanceMeters, false)}` : '';
        return `${base} 추천 동선 · ${this.getTravelModeLabel()} · ${this.mapProgressText()} · ${this.mapStartStatus} · ${minutes}${distance}`;
    }

    public mapRuntimeLine() {
        let google = this.googleMapReady
            ? 'Google Maps 연결됨'
            : (this.googleMapsApiKey ? 'Google Maps 확인 중' : 'Google Maps 키 없음');
        let gps = this.mapGpsDenied
            ? 'GPS 권한 거부'
            : (this.googleUserCoordinate ? 'GPS 연결됨' : 'GPS 확인 중');
        let geofence = this.mapGeoWatchId
            ? '자동 체크인 감지 중'
            : (this.mapGpsDenied ? '수동 체크인 모드' : '자동 체크인 대기');
        return `${google} · ${gps} · ${geofence}`;
    }

    public async openMapSearchSuggestions() {
        this.mapSearchFocused = true;
        this.scheduleMapSearchSuggestionLoad();
        await this.service.render();
    }

    public async onMapSearchInput() {
        this.mapSearchFocused = true;
        this.scheduleMapSearchSuggestionLoad();
        await this.service.render();
    }

    public deferCloseMapSearchSuggestions() {
        if (typeof window === 'undefined') {
            this.mapSearchFocused = false;
            return;
        }
        window.setTimeout(async () => {
            this.mapSearchFocused = false;
            await this.service.render();
        }, 120);
    }

    public async closeMapSearchSuggestions() {
        if (!this.mapSearchFocused) return;
        this.mapSearchFocused = false;
        await this.service.render();
    }

    public showMapSearchSuggestions() {
        return !this.executionCourse && this.mapSearchFocused && this.mapSearchQuery().length > 0 && this.mapSearchSuggestions().length > 0;
    }

    public mapSearchSuggestions() {
        let query = this.mapSearchQuery();
        if (!query) return [];

        let candidates: any[] = [];
        this.savedPlaces().forEach((place: any) => candidates.push(this.mapSearchSuggestionFromPlace(place, '저장 장소')));
        this.mapSpotsForLocation().forEach((spot: any) => candidates.push(this.mapSearchSuggestionFromPlace(spot, '근처 장소')));
        Object.keys(this.mapSpotMap || {}).forEach((key: string) => {
            ((this.mapSpotMap[key] || []) as any[]).forEach((spot: any) => candidates.push(this.mapSearchSuggestionFromPlace(spot, '추천 장소')));
        });
        (this.mapSearchRemoteSuggestions || []).forEach((place: any) => candidates.push(this.mapSearchSuggestionFromPlace(place, '장소')));
        (this.mapSearchGoogleSuggestions || []).forEach((place: any) => candidates.push(this.mapSearchSuggestionFromPlace(place, 'Google')));

        let seen: any = {};
        return candidates
            .filter((item: any) => !!item && this.mapSearchSuggestionMatches(item, query))
            .filter((item: any) => {
                let key = `${item.name}|${item.location || ''}`.toLowerCase();
                if (seen[key]) return false;
                seen[key] = true;
                return true;
            })
            .slice(0, 5);
    }

    public async selectMapSearchSuggestion(suggestion: any, event?: any) {
        if (event && event.preventDefault) event.preventDefault();
        if (event && event.stopPropagation) event.stopPropagation();
        if (!suggestion) return;

        this.mapStartAddress = suggestion.name || '';
        this.mapSearchFocused = false;
        this.mapSearchRemoteSuggestions = [];
        this.mapSearchGoogleSuggestions = [];
        this.recordRecentPlace({
            id: suggestion.id || `search-${suggestion.name}`,
            name: suggestion.name,
            kind: suggestion.kind || '장소',
            category: suggestion.category || '',
            icon: suggestion.icon || 'fa-location-dot',
            location: suggestion.location || this.getMapLocationLabel(),
            description: suggestion.address || suggestion.meta || ''
        });

        if (suggestion.coordinate) {
            await this.applyMapSearchCoordinate(suggestion.coordinate, '검색 위치');
            return;
        }

        await this.setStartFromAddress();
    }

    public async setStartFromAddress() {
        let address = String(this.mapStartAddress || '').trim();
        this.mapSearchFocused = false;
        if (!address) {
            this.requestMapGpsLocation(true);
            return;
        }
        let google = await this.loadGoogleMapsScript();
        if (!google || !google.maps || !google.maps.Geocoder) {
            this.mapStartStatus = '주소 변환 실패';
            await this.service.render();
            return;
        }
        let geocoder = new google.maps.Geocoder();
        geocoder.geocode({ address }, async (results: any[], status: string) => {
            if (status === 'OK' && results && results[0]) {
                let location = results[0].geometry.location;
                let coordinate = { lat: location.lat(), lng: location.lng() };
                await this.applyMapSearchCoordinate(coordinate, this.executionCourse ? '수동 출발' : '검색 위치');
                return;
            }
            this.mapStartStatus = '주소 변환 실패';
            await this.service.render();
        });
    }

    private mapSearchQuery() {
        return String(this.mapStartAddress || '').trim().toLowerCase();
    }

    private scheduleMapSearchSuggestionLoad() {
        if (this.mapSearchTimer) clearTimeout(this.mapSearchTimer);
        let query = this.mapSearchQuery();
        if (!query) {
            this.mapSearchRemoteSuggestions = [];
            this.mapSearchGoogleSuggestions = [];
            return;
        }
        if (typeof window === 'undefined') {
            this.loadMapSearchRemoteSuggestions(query);
            this.loadGoogleMapSearchSuggestions(query);
            return;
        }
        this.mapSearchTimer = window.setTimeout(() => {
            this.loadMapSearchRemoteSuggestions(query);
            this.loadGoogleMapSearchSuggestions(query);
        }, 220);
    }

    private async loadMapSearchRemoteSuggestions(query: string) {
        if (!query || query !== this.mapSearchQuery()) return;
        this.mapSearchSuggestionLoading = true;
        try {
            let center = this.currentMapCenter();
            const response: any = await wiz.call('search_course_places', {
                lat: center.lat,
                lng: center.lng,
                keyword: query,
                region: this.getMapLocationLabel(),
                limit: 6
            });
            if (query === this.mapSearchQuery() && response && response.code === 200) {
                this.mapSearchRemoteSuggestions = (response.data && response.data.rows) || [];
            }
        } catch (e) {
            if (query === this.mapSearchQuery()) this.mapSearchRemoteSuggestions = [];
        }
        this.mapSearchSuggestionLoading = false;
        if (this.mapSearchFocused) await this.service.render();
    }

    private async loadGoogleMapSearchSuggestions(query: string) {
        if (!query || query !== this.mapSearchQuery()) return;
        let google = await this.loadGoogleMapsScript();
        if (query !== this.mapSearchQuery()) return;
        try {
            if (google && google.maps && google.maps.importLibrary) {
                await google.maps.importLibrary('places');
            }
        } catch (e) { }

        let places = google && google.maps ? google.maps.places : null;
        if (!places || typeof places.AutocompleteService !== 'function') {
            await this.loadGoogleGeocodeMapSearchSuggestions(query, google);
            return;
        }

        let service = new places.AutocompleteService();
        service.getPlacePredictions({
            input: query,
            componentRestrictions: { country: 'kr' }
        }, async (predictions: any[], status: string) => {
            if (query !== this.mapSearchQuery()) return;
            let ok = status === 'OK' || (places.PlacesServiceStatus && status === places.PlacesServiceStatus.OK);
            this.mapSearchGoogleSuggestions = ok && Array.isArray(predictions)
                ? predictions.slice(0, 5).map((place: any) => ({
                    id: place.place_id || place.description,
                    place_id: place.place_id || '',
                    name: place.description || (place.structured_formatting && place.structured_formatting.main_text) || query,
                    title: place.description || query,
                    area: 'Google',
                    category: '장소',
                    address: place.description || '',
                    icon: 'fa-location-dot'
                }))
                : [];
            if (this.mapSearchGoogleSuggestions.length === 0) {
                await this.loadGoogleGeocodeMapSearchSuggestions(query, google);
                return;
            }
            if (this.mapSearchFocused) await this.service.render();
        });
    }

    private async loadGoogleGeocodeMapSearchSuggestions(query: string, google: any) {
        if (!google || !google.maps || typeof google.maps.Geocoder !== 'function') {
            if (query === this.mapSearchQuery()) this.mapSearchGoogleSuggestions = [];
            return;
        }
        let geocoder = new google.maps.Geocoder();
        geocoder.geocode({
            address: query,
            componentRestrictions: { country: 'KR' }
        }, async (results: any[], status: string) => {
            if (query !== this.mapSearchQuery()) return;
            this.mapSearchGoogleSuggestions = status === 'OK' && Array.isArray(results)
                ? results.slice(0, 5).map((place: any) => {
                    let location = place && place.geometry && place.geometry.location ? place.geometry.location : null;
                    return {
                        id: place.place_id || place.formatted_address,
                        place_id: place.place_id || '',
                        name: place.formatted_address || query,
                        title: place.formatted_address || query,
                        area: 'Google',
                        category: '장소',
                        address: place.formatted_address || '',
                        lat: location && typeof location.lat === 'function' ? location.lat() : '',
                        lng: location && typeof location.lng === 'function' ? location.lng() : '',
                        icon: 'fa-location-dot'
                    };
                })
                : [];
            if (this.mapSearchFocused) await this.service.render();
        });
    }

    private mapSearchSuggestionFromPlace(place: any, sourceLabel: string) {
        let name = String(place && (place.name || place.title) || '').trim();
        if (!name) return null;
        let lat = this.safeNumber(place.lat || place.latitude);
        let lng = this.safeNumber(place.lng || place.longitude);
        let location = String(place.location || place.area || this.getMapLocationLabel() || '').trim();
        let kind = String(place.kind || place.category || '장소').trim();
        let address = String(place.address || place.summary || place.description || '').trim();
        let meta = [location, kind].filter((item: string) => !!item && item !== '국내').join(' · ');
        if (!meta) meta = sourceLabel;
        return {
            id: String(place.id || place.place_id || name).trim(),
            name,
            kind,
            category: place.category || '',
            icon: place.icon || this.mapSearchSuggestionIcon(place),
            location,
            address,
            meta,
            coordinate: lat !== null && lng !== null ? { lat, lng } : null
        };
    }

    private mapSearchSuggestionMatches(suggestion: any, query: string) {
        let searchable = [
            suggestion.name,
            suggestion.location,
            suggestion.kind,
            suggestion.category,
            suggestion.address,
            suggestion.meta
        ].join(' ').toLowerCase();
        return searchable.indexOf(query) > -1;
    }

    private mapSearchSuggestionIcon(place: any) {
        let key = this.savedPlaceTypeKey(place);
        let filter = this.savedPlaceFilters.find((item: any) => item.key === key);
        return filter ? filter.icon : 'fa-location-dot';
    }

    private async applyMapSearchCoordinate(coordinate: any, status: string) {
        this.googleSearchCoordinate = coordinate;
        this.mapStartCoordinate = coordinate;
        if (this.executionCourse) this.executionLiveOrigin = coordinate;
        this.mapStartStatus = status;
        this.googleCenterOnUser = true;
        this.selectedMapSpotId = '';
        this.userPosition = this.projectMapPosition(coordinate.lat, coordinate.lng);
        if (this.googleMap) {
            this.googleMap.panTo(coordinate);
            this.googleMap.setZoom(Math.max(Number(this.googleMap.getZoom && this.googleMap.getZoom()) || 15, 15));
            this.renderGoogleSearchMarker(coordinate);
        }
        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    private requestMapGpsLocation(forceRender: boolean) {
        if (typeof navigator === 'undefined' || !navigator.geolocation) {
            this.mapGpsDenied = true;
            this.mapStartStatus = '수동 체크인만 가능';
            return;
        }
        navigator.geolocation.getCurrentPosition(
            async (position: any) => {
                let coordinate = { lat: position.coords.latitude, lng: position.coords.longitude };
                this.googleSearchCoordinate = null;
                this.mapStartCoordinate = coordinate;
                this.executionLiveOrigin = coordinate;
                this.googleUserCoordinate = coordinate;
                this.userPosition = this.projectMapPosition(coordinate.lat, coordinate.lng);
                this.mapStartStatus = '현재 위치';
                this.mapGpsDenied = false;
                if (forceRender) await this.service.render();
                this.scheduleGoogleMapRender();
            },
            async () => {
                this.mapGpsDenied = true;
                this.mapStartStatus = '수동 체크인만 가능';
                if (forceRender) await this.service.render();
            },
            { enableHighAccuracy: true, timeout: 5000, maximumAge: 120000 }
        );
    }

    private startExecutionGeofence() {
        if (typeof navigator === 'undefined' || !navigator.geolocation || this.executionPlaces.length === 0) return;
        if (this.mapGeoWatchId) {
            try { navigator.geolocation.clearWatch(this.mapGeoWatchId); } catch (e) { }
        }
        this.mapGeoWatchId = navigator.geolocation.watchPosition(
            (position: any) => this.handleExecutionPosition(position),
            async () => {
                this.mapGpsDenied = true;
                this.mapStartStatus = '수동 체크인만 가능';
                await this.service.render();
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
        );
    }

    private handleExecutionPosition(position: any) {
        let coordinate = { lat: position.coords.latitude, lng: position.coords.longitude };
        this.executionLiveOrigin = coordinate;
        this.googleUserCoordinate = coordinate;
        this.userPosition = this.projectMapPosition(coordinate.lat, coordinate.lng);
        let target = this.executionPlaces.find((spot: any) => {
            if (spot.visited || !this.isFiniteNumber(spot.lat) || !this.isFiniteNumber(spot.lng)) return false;
            let distance = this.distanceKm(coordinate.lat, coordinate.lng, spot.lat, spot.lng);
            return distance !== null && distance <= 0.08;
        });
        if (target) this.checkInSpot(target, 'auto', coordinate);
    }

    public async checkInSpot(spot: any, method: string = 'manual', coordinate?: any) {
        if (!spot || spot.visited || !this.activeExecutionCourseId) return;
        let origin = coordinate || this.executionLiveOrigin || this.mapStartCoordinate || {};
        try {
            const response: any = await wiz.call('course_checkin', {
                course_id: this.activeExecutionCourseId,
                place_id: spot.place_id || spot.id,
                method,
                lat: origin.lat || '',
                lng: origin.lng || '',
            });
            const code = response && response.code;
            const data = response && response.data;
            if (code === 200 && data && data.execution) {
                this.applyExecutionCourse(data.execution);
            } else {
                spot.visited = true;
            }
        } catch (e) {
            spot.visited = true;
        }
        if (origin && this.isFiniteNumber(origin.lat) && this.isFiniteNumber(origin.lng)) {
            this.executionLiveOrigin = { lat: Number(origin.lat), lng: Number(origin.lng) };
        }
        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    public mapSpotsForLocation() {
        if (this.executionPlaces.length > 0) return this.executionPlaces;
        let location = this.selectedFilters.location || '';
        let region = this.getRegionForLocation(location);
        if (location && this.mapSpotMap[location]) return this.mapSpotMap[location];
        if (region && this.mapSpotMap[region]) return this.mapSpotMap[region];
        return this.mapSpotMap.default;
    }

    public filteredMapSpots() {
        if (this.executionPlaces.length > 0) return this.mapSpotsForLocation();
        return this.mapSpotsForLocation().filter((spot: any) => this.activeMapCategories[spot.category]);
    }

    public isMapCategoryActive(key: string) {
        return !!this.activeMapCategories[key];
    }

    public async toggleMapCategory(key: string) {
        this.activeMapCategories[key] = !this.activeMapCategories[key];
        let activeKeys = Object.keys(this.activeMapCategories).filter((item: string) => this.activeMapCategories[item]);
        if (activeKeys.length === 0) this.activeMapCategories[key] = true;
        if (this.selectedMapSpotId && !this.filteredMapSpots().some((spot: any) => spot.id === this.selectedMapSpotId)) {
            this.selectedMapSpotId = '';
        }
        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    public async setTravelMode(mode: string) {
        if (!this.isSupportedTravelMode(mode)) return;
        this.travelMode = mode;
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    public getSpotTravelTime(spot: any) {
        if (!spot) return '';
        if (spot.visited) return spot.checkin_method === 'auto' ? '자동 도착' : '도착 완료';
        if (!spot.times) return this.executionCourse ? '이동 계산 중' : '';
        return spot.times[this.travelMode] || (this.executionCourse ? '이동 계산 중' : '');
    }

    public getTravelModeLabel() {
        let mode = this.mapTravelModes.find((item: any) => item.key === this.travelMode);
        return mode ? mode.label : '';
    }

    public getMoveFilterLabel() {
        let mode = this.moveFilterOptions.find((item: any) => item.key === this.selectedMoveFilter);
        return mode ? mode.label : '전체';
    }

    public isTravelModeFiltered() {
        return !!this.selectedMoveFilter;
    }

    public selectedMapSpot() {
        if (!this.selectedMapSpotId) return null;
        return this.mapSpotsForLocation().find((spot: any) => spot.id === this.selectedMapSpotId) || null;
    }

    public async selectMapSpot(spot: any) {
        this.selectedMapSpotId = spot.id;
        this.recordRecentPlace(spot);
        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    public async closeMapSpotSheet() {
        this.selectedMapSpotId = '';
        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    public async toggleVisit(spot: any, event?: any) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        if (this.executionCourse) {
            await this.checkInSpot(spot, 'manual');
            return;
        }
        spot.visited = !spot.visited;
        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    public async zoomMap(direction: number) {
        this.mapZoom = Math.min(3, Math.max(1, this.mapZoom + direction));
        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    public async centerOnUser() {
        this.mapZoom = Math.max(2, this.mapZoom);
        if (typeof navigator !== 'undefined' && navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                async (position: any) => {
                    let coordinate = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    this.googleSearchCoordinate = null;
                    this.googleUserCoordinate = coordinate;
                    if (this.executionCourse) {
                        this.mapStartCoordinate = coordinate;
                        this.executionLiveOrigin = coordinate;
                        this.mapStartStatus = '현재 위치';
                    }
                    this.googleCenterOnUser = true;
                    this.userPosition = this.projectMapPosition(position.coords.latitude, position.coords.longitude);
                    this.renderGoogleUserMarker(coordinate);
                    if (this.googleMap) this.googleMap.panTo(coordinate);
                    await this.service.render();
                    this.scheduleGoogleMapRender();
                },
                async () => {
                    await this.service.render();
                    this.scheduleGoogleMapRender();
                },
                { enableHighAccuracy: false, timeout: 4000, maximumAge: 600000 }
            );
            return;
        }

        await this.service.render();
        this.scheduleGoogleMapRender();
    }

    public async handleMapWheel(event: any) {
        if (!event) return;
        event.preventDefault();
        let direction = event.deltaY > 0 ? -1 : 1;
        await this.zoomMap(direction);
    }

    public startMapTouch(event: any) {
        if (!event || !event.touches || event.touches.length !== 2) return;
        this.pinchStartDistance = this.touchDistance(event.touches);
        this.pinchStartZoom = this.mapZoom;
    }

    public async moveMapTouch(event: any) {
        if (!event || !event.touches || event.touches.length !== 2 || !this.pinchStartDistance) return;
        event.preventDefault();
        let distance = this.touchDistance(event.touches);
        let diff = distance - this.pinchStartDistance;
        let targetZoom = this.pinchStartZoom;
        if (diff > 28) targetZoom = this.pinchStartZoom + 1;
        if (diff < -28) targetZoom = this.pinchStartZoom - 1;
        targetZoom = Math.min(3, Math.max(1, targetZoom));
        if (targetZoom === this.mapZoom) return;
        this.mapZoom = targetZoom;
        await this.service.render();
    }

    public endMapTouch() {
        this.pinchStartDistance = 0;
    }

    public mapRoutePoints() {
        let spots = this.executionCourse ? this.executionRouteSpots() : this.filteredMapSpots();
        return this.routePoints(spots);
    }

    public mapProgressText() {
        let spots = this.mapSpotsForLocation();
        let visited = spots.filter((spot: any) => spot.visited).length;
        return `${visited}/${spots.length} 방문`;
    }

    public selectedMapTiles() {
        let center = this.currentMapCenter();
        let tile = this.lngLatToTile(center.lng, center.lat, center.zoom);
        let tiles = [];

        for (let row = -1; row <= 1; row++) {
            for (let col = -1; col <= 1; col++) {
                tiles.push({
                    src: `https://tile.openstreetmap.org/${center.zoom}/${tile.x + col}/${tile.y + row}.png`,
                    col: String(col + 2),
                    row: String(row + 2)
                });
            }
        }

        return tiles;
    }

    private scheduleCourseMapRender(retry: number = 0) {
        if (!this.courseComposerOpen || this.courseBuilderStep !== 'places') return;
        if (typeof window === 'undefined') return;
        let root: any = window as any;
        let frame = root.requestAnimationFrame || ((callback: any) => setTimeout(callback, 16));
        frame(() => this.renderCourseGoogleMap(retry));
    }

    private async renderCourseGoogleMap(retry: number = 0) {
        if (!this.courseComposerOpen || this.courseBuilderStep !== 'places' || typeof document === 'undefined') return;
        let element: any = document.querySelector('.course-google-map');
        if (!element || (!element.offsetWidth || !element.offsetHeight)) {
            if (retry < 8) setTimeout(() => this.scheduleCourseMapRender(retry + 1), 80);
            return;
        }

        let google = await this.loadGoogleMapsScript();
        if (!this.isGoogleMapsReady(google)) {
            this.courseGoogleReady = false;
            return;
        }

        let centerData = this.courseSearchCenter();
        let center = { lat: Number(centerData.lat), lng: Number(centerData.lng) };

        if (this.courseGoogleMapElement !== element) {
            this.clearCourseGoogleOverlays();
            this.courseGoogleMap = null;
            this.courseGoogleMapElement = element;
        }

        if (!this.courseGoogleMap) {
            this.courseGoogleMap = new google.maps.Map(element, {
                center,
                zoom: this.courseBuilderPlaces.length > 1 ? 14 : 15,
                clickableIcons: true,
                disableDefaultUI: true,
                gestureHandling: 'greedy',
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: false,
                zoomControl: false
            });
        } else {
            this.courseGoogleMap.setCenter(center);
        }

        this.clearCourseGoogleOverlays();

        let points = this.courseBuilderPlaces
            .filter((place: any) => this.isFiniteNumber(place.lat) && this.isFiniteNumber(place.lng))
            .map((place: any) => ({ lat: Number(place.lat), lng: Number(place.lng) }));

        points.forEach((point: any, index: number) => {
            let marker = new google.maps.Marker({
                map: this.courseGoogleMap,
                position: point,
                title: this.courseBuilderPlaces[index].name,
                label: {
                    text: String(index + 1),
                    color: '#ffffff',
                    fontSize: '12px',
                    fontWeight: '900'
                },
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 15,
                    fillColor: '#e63946',
                    fillOpacity: 1,
                    strokeColor: '#ffffff',
                    strokeWeight: 3
                },
                zIndex: 20 + index
            });
            this.courseGoogleMarkers.push(marker);
        });

        if (points.length > 1) {
            this.courseGoogleRouteLine = new google.maps.Polyline({
                map: this.courseGoogleMap,
                path: points,
                strokeOpacity: 0,
                strokeWeight: 3,
                icons: [{
                    icon: {
                        path: 'M 0,-1 0,1',
                        strokeColor: '#e63946',
                        strokeOpacity: 0.9,
                        strokeWeight: 3,
                        scale: 3
                    },
                    offset: '0',
                    repeat: '14px'
                }]
            });

            let bounds = new google.maps.LatLngBounds();
            points.forEach((point: any) => bounds.extend(point));
            this.courseGoogleMap.fitBounds(bounds, 24);
        } else {
            this.courseGoogleMap.setCenter(center);
            this.courseGoogleMap.setZoom(points.length === 1 ? 16 : 14);
        }

        if (google.maps.event && google.maps.event.trigger) {
            google.maps.event.trigger(this.courseGoogleMap, 'resize');
        }
        this.courseGoogleReady = true;
    }

    private clearCourseGoogleOverlays() {
        this.courseGoogleMarkers.forEach((marker: any) => {
            try { marker.setMap(null); } catch (e) { }
        });
        this.courseGoogleMarkers = [];
        this.courseGoogleReady = false;
        if (this.courseGoogleRouteLine) {
            try { this.courseGoogleRouteLine.setMap(null); } catch (e) { }
            this.courseGoogleRouteLine = null;
        }
    }

    private scheduleGoogleMapRender(retry: number = 0) {
        if (this.activeTab !== 'map' || this.mapContentTab !== 'map') return;
        if (typeof window === 'undefined') return;
        let root: any = window as any;
        let frame = root.requestAnimationFrame || ((callback: any) => setTimeout(callback, 16));
        frame(() => this.renderGoogleMap(retry));
    }

    private async renderGoogleMap(retry: number = 0) {
        if (this.activeTab !== 'map' || this.mapContentTab !== 'map') return;
        if (typeof document === 'undefined') return;

        let element = document.getElementById('access-google-map');
        if (!element) return;
        if ((!element.offsetWidth || !element.offsetHeight) && retry < 10) {
            setTimeout(() => this.scheduleGoogleMapRender(retry + 1), 80);
            return;
        }

        let google = await this.loadGoogleMapsScript();
        if (!this.isGoogleMapsReady(google)) {
            this.googleMapReady = false;
            return;
        }

        let center = this.currentMapCenter();
        let focusCoordinate = this.googleSearchCoordinate || this.googleUserCoordinate;
        let centerPosition = this.googleCenterOnUser && focusCoordinate
            ? focusCoordinate
            : { lat: center.lat, lng: center.lng };
        let zoom = center.zoom + (this.mapZoom - 2);
        let fallback = element.parentElement ? element.parentElement.querySelector('.map-fallback') : null;

        if (this.googleMapElement !== element) {
            this.clearGoogleMapOverlays();
            this.googleMap = null;
            this.googleMapElement = element;
        }

        try {
            if (!this.googleMap) {
                this.googleMap = new google.maps.Map(element, {
                    center: centerPosition,
                    zoom,
                    clickableIcons: true,
                    disableDefaultUI: true,
                    gestureHandling: 'greedy',
                    mapTypeControl: false,
                    streetViewControl: false,
                    fullscreenControl: false,
                    zoomControl: false
                });
                this.googleDirectionsService = new google.maps.DirectionsService();
            } else {
                this.googleMap.setCenter(centerPosition);
                this.googleMap.setZoom(zoom);
            }
        } catch (e) {
            this.googleMapReady = false;
            this.googleMap = null;
            element.classList.remove('ready');
            return;
        }

        this.googleMapReady = true;
        element.classList.add('ready');
        if (fallback) fallback.classList.add('fallback-hidden');
        this.googleCenterOnUser = false;
        if (google.maps.event && google.maps.event.trigger) {
            google.maps.event.trigger(this.googleMap, 'resize');
            this.googleMap.setCenter(centerPosition);
        }

        this.renderGoogleMarkers(google);
        this.renderGoogleRoute(google);
        if (this.googleSearchCoordinate) this.renderGoogleSearchMarker(this.googleSearchCoordinate);
        if (this.googleUserCoordinate) this.renderGoogleUserMarker(this.googleUserCoordinate);
    }

    private loadGoogleMapsScript() {
        if (typeof window === 'undefined' || typeof document === 'undefined') return Promise.resolve(null);
        if (!this.googleMapsApiKey) return Promise.resolve(null);

        let root: any = window as any;
        if (root.google && root.google.maps) return this.prepareGoogleMaps(root.google);
        if (this.googleMapsLoader) return this.googleMapsLoader;

        this.googleMapsLoader = new Promise((resolve) => {
            let settled = false;
            let callbackName = '';
            let finish = (google: any, scriptElement: any = null) => {
                if (settled) return;
                settled = true;
                if (!google) {
                    this.googleMapsLoader = null;
                    if (scriptElement && scriptElement.parentNode) scriptElement.parentNode.removeChild(scriptElement);
                }
                if (callbackName) {
                    try {
                        delete root[callbackName];
                    } catch (e) {
                        root[callbackName] = null;
                    }
                }
                resolve(google);
            };
            let existing = document.getElementById('access-google-maps-sdk');
            if (existing) {
                this.waitForGoogleMapsReady(root).then((google: any) => finish(google, existing));
                existing.addEventListener('error', () => finish(null, existing), { once: true });
                return;
            }

            callbackName = '__tourOnGoogleMapsReady';
            root[callbackName] = async () => {
                let google = await this.prepareGoogleMaps(root.google);
                finish(google, script);
            };

            let script = document.createElement('script');
            script.id = 'access-google-maps-sdk';
            script.async = true;
            script.defer = true;
            script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(this.googleMapsApiKey)}&v=weekly&language=ko&region=KR&loading=async&callback=${callbackName}`;
            script.onerror = () => {
                finish(null, script);
            };
            document.head.appendChild(script);
            this.waitForGoogleMapsReady(root).then((google: any) => finish(google, script));
        });

        return this.googleMapsLoader;
    }

    private waitForGoogleMapsReady(root: any) {
        return new Promise((resolve) => {
            let startedAt = Date.now();
            let poll = async () => {
                let google = await this.prepareGoogleMaps(root.google);
                if (google) {
                    resolve(google);
                    return;
                }
                if (Date.now() - startedAt > 8000) {
                    resolve(null);
                    return;
                }
                setTimeout(poll, 80);
            };
            poll();
        });
    }

    private async prepareGoogleMaps(google: any) {
        if (!google || !google.maps) return null;

        if (google.maps.importLibrary) {
            try {
                await google.maps.importLibrary('maps');
                await google.maps.importLibrary('marker');
                await google.maps.importLibrary('routes');
            } catch (e) {
                return null;
            }
        }

        return this.isGoogleMapsReady(google) ? google : null;
    }

    private isGoogleMapsReady(google: any) {
        return !!(
            google &&
            google.maps &&
            typeof google.maps.Map === 'function' &&
            typeof google.maps.Marker === 'function' &&
            typeof google.maps.DirectionsService === 'function' &&
            typeof google.maps.DirectionsRenderer === 'function' &&
            typeof google.maps.Polyline === 'function' &&
            google.maps.SymbolPath &&
            google.maps.TravelMode
        );
    }

    private clearGoogleMapOverlays() {
        this.googleRouteToken++;
        this.googleMarkers.forEach((marker: any) => marker.setMap(null));
        this.googleMarkers = [];
        if (this.googleRouteLine) {
            this.googleRouteLine.setMap(null);
            this.googleRouteLine = null;
        }
        if (this.googleCompareLine) {
            this.googleCompareLine.setMap(null);
            this.googleCompareLine = null;
        }
        if (this.googleUserMarker) {
            this.googleUserMarker.setMap(null);
            this.googleUserMarker = null;
        }
        if (this.googleSearchMarker) {
            this.googleSearchMarker.setMap(null);
            this.googleSearchMarker = null;
        }
        if (this.googleDirectionsRenderer) {
            this.googleDirectionsRenderer.setMap(null);
            this.googleDirectionsRenderer = null;
        }
    }

    private resolveGoogleMapsApiKey() {
        if (typeof document !== 'undefined') {
            let meta = document.querySelector('meta[name="google-maps-api-key"]') as HTMLMetaElement;
            if (meta && meta.content) return meta.content.trim();
        }

        let root: any = typeof window !== 'undefined' ? window as any : null;
        if (root && root.TOUR_ON_GOOGLE_MAPS_API_KEY) {
            return String(root.TOUR_ON_GOOGLE_MAPS_API_KEY).trim();
        }

        return '';
    }

    private executionRouteSpots() {
        if (!this.executionCourse) return this.filteredMapSpots();
        let remaining = this.executionPlaces.filter((spot: any) => !spot.visited);
        return remaining.length > 0 ? remaining : this.executionPlaces;
    }

    private executionRouteOrigin() {
        if (!this.executionCourse) return null;
        let origin = this.executionLiveOrigin || this.mapStartCoordinate || this.googleUserCoordinate;
        if (!origin || !this.isFiniteNumber(origin.lat) || !this.isFiniteNumber(origin.lng)) return null;
        return { lat: Number(origin.lat), lng: Number(origin.lng) };
    }

    private googleRoutePath(spots: any[], origin: any) {
        let path = (spots || [])
            .map((spot: any) => this.spotLatLng(spot))
            .filter((point: any) => point && this.isFiniteNumber(point.lat) && this.isFiniteNumber(point.lng));
        if (origin && path.length > 0) return [origin, ...path];
        return path;
    }

    private resetExecutionTravelTimes() {
        if (!this.executionCourse) return;
        this.executionPlaces.forEach((spot: any) => {
            if (!spot.times) spot.times = { walk: '', car: '' };
            spot.times[this.travelMode] = '';
        });
    }

    private applyGoogleRouteLegs(legs: any[], spots: any[], hasOrigin: boolean) {
        if (!this.executionCourse) return;
        let totalSeconds = 0;
        let totalMeters = 0;
        (legs || []).forEach((leg: any) => {
            totalSeconds += Number(leg && leg.duration && leg.duration.value ? leg.duration.value : 0);
            totalMeters += Number(leg && leg.distance && leg.distance.value ? leg.distance.value : 0);
        });
        this.executionTotalMinutes = totalSeconds > 0 ? Math.max(1, Math.round(totalSeconds / 60)) : 0;
        this.executionTotalDistanceMeters = Math.round(totalMeters);

        (spots || []).forEach((spot: any, index: number) => {
            if (!spot.times) spot.times = { walk: '', car: '' };
            let legIndex = -1;
            if (hasOrigin && index === 0) {
                legIndex = 0;
            } else if (index < spots.length - 1) {
                legIndex = hasOrigin ? index + 1 : index;
            }
            let leg = legIndex > -1 && legs && legs[legIndex] ? legs[legIndex] : null;
            spot.times[this.travelMode] = this.routeLegText(leg, hasOrigin && index === 0);
        });
    }

    private applyEstimatedRouteLegs(spots: any[], origin: any) {
        if (!this.executionCourse) return;
        let points = this.googleRoutePath(spots, origin);
        let legs: any[] = [];
        let speedKmh = this.travelMode === 'car' ? 35 : 4.5;
        let totalMeters = 0;
        let totalMinutes = 0;

        for (let index = 0; index < points.length - 1; index++) {
            let current = points[index];
            let next = points[index + 1];
            let distance = this.distanceKm(current.lat, current.lng, next.lat, next.lng);
            let meters = distance === null ? 0 : Math.round(distance * 1000);
            let minutes = distance === null ? 0 : Math.max(1, Math.round((distance / speedKmh) * 60));
            totalMeters += meters;
            totalMinutes += minutes;
            legs.push({
                duration: { value: minutes * 60 },
                distance: { value: meters },
            });
        }

        this.executionTotalMinutes = totalMinutes;
        this.executionTotalDistanceMeters = totalMeters;
        (spots || []).forEach((spot: any, index: number) => {
            if (!spot.times) spot.times = { walk: '', car: '' };
            let legIndex = -1;
            if (origin && index === 0) {
                legIndex = 0;
            } else if (index < spots.length - 1) {
                legIndex = origin ? index + 1 : index;
            }
            let leg = legIndex > -1 ? legs[legIndex] || null : null;
            spot.times[this.travelMode] = this.routeLegText(leg, !!origin && index === 0, true);
        });
    }

    private routeLegText(leg: any, fromStart: boolean = false, estimated: boolean = false) {
        if (!leg || !leg.duration) return fromStart ? '출발지 연결 중' : '마지막 장소';
        let minutes = Math.max(1, Math.round(Number(leg.duration.value || 0) / 60));
        let prefix = fromStart ? '출발' : '다음';
        let suffix = estimated ? ' 예상' : '';
        return `${prefix} ${this.getTravelModeLabel()} ${minutes}분${suffix}`;
    }

    private renderGoogleMarkers(google: any) {
        this.googleMarkers.forEach((marker: any) => marker.setMap(null));
        this.googleMarkers = [];
        if (!this.executionCourse) return;

        this.filteredMapSpots().forEach((spot: any) => {
            let dimmed = this.isMapSpotDimmed(spot);
            let marker = new google.maps.Marker({
                map: this.googleMap,
                position: this.spotLatLng(spot),
                title: spot.name,
                label: {
                    text: String(spot.order),
                    color: '#ffffff',
                    fontSize: '12px',
                    fontWeight: '900'
                },
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 17,
                    fillColor: this.googleMarkerColor(spot),
                    fillOpacity: dimmed ? 0.28 : 1,
                    strokeColor: '#ffffff',
                    strokeOpacity: dimmed ? 0.5 : 1,
                    strokeWeight: 3
                },
                opacity: dimmed ? 0.55 : 1,
                zIndex: this.selectedMapSpotId === spot.id ? 20 : 10
            });

            marker.addListener('click', async () => {
                await this.selectMapSpot(spot);
            });

            this.googleMarkers.push(marker);
        });
    }

    private renderGoogleRoute(google: any) {
        this.googleRouteToken++;
        let token = this.googleRouteToken;
        if (this.googleRouteLine) {
            this.googleRouteLine.setMap(null);
            this.googleRouteLine = null;
        }
        if (this.googleDirectionsRenderer) {
            this.googleDirectionsRenderer.setMap(null);
            this.googleDirectionsRenderer = null;
        }
        if (!this.executionCourse) {
            this.executionTotalMinutes = 0;
            this.executionTotalDistanceMeters = 0;
            this.mapRouteLoading = false;
            return;
        }

        let spots = this.executionRouteSpots();
        let origin = this.executionRouteOrigin();
        let path = this.googleRoutePath(spots, origin);
        this.resetExecutionTravelTimes();
        if (path.length < 2) {
            this.executionTotalMinutes = 0;
            this.executionTotalDistanceMeters = 0;
            this.mapRouteLoading = false;
            this.service.render();
            return;
        }

        this.mapRouteLoading = true;

        this.googleDirectionsRenderer = new google.maps.DirectionsRenderer({
            map: this.googleMap,
            suppressMarkers: true,
            preserveViewport: true,
            polylineOptions: {
                strokeColor: '#e63946',
                strokeOpacity: 0.92,
                strokeWeight: 5
            }
        });

        this.googleDirectionsService.route({
            origin: path[0],
            destination: path[path.length - 1],
            waypoints: path.slice(1, -1).map((position: any) => ({ location: position, stopover: true })),
            travelMode: this.travelMode === 'car' ? google.maps.TravelMode.DRIVING : google.maps.TravelMode.WALKING
        }, (result: any, status: string) => {
            if (token !== this.googleRouteToken) return;
            if (status === 'OK') {
                this.googleDirectionsRenderer.setDirections(result);
                let route = result && result.routes && result.routes[0] ? result.routes[0] : {};
                this.applyGoogleRouteLegs(route.legs || [], spots, !!origin);
                this.mapRouteLoading = false;
                this.service.render();
                return;
            }

            this.googleDirectionsRenderer.setMap(null);
            this.googleDirectionsRenderer = null;
            this.googleRouteLine = new google.maps.Polyline({
                map: this.googleMap,
                path,
                strokeColor: '#e63946',
                strokeOpacity: 0.9,
                strokeWeight: 5
            });
            this.applyEstimatedRouteLegs(spots, origin);
            this.mapRouteLoading = false;
            this.service.render();
        });
    }

    private renderGoogleUserMarker(coordinate: any) {
        let root: any = typeof window !== 'undefined' ? window as any : null;
        let google = root && root.google ? root.google : null;
        if (!google || !google.maps || !this.googleMap) return;

        if (this.googleUserMarker) this.googleUserMarker.setMap(null);
        this.googleUserMarker = new google.maps.Marker({
            map: this.googleMap,
            position: coordinate,
            title: '내 위치',
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 9,
                fillColor: '#d94a58',
                fillOpacity: 1,
                strokeColor: '#ffffff',
                strokeWeight: 4
            },
            zIndex: 30
        });
    }

    private renderGoogleSearchMarker(coordinate: any) {
        let root: any = typeof window !== 'undefined' ? window as any : null;
        let google = root && root.google ? root.google : null;
        if (!google || !google.maps || !this.googleMap) return;

        if (this.googleSearchMarker) this.googleSearchMarker.setMap(null);
        this.googleSearchMarker = new google.maps.Marker({
            map: this.googleMap,
            position: coordinate,
            title: '검색 위치',
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 10,
                fillColor: '#e63946',
                fillOpacity: 1,
                strokeColor: '#ffffff',
                strokeWeight: 4
            },
            zIndex: 32
        });
    }

    private googleMarkerColor(spot: any) {
        if (this.executionCourse) return '#e63946';
        if (spot.visited) return '#56504e';
        if (this.selectedMapSpotId === spot.id) return '#e63946';
        let colors: any = {
            cafe: '#1f8a70',
            food: '#d58a1f',
            walk: '#d94a58',
            landmark: '#e63946'
        };
        return colors[spot.category] || '#1f8a70';
    }

    private spotLatLng(spot: any) {
        let lat = this.safeNumber(spot && spot.lat);
        let lng = this.safeNumber(spot && spot.lng);
        if (lat !== null && lng !== null) return { lat, lng };
        return this.canvasPointLatLng(spot.x, spot.y);
    }

    private canvasPointLatLng(x: number, y: number) {
        let center = this.currentMapCenter();
        let centerPoint = this.lngLatToTilePoint(center.lng, center.lat, center.zoom);
        let point = {
            x: centerPoint.x + ((x - 50) / 100),
            y: centerPoint.y + ((y - 50) / 100)
        };
        return this.tilePointToLngLat(point.x, point.y, center.zoom);
    }

    private allCourses() {
        let seen: any = {};
        return [...this.recommendations, ...this.courses, ...this.placeCourses].filter((course: any) => {
            let id = course && course.id ? course.id : '';
            if (!id) return true;
            if (seen[id]) return false;
            seen[id] = true;
            return true;
        });
    }

    private routePoints(spots: any[]) {
        if (!spots || spots.length < 2) return '';
        return spots.map((spot: any) => `${spot.x},${spot.y}`).join(' ');
    }

    private currentMapCenter() {
        if (!this.executionCourse && this.googleSearchCoordinate) {
            return { lat: Number(this.googleSearchCoordinate.lat), lng: Number(this.googleSearchCoordinate.lng), zoom: 15 };
        }
        if (this.executionPlaces && this.executionPlaces.length > 0) {
            let first = this.executionPlaces.find((spot: any) => this.isFiniteNumber(spot.lat) && this.isFiniteNumber(spot.lng));
            if (first) return { lat: Number(first.lat), lng: Number(first.lng), zoom: 15 };
        }
        let location = this.selectedFilters.location || '';
        let region = this.getRegionForLocation(location);
        return this.mapCenters[location] || this.mapCenters[region] || this.mapCenters.default;
    }

    private lngLatToTile(lng: number, lat: number, zoom: number) {
        let latRad = lat * Math.PI / 180;
        let scale = Math.pow(2, zoom);
        let x = Math.floor((lng + 180) / 360 * scale);
        let y = Math.floor((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2 * scale);
        return { x, y };
    }

    private projectMapPosition(lat: number, lng: number) {
        let center = this.currentMapCenter();
        let centerPoint = this.lngLatToTilePoint(center.lng, center.lat, center.zoom);
        let userPoint = this.lngLatToTilePoint(lng, lat, center.zoom);
        let x = 50 + ((userPoint.x - centerPoint.x) * 100);
        let y = 50 + ((userPoint.y - centerPoint.y) * 100);
        return {
            x: Math.min(92, Math.max(8, x)),
            y: Math.min(92, Math.max(8, y))
        };
    }

    private lngLatToTilePoint(lng: number, lat: number, zoom: number) {
        let latRad = lat * Math.PI / 180;
        let scale = Math.pow(2, zoom);
        let x = (lng + 180) / 360 * scale;
        let y = (1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2 * scale;
        return { x, y };
    }

    private tilePointToLngLat(x: number, y: number, zoom: number) {
        let scale = Math.pow(2, zoom);
        let lng = x / scale * 360 - 180;
        let n = Math.PI - (2 * Math.PI * y / scale);
        let lat = 180 / Math.PI * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
        return { lat, lng };
    }

    private touchDistance(touches: any) {
        let first = touches[0];
        let second = touches[1];
        let x = first.clientX - second.clientX;
        let y = first.clientY - second.clientY;
        return Math.sqrt((x * x) + (y * y));
    }

    private getCompanionPhrase(value: string) {
        let phraseMap: any = {
            '연인': '연인과',
            '친구': '친구와',
            '가족': '가족과',
            '혼자': '혼자'
        };
        return phraseMap[value] || '';
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
        let weeks = [];
        let days = [];

        this.calendarMonthLabel = `${year}년 ${month + 1}월`;

        for (let weekIndex = 0; weekIndex < 6; weekIndex++) {
            let week = [];
            for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
                let date = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate() + (weekIndex * 7) + dayIndex);
                let key = this.toDateKey(date);
                let item = {
                    key,
                    label: date.getDate(),
                    inMonth: date.getMonth() === month,
                    isToday: key === this.todayKey,
                    ariaLabel: `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`
                };
                week.push(item);
                days.push(item);
            }
            weeks.push(week);
        }

        this.calendarWeeks = weeks;
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
            this.selectedFilters.schedule = '';
            return;
        }

        this.scheduleRange = range;
        this.draftScheduleRange = range;
        this.selectedFilters.schedule = this.formatScheduleRangeLabel(range.start, range.end);
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

    private scheduleDurationToken() {
        if (!this.scheduleRange.start || !this.scheduleRange.end) return '';
        let startDate = this.fromDateKey(this.scheduleRange.start);
        let endDate = this.fromDateKey(this.scheduleRange.end);
        let diff = endDate.getTime() - startDate.getTime();
        let days = Math.round(diff / 86400000) + 1;

        if (days <= 1) return this.scheduleRange.start === this.todayKey ? '오늘' : '당일치기';
        if (days === 2) return '1박2일';
        return '여행';
    }

    private syncLocationRegion() {
        let location = this.selectedFilters.location || '';
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

    private restoreIncomingState() {
        let stored = this.readAccessState();
        if (stored) {
            if (stored.selectedFilters) {
                this.selectedFilters = { ...this.selectedFilters, ...stored.selectedFilters };
            }
            if (typeof stored.selectedKeyword === 'string') this.selectedKeyword = stored.selectedKeyword;
            if (typeof stored.query === 'string') this.query = stored.query;
            let storedCompanionMode = String(stored.companionMode || '');
            if (['pretrip', 'instant'].indexOf(storedCompanionMode) > -1) {
                this.companionMode = storedCompanionMode;
            } else if (storedCompanionMode === 'friend') {
                this.companionMode = 'pretrip';
            }
            this.applyIncomingAccessTab(stored.activeTab);
            if (this.isSupportedMapContentTab(stored.mapContentTab)) this.mapContentTab = this.normalizeMapContentTab(stored.mapContentTab);
            if (stored.scheduleRange) this.restoreScheduleRange(stored.scheduleRange);
            if (this.isSupportedTravelMode(stored.travelMode)) this.travelMode = String(stored.travelMode);
            if (this.isSupportedMoveFilter(stored.selectedMoveFilter)) this.selectedMoveFilter = String(stored.selectedMoveFilter || '');
        }

        let params = this.currentSearchParams();
        let identityReturnId = params.get('identityVerificationId') || params.get('identity_verification_id') || '';
        if (identityReturnId) {
            this.passIdentityReturnId = identityReturnId;
            this.activeTab = 'my';
        }
        let filterKeys = ['companion', 'schedule', 'location'];
        let hasFilterParams = filterKeys.some((key: string) => params.has(key));
        if (hasFilterParams) {
            this.selectedFilters = {
                companion: '',
                schedule: '',
                location: ''
            };
        }

        filterKeys.forEach((key: string) => {
            if (params.has(key)) this.selectedFilters[key] = params.get(key) || '';
        });

        if (params.has('keyword')) this.selectedKeyword = params.get('keyword') || '';
        if (params.has('q')) this.query = params.get('q') || '';
        this.applyIncomingAccessTab(params.get('tab'));
        let incomingCompanionMode = params.get('companionMode') || '';
        if (['pretrip', 'instant'].indexOf(incomingCompanionMode) > -1) {
            this.companionMode = incomingCompanionMode;
            this.activeTab = 'home';
            this.homeContentTab = 'companion';
        } else if (incomingCompanionMode === 'friend') {
            this.companionMode = 'pretrip';
            this.activeTab = 'home';
            this.homeContentTab = 'companion';
        }
        if (params.has('companionInvite')) {
            this.companionMode = 'pretrip';
            this.activeTab = 'home';
            this.homeContentTab = 'companion';
        }
        if (params.get('compose') === 'course') {
            this.courseComposerOpen = true;
            this.courseBuilderMode = 'manual';
            this.courseBuilderStep = 'info';
        }
        if (this.isSupportedMapContentTab(params.get('mapMode'))) this.mapContentTab = this.normalizeMapContentTab(params.get('mapMode'));
        let incomingTravelMode = params.get('move') || params.get('travelMode');
        if (this.isSupportedMoveFilter(incomingTravelMode)) {
            this.selectedMoveFilter = String(incomingTravelMode || '');
            if (this.selectedMoveFilter && this.isSupportedTravelMode(this.selectedMoveFilter)) this.travelMode = this.selectedMoveFilter;
        }
        let prompt = params.get('prompt') || '';
        if (prompt) {
            this.consumeStoredChatPrompt();
        } else {
            prompt = this.consumeStoredChatPrompt();
        }
        if (prompt) {
            this.activeTab = 'chat';
            this.chatContentTab = 'chat';
            this.pendingChatPrompt = prompt;
        }
        if (params.has('scheduleStart') && params.has('scheduleEnd')) {
            this.restoreScheduleRange({
                start: params.get('scheduleStart'),
                end: params.get('scheduleEnd')
            });
            if (!params.has('schedule') && this.scheduleRange.start) {
                this.selectedFilters.schedule = this.formatScheduleRangeLabel(this.scheduleRange.start, this.scheduleRange.end);
            }
        }

        this.syncLocationRegion();
        this.syncCalendarToSchedule();
        this.persistAccessState();
        this.replaceAccessUrl();
    }

    private restoreScheduleRange(value: any) {
        if (!value || !value.start || !value.end) return;
        let range = this.normalizeDateRange(String(value.start), String(value.end));
        this.scheduleRange = range;
        this.draftScheduleRange = range;
    }

    private syncCalendarToSchedule() {
        if (!this.scheduleRange.start) return;
        let date = this.fromDateKey(this.scheduleRange.start);
        this.calendarMonth = new Date(date.getFullYear(), date.getMonth(), 1);
        this.buildCalendar();
    }

    private persistAccessState() {
        if (typeof window === 'undefined' || !window.sessionStorage) return;
        try {
            window.sessionStorage.setItem('tour-on-access-state', JSON.stringify({
                activeTab: this.activeTab,
                mapContentTab: this.mapContentTab,
                companionMode: this.companionMode,
                travelMode: this.travelMode,
                selectedMoveFilter: this.selectedMoveFilter,
                selectedFilters: { ...this.selectedFilters },
                selectedKeyword: this.selectedKeyword,
                query: this.query,
                scheduleRange: { ...this.scheduleRange }
            }));
        } catch (e) { }
    }

    private readAccessState() {
        if (typeof window === 'undefined' || !window.sessionStorage) return null;
        try {
            let raw = window.sessionStorage.getItem('tour-on-access-state');
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    }

    private clearStoredAccessState() {
        if (typeof window === 'undefined' || !window.sessionStorage) return;
        try {
            window.sessionStorage.removeItem('tour-on-access-state');
            window.sessionStorage.removeItem('tour-on-chat-prompt');
        } catch (e) { }
    }

    private loadRecentPlaces() {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            let raw = window.localStorage.getItem(this.recentPlacesStorageKey()) || '[]';
            let rows = JSON.parse(raw);
            this.recentPlaces = Array.isArray(rows)
                ? rows.filter((place: any) => !this.isLegacyExamplePlaceId(place && place.id)).slice(0, 6)
                : [];
            this.persistRecentPlaces();
        } catch (e) {
            this.recentPlaces = [];
        }
    }

    private persistRecentPlaces() {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            window.localStorage.setItem(this.recentPlacesStorageKey(), JSON.stringify(this.recentPlaces.slice(0, 6)));
        } catch (e) { }
    }

    private isLegacyExamplePlaceId(value: any) {
        let id = String(value || '').trim().toLowerCase();
        return ['default-', 'seoul-', 'busan-', 'jeju-', 'gyeonggi-', 'gangwon-', 'chungcheong-', 'jeolla-', 'gyeongsang-', 'saved-place-']
            .some((prefix: string) => id.indexOf(prefix) === 0);
    }

    private recordRecentPlace(spot: any) {
        if (!spot || !spot.id) return;

        let location = String(spot.location || this.getMapLocationLabel() || '국내').trim() || '국내';
        let place = {
            id: spot.id,
            name: spot.name || spot.title || '추천 장소',
            kind: spot.kind || spot.distance || '장소',
            category: spot.category || '',
            icon: spot.icon || 'fa-location-dot',
            location,
            description: spot.description || spot.summary || '',
            viewedAt: new Date().toISOString()
        };

        this.recentPlaces = [
            place,
            ...this.recentPlaces.filter((item: any) => item && item.id !== place.id)
        ].slice(0, 6);
        this.persistRecentPlaces();
    }

    private recentPlacesStorageKey() {
        let auth = this.service && this.service.auth ? this.service.auth : null;
        let session = auth && auth.session ? auth.session : {};
        let owner = String(session.id || session.email || session.name || '').trim();
        if (!owner) return this.recentPlacesStorageBaseKey;
        return `${this.recentPlacesStorageBaseKey}:${encodeURIComponent(owner)}`;
    }

    private loadMyProfileEdit() {
        if (typeof window === 'undefined' || !window.localStorage) {
            this.myProfileEdit = this.defaultMyProfileEdit();
            return;
        }

        try {
            let raw = window.localStorage.getItem(this.myProfileEditStorageKey());
            let saved = raw ? JSON.parse(raw) : {};
            this.myProfileEdit = { ...this.defaultMyProfileEdit(), ...(saved && typeof saved === 'object' ? saved : {}) };
            this.ensureMyProfileEditDefaults();
        } catch (e) {
            this.myProfileEdit = this.defaultMyProfileEdit();
        }
    }

    private persistMyProfileEdit() {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            window.localStorage.setItem(this.myProfileEditStorageKey(), JSON.stringify(this.myProfileEdit));
        } catch (e) { }
    }

    private myProfileEditStorageKey() {
        let auth = this.service && this.service.auth ? this.service.auth : null;
        let session = auth && auth.session ? auth.session : {};
        let owner = String(session.id || session.email || session.name || '').trim();
        if (!owner) return this.myProfileEditStorageBaseKey;
        return `${this.myProfileEditStorageBaseKey}:${encodeURIComponent(owner)}`;
    }

    private loadMyCourseViewMode() {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            let mode = String(window.localStorage.getItem(this.myCourseViewModeStorageKey()) || 'list');
            this.myCourseViewMode = ['list', 'grid', 'blog'].indexOf(mode) > -1 ? mode : 'list';
        } catch (e) {
            this.myCourseViewMode = 'list';
        }
    }

    private persistMyCourseViewMode() {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            window.localStorage.setItem(this.myCourseViewModeStorageKey(), this.myCourseViewMode);
        } catch (e) { }
    }

    private myCourseViewModeStorageKey() {
        let auth = this.service && this.service.auth ? this.service.auth : null;
        let session = auth && auth.session ? auth.session : {};
        let owner = String(session.id || session.email || session.nickname || session.name || '').trim();
        if (!owner) return this.myCourseViewModeStorageBaseKey;
        return `${this.myCourseViewModeStorageBaseKey}:${encodeURIComponent(owner)}`;
    }

    private defaultMyProfileEdit() {
        return {
            photo: '',
            nickname: '',
            region: '',
            intro: ''
        };
    }

    private ensureMyProfileEditDefaults() {
        if (!this.myProfileEdit || typeof this.myProfileEdit !== 'object') this.myProfileEdit = this.defaultMyProfileEdit();
        if (typeof this.myProfileEdit.photo === 'undefined') this.myProfileEdit.photo = '';
        if (typeof this.myProfileEdit.nickname === 'undefined') this.myProfileEdit.nickname = '';
        if (typeof this.myProfileEdit.region === 'undefined') this.myProfileEdit.region = '';
        if (typeof this.myProfileEdit.intro === 'undefined') this.myProfileEdit.intro = '';
    }

    private loadTravelResume() {
        if (typeof window === 'undefined' || !window.localStorage) {
            this.travelResume = this.defaultTravelResume();
            return;
        }

        try {
            let raw = window.localStorage.getItem(this.travelResumeStorageKey());
            let saved = raw ? JSON.parse(raw) : {};
            this.travelResume = { ...this.defaultTravelResume(), ...(saved && typeof saved === 'object' ? saved : {}) };
            this.migrateTravelResume(saved);
            this.ensureTravelResumeDefaults();
        } catch (e) {
            this.travelResume = this.defaultTravelResume();
        }
    }

    private persistTravelResume() {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            window.localStorage.setItem(this.travelResumeStorageKey(), JSON.stringify(this.travelResume));
        } catch (e) { }
    }

    private travelResumeStorageKey() {
        let auth = this.service && this.service.auth ? this.service.auth : null;
        let session = auth && auth.session ? auth.session : {};
        let owner = String(session.id || session.email || session.name || '').trim();
        if (!owner) return this.travelResumeStorageBaseKey;
        return `${this.travelResumeStorageBaseKey}:${encodeURIComponent(owner)}`;
    }

    private defaultTravelResume() {
        return {
            schemaVersion: 2,
            photo: '',
            fullName: '',
            age: '',
            gender: '',
            region: '',
            companionUses: this.inferredCompanionUseCount(),
            interests: '',
            smoking: '',
            drinking: '',
            travelExperience: '',
            intro: ''
        };
    }

    private migrateTravelResume(saved: any) {
        let source = saved && typeof saved === 'object' ? saved : {};
        if (typeof source.fullName === 'string') {
            this.travelResume.fullName = source.fullName;
        } else {
            let legacyName = String(source.name || '').trim();
            let accountNickname = String(this.myDisplayName() || '').trim();
            this.travelResume.fullName = legacyName && legacyName !== accountNickname ? legacyName : '';
        }
        if (String(this.travelResume.smoking || '') === 'flexible') this.travelResume.smoking = '';
        delete this.travelResume.name;
        delete this.travelResume.travelPace;
        delete this.travelResume.budgetStyle;
        this.travelResume.schemaVersion = 2;
    }

    private ensureTravelResumeDefaults() {
        if (!this.travelResume || typeof this.travelResume !== 'object') this.travelResume = this.defaultTravelResume();
        if (typeof this.travelResume.schemaVersion === 'undefined') this.travelResume.schemaVersion = 2;
        if (typeof this.travelResume.photo === 'undefined') this.travelResume.photo = '';
        if (typeof this.travelResume.fullName === 'undefined') this.travelResume.fullName = '';
        if (typeof this.travelResume.age === 'undefined') this.travelResume.age = '';
        if (typeof this.travelResume.gender === 'undefined') this.travelResume.gender = '';
        if (typeof this.travelResume.region === 'undefined') this.travelResume.region = '';
        if (typeof this.travelResume.companionUses === 'undefined') this.travelResume.companionUses = this.inferredCompanionUseCount();
        if (typeof this.travelResume.interests === 'undefined') this.travelResume.interests = '';
        if (typeof this.travelResume.smoking === 'undefined') this.travelResume.smoking = '';
        if (typeof this.travelResume.drinking === 'undefined') this.travelResume.drinking = '';
        if (typeof this.travelResume.travelExperience === 'undefined') this.travelResume.travelExperience = '';
        if (typeof this.travelResume.intro === 'undefined') this.travelResume.intro = '';
        delete this.travelResume.name;
        delete this.travelResume.travelPace;
        delete this.travelResume.budgetStyle;
    }

    private hasCompletedTravelResume() {
        this.ensureTravelResumeDefaults();
        return this.travelResumeCompletion() === 100;
    }

    private async promptTravelResumeCompletion() {
        this.activeTab = 'my';
        this.myProfileOpen = true;
        this.travelResumeReturnToSettings = false;
        this.myResumeOpen = true;
        this.myResumePreviewOpen = false;
        this.travelResumeStep = 1;
        this.persistAccessState();
        this.replaceAccessUrl();
        await this.loadTravelIdentityStatus();
        await this.showSaveHint('여행 이력서를 완성한 후에 동행 신청해주세요.');
    }

    private createCompanionApplication(post: any) {
        this.ensureTravelResumeDefaults();
        this.travelResume.age = this.normalizePositiveNumber(this.travelResume.age);
        this.travelResume.companionUses = this.normalizePositiveNumber(this.travelResume.companionUses);
        this.persistTravelResume();

        let applicantKey = this.currentCompanionApplicantKey();
        let applicantNickname = this.profileDisplayName();
        return {
            id: `application-${post && post.id ? post.id : Date.now()}-${Date.now()}`,
            applicantKey,
            applicantNickname,
            appliedAt: '방금',
            status: 'pending',
            resume: {
                photo: String(this.travelResume.photo || '').trim(),
                fullName: String(this.travelResume.fullName || '').trim(),
                nickname: applicantNickname,
                age: this.normalizePositiveNumber(this.travelResume.age),
                gender: String(this.travelResume.gender || '').trim(),
                region: String(this.travelResume.region || '').trim(),
                companionUses: this.travelResumeCompanionUses(),
                interests: String(this.travelResume.interests || '').trim(),
                smoking: String(this.travelResume.smoking || '').trim(),
                drinking: String(this.travelResume.drinking || '').trim(),
                identityVerified: this.isTravelResumeIdentityVerified(),
                reviewScore: 0,
                availabilityConfirmed: true,
                travelExperience: String(this.travelResume.travelExperience || '').trim(),
                intro: String(this.travelResume.intro || '').trim()
            }
        };
    }

    private currentCompanionApplicantKey() {
        let auth = this.service && this.service.auth ? this.service.auth : null;
        let session = auth && auth.session ? auth.session : {};
        return String(session.id || session.email || session.name || this.myDisplayName()).trim();
    }

    private companionApplicationResume(application: any) {
        if (!application || !application.resume || typeof application.resume !== 'object') return {};
        return application.resume;
    }

    private inferredCompanionUseCount() {
        return this.companionPosts.filter((post: any) => post && (post.status === 'matched' || post.saved)).length;
    }

    private normalizePositiveNumber(value: any) {
        let number = Number(value || 0);
        if (!isFinite(number) || number < 0) return 0;
        return Math.floor(number);
    }

    private replaceAccessUrl() {
        if (typeof window === 'undefined' || !window.history) return;
        if (this.routeRootHomeIfEmptyFilters()) return;

        let params = new URLSearchParams();
        params.set('tab', this.activeTab);
        if (this.activeTab === 'map' && this.mapContentTab !== 'map') params.set('mapMode', this.mapContentTab === 'zenly' ? 'together' : this.mapContentTab);
        if (this.selectedMoveFilter) params.set('move', this.selectedMoveFilter);
        Object.keys(this.selectedFilters).forEach((key: string) => {
            if (this.selectedFilters[key]) params.set(key, this.selectedFilters[key]);
        });
        if (this.selectedKeyword) params.set('keyword', this.selectedKeyword);
        if (this.query) params.set('q', this.query);
        if (this.scheduleRange.start && this.scheduleRange.end) {
            params.set('scheduleStart', this.scheduleRange.start);
            params.set('scheduleEnd', this.scheduleRange.end);
        }

        let nextUrl = `/access?${params.toString()}`;
        if (window.location.pathname === '/access' && `${window.location.pathname}${window.location.search}` !== nextUrl) {
            window.history.replaceState(null, '', nextUrl);
        }
    }

    private routeRootHomeIfEmptyFilters() {
        return false;
    }

    private routeLoginForMap() {
        if (this.activeTab !== 'map') return false;
        if (this.isLoggedIn()) return false;

        this.goMapLogin();
        return true;
    }

    private shouldUseRootHome() {
        return false;
    }

    private currentSearchParams() {
        if (typeof window === 'undefined') return new URLSearchParams();
        return new URLSearchParams(window.location.search || '');
    }

    private applyIncomingAccessTab(tab: any) {
        let value = String(tab || '');
        if (value === 'zenly' || value === 'together') {
            this.activeTab = 'map';
            this.mapContentTab = 'zenly';
            return;
        }
        if (this.isSupportedAccessTab(value)) this.activeTab = value;
    }

    private isSupportedMapContentTab(tab: any) {
        return ['map', 'zenly', 'together'].indexOf(String(tab || '')) > -1;
    }

    private normalizeMapContentTab(tab: any) {
        let value = String(tab || 'map');
        return value === 'together' ? 'zenly' : value;
    }

    private isSupportedTravelMode(mode: any) {
        return this.mapTravelModes.some((item: any) => item.key === String(mode || ''));
    }

    private isSupportedMoveFilter(mode: any) {
        return this.moveFilterOptions.some((item: any) => item.key === String(mode || ''));
    }

    private isSupportedAccessTab(tab: any) {
        return ['home', 'chat', 'map', 'saved', 'my'].indexOf(String(tab || '')) > -1;
    }

    private defaultChatMessage() {
        return {
            role: 'assistant',
            text: '어디로, 누구와, 언제 가는지만 말해주면 코스 초안을 바로 잡아드릴게요.',
            time: '오전 10:30',
            seed: true
        };
    }

    private defaultCourseDraft() {
        return {
            title: '',
            region: '',
            schedule: '',
            scheduleDate: '',
            scheduleEndDate: '',
            places: '',
            photo: '',
            photoName: '',
            description: '',
            category: '여행',
            companionType: 'friend',
            isPublic: true,
            companionEnabled: false,
            companionDate: '',
            companionTime: '',
            companionCapacity: 2,
            companionCost: '',
            companionBudgetStyle: '',
            companionPace: '',
            companionMood: '',
            companionFlexible: '',
            companionMeetingPoint: '',
            companionSmoking: '',
            companionDrinking: '',
            companionIntro: ''
        };
    }

    private resetCourseComposerDraftState() {
        this.courseDraft = this.defaultCourseDraft();
        this.courseBuilderPlaces = [];
        this.courseComposerPlannerEdit = false;
        this.courseBuilderDayIndex = 0;
        this.courseBuilderDays = [];
        this.courseBuilderOriginalDays = [];
        this.courseAiRebuilding = false;
        this.coursePlaceSearchQuery = '';
        this.coursePlaceSearchResults = [];
        this.coursePlaceSearchOpen = false;
        this.coursePlaceSearching = false;
        this.courseRegionSearchOpen = false;
        this.courseBuilderMode = '';
        this.courseBuilderStep = 'mode';
        this.courseBuilderError = '';
        this.coursePublishModalOpen = false;
        this.coursePublishSubmitting = false;
        this.courseDraftSavedAt = '';
        this.courseAiMood = '';
        this.courseDateDragActive = false;
        this.courseDateDragStartKey = '';
        this.courseDateCalendarMonth = new Date();
    }

    private persistCourseDraft() {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            let savedAt = new Date().toISOString();
            window.localStorage.setItem(this.courseDraftStorageKey(), JSON.stringify({
                ...this.courseDraft,
                builderPlaces: this.courseBuilderPlaces,
                builderMode: this.courseBuilderMode,
                builderStep: this.courseBuilderStep,
                aiMood: this.courseAiMood,
                savedAt
            }));
            this.courseDraftSavedAt = this.formatCourseDraftSavedAt(savedAt);
            this.refreshCourseDraftArchiveSummary();
        } catch (e) { }
    }

    private restoreCourseDraft(force: boolean) {
        let saved = this.readCourseDraft();
        if (!saved) return false;
        this.courseDraftSavedAt = this.formatCourseDraftSavedAt(saved.savedAt);
        if (!force && this.hasCourseDraftContent()) return false;
        let draft = { ...saved };
        delete draft.builderPlaces;
        delete draft.builderMode;
        delete draft.builderStep;
        delete draft.aiMood;
        delete draft.savedAt;
        this.courseDraft = {
            ...this.defaultCourseDraft(),
            ...draft
        };
        this.courseAiMood = String(saved.aiMood || '');
        let mode = String(saved.builderMode || '').trim();
        this.courseBuilderMode = mode === 'manual' || mode === 'ai' ? mode : 'manual';
        let step = String(saved.builderStep || '').trim();
        this.courseBuilderStep = ['mode', 'info', 'ai', 'places'].indexOf(step) > -1 ? step : 'info';
        if (this.courseBuilderStep === 'mode' && this.hasCourseDraftContent()) this.courseBuilderStep = this.courseBuilderMode === 'ai' ? 'ai' : 'info';
        if (this.courseBuilderStep === 'ai') this.courseBuilderMode = 'ai';
        if (this.courseBuilderStep === 'info') this.courseBuilderMode = 'manual';
        this.courseBuilderPlaces = Array.isArray(saved.builderPlaces)
            ? saved.builderPlaces
            : this.splitList(saved.places).map((name: string, index: number) => ({
                placeId: `manual-${index}-${name}`,
                name,
                lat: null,
                lng: null,
                order: index + 1,
                visitTime: this.visitTimeForIndex(index),
                memo: '',
                area: saved.region || '',
                address: '',
                category: '',
                image: '',
                manualTime: false
            }));
        this.normalizeCourseBuilderOrder(false);
        return true;
    }

    private readCourseDraft() {
        if (typeof window === 'undefined' || !window.localStorage) return null;
        try {
            let raw = window.localStorage.getItem(this.courseDraftStorageKey());
            let saved = raw ? JSON.parse(raw) : null;
            if (!saved || typeof saved !== 'object') return null;
            return saved;
        } catch (e) {
            return null;
        }
    }

    private clearCourseDraftStorage() {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            window.localStorage.removeItem(this.courseDraftStorageKey());
            this.refreshCourseDraftArchiveSummary();
        } catch (e) { }
    }

    private ensureCourseDraftArchiveSummary() {
        if (!this.courseDraftArchiveChecked) this.refreshCourseDraftArchiveSummary();
    }

    private refreshCourseDraftArchiveSummary() {
        let saved = this.readCourseDraft();
        this.courseDraftArchiveSummary = saved ? {
            title: saved.title || '',
            region: saved.region || '',
            schedule: saved.schedule || '',
            savedAt: saved.savedAt || '',
            placeCount: Array.isArray(saved.builderPlaces) ? saved.builderPlaces.length : this.splitList(saved.places).length
        } : null;
        this.courseDraftArchiveChecked = true;
    }

    private hasCourseDraftContent() {
        let draft = this.courseDraft || {};
        if (this.courseBuilderPlaces.length > 0) return true;
        return ['title', 'region', 'schedule', 'places', 'photo', 'description'].some((key: string) => {
            return String(draft[key] || '').trim().length > 0;
        });
    }

    private courseDraftStorageKey() {
        let auth = this.service && this.service.auth ? this.service.auth : null;
        let session = auth && auth.session ? auth.session : {};
        let owner = String(session.id || session.email || session.name || '').trim();
        if (!owner) return this.courseDraftStorageBaseKey;
        return `${this.courseDraftStorageBaseKey}:${encodeURIComponent(owner)}`;
    }

    private formatCourseDraftSavedAt(value: any) {
        if (!value) return '';
        let date = new Date(value);
        if (Number.isNaN(date.getTime())) return '';
        return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
    }

    private mapSpotsForCourseDraftRegion() {
        let location = String(this.courseDraft.region || '').trim();
        let region = this.getRegionForLocation(location);
        if (location && this.mapSpotMap[location]) return this.mapSpotMap[location];
        if (region && this.mapSpotMap[region]) return this.mapSpotMap[region];
        return this.mapSpotMap.default;
    }

    private findCourseDraftSpotMatch(place: string, spots: any[]) {
        let normalized = String(place || '').replace(/\s+/g, '').toLowerCase();
        if (!normalized) return null;
        return spots.find((spot: any) => {
            let name = String(spot.name || '').replace(/\s+/g, '').toLowerCase();
            let kind = String(spot.kind || '').replace(/\s+/g, '').toLowerCase();
            return normalized.indexOf(name) > -1 || name.indexOf(normalized) > -1 || (kind && normalized.indexOf(kind) > -1);
        }) || null;
    }

    private fallbackCourseDraftSpot(place: string, index: number, total: number) {
        let radiusX = 28;
        let radiusY = 22;
        let angle = total <= 1 ? -Math.PI / 2 : (-Math.PI / 2) + (Math.PI * 2 * index / total);
        return {
            name: place,
            x: Math.round(50 + (Math.cos(angle) * radiusX)),
            y: Math.round(50 + (Math.sin(angle) * radiusY)),
            icon: 'fa-location-dot'
        };
    }

    private defaultCommunityDraft() {
        return {
            kind: 'post',
            topic: 'recommend',
            title: '',
            body: '',
            hasDestination: true,
            destination: '',
            photo: '',
            photoName: '',
            place: '',
            pollOptions: [],
            pollInput: '',
            tags: [],
            tagInput: ''
        };
    }

    private splitList(value: any) {
        if (Array.isArray(value)) {
            return value
                .map((item: any) => String(item || '').trim())
                .filter((item: string) => item.length > 0);
        }
        return String(value || '')
            .split(/[,\n]/)
            .map((item: string) => item.trim())
            .filter((item: string) => item.length > 0);
    }

    private normalizeDraftList(value: any) {
        return this.splitList(value);
    }

    private normalizeCommunityTag(value: any) {
        return String(value || '')
            .trim()
            .replace(/^#+/, '')
            .replace(/[#,]/g, '')
            .trim();
    }

    private normalizeCommunityDraftTags(value: any) {
        return this.splitList(value)
            .map((tag: string) => this.normalizeCommunityTag(tag))
            .filter((tag: string) => !!tag);
    }

    private ensureDirectChatForCompanion(post: any, application?: any) {
        if (!application) {
            application = this.companionApplications(post).find((item: any) => {
                return item && (item.status === 'accepted' || item.id === post.selectedApplicationId);
            });
        }
        let id = `dm-${post.id}`;
        let existing = this.directChats.find((chat: any) => chat.id === id || chat.companionPostId === post.id);
        let applicantName = this.companionApplicationName(application);
        let chatName = application ? applicantName : (post.host || '동행 작성자');
        let preparation = this.companionPreparationFromPost(post);
        if (!existing) {
            existing = {
                id,
                companionPostId: post.id,
                name: chatName,
                handle: post.route || post.title,
                avatar: String(chatName || '동').charAt(0),
                status: '동행 준비방',
                preview: '코스와 약속 장소, 준비물을 확인하고 채팅해보세요.',
                time: '방금',
                unread: 1,
                category: 'companion',
                preparation,
                muted: false,
                blocked: false,
                messages: [
                    { role: 'other', text: '동행 신청을 수락했어요. 준비방에서 코스와 약속 장소를 같이 확인해요.', time: '방금' }
                ]
            };
            this.directChats = [existing, ...this.directChats];
        } else {
            existing.companionPostId = post.id;
            existing.status = '동행 준비방';
            existing.category = 'companion';
            existing.handle = post.route || post.title;
            existing.preparation = {
                ...preparation,
                ...(existing.preparation || {}),
                packingItems: existing.preparation && Array.isArray(existing.preparation.packingItems)
                    ? existing.preparation.packingItems
                    : preparation.packingItems
            };
        }
        this.activeDirectChatId = existing.id;
        return existing;
    }

    private hydrateCompanionPreparationRooms() {
        this.companionPosts.filter((post: any) => post && post.status === 'matched').forEach((post: any) => {
            this.ensureDirectChatForCompanion(post);
        });
    }

    private companionPreparationFromPost(post: any) {
        let packingItems = Array.isArray(post && post.packingItems) ? post.packingItems : this.splitList(post && post.packingItems ? post.packingItems : '');
        return {
            collapsed: true,
            courseId: String(post && post.courseId ? post.courseId : ''),
            courseConfirmed: !!(post && post.courseConfirmed),
            courseTitle: String(post && post.route ? post.route : post && post.title ? post.title : '여행 코스'),
            routeStops: this.companionRouteStops(post),
            date: String(post && post.date ? post.date : '일정 협의'),
            time: String(post && post.time ? post.time : '시간 협의'),
            meetingPoint: String(post && post.meetingPoint ? post.meetingPoint : '준비방에서 약속 장소를 정해주세요.'),
            estimatedCost: String(post && post.estimatedCost ? post.estimatedCost : '비용 협의'),
            pace: String(post && post.pace ? post.pace : ''),
            moodTags: this.companionMoodTags(post),
            flexibility: this.companionFlexibility(post),
            packingItems: packingItems.map((item: any) => {
                if (item && typeof item === 'object') return { label: String(item.label || '준비물'), done: !!item.done };
                return { label: String(item || '준비물'), done: false };
            })
        };
    }

    private directChatMatchesFilter(chat: any, key: string) {
        if (key === 'unread') return Number(chat && chat.unread ? chat.unread : 0) > 0;
        if (key === 'companion') return (chat && chat.category === 'companion') || String(chat && chat.status || '').indexOf('동행') > -1;
        return true;
    }

    private async loadChatThreads(showLoading: boolean = true) {
        if (!this.isLoggedIn()) {
            this.chatThreads = [];
            this.activeChatThreadId = '';
            return;
        }

        if (showLoading) {
            this.chatHistoryLoading = true;
            await this.service.render();
        }

        const { code, data } = await wiz.call('chat_threads', {});
        if (code === 200) {
            this.chatThreads = data && data.threads ? data.threads : [];
        } else if (code === 401 && this.service.auth) {
            this.service.auth.clearLocalSession();
            this.chatThreads = [];
            this.activeChatThreadId = '';
        }

        this.chatHistoryLoading = false;
        await this.service.render();
    }

    private async sendChatPrompt(prompt: string) {
        let requestTime = this.currentChatTimeLabel();
        this.messages.push({
            role: 'user',
            text: prompt,
            time: requestTime
        });
        this.isChatSending = true;
        let canGenerateCourse = this.plannerConversationCanGenerateCourse(prompt);
        this.isPlannerGenerating = canGenerateCourse;
        if (canGenerateCourse) this.startPlannerProgress();

        await this.service.render();
        this.scrollToLatest();

        let reply: any = {
            role: 'assistant',
            text: canGenerateCourse
                ? '좋아요. 대화 내용을 바탕으로 실시간 코스를 만들고 있어요.'
                : '좋아요. 먼저 여행 조건을 살펴보고 있어요.',
            time: requestTime,
            loading: true
        };
        this.messages.push(reply);
        await this.service.render();
        this.scrollToLatest();

        try {
            let history = this.messages
                .filter((message: any) => !message.loading && !message.seed)
                .slice(0, -1)
                .slice(-12)
                .map((message: any) => ({
                    role: message.role,
                    text: String(message.text || '')
                }));
            let response: any = await wiz.call('chat_send', {
                prompt,
                history: JSON.stringify(history),
                thread_id: this.activeChatThreadId
            });
            let code = Number(response && response.code ? response.code : 0);
            let data = response && response.data ? response.data : response;
            if (code === 200 && data) {
                reply.text = data.message || data.reply || 'AI가 여행 조건을 정리했어요.';
                this.activeChatThreadId = data.thread_id || this.activeChatThreadId;
                this.applyPlannerContract(data);
            } else {
                let fallbackMessage = canGenerateCourse
                    ? '실제 장소를 확인하지 못해 코스를 만들지 않았어요. 잠시 후 다시 요청해주세요.'
                    : 'AI 연결이 불안정해요. 여행지를 정한 뒤 다시 요청해주세요.';
                reply.text = this.responseMessage(data || response, fallbackMessage);
            }
        } catch (e) {
            reply.text = canGenerateCourse
                ? '실제 장소를 확인하지 못해 코스를 만들지 않았어요. 잠시 후 다시 요청해주세요.'
                : 'AI 연결이 불안정해요. 잠시 후 여행지를 정해서 다시 질문해주세요.';
        }
        reply.loading = false;
        this.isChatSending = false;
        this.isPlannerGenerating = false;
        this.stopPlannerProgress();

        await this.service.render();
        this.scrollToLatest();
        if (this.plannerCourseReady) this.scrollToPlannerPreview();
    }

    private currentChatTimeLabel() {
        let date = new Date();
        let hours = date.getHours();
        let minutes = String(date.getMinutes()).padStart(2, '0');
        let period = hours < 12 ? '오전' : '오후';
        return `${period} ${hours % 12 || 12}:${minutes}`;
    }

    private consumeStoredChatPrompt() {
        if (typeof window === 'undefined' || !window.sessionStorage) return '';
        try {
            let prompt = window.sessionStorage.getItem('tour-on-chat-prompt') || '';
            window.sessionStorage.removeItem('tour-on-chat-prompt');
            return prompt.trim();
        } catch (e) {
            return '';
        }
    }

    private scrollToLatest() {
        if (typeof window === 'undefined') return;
        window.setTimeout(() => {
            let list = document.querySelector('.access-shell .message-list');
            if (list) list.scrollTop = list.scrollHeight;
        }, 0);
    }

    public scrollToPlannerPreview() {
        if (typeof window === 'undefined') return;
        window.setTimeout(() => {
            let preview: any = document.querySelector('.access-shell .ai-planner-preview');
            if (preview && preview.scrollIntoView) {
                preview.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 0);
    }

    private resetTravelResumeScroll() {
        if (typeof window === 'undefined') return;
        window.setTimeout(() => {
            let content: any = document.querySelector('.access-shell .app-content');
            if (content) content.scrollTop = 0;
        }, 0);
    }

    private resetHomeContentScroll() {
        if (typeof window === 'undefined') return;
        window.setTimeout(() => {
            let content: any = document.querySelector('.access-shell .home-tab-content');
            let tabs: any = document.querySelector('.access-shell .home-panel > .home-content-tabs:not(.home-community-tabs)');
            if (content) content.scrollTop = 0;
            if (tabs && tabs.scrollIntoView) {
                tabs.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 0);
    }

    private resetChatContentScroll() {
        if (typeof window === 'undefined') return;
        window.setTimeout(() => {
            let content = document.querySelector('.access-shell .chat-tab-content');
            let appContent = document.querySelector('.access-shell .app-content');
            if (content) content.scrollTop = 0;
            if (appContent) appContent.scrollTop = 0;
            this.scrollDirectMessages();
        }, 0);
    }

    private scrollDirectMessages() {
        if (typeof window === 'undefined') return;
        window.setTimeout(() => {
            let list = document.querySelector('.access-shell .direct-message-list');
            if (list) list.scrollTop = list.scrollHeight;
        }, 0);
    }

    private courseFilterValue(key: string) {
        if (key === 'schedule') return this.scheduleDurationToken() || this.selectedFilters.schedule;
        return this.selectedFilters[key];
    }

    private matchesCourse(course: any) {
        let conditionValues = Object.keys(this.selectedFilters)
            .map((key: string) => this.courseFilterValue(key))
            .filter((value: string) => !!value);
        let filterMatched = conditionValues.every((value: string) => this.courseContains(course, value));
        if (!filterMatched) return false;

        let moveKeyword = this.moveFilterCourseKeyword();
        if (moveKeyword && !this.courseContains(course, moveKeyword)) return false;

        if (this.selectedKeyword && !this.courseContains(course, this.selectedKeyword)) return false;

        let text = String(this.query || '').trim().toLowerCase();
        if (!text) return true;

        let tokens = text.split(/\s+/).filter((token: string) => token.length > 0);
        return tokens.every((token: string) => this.courseContains(course, token));
    }

    private moveFilterCourseKeyword() {
        if (this.selectedMoveFilter === 'walk') return '산책';
        if (this.selectedMoveFilter === 'car') return '드라이브';
        return '';
    }

    private matchesSelectedLocation(item: any) {
        let location = String(this.selectedFilters.location || '').trim();
        if (!location) return true;
        return this.itemContains(item, location);
    }

    private expandSearchKeywords(keyword: string) {
        let aliases: any = {
            서울: ['서울', '성수', '종로', '익선동', '한강', '홍대'],
            부산: ['부산', '해운대', '광안리', '영도', '서면'],
            제주: ['제주', '애월', '협재', '서귀포', '성산', '중문'],
            경기: ['경기', '수원', '가평', '양평', '파주', '용인', '고양'],
            충청: ['충청', '충남', '충북', '대전', '세종', '천안', '아산', '공주', '부여', '태안', '보령', '서산', '당진'],
            전라: ['전라', '전북', '전남', '전주', '군산', '목포', '여수', '순천'],
            경상: ['경상', '경북', '경남', '대구', '경주', '포항', '안동', '울산', '통영', '거제', '진주', '부산'],
            강원: ['강원', '강릉', '속초', '춘천', '양양', '평창'],
            인천: ['인천', '송도', '월미도', '강화', '영종'],
            '이번 주말': ['이번 주말', '이번주말', '주말'],
            '다음 달': ['다음 달', '다음달', '여행']
        };
        return aliases[keyword] || [keyword];
    }

    private courseContains(course: any, value: string) {
        let keyword = String(value || '').trim().toLowerCase();
        if (!keyword) return true;

        let searchable = [
            course.title,
            course.location,
            course.summary,
            course.duration,
            course.distance,
            course.category,
            course.source,
            ...(course.tags || [])
        ].join(' ').toLowerCase();

        return this.expandSearchKeywords(keyword).some((item: string) => searchable.indexOf(String(item).toLowerCase()) > -1);
    }

    private itemContains(item: any, value: string) {
        let keyword = String(value || '').trim().toLowerCase();
        if (!keyword) return true;

        let searchable = [
            item.title,
            item.route,
            item.course,
            item.location,
            item.date,
            item.intro,
            item.summary,
            item.author,
            item.host,
            ...(item.tags || [])
        ].join(' ').toLowerCase();

        return this.expandSearchKeywords(keyword).some((token: string) => searchable.indexOf(String(token).toLowerCase()) > -1);
    }
}
