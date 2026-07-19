import re

with open("frontend/app/(main)/tin-nhan/page.tsx", "r") as f:
    content = f.read()

# 1. Replace the Sidebar block (starts from <div className="w-[320px]... down to the end of sidebar)
# It's better to just find the indices.

lines = content.split('\n')

sidebar_start = -1
sidebar_end = -1
header_start = -1
header_end = -1
bubble_start = -1
bubble_end = -1
input_start = -1
input_end = -1

for i, line in enumerate(lines):
    if '<div className="w-[320px] flex-shrink-0 flex flex-col' in line:
        sidebar_start = i
    if '          <div className="px-4 pb-2">' in line and sidebar_start != -1 and sidebar_end == -1:
        pass # Still in sidebar
    if '      {/* End Sidebar */}' in line or (sidebar_start != -1 and '      <div className="flex-1 flex flex-col bg-white relative">' in line):
        sidebar_end = i - 1

    if '        <div className="h-[60px] border-b border-[#E8E8ED] bg-white/80' in line:
        header_start = i
    if header_start != -1 and header_end == -1 and '        {/* Shared Links/Docs Sidebar (Right) */}' in line:
        header_end = i - 1
        
    if '                    <div className={`flex flex-col transition-colors duration-500 mb-2' in line:
        bubble_start = i
    if bubble_start != -1 and bubble_end == -1 and '                    </div>' in line and lines[i+1].startswith('                  </React.Fragment>'):
        bubble_end = i

    if '        <div className="px-4 pb-4 pt-2 bg-transparent relative">' in line:
        input_start = i
    if input_start != -1 and input_end == -1 and '        </div>' in line and lines[i+1].startswith('      </div>'):
        input_end = i

print(f"Sidebar: {sidebar_start} to {sidebar_end}")
print(f"Header: {header_start} to {header_end}")
print(f"Bubble: {bubble_start} to {bubble_end}")
print(f"Input: {input_start} to {input_end}")
