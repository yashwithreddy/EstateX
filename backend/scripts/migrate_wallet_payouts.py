from sqlalchemy import inspect, text

from app.db.session import engine


def _add_wallet_balance_column(dialect: str) -> None:
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "wallet_balance" in columns:
        return

    with engine.begin() as conn:
        if dialect == "sqlite":
            conn.execute(text("ALTER TABLE users ADD COLUMN wallet_balance NUMERIC(14, 2) NOT NULL DEFAULT 0"))
        else:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_balance NUMERIC(14, 2) NOT NULL DEFAULT 0")
            )


def _create_investor_payouts_table(dialect: str) -> None:
    inspector = inspect(engine)
    if "investor_payouts" in inspector.get_table_names():
        return

    with engine.begin() as conn:
        if dialect == "sqlite":
            conn.execute(
                text(
                    """
                    CREATE TABLE investor_payouts (
                        id INTEGER PRIMARY KEY,
                        investor_id INTEGER NOT NULL,
                        property_id INTEGER NOT NULL,
                        payout_month VARCHAR(7) NOT NULL,
                        amount NUMERIC(14, 2) NOT NULL,
                        onchain_tx_hash VARCHAR(66),
                        created_at DATETIME,
                        CONSTRAINT uq_investor_month UNIQUE (investor_id, property_id, payout_month),
                        CONSTRAINT fk_payout_investor FOREIGN KEY (investor_id) REFERENCES users (id),
                        CONSTRAINT fk_payout_property FOREIGN KEY (property_id) REFERENCES properties (id)
                    )
                    """
                )
            )
        else:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS investor_payouts (
                        id SERIAL PRIMARY KEY,
                        investor_id INTEGER NOT NULL REFERENCES users (id),
                        property_id INTEGER NOT NULL REFERENCES properties (id),
                        payout_month VARCHAR(7) NOT NULL,
                        amount NUMERIC(14, 2) NOT NULL,
                        onchain_tx_hash VARCHAR(66),
                        created_at TIMESTAMP,
                        CONSTRAINT uq_investor_month UNIQUE (investor_id, property_id, payout_month)
                    )
                    """
                )
            )


def main() -> None:
    dialect = engine.dialect.name
    _add_wallet_balance_column(dialect)
    _create_investor_payouts_table(dialect)
    print("Migration complete.")


if __name__ == "__main__":
    main()
