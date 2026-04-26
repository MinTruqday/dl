import { Extension } from '@tiptap/core';
import Suggestion from '@tiptap/suggestion';
import { suggestionRenderer } from './LatexSuggestion';

export const LatexAutocomplete = Extension.create({
  name: 'latexAutocomplete',

  addOptions() {
    return {
      suggestion: {
        char: '\\',
        command: ({ editor, range, props }) => {
          const detail = props.detail || '';
          
          if (
            detail.includes('[Cơ bản]') ||
            detail.includes('[Trình bày]') ||
            detail.includes('[Số liệu và Bảng biểu]') ||
            detail.includes('[Cấu trúc tài liệu]')
          ) {
             editor
              .chain()
              .focus()
              .deleteRange(range)
              .setLatexBlock({ text: props.insertText })
              .run();
          } 
          else if (detail.includes('[Toán học]')) {
             editor
              .chain()
              .focus()
              .deleteRange(range)
              .insertContent(`$${props.insertText}$ `)
              .run();
          } 
          else {
             editor
              .chain()
              .focus()
              .deleteRange(range)
              .insertContent(`${props.insertText} `)
              .run();
          }
        },
      },
    };
  },

  addProseMirrorPlugins() {
    return [
      Suggestion({
        editor: this.editor,
        ...this.options.suggestion,
        ...suggestionRenderer
      }),
    ];
  },
});

