// Formatting toolbar wired to the TipTap editor commands.
// Each button reflects the active mark/node state and toggles it.

function Btn({ onClick, active, title, disabled, children }) {
  return (
    <button
      type="button"
      className={`tool-btn ${active ? 'active' : ''}`}
      onMouseDown={(e) => e.preventDefault()} // keep editor selection
      onClick={onClick}
      title={title}
      disabled={disabled}
      aria-pressed={!!active}
      aria-label={title}
    >
      {children}
    </button>
  )
}

export default function EditorToolbar({ editor, disabled }) {
  if (!editor) return null

  return (
    <div className="toolbar" role="toolbar" aria-label="Formatting">
      <Btn
        title="Bold"
        disabled={disabled}
        active={editor.isActive('bold')}
        onClick={() => editor.chain().focus().toggleBold().run()}
      >
        <strong>B</strong>
      </Btn>
      <Btn
        title="Italic"
        disabled={disabled}
        active={editor.isActive('italic')}
        onClick={() => editor.chain().focus().toggleItalic().run()}
      >
        <em>I</em>
      </Btn>
      <Btn
        title="Underline"
        disabled={disabled}
        active={editor.isActive('underline')}
        onClick={() => editor.chain().focus().toggleUnderline().run()}
      >
        <u>U</u>
      </Btn>
      <Btn
        title="Strikethrough"
        disabled={disabled}
        active={editor.isActive('strike')}
        onClick={() => editor.chain().focus().toggleStrike().run()}
      >
        <s>S</s>
      </Btn>

      <span className="tool-sep" />

      <Btn
        title="Heading 1"
        disabled={disabled}
        active={editor.isActive('heading', { level: 1 })}
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
      >
        H1
      </Btn>
      <Btn
        title="Heading 2"
        disabled={disabled}
        active={editor.isActive('heading', { level: 2 })}
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
      >
        H2
      </Btn>
      <Btn
        title="Heading 3"
        disabled={disabled}
        active={editor.isActive('heading', { level: 3 })}
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
      >
        H3
      </Btn>
      <Btn
        title="Normal text"
        disabled={disabled}
        active={editor.isActive('paragraph')}
        onClick={() => editor.chain().focus().setParagraph().run()}
      >
        ¶
      </Btn>

      <span className="tool-sep" />

      <Btn
        title="Bulleted list"
        disabled={disabled}
        active={editor.isActive('bulletList')}
        onClick={() => editor.chain().focus().toggleBulletList().run()}
      >
        • ≣
      </Btn>
      <Btn
        title="Numbered list"
        disabled={disabled}
        active={editor.isActive('orderedList')}
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
      >
        1.
      </Btn>
      <Btn
        title="Quote"
        disabled={disabled}
        active={editor.isActive('blockquote')}
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
      >
        ❝
      </Btn>
      <Btn
        title="Code block"
        disabled={disabled}
        active={editor.isActive('codeBlock')}
        onClick={() => editor.chain().focus().toggleCodeBlock().run()}
      >
        {'</>'}
      </Btn>

      <span className="tool-sep" />

      <Btn
        title="Undo"
        disabled={disabled || !editor.can().undo()}
        onClick={() => editor.chain().focus().undo().run()}
      >
        ↶
      </Btn>
      <Btn
        title="Redo"
        disabled={disabled || !editor.can().redo()}
        onClick={() => editor.chain().focus().redo().run()}
      >
        ↷
      </Btn>
    </div>
  )
}
