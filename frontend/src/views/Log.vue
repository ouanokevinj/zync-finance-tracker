<script setup lang="ts">
import { computed } from 'vue'
import { useFinance } from '../useFinance'
import { fmtCurrency, fmtDate } from '../utils'

const { earnings, subscriptions } = useFinance()

interface LogEntry {
  id: string
  type: 'earning' | 'subscription'
  label: string
  amount: number
  date: string
}

/* Merge earnings and subscriptions into one sorted list */
const log = computed<LogEntry[]>(() => {
  const e = earnings.value.map(e => ({
    id:     e.id,
    type:   'earning' as const,
    label:  e.source,
    amount: e.amount,
    date:   e.date,
  }))
  const s = subscriptions.value.map(s => ({
    id:     s.id,
    type:   'subscription' as const,
    label:  s.name,
    amount: s.amount,
    date:   s.date_started,
  }))
  return [...e, ...s].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
})
</script>

<template>
  <section>
    <h1 class="text-3xl font-bold tracking-tight mb-6">Log</h1>

    <p v-if="log.length === 0" class="text-center py-16 text-dark/30 text-sm">
      No activity yet.
    </p>

    <div v-else class="flex flex-col gap-3">
      <div
        v-for="entry in log"
        :key="entry.id + entry.type"
        :class="[
          'rounded-xl p-4 flex items-center justify-between gap-4',
          entry.type === 'earning'
            ? 'bg-gradient-to-br from-emerald-50 to-green-100'
            : 'bg-gradient-to-br from-rose-50 to-red-100',
        ]"
      >
        <div class="min-w-0">
          <p :class="['text-xs font-medium uppercase tracking-widest mb-0.5',
            entry.type === 'earning' ? 'text-emerald-600/60' : 'text-rose-500/60']">
            {{ entry.type === 'earning' ? 'Earning' : 'Subscription' }}
          </p>
          <p class="font-medium text-dark text-sm truncate">{{ entry.label }}</p>
          <p class="text-xs text-dark/40 mt-0.5">{{ fmtDate(entry.date) }}</p>
        </div>
        <p :class="[
          'font-mono font-bold text-lg shrink-0',
          entry.type === 'earning' ? 'text-emerald-600' : 'text-rose-500',
        ]">
          {{ entry.type === 'earning' ? '+' : '-' }}{{ fmtCurrency(entry.amount) }}
        </p>
      </div>
    </div>
  </section>
</template>
