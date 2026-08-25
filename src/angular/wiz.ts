import { io } from "socket.io-client";

export default class Wiz {
    public namespace: any;
    public baseuri: any;

    constructor(baseuri: any) {
        this.baseuri = baseuri;
    }

    public app(namespace: any) {
        let instance = new Wiz(this.baseuri);
        instance.namespace = namespace;
        return instance;
    }

    public dev() {
        let findcookie = (name: string) => {
            let ca: Array<string> = document.cookie.split(';');
            let caLen: number = ca.length;
            let cookieName = `${name}=`;
            let c: string;

            for (let i: number = 0; i < caLen; i += 1) {
                c = ca[i].replace(/^\s+/g, '');
                if (c.indexOf(cookieName) == 0) {
                    return c.substring(cookieName.length, c.length);
                }
            }
            return '';
        }

        let isdev = findcookie("season-wiz-devmode");
        if (isdev == 'true') return true;
        return false;
    }

    public project() {
        let findcookie = (name: string) => {
            let ca: Array<string> = document.cookie.split(';');
            let caLen: number = ca.length;
            let cookieName = `${name}=`;
            let c: string;

            for (let i: number = 0; i < caLen; i += 1) {
                c = ca[i].replace(/^\s+/g, '');
                if (c.indexOf(cookieName) == 0) {
                    return c.substring(cookieName.length, c.length);
                }
            }
            return '';
        }

        let project = findcookie("season-wiz-project");
        if (project) return project;
        return "main";
    }

    public socket() {
        let socketns = this.baseuri + "/app/" + this.project();
        if (this.namespace)
            socketns = socketns + "/" + this.namespace;
        return io(socketns);
    };

    public url(function_name: string) {
        if (function_name[0] == "/") function_name = function_name.substring(1);
        return this.baseuri + "/api/" + this.namespace + "/" + function_name;
    }

    public call(function_name: string, data: any = {}, options: any = {}): Promise<any> {
        let controller = new AbortController();
        let timeout = Number(options.timeout || 0);
        let timer = timeout > 0 ? window.setTimeout(() => controller.abort(), timeout) : null;
        let body = this.formBody(this.authData(data));
        return fetch(this.url(function_name), {
            method: "POST",
            body,
            headers: {
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                ...this.authHeaders(),
                ...(options.headers || {}),
            },
            credentials: "same-origin",
            signal: controller.signal,
        }).then(async response => {
            let text = await response.text();
            try {
                return JSON.parse(text);
            } catch (e) {
                return response.ok ? text : {
                    status: response.status,
                    statusText: response.statusText,
                    responseText: text,
                };
            }
        }).catch(error => ({
            status: 0,
            statusText: error && error.name === "AbortError" ? "timeout" : "network_error",
        })).finally(() => {
            if (timer !== null) window.clearTimeout(timer);
        });
    }

    private formBody(data: any) {
        let params = new URLSearchParams();
        let append = (key: string, value: any) => {
            if (Array.isArray(value)) {
                value.forEach(item => append(`${key}[]`, item));
            } else if (value && typeof value === "object") {
                Object.keys(value).forEach(child => append(`${key}[${child}]`, value[child]));
            } else {
                params.append(key, value === null || value === undefined ? "" : String(value));
            }
        };
        Object.keys(data || {}).forEach(key => append(key, data[key]));
        return params;
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
