<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Dashboard     from './views/Dashboard.vue'
import Earnings      from './views/Earnings.vue'
import Subscriptions from './views/Subscriptions.vue'
import Spending      from './views/Spending.vue'
import { useFinance } from './useFinance'

type Tab = 'dashboard' | 'earnings' | 'subscriptions' | 'spending'

const tab = ref<Tab>('dashboard')
const { toast, loadAll } = useFinance()

onMounted(loadAll)
</script>

<template>
  <!-- Toast -->
  <Transition
    enter-active-class="transition-all duration-200"
    leave-active-class="transition-all duration-200"
    enter-from-class="opacity-0 translate-y-1"
    leave-to-class="opacity-0 translate-y-1"
  >
    <div
      v-if="toast.show"
      :class="[
        'fixed top-4 right-4 z-50 px-4 py-2.5 rounded-xl text-sm font-medium shadow-lg',
        toast.error ? 'bg-brand text-white' : 'bg-dark text-white',
      ]"
      role="alert"
    >
      {{ toast.msg }}
    </div>
  </Transition>

  <div class="min-h-screen w-screen bg-gradient-to-br from-red-50 via-white to-red-100 text-dark">

    <!-- Header -->
    <header class="bg-white shadow-lg px-4 md:px-6 py-4 sticky top-0 z-40">
      <div class="max-w-3xl lg:max-w-6xl mx-auto w-full flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <!-- Logo mark -->
          <div class="w-7 h-7 bg-brand rounded-lg flex items-center justify-center shrink-0">
            <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>
            </svg>
          </div>
          <span class="text-lg font-bold tracking-tight text-dark">Finance</span>
        </div>

        <!-- Desktop nav -->
        <nav class="hidden md:flex gap-1" role="tablist" aria-label="Main navigation">
          <button
            v-for="t in (['dashboard', 'earnings', 'subscriptions', 'spending'] as const)"
            :key="t"
            role="tab"
            :aria-selected="tab === t"
            @click="tab = t"
            :class="[
              'px-4 py-1.5 rounded-lg text-sm font-medium capitalize transition-colors',
              tab === t ? 'bg-brand text-white' : 'text-dark/40 hover:text-dark hover:bg-dark/5',
            ]"
          >
            {{ t }}
          </button>
        </nav>
      </div>
    </header>

    <!-- Page content with tab fade transition -->
    <main class="max-w-3xl lg:max-w-6xl mx-auto w-full px-4 md:px-8 lg:px-12 py-6 md:py-10 pb-24 md:pb-12">
      <Transition
        mode="out-in"
        enter-active-class="transition-opacity duration-150"
        leave-active-class="transition-opacity duration-100"
        enter-from-class="opacity-0"
        leave-to-class="opacity-0"
      >
        <Dashboard     v-if="tab === 'dashboard'" key="dashboard" />
        <Earnings      v-else-if="tab === 'earnings'" key="earnings" />
        <Subscriptions v-else-if="tab === 'subscriptions'" key="subscriptions" />
        <Spending      v-else-if="tab === 'spending'" key="spending" />
      </Transition>
    </main>

    <!-- Mobile bottom nav — safe-area aware for iPhone -->
    <nav
      class="md:hidden fixed bottom-0 inset-x-0 bg-white border-t border-light grid grid-cols-4"
      style="padding-bottom: env(safe-area-inset-bottom, 0px)"
      role="tablist"
      aria-label="Main navigation"
    >
      <button
        role="tab" :aria-selected="tab === 'dashboard'" @click="tab = 'dashboard'"
        :class="['flex flex-col items-center gap-0.5 py-2 text-[10px] font-medium transition-colors',
          tab === 'dashboard' ? 'text-brand' : 'text-dark/40 hover:text-dark/70']"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
          <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>
        Home
      </button>

      <button
        role="tab" :aria-selected="tab === 'earnings'" @click="tab = 'earnings'"
        :class="['flex flex-col items-center gap-0.5 py-2 text-[10px] font-medium transition-colors',
          tab === 'earnings' ? 'text-brand' : 'text-dark/40 hover:text-dark/70']"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>
        </svg>
        Income
      </button>

      <button
        role="tab" :aria-selected="tab === 'subscriptions'" @click="tab = 'subscriptions'"
        :class="['flex flex-col items-center gap-0.5 py-2 text-[10px] font-medium transition-colors',
          tab === 'subscriptions' ? 'text-brand' : 'text-dark/40 hover:text-dark/70']"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 014-4h14"/>
          <polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 01-4 4H3"/>
        </svg>
        Subs
      </button>

      <button
        role="tab" :aria-selected="tab === 'spending'" @click="tab = 'spending'"
        :class="['flex flex-col items-center gap-0.5 py-2 text-[10px] font-medium transition-colors',
          tab === 'spending' ? 'text-amber-500' : 'text-dark/40 hover:text-dark/70']"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
          <path d="M1 1h4l2.68 13.39a2 2 0 001.98 1.61h9.72a2 2 0 001.98-1.61L23 6H6"/>
        </svg>
        Spend
      </button>
    </nav>

  </div>
</template>
