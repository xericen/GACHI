export default class Request {
    constructor() { }

    public async post(url: string, data: any = {}): Promise<any> {
        let params = new URLSearchParams();
        let source = this.authData(data);
        Object.keys(source || {}).forEach(key => {
            let value = source[key];
            params.append(key, value && typeof value === 'object' ? JSON.stringify(value) : String(value ?? ''));
        });
        try {
            let response = await fetch(url, {
                method: "POST",
                body: params,
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                    ...this.authHeaders(),
                },
                credentials: "same-origin",
            });
            let text = await response.text();
            try {
                return JSON.parse(text);
            } catch (e) {
                return response.ok ? text : { status: response.status, statusText: response.statusText, responseText: text };
            }
        } catch (e) {
            return { status: 0, statusText: "network_error" };
        }
    }

    private authHeaders() {
        let token = this.authToken();
        if (token) return { Authorization: `Bearer ${token}` };
        return {};
    }

    private authData(data: any = {}) {
        let token = this.authToken();
        if (!token || !data || typeof data !== 'object' || data.token) return data;
        return {
            ...data,
            token: token
        };
    }

    private authToken() {
        if (typeof window === 'undefined' || !window.localStorage) return '';
        try {
            return window.localStorage.getItem('tour-on-jwt') || '';
        } catch (e) { }
        return '';
    }

}
