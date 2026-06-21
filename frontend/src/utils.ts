/*
 * Shared formatting helpers.
 * Append T00:00:00 on date strings to avoid UTC-to-local offset shifting
 * the date back by one day in negative-offset timezones.
 */

export function fmtCurrency(n: number): string {
  return '₱' + new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n)
}

export function fmtDate(d: string): string {
  return new Date(d + 'T00:00:00').toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

export function fmtDateShort(d: string): string {
  return new Date(d + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short', day: 'numeric',
  })
}

export function today(): string {
  return new Date().toISOString().split('T')[0]
}
