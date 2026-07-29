type EditorInputOptions = {
  title: string;
  label: string;
  initialValue?: string;
};

function createDialogFrame(title: string) {
  const backdrop = document.createElement("div");
  backdrop.className = "fixed inset-0 z-[100] flex items-center justify-center bg-black/30 p-4";

  const panel = document.createElement("div");
  panel.className = "w-full max-w-md rounded-[var(--radius-panel)] border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-panel)]";

  const heading = document.createElement("h2");
  heading.className = "text-lg font-semibold text-[var(--ink)]";
  heading.textContent = title;
  panel.appendChild(heading);
  backdrop.appendChild(panel);
  document.body.appendChild(backdrop);

  return { backdrop, panel };
}

export function requestEditorInput(options: EditorInputOptions) {
  return new Promise<string | null>((resolve) => {
    const { backdrop, panel } = createDialogFrame(options.title);
    const label = document.createElement("label");
    label.className = "mt-5 block text-sm font-medium text-[var(--ink)]";
    label.textContent = options.label;

    const input = document.createElement("input");
    input.className = "field-control mt-2 w-full";
    input.value = options.initialValue || "";

    const actions = document.createElement("div");
    actions.className = "mt-6 flex justify-end gap-2";

    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.className = "button-secondary";
    cancel.textContent = "Hủy";

    const accept = document.createElement("button");
    accept.type = "button";
    accept.className = "button-primary";
    accept.textContent = "Xác nhận";

    const finish = (value: string | null) => {
      backdrop.remove();
      resolve(value);
    };

    cancel.addEventListener("click", () => finish(null));
    accept.addEventListener("click", () => finish(input.value.trim()));
    backdrop.addEventListener("click", (event) => {
      if (event.target === backdrop) finish(null);
    });
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") finish(input.value.trim());
      if (event.key === "Escape") finish(null);
    });

    actions.append(cancel, accept);
    panel.append(label, input, actions);
    input.focus();
    input.select();
  });
}

export function showEditorNotice(title: string, message: string) {
  const { backdrop, panel } = createDialogFrame(title);
  const body = document.createElement("p");
  body.className = "mt-3 text-sm leading-6 text-[var(--ink-muted)]";
  body.textContent = message;

  const actions = document.createElement("div");
  actions.className = "mt-6 flex justify-end";
  const close = document.createElement("button");
  close.type = "button";
  close.className = "button-primary";
  close.textContent = "Đóng";
  close.addEventListener("click", () => backdrop.remove());
  backdrop.addEventListener("click", (event) => {
    if (event.target === backdrop) backdrop.remove();
  });
  actions.appendChild(close);
  panel.append(body, actions);
  close.focus();
}
