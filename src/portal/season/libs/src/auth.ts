import Service from '../service';
import Request from '../util/request';

export default class Auth {
    public verified: string | null = null;
    private request: Request;

    public timestamp: number = 0;
    public status: any = null;
    public loading: any = null;
    public session: any = {};
    public token: string = '';
    public tokenKey: string = 'tour-on-jwt';
    public userKey: string = 'tour-on-user';

    constructor(public service: Service) {
        this.request = new Request();
    }

    public async init() {
        this.restoreLocalSession();

        try {
            let { code, data } = await this.request.post('/auth/check');
            let { status, session } = data;
            session = this.normalizeSession(session || {});
            this.verified = session.verified;
            this.loading = true;
            if (code != 200) {
                if (!this.hasLocalSession()) this.clearLocalSession();
                return this;
            }
            this.timestamp = new Date().getTime();
            if (status) {
                this.session = session;
                this.status = true;
                this.persistLocalSession(session, this.token || this.createLocalToken(session));
            } else if (this.hasLocalSession()) {
                this.status = true;
                this.persistLocalSession(this.session, this.token);
            } else {
                this.clearLocalSession();
            }
        } catch (e) {
            this.loading = true;
            if (this.hasLocalSession()) {
                this.status = true;
            } else {
                this.clearLocalSession();
            }
        }
        return this;
    }

    public async update() {
        let waitCount = 0;
        while (this.loading === null && waitCount < 20) {
            await this.service.render(100);
            waitCount++;
        }

        if (this.loading === null) {
            this.loading = true;
            return this;
        }

        let diff = new Date().getTime() - this.timestamp;
        if (diff > 1000 * 60) {
            this.loading = null;
            let init = this.init().catch(() => this);
            await Promise.race([init, this.service.sleep(1200)]);
            if (this.loading === null) this.loading = true;
        }
        return this;
    }

    public check: any = new Proxy(((root) => {
        let obj: any = () => {
            return this.status;
        }

        obj.root = root;
        return obj;
    })(this), {
        get(target, propKey) {
            let propValue: any = target.root.session[propKey];

            return (values: any = null) => {
                if (values === null) {
                    return true;
                }

                if (typeof values == 'boolean') {
                    if (values === propValue)
                        return true;
                    return false;
                }

                if (typeof values == 'string')
                    values = [values];

                if (values.indexOf(propValue) >= 0) {
                    return true;
                }

                return false;
            };
        }
    });

    public allow: any = new Proxy(((root) => {
        let obj: any = (redirect: any = null) => {
            if (root.check()) return true;
            if (redirect) location.href = redirect;
            return false;
        }

        obj.root = root;
        obj.check = root.check;
        return obj;
    })(this), {
        get(target, propKey) {
            return (values: any = null, redirect: any = null) => {
                if (target.check[propKey](values)) return true;
                if (redirect) location.href = redirect;
                return false;
            }
        }
    });

    public hash(password: string = '') {
        return this.service.crypto.SHA256(password).toString();
    }

    public isLoggedIn() {
        this.session = this.normalizeSession(this.session);
        return !!this.status && !!(this.session && (this.session.id || this.session.email));
    }

    public setLocalSession(session: any = {}, token: string = '') {
        this.session = this.normalizeSession(session || {});
        this.token = token || this.createLocalToken(this.session);
        this.status = true;
        this.persistLocalSession(this.session, this.token);
    }

    public clearLocalSession() {
        this.session = {};
        this.token = '';
        this.status = false;
        if (typeof window === 'undefined') return;
        try {
            this.clearStorage(window.localStorage);
        } catch (e) { }
        try {
            this.clearStorage(window.sessionStorage);
        } catch (e) { }
    }

    public restoreLocalSession() {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            let token = window.localStorage.getItem(this.tokenKey) || '';
            let rawUser = window.localStorage.getItem(this.userKey) || '';
            if (!token || !rawUser) return;

            this.token = token;
            this.session = this.normalizeSession(JSON.parse(rawUser));
            this.status = true;
        } catch (e) {
            this.clearLocalSession();
        }
    }

    private hasLocalSession() {
        this.session = this.normalizeSession(this.session);
        return !!this.token && !!(this.session && (this.session.id || this.session.email));
    }

    private persistLocalSession(session: any = {}, token: string = '') {
        session = this.normalizeSession(session);
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            window.localStorage.setItem(this.tokenKey, token);
            window.localStorage.setItem(this.userKey, JSON.stringify(session || {}));
        } catch (e) { }
    }

    private clearStorage(storage: Storage | null | undefined) {
        if (!storage) return;
        let keys = [
            this.tokenKey,
            this.userKey,
            'tour-on-token',
            'tour-on-session',
            'tour-on-auth'
        ];
        try {
            for (let key of keys) {
                storage.removeItem(key);
            }
        } catch (e) { }
    }

    private createLocalToken(session: any = {}) {
        session = this.normalizeSession(session);
        let payload = {
            sub: session.id || '',
            email: session.email || '',
            iat: new Date().getTime()
        };
        try {
            return `local.${btoa(unescape(encodeURIComponent(JSON.stringify(payload))))}`;
        } catch (e) {
            return `local.${new Date().getTime()}`;
        }
    }

    private normalizeSession(session: any = {}) {
        if (!session || typeof session !== 'object') session = {};
        let id = session.id || session.user_id || session.userid || session.uid || session.sub || '';
        return {
            ...session,
            id: id,
            email: session.email || '',
            name: session.name || session.nickname || session.display_name || session.displayName || session.username || '',
            role: session.role || 'user'
        };
    }
}
