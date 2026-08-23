# Tiptap assessment editor

The assessment editor uses Tiptap 2 27 2 across all packages to keep one compatible ProseMirror schema

## Registered extensions

- StarterKit with document paragraph text headings bold italic strike inline code blockquote bullet list ordered list horizontal rule hard break undo redo drop cursor and gap cursor
- Link with automatic links paste links editing removal and safe external attributes
- Underline highlight subscript superscript text style color and font family
- Text alignment typography placeholder and character count
- Code Block Lowlight with common language syntax highlighting
- Task List and nested Task Item
- Details Details Summary and Details Content
- Table Table Row Table Header and Table Cell with row column and table operations
- Image with required alternative text and remote HTTP or HTTPS source validation
- YouTube with privacy enhanced playback and HTTPS host validation
- Mathematics with KaTeX rendering
- Assessment Section Question Reference and Page Break domain nodes

The same extension factory is used by the editable and read only surfaces so persisted JSON never depends on a node or mark unavailable to the reader

The assessment service validates the corresponding node mark and attribute allowlists before content can be accepted

## Official references

- https://tiptap.dev/docs/editor/core-concepts/extensions
- https://tiptap.dev/docs/editor/extensions/marks
- https://tiptap.dev/docs/editor/extensions/nodes
- https://tiptap.dev/docs/editor/extensions/marks/link
- https://tiptap.dev/docs/editor/extensions/functionality/textalign
