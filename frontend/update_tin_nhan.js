const fs = require('fs');

const path = '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend/app/(main)/tin-nhan/page.tsx';
let content = fs.readFileSync(path, 'utf8');

// Replace Dropdown 1
const target1 = `                          {activeConvMenuId === conv.other_user_id && (
                            <div className="absolute right-0 top-full mt-1 w-40 bg-white border border-zinc-200 rounded-2xl shadow-lg z-50 overflow-hidden flex flex-col py-1">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleTogglePinConv(conv.other_user_id);
                                }}
                                className="w-full text-left px-3 py-2 text-xs hover:bg-zinc-50 text-zinc-700 flex items-center gap-2 transition-colors"
                              >
                                {isConvPinned ? <PinOff className="w-3.5 h-3.5" /> : <Pin className="w-3.5 h-3.5" />}
                                {isConvPinned ? "Bỏ ghim" : "Ghim"}
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleMarkAsRead(conv.other_user_id);
                                }}
                                className="w-full text-left px-3 py-2 text-xs hover:bg-zinc-50 text-zinc-700 flex items-center gap-2 transition-colors"
                              >
                                <CheckCheck className="w-3.5 h-3.5" /> Đã đọc
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteConv(conv.other_user_id);
                                }}
                                className="w-full text-left px-3 py-2 text-xs hover:bg-red-50 text-red-600 flex items-center gap-2 transition-colors"
                              >
                                <Trash2 className="w-3.5 h-3.5" /> Xóa
                              </button>
                            </div>
                          )}`;

const replace1 = `                          {activeConvMenuId === conv.other_user_id && (
                            <div className="absolute right-0 top-full mt-1 w-44 p-1.5 bg-white border border-zinc-200 rounded-2xl shadow-lg z-50 flex flex-col">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleTogglePinConv(conv.other_user_id);
                                }}
                                className="w-full text-left px-3 py-2 text-xs hover:bg-zinc-100 rounded-xl text-zinc-700 flex items-center gap-2 transition-colors"
                              >
                                {isConvPinned ? <PinOff className="w-3.5 h-3.5" /> : <Pin className="w-3.5 h-3.5" />}
                                {isConvPinned ? "Bỏ ghim" : "Ghim"}
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleMarkAsRead(conv.other_user_id);
                                }}
                                className="w-full text-left px-3 py-2 text-xs hover:bg-zinc-100 rounded-xl text-zinc-700 flex items-center gap-2 transition-colors"
                              >
                                <CheckCheck className="w-3.5 h-3.5" /> Đã đọc
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteConv(conv.other_user_id);
                                }}
                                className="w-full text-left px-3 py-2 text-xs hover:bg-red-50 text-red-600 rounded-xl flex items-center gap-2 transition-colors"
                              >
                                <Trash2 className="w-3.5 h-3.5" /> Xóa
                              </button>
                            </div>
                          )}`;

// Replace Dropdown 2
const target2 = `                        <div className="absolute right-0 top-full mt-2 w-48 bg-white border border-zinc-200 rounded-2xl shadow-lg py-1 z-50">
                        <button
                          onClick={() => setShowSelfDestructMenu(!showSelfDestructMenu)}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center justify-between"
                        >
                          <div className="flex items-center gap-2.5">
                            <Flame className={\`w-4 h-4 \${selfDestructSeconds > 0 ? "text-red-500" : ""}\`} />
                            Tin nhắn tự hủy
                          </div>
                          {selfDestructSeconds > 0 && <span className="text-[10px] font-medium text-red-500">{selfDestructSeconds}s</span>}
                        </button>
                        {showSelfDestructMenu && (
                          <div className="bg-zinc-50 border-y border-zinc-100 flex flex-col text-left text-xs">
                            <button onClick={() => { handleUpdateSelfDestruct(0); setShowConvMenu(false); }} className="px-9 py-2 hover:bg-zinc-100">Tắt tự hủy</button>
                            <button onClick={() => { handleUpdateSelfDestruct(5); setShowConvMenu(false); }} className="px-9 py-2 hover:bg-zinc-100">5 giây</button>
                            <button onClick={() => { handleUpdateSelfDestruct(60); setShowConvMenu(false); }} className="px-9 py-2 hover:bg-zinc-100">1 phút</button>
                            <button onClick={() => { handleUpdateSelfDestruct(3600); setShowConvMenu(false); }} className="px-9 py-2 hover:bg-zinc-100">1 giờ</button>
                          </div>
                        )}

                        <button
                          onClick={() => { handleToggleMute(); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                        >
                          {isMuted ? <VolumeX className="w-4 h-4 text-zinc-400" /> : <Volume2 className="w-4 h-4" />}
                          {isMuted ? "Bật âm thông báo" : "Tắt âm thông báo"}
                        </button>

                        <button
                          onClick={() => { setShowSearchMsgBar(!showSearchMsgBar); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                        >
                          <Search className={\`w-4 h-4 \${showSearchMsgBar ? "text-black" : "text-zinc-500"}\`} />
                          Tìm kiếm tin nhắn
                        </button>

                        <button
                          onClick={() => { setShowSharedSidebar(!showSharedSidebar); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                        >
                          <Paperclip className={\`w-4 h-4 \${showSharedSidebar ? "text-black" : "text-zinc-500"}\`} />
                          Tệp đính kèm
                        </button>

                        <button
                          onClick={() => { handleTogglePinConv(selectedConv.other_user_id); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                        >
                          {user?.pinned_conversations?.includes(selectedConv.other_user_id) ? <PinOff className="w-4 h-4" /> : <Pin className="w-4 h-4" />}
                          {user?.pinned_conversations?.includes(selectedConv.other_user_id) ? "Bỏ ghim" : "Ghim hội thoại"}
                        </button>

                        <button
                          onClick={() => { handleMarkAsRead(selectedConv.other_user_id); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                        >
                          <CheckCheck className="w-4 h-4" />
                          Đánh dấu đã đọc
                        </button>

                        <button
                          onClick={() => { handleBlockUser(); setShowConvMenu(false); }}
                          className={\`w-full text-left px-3 py-2 text-sm transition-colors flex items-center gap-2.5 \${isBlocked ? "text-green-600 hover:bg-green-50" : "text-yellow-600 hover:bg-yellow-50"}\`}
                        >
                          <ShieldAlert className="w-4 h-4" />
                          {isBlocked ? "Mở chặn liên lạc" : "Chặn liên lạc"}
                        </button>

                        <button
                          onClick={() => { handleDeleteConv(selectedConv.other_user_id); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors flex items-center gap-2.5"
                        >
                          <Trash2 className="w-4 h-4" />
                          Xóa cuộc trò chuyện
                        </button>
                      </div>`;

const replace2 = `                        <div className="absolute right-0 top-full mt-2 w-52 p-1.5 bg-white border border-zinc-200 rounded-2xl shadow-lg z-50">
                        <button
                          onClick={() => setShowSelfDestructMenu(!showSelfDestructMenu)}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-100 rounded-xl transition-colors flex items-center justify-between"
                        >
                          <div className="flex items-center gap-2.5">
                            <Flame className={\`w-4 h-4 \${selfDestructSeconds > 0 ? "text-red-500" : ""}\`} />
                            Tin nhắn tự hủy
                          </div>
                          {selfDestructSeconds > 0 && <span className="text-[10px] font-medium text-red-500">{selfDestructSeconds}s</span>}
                        </button>
                        {showSelfDestructMenu && (
                          <div className="bg-zinc-50 border-y border-zinc-100 flex flex-col text-left text-xs my-1 rounded-xl overflow-hidden">
                            <button onClick={() => { handleUpdateSelfDestruct(0); setShowConvMenu(false); }} className="px-9 py-2 hover:bg-zinc-100 transition-colors">Tắt tự hủy</button>
                            <button onClick={() => { handleUpdateSelfDestruct(5); setShowConvMenu(false); }} className="px-9 py-2 hover:bg-zinc-100 transition-colors">5 giây</button>
                            <button onClick={() => { handleUpdateSelfDestruct(60); setShowConvMenu(false); }} className="px-9 py-2 hover:bg-zinc-100 transition-colors">1 phút</button>
                            <button onClick={() => { handleUpdateSelfDestruct(3600); setShowConvMenu(false); }} className="px-9 py-2 hover:bg-zinc-100 transition-colors">1 giờ</button>
                          </div>
                        )}

                        <button
                          onClick={() => { handleToggleMute(); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-100 rounded-xl transition-colors flex items-center gap-2.5"
                        >
                          {isMuted ? <VolumeX className="w-4 h-4 text-zinc-400" /> : <Volume2 className="w-4 h-4" />}
                          {isMuted ? "Bật âm thông báo" : "Tắt âm thông báo"}
                        </button>

                        <button
                          onClick={() => { setShowSearchMsgBar(!showSearchMsgBar); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-100 rounded-xl transition-colors flex items-center gap-2.5"
                        >
                          <Search className={\`w-4 h-4 \${showSearchMsgBar ? "text-black" : "text-zinc-500"}\`} />
                          Tìm kiếm tin nhắn
                        </button>

                        <button
                          onClick={() => { setShowSharedSidebar(!showSharedSidebar); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-100 rounded-xl transition-colors flex items-center gap-2.5"
                        >
                          <Paperclip className={\`w-4 h-4 \${showSharedSidebar ? "text-black" : "text-zinc-500"}\`} />
                          Tệp đính kèm
                        </button>

                        <button
                          onClick={() => { handleTogglePinConv(selectedConv.other_user_id); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-100 rounded-xl transition-colors flex items-center gap-2.5"
                        >
                          {user?.pinned_conversations?.includes(selectedConv.other_user_id) ? <PinOff className="w-4 h-4" /> : <Pin className="w-4 h-4" />}
                          {user?.pinned_conversations?.includes(selectedConv.other_user_id) ? "Bỏ ghim" : "Ghim hội thoại"}
                        </button>

                        <button
                          onClick={() => { handleMarkAsRead(selectedConv.other_user_id); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-100 rounded-xl transition-colors flex items-center gap-2.5"
                        >
                          <CheckCheck className="w-4 h-4" />
                          Đánh dấu đã đọc
                        </button>

                        <button
                          onClick={() => { handleBlockUser(); setShowConvMenu(false); }}
                          className={\`w-full text-left px-3 py-2 text-sm transition-colors rounded-xl flex items-center gap-2.5 \${isBlocked ? "text-green-600 hover:bg-green-50" : "text-yellow-600 hover:bg-yellow-50"}\`}
                        >
                          <ShieldAlert className="w-4 h-4" />
                          {isBlocked ? "Mở chặn liên lạc" : "Chặn liên lạc"}
                        </button>

                        <button
                          onClick={() => { handleDeleteConv(selectedConv.other_user_id); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 hover:text-red-700 rounded-xl transition-colors flex items-center gap-2.5"
                        >
                          <Trash2 className="w-4 h-4" />
                          Xóa cuộc trò chuyện
                        </button>
                      </div>`;

content = content.replace(target1, replace1);
content = content.replace(target2, replace2);

fs.writeFileSync(path, content, 'utf8');
console.log("Successfully updated both dropdown menus!");
