import { NodeViewWrapper, NodeViewProps } from '@tiptap/react'
import { useState, useCallback } from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'

export default function NodeView(props: NodeViewProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const content = props.node.attrs.content

  const updateContent = useCallback((newContent: string) => {
    props.updateAttributes({ content: newContent })
  }, [props])

  const validateAndRender = useCallback((latex: string) => {
    setError(null)
    try {
      // Just testing Katex
      katex.renderToString(latex, { throwOnError: true, displayMode: true })
    } catch (err: any) {
      setError(err.message || 'Công thức toán học không hợp lệ')
    }
  }, [])

  return (
    <NodeViewWrapper className="latex-block-wrapper my-4">
      <div className={`border border-gray-200 bg-gray-50 rounded-md p-4 transition-colors ${props.selected ? 'border-black' : ''}`}>
        {isEditing ? (
          <div className="flex flex-col gap-2">
            <textarea
              className="w-full border border-gray-200 rounded-md p-2 bg-white focus:outline-none focus:border-black font-mono text-sm min-h-[100px]"
              defaultValue={content}
              onChange={(e) => {
                updateContent(e.target.value)
                validateAndRender(e.target.value)
              }}
              placeholder="Nhập mã LaTeX..."
            />
            {error && (
               <div className="text-red-600 text-sm">{error}</div>
            )}
            <div className="flex justify-end">
              <button
                className="px-4 py-2 bg-black text-white rounded-md text-sm hover:bg-gray-800 transition-colors"
                onClick={() => setIsEditing(false)}
              >
                Hoàn tất
              </button>
            </div>
          </div>
        ) : (
          <div 
            className="cursor-pointer min-h-[50px] flex items-center justify-center p-4 bg-white border border-gray-200 rounded-md"
            onClick={() => setIsEditing(true)}
          >
            {content ? (
              <div dangerouslySetInnerHTML={{ 
                  __html: (() => {
                      try {
                          return katex.renderToString(content, { displayMode: true, throwOnError: false })
                      } catch (e) {
                          return `<span class="text-red-600">Lỗi render LaTeX</span>`
                      }
                  })()
               }} />
            ) : (
              <span className="text-gray-400 text-sm">Nhấp để thêm công thức toán học</span>
            )}
          </div>
        )}
      </div>
    </NodeViewWrapper>
  )
}
