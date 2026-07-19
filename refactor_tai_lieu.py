import re

with open("frontend/app/(main)/tai-lieu/page.tsx", "r") as f:
    lines = f.readlines()

new_lines = []
skip_sidebar = False

for i, line in enumerate(lines):
    if line.startswith('import { showToast }'):
        new_lines.append(line)
        new_lines.append('import { DocumentSidebar } from "@/features/content/components/DocumentSidebar";\n')
        continue

    if '<aside className="w-full md:w-[240px] shrink-0 space-y-6 sticky top-0 h-fit mb-6 md:mb-0 md:mr-6">' in line:
        skip_sidebar = True
        new_lines.append('        <DocumentSidebar viewMode={viewMode} setViewMode={setViewMode} setFilterStar={setFilterStar} filterFormat={filterFormat} setFilterFormat={setFilterFormat} />\n')
        continue

    if skip_sidebar and '</aside>' in line:
        skip_sidebar = False
        continue

    if not skip_sidebar:
        new_lines.append(line)

with open("frontend/app/(main)/tai-lieu/page.tsx", "w") as f:
    f.writelines(new_lines)
