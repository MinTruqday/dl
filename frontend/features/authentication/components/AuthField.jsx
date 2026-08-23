export default function AuthField({ label, error, helper, className = "", ...props }) {
  return (
    <div>
      <label htmlFor={props.id} className="mb-2 block text-[13px] font-semibold text-ink">
        {label}
      </label>
      <input
        {...props}
        className={`apple-input w-full ${error ? "border-danger focus:border-danger focus:ring-danger-soft" : ""} ${className}`}
        aria-invalid={Boolean(error)}
        aria-describedby={error || helper ? `${props.id}-detail` : undefined}
      />
      {(error || helper) && (
        <p
          id={`${props.id}-detail`}
          className={`mt-2 text-[12px] ${error ? "text-danger" : "text-ink-muted"}`}
        >
          {error || helper}
        </p>
      )}
    </div>
  );
}
