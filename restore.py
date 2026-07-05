import re

with open('frontend/app/(main)/luu-tru/page.tsx', 'r') as f:
    code = f.read()

start_str = '                <div className="grid grid-cols-1 gap-4">'
end_str = '                </div>'

start_idx = code.find(start_str)
end_idx = code.find(end_str, start_idx) + len(end_str)

dropdown_code = """                            {viewMode === "trash" ? (
                              <div className="relative">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setOpenMenuId(openMenuId === item._id ? null : item._id);
                                  }}
                                  className="p-1.5 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[8px]"
                                >
                                  <MoreVertical className="w-4 h-4" />
                                </button>
                                
                                {openMenuId === item._id && (
                                  <>
                                    <div className="fixed inset-0 z-40" onClick={(e) => { e.stopPropagation(); setOpenMenuId(null); }} />
                                    <div 
                                      className="absolute right-0 top-full mt-1 w-48 bg-white rounded-[12px] shadow-[0_4px_24px_rgba(0,0,0,0.1)] border border-[#E8E8ED] py-2 z-50 flex flex-col"
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleRestore(item);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#0071E3] hover:bg-[#0071E3]/10 text-left"
                                      >
                                        <RotateCcw className="w-4 h-4" /> Khôi phục
                                      </button>
                                      <div className="h-[1px] bg-[#E8E8ED] my-1" />
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleDelete(item);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#FF3B30] hover:bg-[#FF3B30]/10 text-left"
                                      >
                                        <Trash2 className="w-4 h-4" /> Xóa vĩnh viễn
                                      </button>
                                    </div>
                                  </>
                                )}
                              </div>
                            ) : (
                              <div className="relative">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setOpenMenuId(openMenuId === item._id ? null : item._id);
                                  }}
                                  className="p-1.5 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[8px]"
                                >
                                  <MoreVertical className="w-4 h-4" />
                                </button>
                                
                                {openMenuId === item._id && (
                                  <>
                                    <div className="fixed inset-0 z-40" onClick={(e) => { e.stopPropagation(); setOpenMenuId(null); }} />
                                    <div 
                                      className="absolute right-0 top-full mt-1 w-48 bg-white rounded-[12px] shadow-[0_4px_24px_rgba(0,0,0,0.1)] border border-[#E8E8ED] py-2 z-50 flex flex-col"
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleToggleStar(item);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                      >
                                        <Star className={`w-4 h-4 ${item.is_starred ? "text-[#FF9500] fill-[#FF9500]" : ""}`} />
                                        {item.is_starred ? "Bỏ gắn sao" : "Gắn sao"}
                                      </button>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleToggleLock(item);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                      >
                                        {item.is_public ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                                        {item.is_public ? "Khóa" : "Mở khóa"}
                                      </button>
                                      <button
                                        onClick={() => {
                                          setShareItem(item);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                      >
                                        <Share2 className="w-4 h-4" /> Chia sẻ
                                      </button>
                                      {!item.is_folder && (
                                        <button
                                          onClick={() => {
                                            setVersionItem(item);
                                            versionInputRef.current?.click();
                                            setOpenMenuId(null);
                                          }}
                                          className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                        >
                                          <History className="w-4 h-4" /> Cập nhật bản mới
                                        </button>
                                      )}
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setRenameItem(item);
                                          setNewName(item.name);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                      >
                                        <Edit2 className="w-4 h-4" /> Đổi tên
                                      </button>
                                      <button
                                        onClick={() => {
                                          setMoveItem(item);
                                          setMoveTargetId(undefined);
                                          setMoveBreadcrumbs([{ name: "Tất cả" }]);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                      >
                                        <Archive className="w-4 h-4" /> Di chuyển
                                      </button>
                                      <div className="h-[1px] bg-[#E8E8ED] my-1" />
                                      <button
                                        onClick={() => {
                                          handleDelete(item);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#FF3B30] hover:bg-[#FF3B30]/10 text-left"
                                      >
                                        <Trash2 className="w-4 h-4" /> Xóa
                                      </button>
                                    </div>
                                  </>
                                )}
                              </div>
                            )}"""

table_code = f"""                <table className="w-full text-left border-collapse">
                  <thead>
                  <tr className="text-[13px] text-[#6E6E73] border-b border-[#E8E8ED]">
                    <th className="py-3 px-6 font-medium w-12 text-center"></th>
                    <th className="py-3 px-6 font-medium text-left">Tên</th>
                    <th className="py-3 px-6 font-medium text-center hidden md:table-cell">Loại</th>
                    <th className="py-3 px-6 font-medium text-center hidden md:table-cell">Kích thước</th>
                    <th className="py-3 px-6 font-medium text-center hidden md:table-cell">Cập nhật</th>
                    <th className="py-3 px-6 font-medium text-center hidden md:table-cell">Bảo mật</th>
                    <th className="py-3 px-6 font-medium text-right">
                      Thao tác
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {{items.length === 0 ? (
                    <tr>
                      <td
                        colSpan={{7}}
                      >
                        <div className="py-24 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] w-full text-center my-4">
                          <p className="text-[17px] text-[#6E6E73]">Chưa có dữ liệu</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    items.map((item) => (
                      <tr
                        key={{item._id}}
                        onClick={{() => setDetailsItem(item)}}
                        className="hover:bg-[#E8E8ED]/60 transition-colors cursor-pointer group"
                      >
                        <td
                          className="py-3 px-6 text-center"
                          onClick={{(e) => e.stopPropagation()}}
                        >
                          <input
                            type="checkbox"
                            checked={{selectedIds.has(item._id)}}
                            onChange={{() => toggleSelect(item._id)}}
                            className="w-4 h-4 rounded-[4px] border-[#C7C7CC] accent-[#0071E3]"
                          />
                        </td>
                        <td className="py-3 px-6 max-w-[300px]">
                          <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2 flex-1 min-w-0">
                              {{item.is_starred && (
                                <Star className="w-4 h-4 text-[#FF9500] fill-[#FF9500] shrink-0" />
                              )}}
                              {{item.is_folder ? (
                                <button
                                  onClick={{(e) => {{
                                    e.stopPropagation();
                                    handleNavigate(item);
                                  }}}}
                                  className="text-[14px] font-medium text-[#1D1D1F] hover:text-[#0071E3] truncate"
                                >
                                  {{item.name}}
                                </button>
                              ) : item.name.endsWith('.doclib') ? (
                                <a
                                  href={{`/soan-thao?tai-lieu=${{item._id}}`}}
                                  onClick={{(e) => e.stopPropagation()}}
                                  target="_blank"
                                  className="text-[14px] font-medium text-[#1D1D1F] hover:text-[#0071E3] truncate"
                                >
                                  {{item.name}}
                                </a>
                              ) : item.url ? (
                                <a
                                  href={{item.url}}
                                  target="_blank"
                                  className="text-[14px] font-medium text-[#1D1D1F] hover:text-[#0071E3] truncate"
                                >
                                  {{item.name}}
                                </a>
                              ) : (
                                <span className="text-[14px] font-medium text-[#1D1D1F] truncate">
                                  {{item.name}}
                                </span>
                              )}}
                              {{item.versions && item.versions.length > 0 && (
                                <span className="text-[10px] font-medium bg-[#E8E8ED] text-[#6E6E73] px-2 py-0.5 rounded-full shrink-0">
                                  v{{item.versions.length + 1}}
                                </span>
                              )}}
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-6 text-[13px] text-[#6E6E73] text-center hidden md:table-cell">
                          {{item.is_folder ? "Thư mục" : "Tài liệu"}}
                        </td>
                        <td className="py-3 px-6 text-[13px] text-[#6E6E73] text-center hidden md:table-cell">
                          {{item.is_folder ? "--" : formatSize(item.size)}}
                        </td>
                        <td className="py-3 px-6 text-[13px] text-[#6E6E73] text-center hidden md:table-cell">
                          {{new Date(item.updated_at).toLocaleDateString(
                            "vi-VN",
                          )}}
                        </td>
                        <td className="py-3 px-6 text-[13px] text-[#6E6E73] text-center hidden md:table-cell">
                          {{item.is_public ? "Công khai" : "Riêng tư"}}
                        </td>
                        <td className="py-3 px-6 text-right">
                          <div className="flex justify-end gap-1 transition-opacity">
{dropdown_code}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}}
                </tbody>
              </table>"""

code = code[:start_idx] + table_code + code[end_idx:]

code = code.replace(
    'className={`w-full transition-colors ${isDraggingOver ? "border border-[#0071E3] bg-[#F5F5F7]/80 rounded-[18px]" : ""}`}',
    'className={`w-full overflow-x-auto min-h-[400px] transition-colors ${isDraggingOver ? "border border-[#0071E3] bg-[#F5F5F7]/80 rounded-[18px]" : ""}`}'
)

with open('frontend/app/(main)/luu-tru/page.tsx', 'w') as f:
    f.write(code)
