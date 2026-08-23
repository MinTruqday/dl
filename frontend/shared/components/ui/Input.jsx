var __rest = (this && this.__rest) || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
};
import * as React from "react";
import { cn } from "../../lib/app_utils";
const Input = React.forwardRef((_a, ref) => {
    var { className, type } = _a, props = __rest(_a, ["className", "type"]);
    return (<input type={type} className={cn("flex min-h-11 w-full rounded-control border border-border-strong bg-surface px-3.5 py-2.5 text-[15px] text-ink outline-none transition placeholder:text-ink-faint focus:border-brand focus:ring-2 focus:ring-brand-soft disabled:cursor-not-allowed disabled:bg-surface-quiet disabled:opacity-60", className)} ref={ref} {...props}/>);
});
Input.displayName = "Input";
export { Input };
