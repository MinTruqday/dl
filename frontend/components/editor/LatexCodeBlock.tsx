import { NodeViewWrapper, NodeViewProps } from '@tiptap/react';
import React, { useRef, useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

const MonacoEditor = dynamic(
  () => import('@monaco-editor/react'),
  { ssr: false, loading: () => <div className="h-40 bg-gray-100 animate-pulse flex items-center justify-center">Đang tải môi trường soạn thảo</div> }
);

export const LatexCodeBlock = (props: NodeViewProps) => {
  const [isClient, setIsClient] = useState(false);
  
  useEffect(() => {
    setIsClient(true);
  }, []);

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      props.updateAttributes({ text: value });
    }
  };

  return (
    <NodeViewWrapper className="latex-code-block relative border border-black  overflow-hidden my-4 bg-card ">
        <div className="bg-black text-white text-xs px-3 py-1 font-semibold flex justify-between items-center">
            <span>Soạn thảo công thức Toán học</span>
        </div>
        
        {isClient && (
             <div className="h-64 sm:h-96">
              <MonacoEditor
                  height="100%"
                  defaultLanguage="latex"
                  theme="vs-dark"
                  value={props.node.attrs.text || ''}
                  onChange={handleEditorChange}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: 'on',
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    quickSuggestions: true,
                    suggestOnTriggerCharacters: true
                  }}
              />
             </div>
        )}
    </NodeViewWrapper>
  );
};
