import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useState,
} from "react";

export const SuggestionList = forwardRef((props: any, ref) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  const selectItem = (index: number) => {
    const item = props.items[index];

    if (item) {
      props.command(item);
    }
  };

  const upHandler = () => {
    setSelectedIndex(
      (selectedIndex + props.items.length - 1) % props.items.length,
    );
  };

  const downHandler = () => {
    setSelectedIndex((selectedIndex + 1) % props.items.length);
  };

  const enterHandler = () => {
    selectItem(selectedIndex);
  };

  useEffect(() => setSelectedIndex(0), [props.items]);

  useImperativeHandle(ref, () => ({
    onKeyDown: ({ event }: { event: any }) => {
      if (event.key === "ArrowUp") {
        upHandler();
        return true;
      }

      if (event.key === "ArrowDown") {
        downHandler();
        return true;
      }

      if (event.key === "Enter") {
        enterHandler();
        return true;
      }

      return false;
    },
  }));

  return (
    <div className="bg-white border border-zinc-200 rounded-none overflow-hidden w-64 animate-in fade-in slide-in-from-top-2">
      {props.items.length ? (
        <div className="py-0 flex flex-col">
          {props.items.map((item: any, index: number) => (
            <button
              key={index}
              onClick={() => selectItem(index)}
              className={`w-full text-left px-3 py-2 border-b border-zinc-100 last:border-b-0 transition-colors duration-150 ${
                index === selectedIndex
                  ? "bg-zinc-100"
                  : "bg-white hover:bg-zinc-50"
              }`}
            >
              <div className="flex flex-col gap-1 min-w-0">
                <span className="font-mono text-xs font-bold text-black tracking-tight">
                  {item.label}
                </span>
                {item.detail && (
                  <span
                    className={`text-[10px] font-medium truncate ${
                      index === selectedIndex ? "text-zinc-600" : "text-zinc-400"
                    }`}
                  >
                    {item.detail}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div className="text-xs p-4 text-zinc-500 text-center font-medium bg-zinc-50">
          Không tìm thấy lệnh
        </div>
      )}
    </div>
  );
});
