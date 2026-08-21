/**
 * Lightweight markdown subset renderer, zero dependencies.
 *
 * Supported: headings (#/##/###), fenced code blocks, lists (- / *),
 * blockquotes, paragraphs, inline code, **bold**, [links](https://...).
 * Everything else is escaped before output, so the result is safe to v-html.
 */

export function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function renderInline(text) {
  const escaped = escapeHtml(text)
  return escaped
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(
      /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
    )
}

export function renderMarkdown(text) {
  if (!text) return ''

  const lines = String(text).split(/\r?\n/)
  const html = []
  let inList = false
  let listBuffer = []
  let inCode = false
  let codeBuffer = []

  const closeList = () => {
    if (inList) {
      html.push(`<ul>${listBuffer.join('')}</ul>`)
      listBuffer = []
      inList = false
    }
  }

  for (const raw of lines) {
    const line = raw.trimEnd()

    if (line.trimStart().startsWith('```')) {
      if (inCode) {
        html.push(`<pre><code>${escapeHtml(codeBuffer.join('\n'))}</code></pre>`)
        codeBuffer = []
        inCode = false
      } else {
        closeList()
        inCode = true
      }
      continue
    }

    if (inCode) {
      codeBuffer.push(line)
      continue
    }

    const trimmed = line.trim()
    if (!trimmed) {
      closeList()
      continue
    }

    const heading = trimmed.match(/^(#{1,3})\s+(.*)$/)
    if (heading) {
      closeList()
      const level = heading[1].length
      html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`)
      continue
    }

    if (trimmed.startsWith('> ')) {
      closeList()
      html.push(`<blockquote>${renderInline(trimmed.slice(2))}</blockquote>`)
      continue
    }

    const listItem = trimmed.match(/^[-*]\s+(.*)$/)
    if (listItem) {
      if (!inList) {
        inList = true
        listBuffer = []
      }
      listBuffer.push(`<li>${renderInline(listItem[1])}</li>`)
      continue
    }

    closeList()
    html.push(`<p>${renderInline(trimmed)}</p>`)
  }

  if (inCode) {
    html.push(`<pre><code>${escapeHtml(codeBuffer.join('\n'))}</code></pre>`)
  }
  closeList()

  return html.join('\n')
}
