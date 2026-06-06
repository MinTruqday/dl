const fs = require('fs');
const ts = require('typescript');

const content = fs.readFileSync('/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend/app/(main)/tro-chuyen/page.tsx', 'utf8');
const sourceFile = ts.createSourceFile('page.tsx', content, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);

function printErrors() {
    const diagnostics = sourceFile.parseDiagnostics;
    if (diagnostics.length > 0) {
        diagnostics.forEach(diag => {
            const { line, character } = sourceFile.getLineAndCharacterOfPosition(diag.start);
            console.log(`Error at ${line + 1}:${character + 1}: ${diag.messageText}`);
        });
    } else {
        console.log("No syntax errors found by TS parser!");
    }
}
printErrors();
