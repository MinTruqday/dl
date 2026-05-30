const fs = require('fs');
const files = fs.readdirSync('.').filter(f => f.startsWith('DocLib') && f.endsWith('.ts'));
for (const file of files) {
    const lines = fs.readFileSync(file, 'utf8').split('\n');
    lines.forEach((line, i) => {
        let single = 0, double = 0, backtick = 0;
        let escaped = false;
        for (let char of line) {
            if (escaped) { escaped = false; continue; }
            if (char === '\\') { escaped = true; continue; }
            if (char === "'" && backtick % 2 === 0 && double % 2 === 0) single++;
            if (char === '"' && backtick % 2 === 0 && single % 2 === 0) double++;
            if (char === '`' && single % 2 === 0 && double % 2 === 0) backtick++;
        }
        if (single % 2 !== 0 && !line.trim().startsWith('//')) {
             console.log(`Unclosed single quote in ${file}:${i+1} => ${line}`);
        }
        if (double % 2 !== 0 && !line.trim().startsWith('//')) {
             console.log(`Unclosed double quote in ${file}:${i+1} => ${line}`);
        }
    });
}
