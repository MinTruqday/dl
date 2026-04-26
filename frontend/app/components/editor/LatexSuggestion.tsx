import { ReactRenderer } from '@tiptap/react';
import tippy, { Instance } from 'tippy.js';
import { LatexSuggestionList } from './LatexSuggestionList';
import { API_URL } from '@/app/lib/api';

export const suggestionRenderer = {
  items: async ({ query }: { query: string }) => {
    try {
      const res = await fetch(`${API_URL}/latex-snippets`);
      const data = await res.json();
      return data.snippets
        .filter((item: any) => item.label.toLowerCase().includes(query.toLowerCase()) || 
                               (item.detail && item.detail.toLowerCase().includes(query.toLowerCase())))
        .slice(0, 15);
    } catch {
      return [
        { label: '\\frac', type: 'command', insertText: '\\frac{1}{2}', detail: 'Fraction' }
      ];
    }
  },

  render: () => {
    let component: ReactRenderer;
    let popup: Instance[];

    return {
      onStart: props => {
        component = new ReactRenderer(LatexSuggestionList, {
          props,
          editor: props.editor,
        });

        if (!props.clientRect) {
          return;
        }

        popup = tippy('body', {
          getReferenceClientRect: props.clientRect,
          appendTo: () => document.body,
          content: component.element,
          showOnCreate: true,
          interactive: true,
          trigger: 'manual',
          placement: 'bottom-start',
        });
      },

      onUpdate(props) {
        component.updateProps(props);

        if (!props.clientRect) {
          return;
        }

        popup[0].setProps({
          getReferenceClientRect: props.clientRect,
        });
      },

      onKeyDown(props) {
        if (props.event.key === 'Escape') {
          popup[0].hide();
          return true;
        }
        return component.ref?.onKeyDown(props);
      },

      onExit() {
        popup[0].destroy();
        component.destroy();
      },
    };
  },
};
