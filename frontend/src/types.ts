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

export interface User {
  id: string
  email: string
  username: string | null
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
}

/* Login/register both return tokens; register/login also return the user. */
export interface AuthResponse extends AuthTokens {
  user: User
}
