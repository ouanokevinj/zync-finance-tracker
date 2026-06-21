export interface Earning {
  id: string
  amount: number
  source: string
  date: string
  created_at: string
}

export interface Subscription {
  id: string
  name: string
  amount: number
  date_started: string
  created_at: string
}

export interface Spending {
  id: string
  description: string
  amount: number
  date: string
  created_at: string
}

export interface Summary {
  total_earnings: number
  total_subscriptions: number
  total_spending: number
  net: number
}
