const fs = require('fs');
const { execSync } = require('child_process');

// Find all page.tsx in frontend/app/(main)
const files = execSync('find "frontend/app/(main)" -name "page.tsx"').toString().split('\n').filter(Boolean);

let updatedCount = 0;

files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  let originalContent = content;

  // Skip files that already have animate-in
  if (content.includes('animate-in fade-in slide-in-from-bottom-8')) {
    return;
  }
  
  // 1. Update the main wrapper to include min-h-[calc(100dvh-var(--navbar-height))]
  content = content.replace(
    /<div className="w-full max-w-\[1280px\] mx-auto px-6 py-6 font-sans text-black selection:bg-black selection:text-white">/g,
    '<div className="w-full max-w-[1280px] mx-auto px-6 py-6 min-h-[calc(100dvh-var(--navbar-height))] font-sans text-black selection:bg-black selection:text-white">'
  );

  // 2. Animate aside cards (0ms delay)
  content = content.replace(
    /(<aside[^>]*>\s*)<div className="([^"]*bg-white border border-zinc-200[^"]*)"/g,
    '$1<div className="$2 animate-in fade-in slide-in-from-bottom-8 duration-300"'
  );

  // 3. Animate main area (150ms delay)
  content = content.replace(
    /(<main[^>]*>\s*)<div className="([^"]*bg-white border border-zinc-200[^"]*)"/g,
    '$1<div className="$2 animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: \'150ms\', animationFillMode: \'both\' }}'
  );

  // Fallback for simple pages without <main> or <aside>, if there's a primary wrapper inside max-w-[1280px]
  if (!content.includes('<main') && !content.includes('animate-in fade-in')) {
    content = content.replace(
      /(<div className="w-full max-w-\[1280px\][^>]*>\s*)<div className="([^"]*bg-white border border-zinc-200[^"]*)"/g,
      '$1<div className="$2 animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: \'150ms\', animationFillMode: \'both\' }}'
    );
  }

  // Fallback pattern: main -> space-y-6 -> div
  if (content === originalContent) {
    let newContent = content.replace(
      /(<main[^>]*>\s*<div className="space-y-[^"]*">\s*)<div className="([^"]*bg-white border border-zinc-200[^"]*)"/g,
      '$1<div className="$2 animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: \'150ms\', animationFillMode: \'both\' }}'
    );
    if (newContent !== content) {
      content = newContent;
    }
  }

  if (content !== originalContent) {
    fs.writeFileSync(file, content, 'utf8');
    console.log('Updated:', file);
    updatedCount++;
  } else {
    console.log('Skipped (Pattern not matched):', file);
  }
});

console.log(`Successfully updated ${updatedCount} files.`);
