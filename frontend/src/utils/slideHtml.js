/** Helpers for manual slide HTML editing (client-side). */

export function injectBeforeClosingBody(html, snippet) {
  const lower = html.toLowerCase()
  const idx = lower.lastIndexOf('</body>')
  if (idx === -1) return html + snippet
  return html.slice(0, idx) + snippet + html.slice(idx)
}

export function setBodyBackground(html, color) {
  try {
    const parser = new DOMParser()
    const doc = parser.parseFromString(html, 'text/html')
    doc.body.style.backgroundColor = color
    const inner = doc.documentElement.outerHTML
    const hasDoctype = /<!doctype/i.test(html)
    return (hasDoctype ? '<!DOCTYPE html>\n' : '') + inner
  } catch {
    return injectBeforeClosingBody(
      html,
      `<style>body{background-color:${color}!important}</style>`,
    )
  }
}

function serializeHtmlDocument(doc, originalHtml) {
  const inner = doc.documentElement.outerHTML
  const hasDoctype = /<!doctype/i.test(originalHtml || '')
  return (hasDoctype ? '<!DOCTYPE html>\n' : '') + inner
}

/** Inject minimax-style theme tokens (primary … bg) as CSS variables on :root + base body styles. */
export function injectThemeTokens(html, palette) {
  try {
    const parser = new DOMParser()
    const doc = parser.parseFromString(html, 'text/html')
    doc.getElementById('_ppt_theme_tokens')?.remove()
    const style = doc.createElement('style')
    style.id = '_ppt_theme_tokens'
    style.textContent = `
:root {
  --ppt-primary:${palette.primary};
  --ppt-secondary:${palette.secondary};
  --ppt-accent:${palette.accent};
  --ppt-light:${palette.light};
  --ppt-bg:${palette.bg};
}
body {
  background-color: var(--ppt-bg) !important;
  color: var(--ppt-primary);
  font-family: "Microsoft YaHei","PingFang SC",Arial,sans-serif;
}
`.trim()
    doc.head.appendChild(style)
    return serializeHtmlDocument(doc, html)
  } catch {
    return html
  }
}

/** Replace entire body inner HTML (for slide-type skeletons). */
export function replaceBodyInnerHtml(html, innerHtml) {
  try {
    const parser = new DOMParser()
    const doc = parser.parseFromString(html, 'text/html')
    doc.body.innerHTML = innerHtml
    return serializeHtmlDocument(doc, html)
  } catch {
    return injectBeforeClosingBody(html, innerHtml)
  }
}

/** Bottom-right circular page badge (see pptx-generator skill). Removes previous badge if any. */
export function injectPageBadge(html, pageNum, palette) {
  try {
    const parser = new DOMParser()
    const doc = parser.parseFromString(html, 'text/html')
    const accent = palette?.accent || '#0078d4'
    doc.getElementById('_ppt_page_badge')?.remove()
    let bs = doc.body.getAttribute('style') || ''
    if (!/position\s*:\s*relative/i.test(bs)) {
      bs = bs.trim()
      bs = bs ? `${bs.replace(/;\s*$/, '')}; position:relative;` : 'position:relative;'
      doc.body.setAttribute('style', bs)
    }
    const badge = doc.createElement('div')
    badge.id = '_ppt_page_badge'
    badge.textContent = String(pageNum)
    badge.setAttribute(
      'style',
      [
        'position:absolute',
        'right:36px',
        'bottom:32px',
        'width:56px',
        'height:56px',
        'border-radius:50%',
        `background:${accent}`,
        'display:flex',
        'align-items:center',
        'justify-content:center',
        'font-family:"Microsoft YaHei",Arial,sans-serif',
        'font-size:22px',
        'font-weight:700',
        'color:#fff',
        'box-shadow:0 2px 10px rgba(0,0,0,.18)',
        'z-index:999',
        'pointer-events:none',
      ].join(';'),
    )
    doc.body.appendChild(badge)
    return serializeHtmlDocument(doc, html)
  } catch {
    return html
  }
}

export const SNIPPETS = {
  divider:
    '<div style="margin:28px 0;height:3px;background:linear-gradient(90deg,#0078d4,transparent);border-radius:2px;"></div>',
  textCard:
    '<section style="margin:18px;padding:22px 26px;background:rgba(0,120,212,0.08);border-radius:12px;border-left:4px solid #0078d4;"><h3 style="margin:0 0 10px;font-size:30px;color:#323130;">标题</h3><p style="margin:0;font-size:21px;line-height:1.55;color:#323130;">正文：可直接在「可视化」模式双击编辑，或切换到「HTML代码」精细修改。</p></section>',
  shapeSvg:
    '<svg width="140" height="140" viewBox="0 0 140 140" aria-hidden="true" style="display:block;margin:20px auto;"><circle cx="70" cy="70" r="56" fill="#0078d4" opacity="0.88"/><rect x="42" y="42" width="56" height="56" rx="8" fill="#ffffff" opacity="0.35"/></svg>',
  chartSvg:
    '<svg width="520" height="260" viewBox="0 0 520 260" role="img" aria-label="示例柱状图" style="display:block;margin:18px auto;"><rect x="36" y="36" width="448" height="176" fill="#faf9f8" stroke="#edebe9"/><text x="260" y="26" text-anchor="middle" font-size="17" fill="#323130" font-family="Microsoft YaHei,PingFang SC,sans-serif">示例柱状图（可改数据）</text><rect x="72" y="148" width="56" height="64" fill="#0078d4"/><rect x="156" y="112" width="56" height="100" fill="#50e6ff"/><rect x="240" y="128" width="56" height="84" fill="#8764b8"/><rect x="324" y="92" width="56" height="120" fill="#107c10"/><text x="260" y="236" text-anchor="middle" font-size="14" fill="#605e5c" font-family="Microsoft YaHei,PingFang SC,sans-serif">内联 SVG，导出前仍可编辑</text></svg>',
  imagePlaceholder:
    '<div style="margin:18px auto;width:74%;max-width:760px;height:300px;background:linear-gradient(135deg,#edebe9,#f3f2f1);border:2px dashed #c8c6c4;display:flex;align-items:center;justify-content:center;color:#605e5c;font-size:23px;border-radius:10px;font-family:Microsoft YaHei,PingFang SC,sans-serif;">图片占位 · 可改为 SVG / base64 / data URL</div>',
}
