const edjsHTML = require("editorjs-html");
const parser = edjsHTML();

const data = {
    blocks: [
        { type: "paragraph", data: { text: "Hello" } },
        { type: "unknown", data: { text: "World" } }
    ]
};

try {
    console.log(parser.parse(data));
} catch (e) {
    console.log("Error:", e.message);
}
