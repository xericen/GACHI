import { OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    public form: any = {
        title: '',
        region: '',
        description: '',
        category: '카페',
        duration_type: 'hours',
        duration_value: '4',
        cover_image: '',
        is_featured: true
    };
    public placeQuery: string = '';
    public placeResults: any[] = [];
    public selectedPlaces: any[] = [];
    public searching: boolean = false;
    public submitting: boolean = false;
    public errorMessage: string = '';
    public dragIndex: number = -1;

    constructor(public service: Service) { }

    public async ngOnInit() {
        await this.service.init();
        let returnTo = encodeURIComponent('/admin/courses/new');
        if (!this.service.auth.allow(`/login?returnTo=${returnTo}`)) return;
        if (!this.service.auth.allow.role('admin', '/')) return;
        await this.searchPlaces();
    }

    public goBack() {
        this.service.href('/admin/courses');
    }

    public async searchPlaces() {
        this.searching = true;
        await this.service.render();
        let result = await wiz.call('search_places', { search: this.placeQuery });
        this.searching = false;
        if (result.code === 200) {
            this.placeResults = (result.data && result.data.rows) || [];
        }
        await this.service.render();
    }

    public addPlace(place: any) {
        if (this.selectedPlaces.some((item: any) => item.id === place.id)) return;
        this.selectedPlaces.push(place);
        if (!this.form.cover_image && place.image) this.form.cover_image = place.image;
        if (!this.form.region && place.area) this.form.region = place.area;
    }

    public removePlace(index: number) {
        this.selectedPlaces.splice(index, 1);
        if (!this.form.cover_image && this.selectedPlaces[0] && this.selectedPlaces[0].image) {
            this.form.cover_image = this.selectedPlaces[0].image;
        }
    }

    public dragStart(index: number) {
        this.dragIndex = index;
    }

    public allowDrop(event: any) {
        event.preventDefault();
    }

    public dropPlace(index: number) {
        if (this.dragIndex < 0 || this.dragIndex === index) return;
        let item = this.selectedPlaces.splice(this.dragIndex, 1)[0];
        this.selectedPlaces.splice(index, 0, item);
        this.dragIndex = -1;
    }

    public isSelected(place: any) {
        return this.selectedPlaces.some((item: any) => item.id === place.id);
    }

    public durationPlaceholder() {
        return this.form.duration_type === 'hours' ? '4' : '1박 2일';
    }

    public async submit() {
        this.errorMessage = '';
        if (!String(this.form.title || '').trim()) {
            this.errorMessage = '코스 제목을 입력해주세요.';
            await this.service.render();
            return;
        }
        if (this.selectedPlaces.length === 0) {
            this.errorMessage = '코스에 포함할 장소를 1개 이상 추가해주세요.';
            await this.service.render();
            return;
        }

        this.submitting = true;
        await this.service.render();
        let payload = {
            ...this.form,
            place_ids: this.selectedPlaces.map((place: any) => place.id)
        };
        let result = await wiz.call('create_course', { data: JSON.stringify(payload) });
        this.submitting = false;
        if (result.code !== 200) {
            this.errorMessage = this.responseMessage(result.data, '코스 저장에 실패했습니다.');
            await this.service.render();
            return;
        }
        this.service.href('/admin/courses');
    }

    private responseMessage(data: any, fallback: string) {
        if (typeof data === 'string' && data) return data;
        if (data && data.message) return data.message;
        return fallback;
    }
}
