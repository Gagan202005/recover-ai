-- ============================================
-- RecoverAI — Supabase Schema
-- Run this in Supabase SQL Editor (once)
-- ============================================

-- 1. Customers
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    city TEXT,
    segment TEXT CHECK (segment IN ('vip', 'regular', 'new', 'b2b', 'subscription')),
    lifetime_value INTEGER DEFAULT 0,
    preferred_payment TEXT,
    preferred_language TEXT CHECK (preferred_language IN ('english', 'hinglish', 'hindi')),
    preferred_channel TEXT CHECK (preferred_channel IN ('whatsapp', 'sms', 'email')),
    on_dnd BOOLEAN DEFAULT FALSE,
    opted_out BOOLEAN DEFAULT FALSE,
    is_live_demo BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Transactions
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    razorpay_order_id TEXT,
    razorpay_payment_id TEXT,
    customer_id TEXT REFERENCES customers(id),
    amount INTEGER NOT NULL,
    product_name TEXT,
    method TEXT,
    bank TEXT,
    status TEXT CHECK (status IN ('success', 'failed', 'abandoned', 'overdue')),
    failure_reason TEXT,
    error_code TEXT,
    error_description TEXT,
    error_source TEXT,
    recovery_status TEXT DEFAULT 'pending' CHECK (recovery_status IN ('pending', 'in_progress', 'recovered', 'exception', 'human_review')),
    recovery_amount INTEGER DEFAULT 0,
    attempt_count INTEGER DEFAULT 0,
    is_outage_related BOOLEAN DEFAULT FALSE,
    is_live_demo BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    recovered_at TIMESTAMPTZ
);

-- 3. Recovery Actions (Audit Trail)
CREATE TABLE IF NOT EXISTS recovery_actions (
    id SERIAL PRIMARY KEY,
    transaction_id TEXT REFERENCES transactions(id),
    agent TEXT NOT NULL,
    action TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    rag_citations JSONB,
    result TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Agent Debates
CREATE TABLE IF NOT EXISTS agent_debates (
    id SERIAL PRIMARY KEY,
    transaction_id TEXT REFERENCES transactions(id),
    proposer TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    original_action JSONB NOT NULL,
    objection TEXT NOT NULL,
    resolution JSONB NOT NULL,
    compliance_citation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Promise to Pay
CREATE TABLE IF NOT EXISTS promise_to_pay (
    id SERIAL PRIMARY KEY,
    transaction_id TEXT REFERENCES transactions(id),
    customer_id TEXT REFERENCES customers(id),
    promise_date DATE NOT NULL,
    promise_amount INTEGER NOT NULL,
    status TEXT DEFAULT 'promised' CHECK (status IN ('promised', 'fulfilled', 'broken')),
    whatsapp_message_sid TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    fulfilled_at TIMESTAMPTZ
);

-- 6. Channel Messages
CREATE TABLE IF NOT EXISTS channel_messages (
    id SERIAL PRIMARY KEY,
    transaction_id TEXT REFERENCES transactions(id),
    customer_id TEXT REFERENCES customers(id),
    channel TEXT NOT NULL CHECK (channel IN ('whatsapp', 'sms', 'email', 'voice', 'auto_retry', 'payment_link')),
    language TEXT,
    message_content TEXT,
    external_id TEXT,
    payment_link_url TEXT,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. A/B Tests
CREATE TABLE IF NOT EXISTS ab_tests (
    id SERIAL PRIMARY KEY,
    experiment_name TEXT,
    failure_type TEXT,
    variant_a TEXT,
    variant_b TEXT,
    variant_a_successes INTEGER DEFAULT 0,
    variant_a_trials INTEGER DEFAULT 0,
    variant_b_successes INTEGER DEFAULT 0,
    variant_b_trials INTEGER DEFAULT 0,
    p_value FLOAT,
    is_significant BOOLEAN DEFAULT FALSE,
    winner TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Enable Supabase Realtime on key tables
-- ============================================
ALTER PUBLICATION supabase_realtime ADD TABLE recovery_actions;
ALTER PUBLICATION supabase_realtime ADD TABLE transactions;
ALTER PUBLICATION supabase_realtime ADD TABLE agent_debates;
ALTER PUBLICATION supabase_realtime ADD TABLE promise_to_pay;
ALTER PUBLICATION supabase_realtime ADD TABLE channel_messages;

-- ============================================
-- Indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_recovery ON transactions(recovery_status);
CREATE INDEX IF NOT EXISTS idx_transactions_customer ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_bank ON transactions(bank);
CREATE INDEX IF NOT EXISTS idx_recovery_actions_txn ON recovery_actions(transaction_id);
CREATE INDEX IF NOT EXISTS idx_channel_messages_txn ON channel_messages(transaction_id);
CREATE INDEX IF NOT EXISTS idx_channel_messages_customer ON channel_messages(customer_id);
