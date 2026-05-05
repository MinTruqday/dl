import { ReactRenderer } from "@tiptap/react";
import tippy, { Instance } from "tippy.js";
import { SuggestionList } from "./SuggestionList";
import { getLatexSnippetsAPI } from "@/services/editor.service";

let cachedSnippets: any[] = [];

export const suggestionRenderer = {
  items: async ({ query }: { query: string }) => {
    try {
      if (cachedSnippets.length === 0) {
        console.log("Fetching LaTeX snippets");
        cachedSnippets = await getLatexSnippetsAPI();
        console.log(`Loaded ${cachedSnippets.length} snippets.`);
      }
      
      const filtered = cachedSnippets
        .filter(
          (item: any) =>
            item.label.toLowerCase().includes(query.toLowerCase()) ||
            (item.detail &&
              item.detail.toLowerCase().includes(query.toLowerCase())),
        )
        .slice(0, 15);
        
      console.log(`Autocomplete query: "${query}", found ${filtered.length} items`);
      return filtered;
    } catch (error) {
      console.error("Failed to fetch LaTeX snippets:", error);
      return [];
    }
  },

  render: () => {
    let component: any;
    let popup: any;

    return {
      onStart: (props: any) => {
        console.log("Suggestion started", props);
        component = new ReactRenderer(SuggestionList, {
          props,
          editor: props.editor,
        });

        if (!props.clientRect) {
          console.warn("No clientRect provided for suggestion");
          return;
        }

        popup = tippy("body", {
          getReferenceClientRect: props.clientRect,
          appendTo: () => document.body,
          content: component.element,
          showOnCreate: true,
          interactive: true,
          trigger: "manual",
          placement: "bottom-start",
        });
      },

      onUpdate(props: any) {
        component.updateProps(props);

        if (!props.clientRect) {
          return;
        }

        if (popup && popup[0]) {
          popup[0].setProps({
            getReferenceClientRect: props.clientRect,
          });
        }
      },

      onKeyDown(props: any) {
        if (props.event.key === "Escape") {
          if (popup && popup[0]) {
            popup[0].hide();
          }
          return true;
        }

        return component.ref?.onKeyDown(props);
      },

      onExit() {
        console.log("Suggestion exited");
        if (popup && popup[0]) {
          popup[0].destroy();
        }
        component.destroy();
      },
    };
  },
};
