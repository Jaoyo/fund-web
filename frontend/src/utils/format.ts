import dayjs from 'dayjs'

export function formatMoney(n: number | null | undefined, digits = 2): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '-'
  return n.toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

export function formatPercent(n: number | null | undefined, digits = 2): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '-'
  return (n * 100).toFixed(digits) + '%'
}

export function formatDate(d: string | null | undefined, fmt = 'YYYY-MM-DD'): string {
  if (!d) return '-'
  return dayjs(d).format(fmt)
}

export function profitColor(n: number | null | undefined): string {
  if (n === null || n === undefined || n === 0) return 'inherit'
  return n > 0 ? '#e6321c' : '#0a9d29'
}
