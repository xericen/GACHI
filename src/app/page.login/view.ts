import { OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    public authMode: string = 'login';
    public authSubmitting: boolean = false;
    public authAttempted: boolean = false;
    public authServerError: string = '';
    public authForm: any = {
        email: '',
        password: '',
        passwordConfirm: '',
        nickname: ''
    };
    public authErrors: any = {};

    constructor(public service: Service) { }

    public async ngOnInit() {
        await this.service.init();
        let params = this.currentSearchParams();
        if (params.get('mode') === 'register') this.authMode = 'register';
        await this.service.render();
    }

    public goHome() {
        window.location.href = '/';
    }

    public async switchAuthMode(mode: string) {
        this.authMode = mode;
        this.authAttempted = false;
        this.authServerError = '';
        this.authErrors = {};
        await this.service.render();
    }

    public async submitAuth() {
        this.authAttempted = true;
        if (!this.validateAuthForm(true)) {
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
            this.resetAuthForm();
            window.location.href = this.returnTo(session, data && data.token ? data.token : '');
            return;
        }

        this.authServerError = this.responseMessage(data, this.authMode === 'register' ? '회원가입에 실패했습니다.' : '로그인에 실패했습니다.');
        this.authSubmitting = false;
        await this.service.render();
    }

    public async handleAuthInputChange() {
        if (this.authSubmitting) return;
        this.validateAuthForm(this.authAttempted);
        await this.service.render();
    }

    public authSubmitLabel() {
        if (this.authSubmitting) return '처리 중';
        return this.authMode === 'register' ? '가입하기' : '로그인';
    }

    private async requestAuth(payload: any) {
        let action = this.authMode === 'register' ? 'register' : 'login';
        let result: any = null;
        try {
            result = await wiz.call(action, payload);
            if (this.isAuthResult(result)) return this.normalizeAuthResult(result);
        } catch (error) { }

        let endpoint = this.authMode === 'register' ? '/auth/signup' : '/auth/login';
        try {
            result = await this.service.request.post(endpoint, payload);
            if (this.isAuthResult(result)) return this.normalizeAuthResult(result);
        } catch (error) {
            return { code: 500, data: { message: '인증 요청 중 오류가 발생했습니다.' } };
        }

        return { code: 500, data: { message: '인증 응답을 확인할 수 없습니다.' } };
    }

    private isAuthResult(result: any): boolean {
        if (!result) return false;
        if (result.responseJSON && typeof result.responseJSON.code !== 'undefined') {
            return this.isAuthResult(result.responseJSON);
        }
        if (result.session) return true;
        if (result.data && result.data.session) return true;
        if (typeof result.code !== 'undefined') return Number(result.code) !== 200;
        return false;
    }

    private normalizeAuthResult(result: any): any {
        if (result && result.responseJSON && typeof result.responseJSON.code !== 'undefined') {
            return result.responseJSON;
        }
        if (result && result.session) return { code: 200, data: result };
        if (result && result.data && result.data.session) return { code: 200, data: result.data };
        return result;
    }

    private validateAuthForm(showRequired: boolean = true) {
        let errors: any = {};
        let email = String(this.authForm.email || '').trim();
        let password = String(this.authForm.password || '');
        let passwordConfirm = String(this.authForm.passwordConfirm || '');
        let nickname = String(this.authForm.nickname || '').trim();
        let isAdminLogin = this.authMode === 'login' && email === 'admin';
        let isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

        if (!email && showRequired) {
            errors.email = '이메일을 입력해주세요.';
        } else if (email && !isAdminLogin && !isEmail) {
            errors.email = '올바른 이메일 형식으로 입력해주세요.';
        }
        if (!password && showRequired) {
            errors.password = '비밀번호를 입력해주세요.';
        }
        if (this.authMode === 'register') {
            if (!email && showRequired) errors.email = '이메일을 입력해주세요.';
            if (email && !isEmail) errors.email = '올바른 이메일 형식으로 입력해주세요.';
            if (!nickname && showRequired) errors.nickname = '닉네임을 입력해주세요.';
            if (!password && showRequired) errors.password = '비밀번호를 입력해주세요.';
            if (password && password.length < 6) errors.password = '비밀번호는 6자 이상 입력해주세요.';
            if (!passwordConfirm && showRequired) errors.passwordConfirm = '비밀번호 확인을 입력해주세요.';
            if (passwordConfirm && password !== passwordConfirm) errors.passwordConfirm = '비밀번호가 일치하지 않습니다.';
        }

        this.authErrors = errors;
        this.authServerError = '';
        return Object.keys(errors).length === 0;
    }

    private resetAuthForm() {
        this.authAttempted = false;
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

    private currentSearchParams() {
        if (typeof window === 'undefined') return new URLSearchParams();
        return new URLSearchParams(window.location.search || '');
    }

    private returnTo(session: any = {}, token: string = '') {
        let value = this.currentSearchParams().get('returnTo') || '';
        if (session && session.role === 'admin' && (!value || value === '/')) {
            value = '/admin/dashboard';
        }
        if (value.indexOf('/') !== 0) value = '/';
        if (session && session.role === 'admin' && value.indexOf('/admin') === 0 && token) {
            let separator = value.indexOf('?') >= 0 ? '&' : '?';
            return `${value}${separator}token=${encodeURIComponent(token)}`;
        }
        return value;
    }
}
