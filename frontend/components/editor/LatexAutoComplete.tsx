import { Extension } from '@tiptap/core';
import Suggestion from '@tiptap/suggestion';
import { suggestionRenderer } from './LatexSuggestion';

export const LatexAutocomplete = Extension.create({
  name: 'latexAutocomplete',

  addOptions() {
    return {
      suggestion: {
        char: '\\',
        command: ({ editor, range, props }: any) => {
          const category = props.category || '';
          
          if (category === 'environment') {
             editor
              .chain()
              .focus()
              .deleteRange(range)
              .setLatexBlock({ text: props.insertText })
              .run();
          } 
          else if (category === 'math') {
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

