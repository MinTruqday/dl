import re

def update_page():
    path = "frontend/app/(main)/tin-nhan/page.tsx"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Imports
    if "Share2" not in content:
        content = content.replace("FileText,\n} from \"lucide-react\";", "FileText,\n  Share2,\n  BarChart2,\n} from \"lucide-react\";")

    if "forwardMessageAPI" not in content:
        content = content.replace("import {\n  getConversationsAPI,", "import {\n  getConversationsAPI,\n  forwardMessageAPI,\n  createPollAPI,\n  votePollAPI,")

    # 2. Handlers
    handlers = """
  const handleForward = async (messageId: string, receiverIds: string[]) => {
    await forwardMessageAPI(messageId, receiverIds);
  };

  const handleCreatePoll = async (question: string, options: string[]) => {
    if (!selectedConv) return;
    const receiverId = selectedConv.type === "group" ? selectedConv._id : selectedConv.participants.find((p: any) => p._id !== user?._id)?._id;
    await createPollAPI(receiverId, question, options);
  };

  const handleVote = async (messageId: string, optionId: string) => {
    await votePollAPI(messageId, optionId);
    // UI update will happen via websocket or just fetch again
  };
"""
    if "handleForward = async" not in content:
        content = content.replace("const handleAddReaction = async", handlers + "\n  const handleAddReaction = async")

    # 3. Context Menu - Add Forward
    forward_btn = """
                {!isRecalled && (
                  <button
                    onClick={() => { setShowForwardModal(msgId); dismiss(); }}
                    className="flex items-center gap-3 w-full px-4 py-3 text-[15px] text-[#1D1D1F] hover:bg-[#F5F5F7] border-b border-[#F2F2F7] text-left transition-colors"
                  >
                    <Share2 className="w-[18px] h-[18px] text-[#6E6E73]" />
                    Chuyển tiếp
                  </button>
                )}
"""
    if "setShowForwardModal(msgId)" not in content:
        content = content.replace("Trả lời\n                  </button>\n                )}", "Trả lời\n                  </button>\n                )}\n" + forward_btn)

    # 4. Input Area - ReplyBlock & Poll Button
    reply_block = """
                <ReplyBlock replyingTo={replyingTo} onCancel={() => setReplyingTo(null)} />
"""
    if "ReplyBlock" not in content:
        content = content.replace("<div className=\"px-4 pb-4 pt-2 bg-transparent relative\">", "<div className=\"px-4 pb-4 pt-2 bg-transparent relative\">\n" + reply_block)

    poll_btn = """
                        <button
                          onClick={() => setShowPollModal(true)}
                          className="absolute left-[36px] top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full z-10"
                        >
                          <BarChart2 className="w-[18px] h-[18px]" />
                        </button>
"""
    if "setShowPollModal(true)" not in content:
        content = content.replace("className=\"absolute left-1.5 top-1/2 -translate-y-1/2 w-8 h-8", "className=\"absolute left-1.5 top-1/2 -translate-y-1/2 w-8 h-8")
        # Let's just insert it after the Paperclip button
        content = content.replace("</button>\n                        <input", "</button>\n" + poll_btn + "                        <input")
        # Adjust input padding
        content = content.replace("pl-[40px] pr-[40px]", "pl-[70px] pr-[40px]")

    # 5. Modals at the end
    modals = """
      {showForwardModal && (
        <ForwardModal 
          messageId={showForwardModal}
          conversations={conversations}
          user={user}
          onClose={() => setShowForwardModal(null)}
          onForward={handleForward}
        />
      )}
      {showPollModal && (
        <CreatePollModal 
          onClose={() => setShowPollModal(false)}
          onSubmit={handleCreatePoll}
        />
      )}
"""
    if "ForwardModal" not in content:
        content = content.replace("    </div>\n  );\n}\n", modals + "    </div>\n  );\n}\n")

    # 6. PollMessage inside chat bubble
    poll_msg = """
                              {msg.poll_data && (
                                <PollMessage 
                                  messageId={msg._id || msg.id}
                                  pollData={msg.poll_data}
                                  currentUserId={user?._id}
                                  onVote={handleVote}
                                />
                              )}
"""
    if "msg.poll_data" not in content:
        content = content.replace("{!msg.is_recalled && msg.content && msg.content !== \"Tin nhắn thoại\" && (\n                                <p", poll_msg + "\n                              {!msg.is_recalled && !msg.poll_data && msg.content && msg.content !== \"Tin nhắn thoại\" && (\n                                <p")


    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

update_page()
