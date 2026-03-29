BEGIN;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS wallet_balance NUMERIC(14, 2) NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS investor_payouts (
    id SERIAL PRIMARY KEY,
    investor_id INTEGER NOT NULL REFERENCES users(id),
    property_id INTEGER NOT NULL REFERENCES properties(id),
    payout_month VARCHAR(7) NOT NULL,
    amount NUMERIC(14, 2) NOT NULL,
    onchain_tx_hash VARCHAR(66),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_investor_month UNIQUE (investor_id, property_id, payout_month)
);

COMMIT;
