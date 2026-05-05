/**
 * Theme presets aligned with pptx-generator / minimax skill (theme.primary … theme.bg).
 * Hex includes # for CSS.
 */

export const DESIGN_PALETTES = [
  {
    id: 'luxury-muted',
    name: '典雅灰紫',
    primary: '#22223b',
    secondary: '#4a4e69',
    accent: '#9a8c98',
    light: '#c9ada7',
    bg: '#f2e9e4',
  },
  {
    id: 'pure-tech-blue',
    name: '科技深蓝',
    primary: '#03045e',
    secondary: '#0077b6',
    accent: '#00b4d8',
    light: '#90e0ef',
    bg: '#caf0f8',
  },
  {
    id: 'business-authority',
    name: '商务权威',
    primary: '#2b2d42',
    secondary: '#8d99ae',
    accent: '#ef233c',
    light: '#edf2f4',
    bg: '#edf2f4',
  },
  {
    id: 'education-charts',
    name: '图表教育',
    primary: '#264653',
    secondary: '#2a9d8f',
    accent: '#e76f51',
    light: '#e9c46a',
    bg: '#fdf8f3',
  },
  {
    id: 'vibrant-tech',
    name: '活力科技',
    primary: '#023047',
    secondary: '#219ebc',
    accent: '#fb8500',
    light: '#ffb703',
    bg: '#f8fafc',
  },
  {
    id: 'forest-eco',
    name: '森林生态',
    primary: '#344e41',
    secondary: '#588157',
    accent: '#a3b18a',
    light: '#dad7cd',
    bg: '#f4f6f4',
  },
  {
    id: 'coastal-coral',
    name: '海岸珊瑚',
    primary: '#0081a7',
    secondary: '#00afb9',
    accent: '#f07167',
    light: '#fed9b7',
    bg: '#fdfcdc',
  },
  {
    id: 'platinum-gold',
    name: '白金商务',
    primary: '#0a0a0a',
    secondary: '#525252',
    accent: '#0070f3',
    light: '#d4af37',
    bg: '#ffffff',
  },
]

export function getPalette(id) {
  return DESIGN_PALETTES.find((p) => p.id === id) || DESIGN_PALETTES[0]
}
