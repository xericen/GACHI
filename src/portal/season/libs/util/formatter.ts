export default class Formatter {
    constructor() { }

    public date(date: any, text: any) {
        if (!text) text = "-";
        if (!date) return text;
        let value = date instanceof Date ? date : new Date(date);
        if (Number.isNaN(value.getTime())) return text;
        let year = value.getFullYear();
        let month = String(value.getMonth() + 1).padStart(2, '0');
        let day = String(value.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    public currency(number: any, isString: boolean = true) {
        if (!number) return "-";
        if (isString) {
            let num = number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
            return num + "원";
        }

        const units = ['', '만', '억', '조', '경'];
        const parts = [];
        let remaining = number;

        for (let i = units.length - 1; i >= 0; i--) {
            const unit = Math.pow(10000, i);
            const part = Math.floor(remaining / unit);
            remaining = remaining % unit;

            if (part > 0) {
                parts.push(part + units[i]);
            }
        }

        if (remaining > 0) {
            parts.push(remaining);
        }
        if (parts.length == 0) return '-';
        return parts.join(' ') + '원';
    }

}
