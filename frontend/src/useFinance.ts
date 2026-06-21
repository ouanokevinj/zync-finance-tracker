/*
 * Module-level shared state — persists across component mounts.
 * isLoading is true only on the initial fetch; subsequent reloads are silent.
 */
import { ref, reactive } from 'vue'
import * as api from './api'
import type { Earning, Spending, Subscription, Summary } from './types'

const earnings      = ref<Earning[]>([])
const subscriptions = ref<Subscription[]>([])
const spending      = ref<Spending[]>([])
const summary       = reactive<Summary>({ total_earnings: 0, total_subscriptions: 0, total_spending: 0, net: 0 })
const toast         = reactive({ show: false, msg: '', error: false })
const isLoading     = ref(true)

let toastTimer: ReturnType<typeof setTimeout>

function showToast(msg: string, error = false): void {
  clearTimeout(toastTimer)
  Object.assign(toast, { show: true, msg, error })
  toastTimer = setTimeout(() => (toast.show = false), 3000)
}

async function loadAll(): Promise<void> {
  try {
    const [e, s, sp, sum] = await Promise.all([
      api.getEarnings(),
      api.getSubscriptions(),
      api.getSpending(),
      api.getSummary(),
    ])
    earnings.value      = e
    subscriptions.value = s
    spending.value      = sp
    Object.assign(summary, sum)
  } catch {
    showToast('Failed to load data', true)
  } finally {
    isLoading.value = false
  }
}

export function useFinance() {
  return { earnings, subscriptions, spending, summary, toast, isLoading, loadAll, showToast }
}
