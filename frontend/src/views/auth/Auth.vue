<script setup lang="ts">
/*
 * Single auth screen — one form that swaps its fields between login and
 * register. Validation is client-side (email format via the native type, password
 * length + match); the server is the real gatekeeper. On success the parent
 * App.vue auth gate reveals the app automatically (isAuthenticated flips).
 */
import { computed, reactive, ref } from 'vue'
import * as api from '../../api'
import { setSession } from '../../session'

type Mode = 'login' | 'register'
const mode        = ref<Mode>('login')
const confirmed   = ref('')   // non-empty = show "check your email" screen
const form        = reactive({ email: '', username: '', password: '', confirm: '' })
const error       = ref('')
const submitting  = ref(false)
const isRegister  = computed(() => mode.value === 'register')

function switchMode(): void {
  mode.value  = isRegister.value ? 'login' : 'register'
  error.value = ''
  confirmed.value = ''
}

function validate(): string {
  if (isRegister.value) {
    if (!/^[a-zA-Z0-9_]{3,20}$/.test(form.username))
      return 'Username must be 3–20 letters, numbers or underscores.'
    if (form.password.length < 8)
      return 'Password must be at least 8 characters.'
    if (form.password !== form.confirm)
      return 'Passwords do not match.'
  }
  return ''
}

async function submit(): Promise<void> {
  if (submitting.value) return
  const msg = validate()
  if (msg) { error.value = msg; return }

  submitting.value = true
  error.value = ''
  try {
    if (isRegister.value) {
      const res = await api.register({ email: form.email, username: form.username, password: form.password })
      if ((res as any).needs_confirmation) {
        confirmed.value = form.email   // show confirmation screen
      } else {
        setSession(res)
      }
    } else {
      setSession(await api.login({ email: form.email, password: form.password }))
    }
  } catch {
    error.value = isRegister.value
      ? 'Could not create your account. Try a different email or username.'
      : 'Invalid email or password.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen w-screen bg-gradient-to-br from-red-50 via-white to-red-100 text-dark flex items-center justify-center px-5 py-10">
    <div class="w-full max-w-sm">

      <!-- Brand -->
      <div class="flex items-center justify-center gap-2.5 mb-8">
        <img src="/logo.png" alt="Zync Logo" class="w-9 h-9 rounded-lg shrink-0" />
        <span class="text-lg font-extrabold tracking-tight text-brand">Spend Wisely!</span>
      </div>

      <!-- Email confirmation screen -->
      <div v-if="confirmed" class="bg-white rounded-2xl shadow-lg p-7 text-center">
        <div class="w-12 h-12 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-6 h-6 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
          </svg>
        </div>
        <h2 class="text-xl font-bold tracking-tight mb-2">Check your email</h2>
        <p class="text-sm text-dark/50 mb-1">We sent a confirmation link to</p>
        <p class="text-sm font-semibold text-dark mb-5">{{ confirmed }}</p>
        <p class="text-xs text-dark/30">Click the link in the email to activate your account, then sign in below.</p>
        <button @click="switchMode" class="mt-5 text-sm font-semibold text-brand hover:underline">
          Back to sign in
        </button>
      </div>

      <!-- Card -->
      <div v-if="!confirmed" class="bg-white rounded-2xl shadow-lg p-7">
        <h1 class="text-2xl font-bold tracking-tight mb-1">
          {{ isRegister ? 'Create account' : 'Welcome back' }}
        </h1>
        <p class="text-sm text-dark/40 mb-6">
          {{ isRegister ? 'Start tracking your money in seconds.' : 'Sign in to your tracker.' }}
        </p>

        <form @submit.prevent="submit" class="flex flex-col gap-4" novalidate>
          <div>
            <label class="block text-xs font-medium text-dark/40 uppercase tracking-widest mb-1.5">Email</label>
            <input
              v-model.trim="form.email" type="email" autocomplete="email" required
              placeholder="you@example.com"
              class="w-full px-4 py-3 rounded-xl bg-light text-base focus:ring-2 focus:ring-brand focus:outline-none"
            />
          </div>

          <!-- Register-only: username -->
          <div v-if="isRegister">
            <label class="block text-xs font-medium text-dark/40 uppercase tracking-widest mb-1.5">Username</label>
            <input
              v-model.trim="form.username" type="text" autocomplete="username" required
              placeholder="e.g. ouanokevinj"
              class="w-full px-4 py-3 rounded-xl bg-light text-base focus:ring-2 focus:ring-brand focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-xs font-medium text-dark/40 uppercase tracking-widest mb-1.5">Password</label>
            <input
              v-model="form.password" type="password" required
              :autocomplete="isRegister ? 'new-password' : 'current-password'"
              placeholder="••••••••"
              class="w-full px-4 py-3 rounded-xl bg-light text-base focus:ring-2 focus:ring-brand focus:outline-none"
            />
          </div>

          <!-- Register-only: confirm -->
          <div v-if="isRegister">
            <label class="block text-xs font-medium text-dark/40 uppercase tracking-widest mb-1.5">Confirm Password</label>
            <input
              v-model="form.confirm" type="password" autocomplete="new-password" required
              placeholder="••••••••"
              class="w-full px-4 py-3 rounded-xl bg-light text-base focus:ring-2 focus:ring-brand focus:outline-none"
            />
          </div>

          <!-- Error -->
          <p v-if="error" class="text-sm text-brand font-medium" role="alert">{{ error }}</p>

          <button type="submit" :disabled="submitting"
            class="w-full py-3.5 bg-brand text-white font-semibold rounded-xl hover:bg-brand/90 transition-colors disabled:opacity-60 mt-1">
            {{ submitting ? 'Please wait…' : isRegister ? 'Create account' : 'Sign in' }}
          </button>
        </form>
      </div>

      <!-- Mode switch -->
      <p v-if="!confirmed" class="text-center text-sm text-dark/50 mt-6">
        {{ isRegister ? 'Already have an account?' : 'New here?' }}
        <button @click="switchMode" class="font-semibold text-brand hover:underline ml-1">
          {{ isRegister ? 'Sign in' : 'Create one' }}
        </button>
      </p>

    </div>
  </div>
</template>
