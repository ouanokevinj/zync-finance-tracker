<script setup lang="ts">
import { computed, ref, reactive } from 'vue'
import { useFinance } from '../useFinance'
import { fmtCurrency, fmtDate, today } from '../utils'
import * as api from '../api'

const { summary, earnings, subscriptions, spending, isLoading, loadAll, showToast } = useFinance()

/* ── quick action ─────────────────────────────────────────── */
type QuickMode = null | 'earning' | 'subscription' | 'spending'
const quickMode    = ref<QuickMode>(null)
const isSubmitting = ref(false)

const earningForm  = reactive({ amount: '', source: '', date: today() })
const subForm      = reactive({ name: '', amount: '', date_started: today() })
const spendingForm = reactive({ description: '', amount: '', date: today() })

function toggleQuick(mode: 'earning' | 'subscription' | 'spending'): void {
  quickMode.value = quickMode.value === mode ? null : mode
}

async function quickAddEarning(): Promise<void> {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    await api.createEarning({
      amount: parseFloat(earningForm.amount),
      source: earningForm.source,
      date:   earningForm.date,
    })
    Object.assign(earningForm, { amount: '', source: '', date: today() })
    quickMode.value = null
    await loadAll()
    showToast('Earning added')
  } catch {
    showToast('Failed to add earning', true)
  } finally {
    isSubmitting.value = false
  }
}

async function quickAddSub(): Promise<void> {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    await api.createSubscription({
      name:         subForm.name,
      amount:       parseFloat(subForm.amount),
      date_started: subForm.date_started,
    })
    Object.assign(subForm, { name: '', amount: '', date_started: today() })
    quickMode.value = null
    await loadAll()
    showToast('Subscription added')
  } catch {
    showToast('Failed to add subscription', true)
  } finally {
    isSubmitting.value = false
  }
}

async function quickAddSpending(): Promise<void> {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    await api.createSpending({
      description: spendingForm.description,
      amount:      parseFloat(spendingForm.amount),
      date:        spendingForm.date,
    })
    Object.assign(spendingForm, { description: '', amount: '', date: today() })
    quickMode.value = null
    await loadAll()
    showToast('Spending added')
  } catch {
    showToast('Failed to add spending', true)
  } finally {
    isSubmitting.value = false
  }
}

/* ── log ─────────────────────────────────────────────────── */
type FilterType = 'all' | 'earning' | 'subscription' | 'spending'
const activeFilter = ref<FilterType>('all')

interface LogEntry {
  id: string
  type: 'earning' | 'subscription' | 'spending'
  label: string
  amount: number
  date: string
  created_at: string
}

const log = computed<LogEntry[]>(() => {
  const e = earnings.value.map(e => ({
    id: e.id, type: 'earning' as const,
    label: e.source, amount: e.amount,
    date: e.date, created_at: e.created_at,
  }))
  const s = subscriptions.value.map(s => ({
    id: s.id, type: 'subscription' as const,
    label: s.name, amount: s.amount,
    date: s.date_started, created_at: s.created_at,
  }))
  const sp = spending.value.map(sp => ({
    id: sp.id, type: 'spending' as const,
    label: sp.description, amount: sp.amount,
    date: sp.date, created_at: sp.created_at,
  }))
  /* Latest first — created_at breaks ties on same-day entries */
  const all = [...e, ...s, ...sp].sort((a, b) => {
    const d = new Date(b.date).getTime() - new Date(a.date).getTime()
    return d !== 0 ? d : new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
  return activeFilter.value === 'all' ? all : all.filter(e => e.type === activeFilter.value)
})

const groupedLog = computed(() => {
  const groups: { date: string; entries: typeof log.value }[] = []
  for (const entry of log.value) {
    const last = groups[groups.length - 1]
    if (last && last.date === entry.date) {
      last.entries.push(entry)
    } else {
      groups.push({ date: entry.date, entries: [entry] })
    }
  }
  return groups
})
</script>

<template>
  <section>

    <!-- ── Skeleton (initial load only) ─────────────────── -->
    <template v-if="isLoading">
      <div class="mb-8">
        <div class="h-3 w-16 bg-light rounded animate-pulse mb-3"></div>
        <div class="h-14 w-56 bg-light rounded-xl animate-pulse"></div>
      </div>
      <div class="grid grid-cols-2 gap-3 mb-8">
        <div class="bg-light rounded-xl h-24 animate-pulse"></div>
        <div class="bg-light rounded-xl h-24 animate-pulse"></div>
      </div>
      <div class="space-y-3">
        <div class="h-3 w-24 bg-light rounded animate-pulse mb-3"></div>
        <div class="bg-light rounded-xl h-20 animate-pulse"></div>
        <div class="bg-light rounded-xl h-20 animate-pulse"></div>
        <div class="bg-light rounded-xl h-20 animate-pulse"></div>
      </div>
    </template>

    <!-- ── Content ───────────────────────────────────────── -->
    <template v-else>
      <div class="lg:grid lg:grid-cols-[1fr_420px] lg:gap-12 lg:items-start">

      <!-- Left column: balance, stats, quick add -->
      <div class="min-w-0">

      <!-- Balance hero -->
      <div class="mb-8">
        <p class="text-xs font-medium text-dark/40 uppercase tracking-widest mb-2">Balance</p>
        <p :class="['font-mono font-bold tracking-tight leading-none text-5xl md:text-6xl',
          summary.net < 0 ? 'text-brand' : 'text-dark']">
          {{ fmtCurrency(summary.net) }}
        </p>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-3 gap-3 mb-8">
        <div class="bg-white border border-light rounded-xl p-3 md:p-4 shadow-sm min-h-20 md:min-h-24 flex flex-col justify-between">
          <p class="text-[10px] md:text-xs font-medium text-dark/40 uppercase tracking-widest">Earned</p>
          <p class="font-mono text-sm md:text-base font-bold truncate">{{ fmtCurrency(summary.total_earnings) }}</p>
        </div>
        <div class="bg-white border border-light rounded-xl p-3 md:p-4 shadow-sm min-h-20 md:min-h-24 flex flex-col justify-between">
          <p class="text-[10px] md:text-xs font-medium text-dark/40 uppercase tracking-widest">Subscriptions</p>
          <p class="font-mono text-sm md:text-base font-bold truncate">{{ fmtCurrency(summary.total_subscriptions) }}</p>
        </div>
        <div class="bg-white border border-light rounded-xl p-3 md:p-4 shadow-sm min-h-20 md:min-h-24 flex flex-col justify-between">
          <p class="text-[10px] md:text-xs font-medium text-dark/40 uppercase tracking-widest">Spending</p>
          <p class="font-mono text-sm md:text-base font-bold text-amber-600 truncate">{{ fmtCurrency(summary.total_spending) }}</p>
        </div>
      </div>

      <!-- Quick add -->
      <div class="mb-8">
        <p class="text-xs font-medium text-dark/40 uppercase tracking-widest mb-3">Quick Add</p>

        <div class="flex gap-2 mb-3">
          <button
            @click="toggleQuick('earning')"
            :class="['flex-1 py-2.5 rounded-lg text-sm font-medium border transition-colors',
              quickMode === 'earning'
                ? 'bg-emerald-600 text-white border-emerald-600'
                : 'border-light text-dark/50 hover:text-dark hover:border-dark/20']"
          >
            + Earning
          </button>
          <button
            @click="toggleQuick('subscription')"
            :class="['flex-1 py-2.5 rounded-lg text-sm font-medium border transition-colors',
              quickMode === 'subscription'
                ? 'bg-brand text-white border-brand'
                : 'border-light text-dark/50 hover:text-dark hover:border-dark/20']"
          >
            + Subscription
          </button>
          <button
            @click="toggleQuick('spending')"
            :class="['flex-1 py-2.5 rounded-lg text-sm font-medium border transition-colors',
              quickMode === 'spending'
                ? 'bg-amber-500 text-white border-amber-500'
                : 'border-light text-dark/50 hover:text-dark hover:border-dark/20']"
          >
            + Spending
          </button>
        </div>

        <!-- Earning quick form -->
        <Transition
          enter-active-class="transition-all duration-200 overflow-hidden"
          leave-active-class="transition-all duration-150 overflow-hidden"
          enter-from-class="opacity-0 max-h-0"
          enter-to-class="opacity-100 max-h-64"
          leave-from-class="opacity-100 max-h-64"
          leave-to-class="opacity-0 max-h-0"
        >
          <form v-if="quickMode === 'earning'" @submit.prevent="quickAddEarning"
            class="flex flex-col gap-2 p-4 rounded-xl bg-emerald-50 border border-emerald-100">
            <div class="flex gap-2">
              <div class="flex-1">
                <label for="qa-e-amount" class="sr-only">Amount</label>
                <input id="qa-e-amount" v-model="earningForm.amount" type="number" step="0.01" min="0"
                  placeholder="Amount" required
                  class="w-full px-3 py-2 rounded-lg border border-emerald-200 bg-white text-sm font-mono focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
              <div class="flex-[2]">
                <label for="qa-e-source" class="sr-only">Source</label>
                <input id="qa-e-source" v-model="earningForm.source" type="text"
                  placeholder="Source" required
                  class="w-full px-3 py-2 rounded-lg border border-emerald-200 bg-white text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
            </div>
            <div class="flex gap-2">
              <div class="flex-1">
                <label for="qa-e-date" class="sr-only">Date</label>
                <input id="qa-e-date" v-model="earningForm.date" type="date" required
                  class="w-full px-3 py-2 rounded-lg border border-emerald-200 bg-white text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
              <button type="submit" :disabled="isSubmitting"
                class="px-5 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-60">
                {{ isSubmitting ? 'Adding…' : 'Add' }}
              </button>
            </div>
          </form>
        </Transition>

        <!-- Subscription quick form -->
        <Transition
          enter-active-class="transition-all duration-200 overflow-hidden"
          leave-active-class="transition-all duration-150 overflow-hidden"
          enter-from-class="opacity-0 max-h-0"
          enter-to-class="opacity-100 max-h-64"
          leave-from-class="opacity-100 max-h-64"
          leave-to-class="opacity-0 max-h-0"
        >
          <form v-if="quickMode === 'subscription'" @submit.prevent="quickAddSub"
            class="flex flex-col gap-2 p-4 rounded-xl bg-rose-50 border border-rose-100">
            <div class="flex gap-2">
              <div class="flex-[2]">
                <label for="qa-s-name" class="sr-only">Name</label>
                <input id="qa-s-name" v-model="subForm.name" type="text"
                  placeholder="Name" required
                  class="w-full px-3 py-2 rounded-lg border border-rose-200 bg-white text-sm focus:ring-2 focus:ring-brand focus:outline-none"
                />
              </div>
              <div class="flex-1">
                <label for="qa-s-amount" class="sr-only">Amount</label>
                <input id="qa-s-amount" v-model="subForm.amount" type="number" step="0.01" min="0"
                  placeholder="Amount" required
                  class="w-full px-3 py-2 rounded-lg border border-rose-200 bg-white text-sm font-mono focus:ring-2 focus:ring-brand focus:outline-none"
                />
              </div>
            </div>
            <div class="flex gap-2">
              <div class="flex-1">
                <label for="qa-s-date" class="sr-only">Start date</label>
                <input id="qa-s-date" v-model="subForm.date_started" type="date" required
                  class="w-full px-3 py-2 rounded-lg border border-rose-200 bg-white text-sm focus:ring-2 focus:ring-brand focus:outline-none"
                />
              </div>
              <button type="submit" :disabled="isSubmitting"
                class="px-5 py-2 bg-brand text-white text-sm font-medium rounded-lg hover:bg-brand/90 transition-colors disabled:opacity-60">
                {{ isSubmitting ? 'Adding…' : 'Add' }}
              </button>
            </div>
          </form>
        </Transition>

        <!-- Spending quick form -->
        <Transition
          enter-active-class="transition-all duration-200 overflow-hidden"
          leave-active-class="transition-all duration-150 overflow-hidden"
          enter-from-class="opacity-0 max-h-0"
          enter-to-class="opacity-100 max-h-64"
          leave-from-class="opacity-100 max-h-64"
          leave-to-class="opacity-0 max-h-0"
        >
          <form v-if="quickMode === 'spending'" @submit.prevent="quickAddSpending"
            class="flex flex-col gap-2 p-4 rounded-xl bg-amber-50 border border-amber-100">
            <div class="flex gap-2">
              <div class="flex-[2]">
                <label for="qa-sp-desc" class="sr-only">Description</label>
                <input id="qa-sp-desc" v-model="spendingForm.description" type="text"
                  placeholder="Description" required
                  class="w-full px-3 py-2 rounded-lg border border-amber-200 bg-white text-sm focus:ring-2 focus:ring-amber-500 focus:outline-none"
                />
              </div>
              <div class="flex-1">
                <label for="qa-sp-amount" class="sr-only">Amount</label>
                <input id="qa-sp-amount" v-model="spendingForm.amount" type="number" step="0.01" min="0"
                  placeholder="Amount" required
                  class="w-full px-3 py-2 rounded-lg border border-amber-200 bg-white text-sm font-mono focus:ring-2 focus:ring-amber-500 focus:outline-none"
                />
              </div>
            </div>
            <div class="flex gap-2">
              <div class="flex-1">
                <label for="qa-sp-date" class="sr-only">Date</label>
                <input id="qa-sp-date" v-model="spendingForm.date" type="date" required
                  class="w-full px-3 py-2 rounded-lg border border-amber-200 bg-white text-sm focus:ring-2 focus:ring-amber-500 focus:outline-none"
                />
              </div>
              <button type="submit" :disabled="isSubmitting"
                class="px-5 py-2 bg-amber-500 text-white text-sm font-medium rounded-lg hover:bg-amber-600 transition-colors disabled:opacity-60">
                {{ isSubmitting ? 'Adding…' : 'Add' }}
              </button>
            </div>
          </form>
        </Transition>
      </div>

      </div><!-- end left column -->

      <!-- Right column: activity log -->
      <div class="mt-8 lg:mt-0 min-w-0">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs font-medium text-dark/40 uppercase tracking-widest">Activity</p>
          <span v-if="log.length > 0" class="text-xs text-dark/30 font-mono">{{ log.length }} entries</span>
        </div>

        <!-- Filter pills -->
        <div class="flex gap-1.5 mb-3 flex-wrap">
          <button v-for="f in [
            { key: 'all',          label: 'All' },
            { key: 'earning',      label: 'Earnings' },
            { key: 'subscription', label: 'Subscriptions' },
            { key: 'spending',     label: 'Spending' },
          ]" :key="f.key"
            @click="activeFilter = f.key as FilterType"
            :class="[
              'px-3 py-1 rounded-full text-xs font-medium transition-colors',
              activeFilter === f.key
                ? f.key === 'all'          ? 'bg-dark text-white'
                : f.key === 'earning'      ? 'bg-emerald-600 text-white'
                : f.key === 'subscription' ? 'bg-brand text-white'
                :                            'bg-amber-500 text-white'
                : 'bg-light text-dark/50 hover:text-dark',
            ]"
          >{{ f.label }}</button>
        </div>

        <!-- Empty -->
        <div v-if="log.length === 0" class="text-center py-14">
          <svg class="w-10 h-10 text-dark/10 mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
          <p class="text-dark/30 text-sm">No activity yet.</p>
          <p class="text-dark/20 text-xs mt-1">Add an earning or subscription to get started.</p>
        </div>

        <div v-else class="flex flex-col gap-4 max-h-80 lg:max-h-[calc(100vh-12rem)] overflow-y-auto pr-1">
          <div v-for="group in groupedLog" :key="group.date">
            <p class="text-xs font-semibold text-dark/30 uppercase tracking-widest mb-2">{{ fmtDate(group.date) }}</p>
            <div class="flex flex-col gap-2">
              <div
                v-for="entry in group.entries"
                :key="entry.id + entry.type"
                :class="[
                  'rounded-xl p-4 flex items-center justify-between gap-4',
                  entry.type === 'earning'
                    ? 'bg-gradient-to-br from-emerald-50 to-green-100'
                    : entry.type === 'subscription'
                      ? 'bg-gradient-to-br from-rose-50 to-red-100'
                      : 'bg-gradient-to-br from-amber-50 to-yellow-100',
                ]"
              >
                <div class="min-w-0">
                  <p :class="['text-xs font-medium uppercase tracking-widest mb-0.5',
                    entry.type === 'earning' ? 'text-emerald-600/60'
                    : entry.type === 'subscription' ? 'text-rose-500/60'
                    : 'text-amber-600/60']">
                    {{ entry.type === 'earning' ? 'Earning' : entry.type === 'subscription' ? 'Subscription' : 'Spending' }}
                  </p>
                  <p class="font-medium text-dark text-sm truncate">{{ entry.label }}</p>
                </div>
                <p :class="[
                  'font-mono font-bold text-lg shrink-0',
                  entry.type === 'earning' ? 'text-emerald-600'
                  : entry.type === 'subscription' ? 'text-rose-500'
                  : 'text-amber-600',
                ]">
                  {{ entry.type === 'earning' ? '+' : '−' }}{{ fmtCurrency(entry.amount) }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div><!-- end right column -->

      </div><!-- end lg:grid -->

    </template>
  </section>
</template>
