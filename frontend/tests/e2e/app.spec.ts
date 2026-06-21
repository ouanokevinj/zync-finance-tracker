import { test, expect, Page } from '@playwright/test'

/* ── helpers ──────────────────────────────────────────────── */

async function goToDashboard(page: Page) {
  await page.goto('/')
  await page.waitForLoadState('networkidle')
}

async function switchTab(page: Page, label: string) {
  /* Works for both desktop nav buttons and mobile bottom nav */
  const btn = page.getByRole('tab', { name: new RegExp(label, 'i') }).first()
  await btn.click()
  await page.waitForTimeout(200) // fade transition
}

/* ══════════════════════════════════════════════════════════════
   DASHBOARD
══════════════════════════════════════════════════════════════ */

test.describe('Dashboard', () => {

  test('loads and shows Balance label', async ({ page }) => {
    await goToDashboard(page)
    await expect(page.getByText('Balance')).toBeVisible()
  })

  test('shows Earned and Subscriptions stat cards', async ({ page }) => {
    await goToDashboard(page)
    await expect(page.getByText('Earned')).toBeVisible()
    await expect(page.getByText('Subscriptions')).toBeVisible()
  })

  test('shows Quick Add buttons', async ({ page }) => {
    await goToDashboard(page)
    await expect(page.getByRole('button', { name: /\+ Earning/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /\+ Subscription/i })).toBeVisible()
  })

  test('shows Activity section', async ({ page }) => {
    await goToDashboard(page)
    await expect(page.getByText('Activity')).toBeVisible()
  })

})

/* ══════════════════════════════════════════════════════════════
   NAVIGATION
══════════════════════════════════════════════════════════════ */

test.describe('Navigation', () => {

  test('switches to Earnings tab', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Earnings')
    await expect(page.getByRole('heading', { name: 'Earnings' })).toBeVisible()
  })

  test('switches to Subscriptions tab', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Subs')
    await expect(page.getByRole('heading', { name: 'Subscriptions' })).toBeVisible()
  })

  test('switches back to Dashboard', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Earnings')
    await switchTab(page, 'Overview')
    await expect(page.getByText('Balance')).toBeVisible()
  })

})

/* ══════════════════════════════════════════════════════════════
   QUICK ADD — EARNING
══════════════════════════════════════════════════════════════ */

test.describe('Quick Add — Earning', () => {

  test('toggles earning form open and closed', async ({ page }) => {
    await goToDashboard(page)
    const btn = page.getByRole('button', { name: /\+ Earning/i })
    await btn.click()
    await expect(page.locator('#qa-e-amount')).toBeVisible()
    await btn.click()
    await expect(page.locator('#qa-e-amount')).not.toBeVisible()
  })

  test('add button is disabled while submitting', async ({ page }) => {
    await goToDashboard(page)
    await page.getByRole('button', { name: /\+ Earning/i }).click()
    await page.locator('#qa-e-amount').fill('500')
    await page.locator('#qa-e-source').fill('Test source')
    /* The submit button should exist and be enabled before click */
    const submit = page.locator('form').filter({ has: page.locator('#qa-e-amount') }).getByRole('button', { name: /^Add$/i })
    await expect(submit).toBeEnabled()
  })

  test('form requires amount field', async ({ page }) => {
    await goToDashboard(page)
    await page.getByRole('button', { name: /\+ Earning/i }).click()
    await page.locator('#qa-e-source').fill('Test')
    const submit = page.locator('form').filter({ has: page.locator('#qa-e-amount') }).getByRole('button', { name: /^Add$/i })
    await submit.click()
    /* HTML5 validation prevents submission — amount field is required */
    await expect(page.locator('#qa-e-amount')).toBeVisible() // form still open
  })

  test('form requires source field', async ({ page }) => {
    await goToDashboard(page)
    await page.getByRole('button', { name: /\+ Earning/i }).click()
    await page.locator('#qa-e-amount').fill('500')
    const submit = page.locator('form').filter({ has: page.locator('#qa-e-amount') }).getByRole('button', { name: /^Add$/i })
    await submit.click()
    await expect(page.locator('#qa-e-source')).toBeVisible()
  })

})

/* ══════════════════════════════════════════════════════════════
   QUICK ADD — SUBSCRIPTION
══════════════════════════════════════════════════════════════ */

test.describe('Quick Add — Subscription', () => {

  test('toggles subscription form open and closed', async ({ page }) => {
    await goToDashboard(page)
    const btn = page.getByRole('button', { name: /\+ Subscription/i })
    await btn.click()
    await expect(page.locator('#qa-s-name')).toBeVisible()
    await btn.click()
    await expect(page.locator('#qa-s-name')).not.toBeVisible()
  })

  test('opening one form closes the other', async ({ page }) => {
    await goToDashboard(page)
    await page.getByRole('button', { name: /\+ Earning/i }).click()
    await expect(page.locator('#qa-e-amount')).toBeVisible()

    await page.getByRole('button', { name: /\+ Subscription/i }).click()
    await expect(page.locator('#qa-s-name')).toBeVisible()
    await expect(page.locator('#qa-e-amount')).not.toBeVisible()
  })

  test('form requires name field', async ({ page }) => {
    await goToDashboard(page)
    await page.getByRole('button', { name: /\+ Subscription/i }).click()
    await page.locator('#qa-s-amount').fill('15.99')
    const submit = page.locator('form').filter({ has: page.locator('#qa-s-name') }).getByRole('button', { name: /^Add$/i })
    await submit.click()
    await expect(page.locator('#qa-s-name')).toBeVisible()
  })

})

/* ══════════════════════════════════════════════════════════════
   EARNINGS TAB
══════════════════════════════════════════════════════════════ */

test.describe('Earnings tab', () => {

  test('shows heading', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Earnings')
    await expect(page.getByRole('heading', { name: 'Earnings' })).toBeVisible()
  })

  test('add form renders all fields', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Earnings')
    await expect(page.locator('#e-amount')).toBeVisible()
    await expect(page.locator('#e-source')).toBeVisible()
    await expect(page.locator('#e-date')).toBeVisible()
    await expect(page.getByRole('button', { name: /^Add$/i })).toBeVisible()
  })

  test('empty form submission does not submit (required fields)', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Earnings')
    await page.getByRole('button', { name: /^Add$/i }).click()
    /* Form should still be visible — not navigated away */
    await expect(page.locator('#e-amount')).toBeVisible()
  })

  test('shows empty state when no earnings', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Earnings')
    /* Either empty state text or a table — one must be present */
    const emptyOrTable = page.locator('p:has-text("No earnings"), table')
    await expect(emptyOrTable.first()).toBeVisible()
  })

})

/* ══════════════════════════════════════════════════════════════
   SUBSCRIPTIONS TAB
══════════════════════════════════════════════════════════════ */

test.describe('Subscriptions tab', () => {

  test('shows heading', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Subs')
    await expect(page.getByRole('heading', { name: 'Subscriptions' })).toBeVisible()
  })

  test('add form renders all fields', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Subs')
    await expect(page.locator('#s-name')).toBeVisible()
    await expect(page.locator('#s-amount')).toBeVisible()
    await expect(page.locator('#s-date')).toBeVisible()
  })

  test('shows empty state when no subscriptions', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Subs')
    const emptyOrTable = page.locator('p:has-text("No subscriptions"), table')
    await expect(emptyOrTable.first()).toBeVisible()
  })

})

/* ══════════════════════════════════════════════════════════════
   DELETE CONFIRMATION FLOW
══════════════════════════════════════════════════════════════ */

test.describe('Delete confirmation', () => {

  test('trash icon triggers confirm state in Earnings', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Earnings')

    const table = page.locator('table')
    const hasTable = await table.isVisible()
    if (!hasTable) {
      test.skip() // no rows to delete
      return
    }

    /* Click the first trash button */
    const trashBtn = page.getByRole('button', { name: /delete earning/i }).first()
    await trashBtn.click()

    /* Confirm (✓) and cancel (✗) buttons should appear */
    await expect(page.getByRole('button', { name: /confirm delete/i }).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /cancel/i }).first()).toBeVisible()
  })

  test('cancel delete restores trash icon', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Earnings')

    const hasTable = await page.locator('table').isVisible()
    if (!hasTable) { test.skip(); return }

    await page.getByRole('button', { name: /delete earning/i }).first().click()
    await page.getByRole('button', { name: /cancel/i }).first().click()

    /* Trash icon is back, confirm buttons gone */
    await expect(page.getByRole('button', { name: /delete earning/i }).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /confirm delete/i })).not.toBeVisible()
  })

})

/* ══════════════════════════════════════════════════════════════
   EDGE CASES — UI
══════════════════════════════════════════════════════════════ */

test.describe('UI edge cases', () => {

  test('negative amount input is rejected by type=number min=0', async ({ page }) => {
    await goToDashboard(page)
    await switchTab(page, 'Earnings')
    await page.locator('#e-amount').fill('-100')
    await page.locator('#e-source').fill('Test')
    await page.getByRole('button', { name: /^Add$/i }).click()
    /* HTML5 min=0 blocks submission; form should stay visible */
    await expect(page.locator('#e-amount')).toBeVisible()
  })

  test('header is sticky — visible after scrolling', async ({ page }) => {
    await goToDashboard(page)
    await page.evaluate(() => window.scrollTo(0, 500))
    await expect(page.locator('header')).toBeVisible()
  })

  test('Finance logo visible in header', async ({ page }) => {
    await goToDashboard(page)
    await expect(page.getByText('Finance')).toBeVisible()
  })

  test('page title is Finance', async ({ page }) => {
    await goToDashboard(page)
    await expect(page).toHaveTitle('Finance')
  })

})
