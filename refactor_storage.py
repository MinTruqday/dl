import re

with open("frontend/app/(main)/luu-tru/page.tsx", "r") as f:
    lines = f.readlines()

new_lines = []
skip_sidebar = False
skip_details = False

for i, line in enumerate(lines):
    if line.startswith('import { showToast }'):
        new_lines.append(line)
        new_lines.append('import { StorageSidebar } from "@/features/storage/components/StorageSidebar";\n')
        new_lines.append('import { StorageDetails } from "@/features/storage/components/StorageDetails";\n')
        continue

    if '<aside className="w-full md:w-[240px] shrink-0 space-y-6 sticky top-0 h-fit mb-6 md:mb-0 md:mr-6">' in line:
        skip_sidebar = True
        new_lines.append('        <StorageSidebar viewMode={viewMode} setViewMode={setViewMode} />\n')
        continue

    if skip_sidebar and '<main className="flex-1 min-w-0' in line:
        skip_sidebar = False
        new_lines.append(line)
        continue

    if '<aside className="w-full h-full min-h-0 bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] flex flex-col gap-6 overflow-hidden relative">' in line:
        skip_details = True
        new_lines.append('          <StorageDetails detailsItem={detailsItem} setDetailsItem={setDetailsItem} viewMode={viewMode} />\n')
        continue

    if skip_details and '</aside>' in line:
        skip_details = False
        continue

    if not skip_sidebar and not skip_details:
        new_lines.append(line)

with open("frontend/app/(main)/luu-tru/page.tsx", "w") as f:
    f.writelines(new_lines)
