import re

with open("frontend/app/(main)/tro-chuyen/page.tsx", "r") as f:
    lines = f.readlines()

new_lines = []
skip_sidebar = False

for i, line in enumerate(lines):
    if line.startswith('import { showToast }'):
        new_lines.append(line)
        new_lines.append('import { AgenticSidebar } from "@/features/agentic_ai/components/AgenticSidebar";\n')
        continue

    if '<aside className="w-full lg:w-[320px] bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none flex flex-col overflow-hidden shrink-0 hidden lg:flex">' in line:
        skip_sidebar = True
        new_lines.append('        <AgenticSidebar sessions={sessions} currentSessionId={currentSessionId} onSelectSession={handleSessionSelect} onNewSession={() => {setCurrentSessionId(null); setMessages([]);}} onDeleteSession={handleDeleteSession} />\n')
        continue

    if skip_sidebar and '</aside>' in line:
        skip_sidebar = False
        continue

    if not skip_sidebar:
        new_lines.append(line)

with open("frontend/app/(main)/tro-chuyen/page.tsx", "w") as f:
    f.writelines(new_lines)
