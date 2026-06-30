import os

path = "frontend/app/(main)/page.tsx"
with open(path, "r") as f:
    content = f.read()

# Fix the main tag to have overflow-y-auto no-scrollbar
content = content.replace('<main className="lg:col-span-9 space-y-8">', '<main className="lg:col-span-9 space-y-8 overflow-y-auto no-scrollbar pb-6">')

# Fix grid/list button size
old_btn = """<div className="flex items-center">
                <div className="flex bg-[#E8E8ED] p-1 rounded-full shrink-0">
                    <button onClick={() => setViewMode("grid")} className={`p-1.5 rounded-full transition-colors ${viewMode === "grid" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}>
                      <LayoutGrid className="w-4 h-4" />
                    </button>
                    <button onClick={() => setViewMode("list")} className={`p-1.5 rounded-full transition-colors ${viewMode === "list" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}>
                      <List className="w-4 h-4" />
                    </button>
                  </div>
              </div>"""

new_btn = """<div className="flex bg-[#E8E8ED] rounded-full p-0.5 shrink-0">
                <button onClick={() => setViewMode("grid")} className={`p-1 rounded-full transition-colors ${viewMode === "grid" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}>
                  <LayoutGrid className="w-4 h-4" />
                </button>
                <button onClick={() => setViewMode("list")} className={`p-1 rounded-full transition-colors ${viewMode === "list" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}>
                  <List className="w-4 h-4" />
                </button>
              </div>"""
content = content.replace(old_btn, new_btn)

with open(path, "w") as f:
    f.write(content)

