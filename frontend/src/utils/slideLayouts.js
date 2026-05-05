/**
 * Slide-type skeletons (reference: minimax slide-types.md).
 * Use CSS variables --ppt-* injected via injectThemeTokens().
 */

export const LAYOUT_LABELS = {
  cover: '封面',
  toc: '目录',
  section: '章节分隔',
  content: '正文双栏',
  summary: '结尾回顾',
}

/** Inner HTML only (replaces document body children). */
export const LAYOUT_BODIES = {
  cover: `
<div style="width:100%;height:100%;box-sizing:border-box;position:relative;display:flex;flex-direction:column;justify-content:center;padding:72px 96px;background:var(--ppt-bg);">
  <div style="width:120px;height:6px;background:var(--ppt-accent);border-radius:3px;margin-bottom:28px;"></div>
  <h1 style="margin:0;font-size:88px;font-weight:700;color:var(--ppt-primary);line-height:1.08;letter-spacing:-0.02em;">演示主标题</h1>
  <p style="margin:28px 0 0;font-size:34px;font-weight:400;color:var(--ppt-secondary);max-width:1400px;line-height:1.35;">副标题：一句话说明价值主张</p>
  <p style="margin:56px 0 0;font-size:22px;color:var(--ppt-accent);">演讲者姓名 · 日期 / 场合</p>
</div>`.trim(),

  toc: `
<div style="width:100%;height:100%;box-sizing:border-box;padding:64px 88px;background:var(--ppt-bg);position:relative;display:flex;flex-direction:column;">
  <h2 style="margin:0;font-size:42px;font-weight:700;color:var(--ppt-primary);letter-spacing:0.04em;">目录</h2>
  <div style="margin-top:48px;display:grid;gap:26px;max-width:1200px;">
    <div style="display:flex;align-items:baseline;gap:20px;border-left:4px solid var(--ppt-accent);padding-left:20px;">
      <span style="font-size:30px;font-weight:700;color:var(--ppt-accent);min-width:52px;">01</span>
      <span style="font-size:26px;color:var(--ppt-secondary);">第一节标题</span>
    </div>
    <div style="display:flex;align-items:baseline;gap:20px;border-left:4px solid var(--ppt-light);padding-left:20px;">
      <span style="font-size:30px;font-weight:700;color:var(--ppt-accent);min-width:52px;">02</span>
      <span style="font-size:26px;color:var(--ppt-secondary);">第二节标题</span>
    </div>
    <div style="display:flex;align-items:baseline;gap:20px;border-left:4px solid var(--ppt-light);padding-left:20px;">
      <span style="font-size:30px;font-weight:700;color:var(--ppt-accent);min-width:52px;">03</span>
      <span style="font-size:26px;color:var(--ppt-secondary);">第三节标题</span>
    </div>
    <div style="display:flex;align-items:baseline;gap:20px;border-left:4px solid var(--ppt-light);padding-left:20px;">
      <span style="font-size:30px;font-weight:700;color:var(--ppt-accent);min-width:52px;">04</span>
      <span style="font-size:26px;color:var(--ppt-secondary);">第四节标题</span>
    </div>
  </div>
</div>`.trim(),

  section: `
<div style="width:100%;height:100%;box-sizing:border-box;display:flex;align-items:center;background:var(--ppt-bg);padding:0 80px;position:relative;">
  <div style="display:flex;align-items:center;width:100%;">
    <span style="font-size:132px;font-weight:800;color:var(--ppt-accent);opacity:0.45;line-height:1;margin-right:40px;">03</span>
    <div style="flex:1;">
      <h2 style="margin:0;font-size:52px;font-weight:700;color:var(--ppt-primary);">章节标题</h2>
      <p style="margin:18px 0 0;font-size:24px;color:var(--ppt-secondary);max-width:1100px;line-height:1.5;">可选：本节导读一句话。</p>
    </div>
  </div>
</div>`.trim(),

  content: `
<div style="width:100%;height:100%;box-sizing:border-box;padding:52px 72px;background:var(--ppt-bg);display:grid;grid-template-columns:1.05fr 0.95fr;gap:52px;position:relative;">
  <div>
    <h2 style="margin:0 0 28px;font-size:40px;font-weight:700;color:var(--ppt-primary);">幻灯片标题</h2>
    <ul style="margin:0;padding-left:30px;font-size:23px;line-height:1.65;color:var(--ppt-secondary);">
      <li style="margin-bottom:14px;">要点一：支持可视化或 HTML 代码修改</li>
      <li style="margin-bottom:14px;">要点二：右侧可配图示或 SVG 图表</li>
      <li style="margin-bottom:14px;">要点三：保持与主题色板一致</li>
    </ul>
    <p style="margin:28px 0 0;font-size:18px;color:var(--ppt-accent);">来源 / 注释（可选）</p>
  </div>
  <div style="background:var(--ppt-light);border-radius:14px;display:flex;align-items:center;justify-content:center;color:var(--ppt-secondary);font-size:22px;padding:24px;text-align:center;border:1px solid rgba(0,0,0,0.06);">
    图示 / 图表占位<br/><span style="font-size:17px;opacity:0.85;margin-top:12px;display:block;">可替换为内联 SVG 或装饰形状</span>
  </div>
</div>`.trim(),

  summary: `
<div style="width:100%;height:100%;box-sizing:border-box;padding:64px 80px;background:var(--ppt-bg);display:flex;flex-direction:column;position:relative;">
  <h2 style="margin:0;font-size:48px;font-weight:700;color:var(--ppt-primary);">要点回顾</h2>
  <ul style="margin:36px 0 0;padding-left:32px;font-size:26px;line-height:1.75;color:var(--ppt-secondary);flex:1;">
    <li style="margin-bottom:16px;">核心结论一</li>
    <li style="margin-bottom:16px;">核心结论二</li>
    <li style="margin-bottom:16px;">核心结论三</li>
  </ul>
  <p style="margin:32px 0 0;font-size:32px;font-weight:700;color:var(--ppt-accent);text-align:center;">谢谢观看 · 欢迎交流</p>
</div>`.trim(),
}

export function getLayoutBody(key) {
  return LAYOUT_BODIES[key] || ''
}
