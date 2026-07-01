import $ from "jquery";

export default class Request {
    constructor() { }

    public async post(url: string, data: any = {}): Promise<any> {
        let request = () => {
            return new Promise((resolve) => {
                $.ajax({
                    url: url,
                    type: "POST",
                    data: this.authData(data),
                    headers: this.authHeaders()
                }).always(function (res: any) {
                    resolve(res);
                });
            });
        }

        return await request();
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
