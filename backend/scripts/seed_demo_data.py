"""
seed_demo_data.py
─────────────────
Comprehensive demo seed for the EstateX Hyderabad platform.

What this seeds
───────────────
Users (3)
  • admin@estatex.in       / Admin@123       role: ADMIN
  • owner@estatex.in       / Owner@123       role: PROPERTY_OWNER
  • investor@estatex.in    / Investor@123    role: INVESTOR

Properties (150)
  • 20 Hyderabad localities (Gachibowli, Hitech City, Kondapur, …)
  • Types: Residential, Commercial, Office, Retail
  • All 148 approved and verified; 2 kept PENDING for admin-flow demo

Documents (4 per property: sale deed, encumbrance cert, tax receipt, ID proof)
  • All verified for approved properties

Investment portfolio (5 holdings seeded for the demo investor)
  • Ownership records + InvestmentTransaction records

Secondary-market listings (2 active sell orders so liquidity page has data)

Usage
─────
cd backend
PYTHONPATH=. python3 scripts/seed_demo_data.py
"""

from scripts.seed_data import main

if __name__ == "__main__":
    main()
