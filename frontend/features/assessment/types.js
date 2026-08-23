export const emptyTiptapDoc = () => ({ type: "doc", content: [] });
export function textDoc(text) {
    return {
        type: "doc",
        content: text
            ? [{ type: "paragraph", content: [{ type: "text", text }] }]
            : [],
    };
}
