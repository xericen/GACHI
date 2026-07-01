const INDEX_PAGE = "/";

import { URLPattern } from "urlpattern-polyfill";
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

let app_routes: any[] = wiz.routes();

let normalizeMainRoutes = () => {
    for (let i = 0; i < app_routes.length; i++) {
        let layout: any = app_routes[i];
        let layout_childs: any[] = layout.children || [];
        let dashboard = layout_childs.find((child: any) => child.app_id === "page.dashboard");
        let access = layout_childs.find((child: any) => child.app_id === "page.access");

        if (access) {
            access.path = "";
            let hasAccessAlias = layout_childs.some((child: any) => child !== access && child.path === "access");
            if (!hasAccessAlias) {
                layout_childs.push({ ...access, path: "access" });
            }
        }

        if (dashboard) {
            dashboard.path = access ? "dashboard" : "";
            let hasDashboardAlias = layout_childs.some((child: any) => child !== dashboard && child.path === "dashboard");
            if (!hasDashboardAlias && !access) {
                layout_childs.push({ ...dashboard, path: "dashboard" });
            }
        }
    }
};

normalizeMainRoutes();

export class RouteInfo {
    public path: any = "";
    public segment: any = {};

    constructor() { }
}

declare global {
    interface Window {
        WizRoute: RouteInfo;
    }
}

window.WizRoute = new RouteInfo();

let patternMatcher = (pattern: any, url: any) => {
    let urlpath = url.map((x: any) => x.path).join("/");
    let testurl = 'http://test/';
    pattern = '/' + pattern;
    urlpath = testurl + urlpath;
    pattern = new URLPattern({ pathname: pattern });
    pattern = pattern.exec(urlpath)
    if (pattern && pattern.pathname) {
        let posParams: any = {};
        for (let key in pattern.pathname.groups) {
            if (pattern.pathname.groups[key]) {
                posParams[key] = pattern.pathname.groups[key];
            }
        }
        window.WizRoute.path = url.map((x: any) => x.path).join("/");
        window.WizRoute.segment = posParams;

        return { consumed: url, posParams: posParams };
    }
    return null
}

let layoutMatcher = (layout_childs: any[]) => {
    return (url: any) => {
        for (let i = 0; i < layout_childs.length; i++) {
            let child = layout_childs[i];
            if (patternMatcher(child.path, url)) {
                return { consumed: [], posParams: {} };
            }
        }
        return null;
    };
};

let routes: Routes = [{
    matcher: (url: any) => {
        for (let i = 0; i < app_routes.length; i++) {
            let layout: any = app_routes[i];
            let layout_childs: any[] = layout.children || [];
            for (let j = 0; j < layout_childs.length; j++) {
                let child = layout_childs[j];
                let matcher = patternMatcher(child.path, url);
                if (matcher)
                    return null;
            }
        }
        return { consumed: url, posParams: {} };
    },
    redirectTo: INDEX_PAGE
}];

for (let i = 0; i < app_routes.length; i++) {
    let layout: any = app_routes[i];
    let layout_component = layout.component;
    let layout_childs: any[] = layout.children || [];

    let router: any = {
        matcher: layoutMatcher(layout_childs),
        component: layout_component,
        children: []
    };

    for (let j = 0; j < layout_childs.length; j++) {
        let child = layout_childs[j];
        router.children.push({
            matcher: (url: any) => {
                let matcher = patternMatcher(child.path, url);
                if (matcher) return matcher;
                return null;
            },
            component: child.component
        });
    }
    routes.push(router);
}

@NgModule({ imports: [RouterModule.forRoot(routes)], exports: [RouterModule] })
export class AppRoutingModule { }
