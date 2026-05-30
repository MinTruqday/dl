const fs = require('fs');

let content = fs.readFileSync('/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend/components/editor/Editor.tsx', 'utf8');
const lines = content.split('\n');
const newLines = [];

const toRemove = new Set();

for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // Find NPM imports
    const importMatch = line.match(/const\s+([A-Za-z0-9_]+)\s*=\s*\(await\s+import\(['"]([^'"]+)['"]\)\)\.default;/);
    if (importMatch) {
        const varName = importMatch[1];
        const moduleName = importMatch[2];
        if (moduleName !== '@editorjs/editorjs' && !moduleName.startsWith('./') && !moduleName.startsWith('@/')) {
            toRemove.add(varName);
            console.log('Removing import for:', varName, moduleName);
            continue; // Skip this line
        }
    }
    
    // Also remove any line that uses these variables in an `if (VarName)` check
    let skipLine = false;
    for (const varName of toRemove) {
        if (line.includes(`if (${varName})`) || line.includes(`if (${varName} `) || line.includes(`if (${varName}!`)) {
            console.log('Removing assignment for:', varName);
            skipLine = true;
            break;
        }
        if (line.includes(`new ${varName}(`)) {
            console.log('Removing instantiation for:', varName);
            skipLine = true;
            break;
        }
    }
    
    // Also manual hardcoded removals for Inline/Undo/DragDrop which might have been deleted as imports but still have `if` checks
    if (line.includes('if (InlineTool) tools.inlineTool = InlineTool;') ||
        line.includes('if (Inline) tools.inline = Inline;') ||
        line.includes('if (InlineTemplate) tools.inlineTemplate = InlineTemplate;') ||
        line.includes('if (InlineHotkey) tools.inlineHotkey = InlineHotkey;') ||
        line.includes('if (Undo) new Undo') ||
        line.includes('if (DragDrop) new DragDrop')
       ) {
        console.log('Removing leftover assignment:', line.trim());
        continue;
    }

    if (!skipLine) {
        newLines.push(line);
    }
}

fs.writeFileSync('/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend/components/editor/Editor.tsx', newLines.join('\n'), 'utf8');
console.log('Cleaned up Editor.tsx successfully!');
