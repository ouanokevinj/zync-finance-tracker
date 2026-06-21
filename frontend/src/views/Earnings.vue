<script setup lang="ts">
import { computed, ref, reactive } from 'vue'
import { useFinance } from '../useFinance'
import { fmtCurrency, fmtDate, today } from '../utils'
import type { Earning } from '../types'
import * as api from '../api'

const { earnings, loadAll, showToast } = useFinance()

/* ── grouped by date ─────────────────────────────────────── */
const grouped = computed(() => {
  const sorted = [...earnings.value].sort((a, b) =>
    new Date(b.date).getTime() - new Date(a.date).getTime()
  )
  const groups: { date: string; items: Earning[] }[] = []
  for (const e of sorted) {
    const last = groups[groups.length - 1]
    if (last && last.date === e.date) last.items.push(e)
    else groups.push({ date: e.date, items: [e] })
  }
  return groups
})

/* ── add ─────────────────────────────────────────────────── */
const form         = reactive({ amount: '', source: '', date: today() })
const isSubmitting = ref(false)
const showModal    = ref(false)

async function add(): Promise<void> {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    await api.createEarning({
      amount: parseFloat(form.amount),
      source: form.source,
      date:   form.date,
    })
    Object.assign(form, { amount: '', source: '', date: today() })
    showModal.value = false
    await loadAll()
    showToast('Earning added')
  } catch {
    showToast('Failed to add earning', true)
  } finally {
    isSubmitting.value = false
  }
}

/* ── edit ────────────────────────────────────────────────── */
const editingId = ref<string | null>(null)
const editForm  = reactive({ amount: '', source: '', date: '' })

function startEdit(e: Earning): void {
  editingId.value = e.id
  Object.assign(editForm, { amount: e.amount.toString(), source: e.source, date: e.date })
}
function cancelEdit(): void { editingId.value = null }
async function saveEdit(id: string): Promise<void> {
  try {
    await api.updateEarning(id, {
      amount: parseFloat(editForm.amount),
      source: editForm.source,
      date:   editForm.date,
    })
    editingId.value = null
    await loadAll()
    showToast('Earning updated')
  } catch {
    showToast('Failed to update earning', true)
  }
}

/* ── delete ──────────────────────────────────────────────── */
const confirmingId = ref<string | null>(null)

function requestDelete(id: string): void { confirmingId.value = id }
function cancelDelete(): void            { confirmingId.value = null }
async function confirmDelete(id: string): Promise<void> {
  try {
    await api.deleteEarning(id)
    confirmingId.value = null
    await loadAll()
    showToast('Earning removed')
  } catch {
    showToast('Failed to delete', true)
  }
}
</script>

<template>
  <section>
    <h1 class="text-3xl font-bold tracking-tight mb-6">Earnings</h1>

    <!-- Add form — desktop only -->
    <form @submit.prevent="add" class="hidden md:flex flex-row gap-3 mb-10">
      <div class="flex-1 min-w-0">
        <label for="e-amount" class="sr-only">Amount</label>
        <input id="e-amount" v-model="form.amount" type="number" step="0.01" min="0"
          placeholder="Amount" required
          class="w-full px-4 py-2.5 rounded-lg border border-light bg-white text-base font-mono focus:ring-2 focus:ring-brand focus:outline-none transition-shadow"
        />
      </div>
      <div class="flex-[2] min-w-0">
        <label for="e-source" class="sr-only">Source</label>
        <input id="e-source" v-model="form.source" type="text"
          placeholder="Source (e.g. Freelance)" required
          class="w-full px-4 py-2.5 rounded-lg border border-light bg-white text-base focus:ring-2 focus:ring-brand focus:outline-none transition-shadow"
        />
      </div>
      <div>
        <label for="e-date" class="sr-only">Date</label>
        <input id="e-date" v-model="form.date" type="date" required
          class="w-full px-4 py-2.5 rounded-lg border border-light bg-white text-base focus:ring-2 focus:ring-brand focus:outline-none transition-shadow"
        />
      </div>
      <button type="submit" :disabled="isSubmitting"
        class="px-6 py-2.5 bg-brand text-white text-sm font-medium rounded-lg hover:bg-brand/90 transition-colors disabled:opacity-60 shrink-0">
        {{ isSubmitting ? 'Adding…' : 'Add' }}
      </button>
    </form>

    <!-- Empty state -->
    <div v-if="earnings.length === 0" class="text-center py-16">
      <svg class="w-10 h-10 text-dark/10 mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>
      </svg>
      <p class="text-dark/30 text-sm">No earnings yet.</p>
      <p class="text-dark/20 text-xs mt-1">Add your first one above.</p>
    </div>

    <!-- Grouped cards -->
    <div v-else class="flex flex-col gap-6">
      <div v-for="group in grouped" :key="group.date">
        <p class="text-xs font-semibold text-dark/30 uppercase tracking-widest mb-2">{{ fmtDate(group.date) }}</p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
          <div v-for="e in group.items" :key="e.id"
            class="bg-white border border-light rounded-xl pl-4 pr-3 py-3.5 shadow-sm"
          >
            <!-- Normal view -->
            <template v-if="editingId !== e.id">
              <div class="flex items-start justify-between gap-3">
                <p class="font-semibold text-dark truncate flex-1 min-w-0">{{ e.source }}</p>
                <div class="flex flex-col items-end gap-1 shrink-0">
                  <div class="flex items-center gap-0.5">
                    <template v-if="confirmingId !== e.id">
                      <button @click="startEdit(e)" aria-label="Edit" class="text-dark/20 hover:text-brand transition-colors p-1 rounded">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                      </button>
                      <button @click="requestDelete(e.id)" aria-label="Delete" class="text-dark/20 hover:text-brand transition-colors p-1 rounded">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                          <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                          <path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
                        </svg>
                      </button>
                    </template>
                    <template v-else>
                      <button @click="cancelDelete" aria-label="Cancel" class="p-1 rounded text-dark/40 hover:text-dark transition-colors">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                      </button>
                      <button @click="confirmDelete(e.id)" aria-label="Confirm delete" class="p-1 rounded text-brand transition-colors">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                      </button>
                    </template>
                  </div>
                </div>
              </div>
              <div class="flex items-center justify-between mt-2">
                <p class="text-xs text-dark/40 font-medium">Amount</p>
                <p class="font-mono font-bold text-emerald-600">+{{ fmtCurrency(e.amount) }}</p>
              </div>
            </template>

            <!-- Edit view -->
            <template v-else>
              <div class="flex flex-col gap-2">
                <div class="flex gap-2">
                  <input v-model="editForm.source" type="text" placeholder="Source"
                    class="flex-[2] bg-transparent border-b border-brand text-sm font-semibold text-dark focus:outline-none pb-0.5"
                  />
                  <input v-model="editForm.amount" type="number" step="0.01"
                    class="flex-1 bg-transparent border-b border-brand text-sm font-mono font-bold text-emerald-600 text-right focus:outline-none pb-0.5"
                  />
                </div>
                <div class="flex items-center justify-between">
                  <input v-model="editForm.date" type="date"
                    class="bg-transparent border-b border-brand text-xs text-dark/50 focus:outline-none pb-0.5"
                  />
                  <div class="flex gap-1">
                    <button @click="saveEdit(e.id)" aria-label="Save" class="p-1 rounded text-brand transition-colors">
                      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                    </button>
                    <button @click="cancelEdit" aria-label="Cancel" class="p-1 rounded text-dark/30 hover:text-dark transition-colors">
                      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile FAB -->
    <button @click="showModal = true"
      class="md:hidden fixed bottom-20 right-5 w-12 h-12 bg-brand text-white rounded-xl shadow-lg flex items-center justify-center z-30"
      aria-label="Add earning"
    >
      <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
      </svg>
    </button>

    <!-- Mobile modal -->
    <Transition enter-active-class="transition-all duration-200" leave-active-class="transition-all duration-150" enter-from-class="opacity-0" leave-to-class="opacity-0">
      <div v-if="showModal" class="md:hidden fixed inset-0 z-50 bg-black/30 flex items-end" @click.self="showModal = false">
        <div class="w-full bg-white rounded-t-2xl shadow-xl px-5 pt-5 pb-10">
          <div class="w-10 h-1 bg-dark/10 rounded-full mx-auto mb-5"></div>
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold tracking-tight">Add Earning</h2>
            <button @click="showModal = false" class="text-dark/30 hover:text-dark p-1 rounded-lg">
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <form @submit.prevent="add" class="flex flex-col gap-4">
            <div>
              <label class="block text-xs font-medium text-dark/40 uppercase tracking-widest mb-1.5">Amount</label>
              <input v-model="form.amount" type="number" step="0.01" min="0" placeholder="0.00" required
                class="w-full px-4 py-3 rounded-xl border border-light bg-white text-base font-mono focus:ring-2 focus:ring-brand focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-dark/40 uppercase tracking-widest mb-1.5">Source</label>
              <input v-model="form.source" type="text" placeholder="e.g. Freelance" required
                class="w-full px-4 py-3 rounded-xl border border-light bg-white text-base focus:ring-2 focus:ring-brand focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-dark/40 uppercase tracking-widest mb-1.5">Date</label>
              <input v-model="form.date" type="date" required
                class="w-full px-4 py-3 rounded-xl border border-light bg-white text-base focus:ring-2 focus:ring-brand focus:outline-none"
              />
            </div>
            <button type="submit" :disabled="isSubmitting"
              class="w-full py-3.5 bg-brand text-white font-semibold rounded-xl hover:bg-brand/90 transition-colors disabled:opacity-60 mt-1">
              {{ isSubmitting ? 'Adding…' : 'Add Earning' }}
            </button>
          </form>
        </div>
      </div>
    </Transition>
  </section>
</template>
