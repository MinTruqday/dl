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
    <div className="bg-white border border-black rounded-none overflow-hidden w-80 animate-in fade-in slide-in-from-top-2">
      {props.items.length ? (
        <div className="py-0">
          {props.items.map((item: any, index: number) => (
            <button
              className={`w-full text-left px-3 py-2 text-sm flex flex-col gap-0.5 border-b border-zinc-100 last:border-b-0 transition-colors ${
                index === selectedIndex
                  ? "bg-black text-white"
                  : "text-zinc-600 hover:bg-zinc-50"
              }`}
              key={index}
              onClick={() => selectItem(index)}
            >
              <div className="flex justify-between items-center w-full">
                <span className={`font-mono font-medium ${index === selectedIndex ? "text-white" : "text-black"}`}>
                  {item.label}
                </span>
                <span className={`text-[10px] uppercase tracking-wider font-bold ${index === selectedIndex ? "text-zinc-400" : "text-zinc-400"}`}>
                  {item.type || "Lệnh"}
                </span>
              </div>
              {item.detail && (
                <span className={`text-xs truncate w-full ${index === selectedIndex ? "text-zinc-400" : "text-zinc-500"}`}>
                  {item.detail}
                </span>
              )}
            </button>
          ))}
        </div>
      ) : (
        <div className="text-sm p-4 text-zinc-500 text-center font-medium bg-zinc-50">
          Không tìm thấy lệnh phù hợp
        </div>
      )}
    </div>
  );
});
