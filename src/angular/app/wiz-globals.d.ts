declare module 'jquery';

declare module 'sortablejs' {
    const Sortable: any;
    export default Sortable;
    export type Options = any;
}

declare const WizRoute: any;

interface Navigator {
    userLanguage?: string;
}
