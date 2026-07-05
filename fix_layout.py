import re

with open('frontend/app/(main)/luu-tru/page.tsx', 'r') as f:
    code = f.read()

start_str = '                <table className="w-full text-left border-collapse">'
end_str = '              </table>'

start_idx = code.find(start_str)
end_idx = code.find(end_str) + len(end_str)

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

new_code = f"""                <div className="grid grid-cols-1 gap-4">
                  {{items.length === 0 ? (
                    <div className="py-24 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] w-full text-center">
                      <p className="text-[17px] text-[#6E6E73]">Chưa có dữ liệu</p>
                    </div>
                  ) : (
                    items.map((item) => (
                      <div
                        key={{item._id}}
                        onClick={{() => setDetailsItem(item)}}
                        className="flex flex-col sm:flex-row gap-6 p-4 items-center bg-[#F5F5F7] rounded-[18px] transition-transform hover:scale-[1.02] cursor-pointer relative"
                      >
                        <div className="absolute top-4 left-4 z-10 sm:static sm:z-auto">
                          <input
                            type="checkbox"
                            checked={{selectedIds.has(item._id)}}
                            onChange={{() => toggleSelect(item._id)}}
                            onClick={{(e) => e.stopPropagation()}}
                            className="w-4 h-4 rounded-[4px] border-[#C7C7CC] accent-[#0071E3]"
                          />
                        </div>
                        <div className="w-[120px] h-[120px] shrink-0 rounded-[10px] bg-white relative overflow-hidden flex items-center justify-center mt-6 sm:mt-0">
                          {{item.is_folder ? (
                            <Folder className="w-12 h-12 text-[#1D1D1F]" />
                          ) : item.mime_type?.startsWith("image/") ? (
                            <img
                              src={{item.url}}
                              alt={{item.name}}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <File className="w-12 h-12 text-[#6E6E73]" />
                          )}}
                        </div>

                        <div className="flex-1 flex flex-col gap-2 w-full">
                          <div className="flex flex-wrap gap-2 mb-1 items-center">
                            <span className="text-[12px] font-medium text-[#0071E3]">
                              {{item.is_folder ? "Thư mục" : "Tài liệu"}}
                            </span>
                            {{item.is_public && (
                              <span className="text-[12px] font-medium text-[#34C759]">
                                Công khai
                              </span>
                            )}}
                            {{item.is_starred && (
                              <Star className="w-3.5 h-3.5 text-[#FF9500] fill-[#FF9500]" />
                            )}}
                            {{item.versions && item.versions.length > 0 && (
                              <span className="text-[10px] font-medium bg-[#E8E8ED] text-[#6E6E73] px-2 py-0.5 rounded-full">
                                v{{item.versions.length + 1}}
                              </span>
                            )}}
                          </div>

                          <h3 className="text-[20px] font-medium text-[#1D1D1F] line-clamp-2 leading-snug">
                            {{item.name}}
                          </h3>

                          <div className="text-[13px] text-[#6E6E73] flex items-center gap-2">
                            <span className="truncate">
                              {{item.is_folder ? "--" : formatSize(item.size)}}
                            </span>
                            <span>•</span>
                            <span className="shrink-0">
                              {{new Date(item.updated_at).toLocaleDateString("vi-VN")}}
                            </span>
                          </div>

                          <div className="mt-4 pt-4 border-t border-[#E8E8ED] flex items-center justify-between">
                            <span className="text-[15px] font-medium text-[#1D1D1F]">
                              Thao tác
                            </span>
{dropdown_code}
                          </div>
                        </div>
                      </div>
                    ))
                  )}}
                </div>"""

code = code[:start_idx] + new_code + code[end_idx:]
with open('frontend/app/(main)/luu-tru/page.tsx', 'w') as f:
    f.write(code)
