import React, { forwardRef, useEffect, useImperativeHandle, useState } from 'react';

export const LatexSuggestionList = forwardRef((props: any, ref) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  const selectItem = index => {
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
    onKeyDown: ({ event }) => {
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
    <div className="bg-card   border border-border overflow-hidden w-64">
      {props.items.length ? (
        props.items.map((item, index) => (
          <button
            className={`w-full text-left px-4 py-2 text-sm ${
              index === selectedIndex ? 'bg-gray-100 text-black font-semibold' : 'text-gray-700 hover:bg-background'
            }`}
            key={index}
            onClick={() => selectItem(index)}
          >
            <div className="flex justify-between items-center">
              <code className="bg-gray-100 px-1 rounded">{item.label}</code>
              <span className="text-xs text-muted-foreground max-w-[50%] truncate ml-2">
                {item.detail}
              </span>
            </div>
          </button>
        ))
      ) : (
        <div className="text-sm p-4 text-muted-foreground text-center">Không tìm thấy lệnh</div>
      )}
    </div>
  );
});
