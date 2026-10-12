import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { Placeholder } from '@tiptap/extensions'
import { useEffect } from 'react'
import EditorToolbar from './EditorToolbar.jsx'

// Rich-text editor built on TipTap (ProseMirror). StarterKit v3 provides bold,
// italic, underline, strike, headings, bullet/ordered lists, blockquote and
// code. The parent owns persistence; this component just emits HTML on change.
export default function Editor({ content, editable, onChange }) {
  const editor = useEditor({
    editable,
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
        link: { openOnClick: false },
      }),
      Placeholder.configure({
        placeholder: 'Start writing, or import a file…',
      }),
    ],
    content: content || '',
    onUpdate: ({ editor }) => {
      onChange?.(editor.getHTML())
    },
  })

  // Reflect editable changes (e.g. viewer vs editor role).
  useEffect(() => {
    if (editor) editor.setEditable(editable)
  }, [editor, editable])

  return (
    <div>
      <EditorToolbar editor={editor} disabled={!editable} />
      <div className="editor-shell">
        <EditorContent editor={editor} />
      </div>
    </div>
  )
}
