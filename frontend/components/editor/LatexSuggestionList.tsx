import React, { forwardRef, useEffect, useImperativeHandle, useState } from 'react';

export const LatexSuggestionList = forwardRef((props: any, ref) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  const selectItem = (index: number) => {
    const item = props.items[index];

    if (item) {
      props.command(item);
    }
  };

  const upHandler = () => {
    setSelectedIndex((selectedIndex + props.items.length - 1) % props.items.length);
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
      if (event.key === 'ArrowUp') {
        upHandler();
        return true;
      }

      if (event.key === 'ArrowDown') {
        downHandler();
        return true;
      }

      if (event.key === 'Enter') {
        enterHandler();
        return true;
      }

      return false;
    },
  }));

  return (
    <div className="bg-white border border-gray-200 rounded-md overflow-hidden w-80 animate-in fade-in slide-in-from-top-2 duration-200">
      {props.items.length ? (
        <div className="py-1">
          {props.items.map((item: any, index: number) => (
            <button
              className={`w-full text-left px-3 py-1.5 text-sm flex flex-col gap-0.5 transition-colors ${
                index === selectedIndex ? 'bg-gray-100 text-black' : 'text-gray-600 hover:bg-gray-50'
              }`}
              key={index}
              onClick={() => selectItem(index)}
            >
              <div className="flex justify-between items-center w-full">
                <span className="font-mono font-medium text-black">{item.label}</span>
                <span className="text-[10px] uppercase tracking-wider text-gray-400 font-semibold">
                  {item.type || 'Lệnh'}
                </span>
              </div>
              {item.detail && (
                <span className="text-xs text-gray-400 truncate w-full">
                  {item.detail}
                </span>
              )}
            </button>
          ))}
        </div>
      ) : (
        <div className="text-sm p-4 text-gray-400 text-center">Không tìm thấy lệnh phù hợp</div>
      )}
    </div>
  );
});
