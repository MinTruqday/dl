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
export default function AuthField(_a) {
    var { label, error, helper, className = "" } = _a, props = __rest(_a, ["label", "error", "helper", "className"]);
    return (<div>
      <label htmlFor={props.id} className="mb-2 block text-[13px] font-semibold text-ink">
        {label}
      </label>
      <input {...props} className={`apple-input w-full ${error ? "border-danger focus:border-danger focus:ring-danger-soft" : ""} ${className}`} aria-invalid={Boolean(error)} aria-describedby={error || helper ? `${props.id}-detail` : undefined}/>
      {(error || helper) && (<p id={`${props.id}-detail`} className={`mt-2 text-[12px] ${error ? "text-danger" : "text-ink-muted"}`}>
          {error || helper}
        </p>)}
    </div>);
}
