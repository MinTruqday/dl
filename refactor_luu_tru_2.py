import re

with open("frontend/app/(main)/luu-tru/page.tsx", "r") as f:
    lines = f.readlines()

new_lines = []
skip_toolbar = False
skip_grid = False
found_toolbar = False
found_grid = False

for i, line in enumerate(lines):
    if line.startswith('import { StorageSidebar }'):
        new_lines.append(line)
        new_lines.append('import { StorageToolbar } from "@/features/storage/components/StorageToolbar";\n')
        new_lines.append('import { StorageFileGrid } from "@/features/storage/components/StorageFileGrid";\n')
        continue

    # Identify toolbar start
    if '<div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">' in line and not found_toolbar:
        skip_toolbar = True
        found_toolbar = True
        new_lines.append('          <StorageToolbar\n')
        new_lines.append('            viewMode={viewMode}\n')
        new_lines.append('            breadcrumbs={breadcrumbs}\n')
        new_lines.append('            handleNavigateBreadcrumb={handleNavigateBreadcrumb}\n')
        new_lines.append('            layout={layout}\n')
        new_lines.append('            setLayout={setLayout}\n')
        new_lines.append('            handleUploadClick={handleUploadClick}\n')
        new_lines.append('            handleUploadClickDoc={handleUploadClickDoc}\n')
        new_lines.append('            setShowNewFolderModal={setShowNewFolderModal}\n')
        new_lines.append('            handleDeleteEmptyTrash={handleDeleteEmptyTrash}\n')
        new_lines.append('          />\n')
        continue

    if skip_toolbar and '          <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">' in line:
        skip_toolbar = False
        new_lines.append(line)
        continue

    # Identify grid start
    if '            {displayItems.length === 0 ? (' in line and not found_grid:
        skip_grid = True
        found_grid = True
        new_lines.append('              <StorageFileGrid\n')
        new_lines.append('                layout={layout}\n')
        new_lines.append('                displayItems={displayItems}\n')
        new_lines.append('                viewMode={viewMode}\n')
        new_lines.append('                handleFolderClick={handleFolderClick}\n')
        new_lines.append('                setDetailsItem={setDetailsItem}\n')
        new_lines.append('                handleContextMenu={handleContextMenu}\n')
        new_lines.append('              />\n')
        continue

    # Grid ends before closing main div
    if skip_grid and '          </div>' in line and '        </main>' in lines[i+1]:
        skip_grid = False
        new_lines.append(line)
        continue

    if not skip_toolbar and not skip_grid:
        new_lines.append(line)

with open("frontend/app/(main)/luu-tru/page.tsx", "w") as f:
    f.writelines(new_lines)
