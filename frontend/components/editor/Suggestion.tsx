import { ReactRenderer } from "@tiptap/react";
import { SuggestionList } from "./SuggestionList";
import { getLatexSnippetsAPI } from "@/services/editor.service";

let cachedSnippets: any[] = [];

export const suggestionRenderer = {
  items: async ({ query }: { query: string }) => {
    try {
      if (cachedSnippets.length === 0) {
        cachedSnippets = await getLatexSnippetsAPI();
      }

      const filtered = cachedSnippets
        .filter(
          (item: any) =>
            item.label.toLowerCase().includes(query.toLowerCase()) ||
            (item.detail &&
              item.detail.toLowerCase().includes(query.toLowerCase())),
        )
        .slice(0, 15);

      return filtered;
    } catch (error) {
      console.error("Failed to fetch LaTeX snippets:", error);
      return [];
    }
  },

  render: () => {
    let component: any;
    let wrapper: HTMLDivElement | null = null;

    return {
      onStart: (props: any) => {
        component = new ReactRenderer(SuggestionList, {
          props,
          editor: props.editor,
        });

        wrapper = document.createElement("div");
        wrapper.style.position = "fixed";
        wrapper.style.zIndex = "99999";
        wrapper.style.pointerEvents = "auto";
        document.body.appendChild(wrapper);
        wrapper.appendChild(component.element);

        if (props.clientRect) {
          const rect = props.clientRect();
          if (rect) {
            wrapper.style.left = `${rect.left}px`;
            wrapper.style.top = `${rect.bottom + 4}px`;
          }
        }
      },

      onUpdate(props: any) {
        component.updateProps(props);

        if (props.clientRect && wrapper) {
          const rect = props.clientRect();
          if (rect) {
            wrapper.style.left = `${rect.left}px`;
            wrapper.style.top = `${rect.bottom + 4}px`;
          }
        }
      },

      onKeyDown(props: any) {
        if (props.event.key === "Escape") {
          if (wrapper) {
            wrapper.style.display = "none";
          }
          return true;
        }

        return component.ref?.onKeyDown(props);
      },

      onExit() {
        if (wrapper) {
          wrapper.remove();
          wrapper = null;
        }
        component.destroy();
      },
    };
  },
};
