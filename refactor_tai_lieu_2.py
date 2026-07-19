import re

with open("frontend/app/(main)/tai-lieu/page.tsx", "r") as f:
    lines = f.readlines()

new_lines = []
skip_toolbar = False
skip_list = False
found_toolbar = False
found_list = False

for i, line in enumerate(lines):
    if line.startswith('import { DocumentSidebar }'):
        new_lines.append(line)
        new_lines.append('import { DocumentToolbar } from "@/features/content/components/DocumentToolbar";\n')
        new_lines.append('import { DocumentList } from "@/features/content/components/DocumentList";\n')
        continue

    # Identify toolbar start
    if '<div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">' in line and not found_toolbar:
        skip_toolbar = True
        found_toolbar = True
        new_lines.append('          <DocumentToolbar\n')
        new_lines.append('            currentFolder={currentFolder}\n')
        new_lines.append('            breadcrumbs={breadcrumbs}\n')
        new_lines.append('            setCurrentFolder={setCurrentFolder}\n')
        new_lines.append('            setBreadcrumbs={setBreadcrumbs}\n')
        new_lines.append('            showSearch={showSearch}\n')
        new_lines.append('            setShowSearch={setShowSearch}\n')
        new_lines.append('            searchQuery={searchQuery}\n')
        new_lines.append('            setSearchQuery={setSearchQuery}\n')
        new_lines.append('            sortOrder={sortOrder}\n')
        new_lines.append('            setSortOrder={setSortOrder}\n')
        new_lines.append('            layout={layout}\n')
        new_lines.append('            setLayout={setLayout}\n')
        new_lines.append('            setShowPublishModal={setShowPublishModal}\n')
        new_lines.append('          />\n')
        continue

    if skip_toolbar and '          {showSearch && (' in line:
        skip_toolbar = False
        new_lines.append(line)
        continue

    # Identify list start
    if '            {displayItems.length === 0 && !isLoading && !isRefreshing ? (' in line and not found_list:
        skip_list = True
        found_list = True
        new_lines.append('            <DocumentList\n')
        new_lines.append('              layout={layout}\n')
        new_lines.append('              displayItems={displayItems}\n')
        new_lines.append('              handleContextMenu={handleContextMenu}\n')
        new_lines.append('              isLoading={isLoading}\n')
        new_lines.append('              hasMore={hasMore}\n')
        new_lines.append('              isRefreshing={isRefreshing}\n')
        new_lines.append('              loaderRef={loaderRef}\n')
        new_lines.append('            />\n')
        continue

    # List ends before closing main div
    if skip_list and '          </div>' in line and '        </main>' in lines[i+1]:
        skip_list = False
        new_lines.append(line)
        continue

    if not skip_toolbar and not skip_list:
        new_lines.append(line)

with open("frontend/app/(main)/tai-lieu/page.tsx", "w") as f:
    f.writelines(new_lines)
