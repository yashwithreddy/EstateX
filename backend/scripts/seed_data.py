from pathlib import Path

from app.core.security import hash_password
from app.db.mongo import get_next_sequence, utc_now
from app.db.session import get_database
from app.models import DocumentType, ListingStatus, PropertyType, RiskLevel, TransactionType, UserRole
from app.utils.hash_utils import sha256_file

# ---------------------------------------------------------------------------
# Image pools per property category
# ---------------------------------------------------------------------------
_APT = [
    "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1560185007-cde436f6a4d0?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1548407260-da850faa41e3?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1568605114967-8130f3a36994?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1600047508788-786f3865b4a5?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1572120360610-d971b9d7767c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1200&q=80",
]
_VILLA = [
    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1523217582562-09d0def993a6?auto=format&fit=crop&w=1200&q=80",
]
_OFFICE = [
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1460317442991-0ec209397118?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=1200&q=80",
]

def _img(pool, idx): return pool[idx % len(pool)]

# ---------------------------------------------------------------------------
# 150 Hyderabad properties
# Columns: title, locality, ptype, price_lakh, area_sqft, beds,
#          rental_yield, loc_score(1-10), conn_score(1-10),
#          infra_growth(0-1), appreciation('G'/'S'/'D'),
#          roi, risk, img_pool, img_idx
# ---------------------------------------------------------------------------
R, C, O = PropertyType.RESIDENTIAL, PropertyType.COMMERCIAL, PropertyType.OFFICE
L, M, H = RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH

HYDERABAD_PROPERTIES = [
    # ── GACHIBOWLI (10) ─────────────────────────────────────────────────────
    ("Gachibowli Prestige Towers",        "Gachibowli", R, 92,  1580, 3, 4.3, 9, 9, 0.90, "G", 13.5, L, _APT,   0),
    ("Gachibowli IT Park Residences",     "Gachibowli", R, 76,  1280, 2, 4.1, 9, 9, 0.90, "G", 12.8, L, _APT,   1),
    ("Gachibowli Enclave",                "Gachibowli", R, 88,  1480, 3, 4.4, 9, 9, 0.88, "G", 13.2, L, _APT,   2),
    ("Gachibowli Grand Villas",           "Gachibowli", R, 210, 3200, 4, 3.8, 9, 8, 0.85, "G", 13.0, L, _VILLA, 0),
    ("Gachibowli One – Office Park",      "Gachibowli", O, 168, 2800, 0, 6.8, 9, 9, 0.92, "G", 14.2, L, _OFFICE,0),
    ("Gachibowli Elite Homes",            "Gachibowli", R, 68,  1180, 2, 3.9, 8, 9, 0.87, "G", 11.8, L, _APT,   3),
    ("Gachibowli Skyline Offices",        "Gachibowli", O, 215, 3600, 0, 7.2, 9, 9, 0.93, "G", 15.1, L, _OFFICE,1),
    ("Gachibowli Paradise",               "Gachibowli", R, 106, 1720, 3, 4.6, 9, 9, 0.90, "G", 14.0, L, _APT,   4),
    ("Gachibowli Silicon Valley Apt",     "Gachibowli", R, 82,  1380, 3, 4.2, 9, 9, 0.88, "G", 13.0, L, _APT,   5),
    ("Gachibowli Cyberspace Offices",     "Gachibowli", O, 195, 3200, 0, 7.0, 9, 9, 0.91, "G", 14.8, L, _OFFICE,2),

    # ── HITECH CITY (10) ────────────────────────────────────────────────────
    ("Hitech City Platinum Heights",      "Hitech City", R, 118, 1820, 3, 4.8, 10, 10, 0.95, "G", 15.0, L, _APT,   6),
    ("Hitech City Towers – Office",       "Hitech City", O, 285, 4800, 0, 7.5, 10, 10, 0.96, "G", 15.8, L, _OFFICE,3),
    ("Hitech City Residences",            "Hitech City", R, 88,  1500, 2, 4.5, 10, 10, 0.93, "G", 13.5, L, _APT,   7),
    ("Hitech City Commerce Hub",          "Hitech City", C, 325, 5200, 0, 7.8, 10, 10, 0.95, "G", 14.5, L, _OFFICE,4),
    ("Hitech City Elite Homes",           "Hitech City", R, 128, 2050, 3, 5.0, 10, 10, 0.94, "G", 14.8, L, _APT,   8),
    ("Hitech City Skyview",               "Hitech City", R, 95,  1580, 2, 4.6, 10, 10, 0.92, "G", 13.2, L, _APT,   9),
    ("Hitech City Business Offices",      "Hitech City", O, 198, 3300, 0, 7.2, 10, 10, 0.94, "G", 14.9, L, _OFFICE,5),
    ("Hitech City Metro Homes",           "Hitech City", R, 102, 1680, 3, 4.7, 10, 10, 0.93, "G", 14.1, L, _APT,   0),
    ("Hitech City Pearl Residences",      "Hitech City", R, 112, 1780, 3, 4.9, 10, 10, 0.95, "G", 14.5, L, _APT,   1),
    ("Hitech City Pinnacle Offices",      "Hitech City", O, 245, 4100, 0, 7.4, 10, 10, 0.96, "G", 15.5, L, _OFFICE,0),

    # ── KONDAPUR (7) ────────────────────────────────────────────────────────
    ("Kondapur Green Heights",            "Kondapur", R, 72,  1320, 3, 4.0, 8, 8, 0.82, "G", 12.1, L, _APT,   2),
    ("Kondapur Valley View",              "Kondapur", R, 58,  1120, 2, 3.8, 8, 8, 0.80, "G", 11.5, M, _APT,   3),
    ("Kondapur Premium Homes",            "Kondapur", R, 85,  1480, 3, 4.2, 8, 8, 0.83, "G", 12.8, L, _APT,   4),
    ("Kondapur Business Hub",             "Kondapur", O, 128, 2150, 0, 6.5, 8, 9, 0.84, "G", 13.5, L, _OFFICE,1),
    ("Kondapur Panorama Villas",          "Kondapur", R, 158, 2650, 4, 3.5, 8, 8, 0.80, "G", 12.3, L, _VILLA, 1),
    ("Kondapur Grand Apartments",         "Kondapur", R, 64,  1180, 2, 3.7, 7, 8, 0.78, "G", 11.2, M, _APT,   5),
    ("Kondapur Tech Park Offices",        "Kondapur", O, 148, 2500, 0, 6.8, 8, 9, 0.85, "G", 14.1, L, _OFFICE,2),

    # ── MADHAPUR (7) ────────────────────────────────────────────────────────
    ("Madhapur IT Residences",            "Madhapur", R, 96,  1580, 3, 4.4, 9, 9, 0.88, "G", 13.8, L, _APT,   6),
    ("Madhapur Sky Heights",              "Madhapur", R, 72,  1280, 2, 4.1, 9, 9, 0.86, "G", 12.4, L, _APT,   7),
    ("Madhapur Business Park",            "Madhapur", O, 178, 3000, 0, 7.0, 9, 9, 0.90, "G", 14.5, L, _OFFICE,3),
    ("Madhapur Skyview Towers",           "Madhapur", R, 110, 1780, 3, 4.6, 9, 9, 0.88, "G", 13.5, L, _APT,   8),
    ("Madhapur Elite Residences",         "Madhapur", R, 84,  1420, 2, 4.3, 9, 9, 0.87, "G", 12.9, L, _APT,   9),
    ("Madhapur Commerce Center",          "Madhapur", C, 158, 2650, 0, 6.5, 8, 9, 0.86, "G", 13.8, M, _OFFICE,4),
    ("Madhapur Platinum Apartments",      "Madhapur", R, 120, 1950, 3, 4.8, 9, 9, 0.89, "G", 14.2, L, _APT,   0),

    # ── MANIKONDA (7) ────────────────────────────────────────────────────────
    ("Manikonda Sunrise Heights",         "Manikonda", R, 52,  1080, 2, 3.5, 7, 7, 0.72, "G", 10.5, M, _APT,   1),
    ("Manikonda Valley View",             "Manikonda", R, 65,  1280, 3, 3.8, 7, 7, 0.74, "G", 11.2, M, _APT,   2),
    ("Manikonda Green Residences",        "Manikonda", R, 48,  980,  2, 3.3, 6, 7, 0.70, "G", 9.8,  M, _APT,   3),
    ("Manikonda Smart Homes",             "Manikonda", R, 72,  1380, 3, 3.9, 7, 7, 0.75, "G", 11.5, M, _APT,   4),
    ("Manikonda City Apartments",         "Manikonda", R, 56,  1120, 2, 3.6, 7, 7, 0.72, "G", 10.2, M, _APT,   5),
    ("Manikonda Premium Villas",          "Manikonda", R, 138, 2280, 4, 3.2, 7, 7, 0.70, "G", 11.8, M, _VILLA, 2),
    ("Manikonda Grand Towers",            "Manikonda", R, 68,  1320, 3, 3.8, 7, 7, 0.73, "G", 11.0, M, _APT,   6),

    # ── NARSINGI (7) ─────────────────────────────────────────────────────────
    ("Narsingi Lakewood Homes",           "Narsingi", R, 58,  1150, 2, 3.6, 7, 7, 0.75, "G", 10.8, M, _APT,   7),
    ("Narsingi Hill View Heights",        "Narsingi", R, 72,  1380, 3, 3.9, 7, 7, 0.76, "G", 11.5, M, _APT,   8),
    ("Narsingi Emerald Villas",           "Narsingi", R, 148, 2450, 4, 3.3, 7, 7, 0.74, "G", 12.2, M, _VILLA, 3),
    ("Narsingi Township Residences",      "Narsingi", R, 52,  1050, 2, 3.4, 7, 7, 0.73, "G", 10.2, M, _APT,   9),
    ("Narsingi Green Park",               "Narsingi", R, 68,  1300, 3, 3.8, 7, 7, 0.75, "G", 11.0, M, _APT,   0),
    ("Narsingi Business Hub",             "Narsingi", O, 98,  1650, 0, 5.8, 7, 7, 0.76, "G", 12.5, M, _OFFICE,5),
    ("Narsingi Smart Residences",         "Narsingi", R, 56,  1100, 2, 3.5, 7, 7, 0.73, "G", 10.5, M, _APT,   1),

    # ── TELLAPUR (6) ─────────────────────────────────────────────────────────
    ("Tellapur Township Phase 1",         "Tellapur", R, 48,  1000, 2, 3.2, 6, 6, 0.70, "G", 10.2, M, _APT,   2),
    ("Tellapur Heights Apartments",       "Tellapur", R, 62,  1250, 3, 3.5, 6, 6, 0.72, "G", 11.0, M, _APT,   3),
    ("Tellapur Green Villas",             "Tellapur", R, 120, 2050, 3, 3.0, 6, 6, 0.68, "G", 11.5, M, _VILLA, 0),
    ("Tellapur Smart City Apts",          "Tellapur", R, 44,  920,  2, 3.0, 6, 6, 0.68, "G", 9.8,  M, _APT,   4),
    ("Tellapur Sunrise Residences",       "Tellapur", R, 58,  1180, 3, 3.3, 6, 7, 0.70, "G", 10.5, M, _APT,   5),
    ("Tellapur Orchid Gardens",           "Tellapur", R, 45,  950,  2, 3.1, 6, 6, 0.65, "S", 9.5,  H, _APT,   6),

    # ── KUKATPALLY (7) ───────────────────────────────────────────────────────
    ("Kukatpally KPHB Colony Apts",       "Kukatpally", R, 45,  950,  2, 3.1, 7, 8, 0.70, "S", 9.5,  M, _APT,   7),
    ("Kukatpally Prime Towers",           "Kukatpally", R, 62,  1230, 3, 3.6, 7, 8, 0.72, "G", 10.8, M, _APT,   8),
    ("Kukatpally Business Centre",        "Kukatpally", C, 98,  1650, 0, 5.8, 7, 8, 0.73, "G", 12.2, M, _OFFICE,0),
    ("Kukatpally Metro Heights",          "Kukatpally", R, 52,  1050, 2, 3.4, 7, 8, 0.71, "G", 10.2, M, _APT,   9),
    ("Kukatpally Signature Towers",       "Kukatpally", R, 68,  1330, 3, 3.7, 7, 8, 0.72, "G", 11.2, M, _APT,   0),
    ("Kukatpally Platinum Residences",    "Kukatpally", R, 56,  1120, 2, 3.5, 7, 8, 0.71, "G", 10.5, M, _APT,   1),
    ("Kukatpally IT Hub Offices",         "Kukatpally", O, 115, 1950, 0, 6.2, 7, 8, 0.74, "G", 12.8, M, _OFFICE,1),

    # ── MIYAPUR (7) ──────────────────────────────────────────────────────────
    ("Miyapur Metro Station Apts",        "Miyapur", R, 42,  900,  2, 3.0, 6, 7, 0.68, "G", 9.2,  M, _APT,   2),
    ("Miyapur Heights",                   "Miyapur", R, 58,  1150, 3, 3.4, 6, 7, 0.70, "G", 10.5, M, _APT,   3),
    ("Miyapur Township Residences",       "Miyapur", R, 48,  980,  2, 3.2, 6, 7, 0.68, "G", 9.8,  M, _APT,   4),
    ("Miyapur Valley Apartments",         "Miyapur", R, 62,  1230, 3, 3.5, 6, 7, 0.70, "G", 10.8, M, _APT,   5),
    ("Miyapur Green Enclave",             "Miyapur", R, 46,  950,  2, 3.1, 6, 7, 0.67, "S", 9.5,  M, _APT,   6),
    ("Miyapur Premium Villas",            "Miyapur", R, 108, 1850, 3, 2.9, 6, 7, 0.68, "G", 11.2, M, _VILLA, 1),
    ("Miyapur Commerce Square",           "Miyapur", C, 88,  1500, 0, 5.5, 6, 7, 0.70, "G", 11.8, M, _OFFICE,2),

    # ── BANJARA HILLS (10) ───────────────────────────────────────────────────
    ("Banjara Hills Luxury Towers",       "Banjara Hills", R, 168, 2650, 3, 4.2, 10, 9, 0.88, "G", 12.5, L, _APT,   7),
    ("Banjara Hills Premium Villas",      "Banjara Hills", R, 425, 5800, 5, 3.6, 10, 9, 0.85, "G", 11.8, L, _VILLA, 0),
    ("Banjara Hills Signature",           "Banjara Hills", R, 188, 2900, 3, 4.3, 10, 9, 0.87, "G", 12.2, L, _APT,   8),
    ("Banjara Hills Business Hub",        "Banjara Hills", C, 285, 4800, 0, 6.5, 10, 9, 0.88, "G", 13.5, L, _OFFICE,3),
    ("Banjara Hills Elite Residences",    "Banjara Hills", R, 225, 3500, 4, 4.1, 10, 9, 0.86, "G", 12.8, L, _APT,   9),
    ("Banjara Hills Grand Estates",       "Banjara Hills", R, 355, 4800, 4, 3.5, 10, 9, 0.84, "G", 11.5, L, _VILLA, 1),
    ("Banjara Hills Skypark",             "Banjara Hills", R, 198, 3100, 3, 4.2, 10, 9, 0.87, "G", 12.1, L, _APT,   0),
    ("Banjara Hills Avenue Offices",      "Banjara Hills", O, 248, 4100, 0, 6.8, 10, 9, 0.88, "G", 13.8, L, _OFFICE,4),
    ("Banjara Hills The Residency",       "Banjara Hills", R, 245, 3800, 4, 4.0, 10, 9, 0.86, "G", 12.5, L, _APT,   1),
    ("Banjara Hills Boulevard Towers",    "Banjara Hills", R, 178, 2750, 3, 4.2, 10, 9, 0.87, "G", 12.3, L, _APT,   2),

    # ── JUBILEE HILLS (7) ────────────────────────────────────────────────────
    ("Jubilee Hills Palatial Villas",     "Jubilee Hills", R, 525, 7200, 5, 3.5, 10, 9, 0.86, "G", 12.0, L, _VILLA, 2),
    ("Jubilee Hills High Rise",           "Jubilee Hills", R, 268, 4100, 4, 4.0, 10, 9, 0.86, "G", 12.5, L, _APT,   3),
    ("Jubilee Hills Grand Estates",       "Jubilee Hills", R, 385, 5200, 4, 3.4, 10, 9, 0.85, "G", 11.5, L, _VILLA, 3),
    ("Jubilee Hills Prestige Towers",     "Jubilee Hills", R, 198, 3100, 3, 4.1, 10, 9, 0.86, "G", 12.2, L, _APT,   4),
    ("Jubilee Hills Premium Apts",        "Jubilee Hills", R, 238, 3700, 4, 4.2, 10, 9, 0.87, "G", 12.8, L, _APT,   5),
    ("Jubilee Hills Business Centre",     "Jubilee Hills", C, 318, 5200, 0, 6.5, 10, 9, 0.86, "G", 13.2, L, _OFFICE,5),
    ("Jubilee Hills Signature Villas",    "Jubilee Hills", R, 485, 6600, 5, 3.4, 10, 9, 0.85, "G", 11.8, L, _VILLA, 0),

    # ── FINANCIAL DISTRICT (10) ──────────────────────────────────────────────
    ("Financial District Trophy Office",  "Financial District", O, 325, 5500, 0, 7.8, 10, 10, 0.96, "G", 15.5, L, _OFFICE,0),
    ("Financial District Towers A",       "Financial District", O, 282, 4750, 0, 7.5, 10, 10, 0.95, "G", 14.8, L, _OFFICE,1),
    ("Financial District Premium",        "Financial District", O, 248, 4200, 0, 7.3, 10, 10, 0.94, "G", 14.5, L, _OFFICE,2),
    ("Financial District Commerce",       "Financial District", C, 198, 3350, 0, 7.0, 10, 10, 0.94, "G", 14.2, L, _OFFICE,3),
    ("Financial District Residences",     "Financial District", R, 128, 2050, 3, 5.0, 10, 10, 0.93, "G", 13.8, L, _APT,   6),
    ("Financial District Business Park",  "Financial District", O, 355, 5900, 0, 8.0, 10, 10, 0.97, "G", 15.8, L, _OFFICE,4),
    ("Financial District Hub",            "Financial District", O, 228, 3800, 0, 7.2, 10, 10, 0.93, "G", 14.1, L, _OFFICE,5),
    ("Financial District Plaza",          "Financial District", C, 168, 2850, 0, 6.8, 10, 10, 0.92, "G", 13.5, L, _OFFICE,0),
    ("Financial District Skyview",        "Financial District", R, 148, 2350, 3, 5.2, 10, 10, 0.94, "G", 14.0, L, _APT,   7),
    ("Financial District Innovate Hub",   "Financial District", O, 295, 5000, 0, 7.6, 10, 10, 0.95, "G", 15.2, L, _OFFICE,1),

    # ── BEGUMPET (7) ─────────────────────────────────────────────────────────
    ("Begumpet Heritage Apartments",      "Begumpet", R, 86,  1460, 3, 3.9, 8, 8, 0.75, "S", 11.5, M, _APT,   8),
    ("Begumpet Business District",        "Begumpet", C, 148, 2500, 0, 6.2, 8, 8, 0.76, "S", 12.8, M, _OFFICE,2),
    ("Begumpet Classic Residences",       "Begumpet", R, 68,  1300, 2, 3.7, 8, 8, 0.74, "S", 10.8, M, _APT,   9),
    ("Begumpet Station Heights",          "Begumpet", R, 92,  1550, 3, 4.0, 8, 8, 0.75, "S", 11.8, M, _APT,   0),
    ("Begumpet Central Offices",          "Begumpet", O, 128, 2150, 0, 6.0, 8, 8, 0.75, "S", 12.5, M, _OFFICE,3),
    ("Begumpet Premium Apartments",       "Begumpet", R, 98,  1650, 3, 4.1, 8, 8, 0.76, "G", 12.0, M, _APT,   1),
    ("Begumpet Grand View",               "Begumpet", R, 74,  1350, 2, 3.8, 8, 8, 0.74, "S", 11.2, M, _APT,   2),

    # ── SECUNDERABAD (7) ─────────────────────────────────────────────────────
    ("Secunderabad Station View Apts",    "Secunderabad", R, 58,  1150, 2, 3.5, 7, 8, 0.72, "S", 10.2, M, _APT,   3),
    ("Secunderabad Business Hub",         "Secunderabad", C, 128, 2150, 0, 6.0, 7, 8, 0.73, "S", 12.5, M, _OFFICE,4),
    ("Secunderabad Classic Heights",      "Secunderabad", R, 72,  1380, 3, 3.8, 7, 8, 0.72, "S", 11.2, M, _APT,   4),
    ("Secunderabad Prime Residences",     "Secunderabad", R, 62,  1220, 2, 3.6, 7, 8, 0.72, "S", 10.5, M, _APT,   5),
    ("Secunderabad Park Lane",            "Secunderabad", R, 82,  1450, 3, 3.9, 7, 8, 0.73, "G", 11.8, M, _APT,   6),
    ("Secunderabad Cantonment Villas",    "Secunderabad", R, 188, 3100, 4, 3.3, 7, 8, 0.71, "S", 11.5, M, _VILLA, 1),
    ("Secunderabad IT Centre",            "Secunderabad", O, 148, 2500, 0, 6.2, 7, 8, 0.74, "G", 12.8, M, _OFFICE,5),

    # ── UPPAL (7) ────────────────────────────────────────────────────────────
    ("Uppal Metro Homes",                 "Uppal", R, 38,  810,  2, 2.9, 6, 7, 0.68, "G", 9.5,  M, _APT,   7),
    ("Uppal Township Residences",         "Uppal", R, 48,  1000, 3, 3.2, 6, 7, 0.70, "G", 10.2, M, _APT,   8),
    ("Uppal Industrial Commerce",         "Uppal", C, 88,  1500, 0, 5.5, 6, 7, 0.70, "G", 11.5, M, _OFFICE,0),
    ("Uppal Heights",                     "Uppal", R, 42,  900,  2, 3.0, 6, 7, 0.68, "G", 9.8,  M, _APT,   9),
    ("Uppal Green Towers",                "Uppal", R, 52,  1050, 3, 3.3, 6, 7, 0.69, "G", 10.5, M, _APT,   0),
    ("Uppal Smart City Apts",             "Uppal", R, 45,  950,  2, 3.1, 5, 7, 0.65, "G", 9.8,  H, _APT,   1),
    ("Uppal Trade Centre",                "Uppal", C, 72,  1230, 0, 5.2, 6, 7, 0.68, "S", 11.0, M, _OFFICE,1),

    # ── LB NAGAR (7) ─────────────────────────────────────────────────────────
    ("LB Nagar Junction Apartments",      "LB Nagar", R, 32,  720,  2, 2.7, 5, 6, 0.60, "S", 8.5,  H, _APT,   2),
    ("LB Nagar Hilltop Heights",          "LB Nagar", R, 45,  950,  3, 3.0, 5, 6, 0.62, "G", 9.8,  H, _APT,   3),
    ("LB Nagar Metro Station Apts",       "LB Nagar", R, 35,  760,  2, 2.8, 5, 6, 0.60, "S", 8.8,  H, _APT,   4),
    ("LB Nagar Commercial Centre",        "LB Nagar", C, 68,  1180, 0, 5.0, 5, 6, 0.63, "G", 10.5, M, _OFFICE,2),
    ("LB Nagar Meadow Residences",        "LB Nagar", R, 48,  1000, 3, 3.1, 5, 6, 0.62, "G", 9.5,  H, _APT,   5),
    ("LB Nagar Garden Enclave",           "LB Nagar", R, 38,  820,  2, 2.8, 5, 6, 0.60, "S", 8.8,  H, _APT,   6),
    ("LB Nagar Township",                 "LB Nagar", R, 52,  1080, 3, 3.2, 5, 6, 0.62, "G", 10.2, M, _APT,   7),

    # ── ATTAPUR (6) ──────────────────────────────────────────────────────────
    ("Attapur Lake View Heights",         "Attapur", R, 42,  900,  2, 3.0, 6, 6, 0.68, "G", 9.2,  M, _APT,   8),
    ("Attapur Hilltop Towers",            "Attapur", R, 56,  1130, 3, 3.4, 6, 6, 0.70, "G", 10.5, M, _APT,   9),
    ("Attapur Sunrise Residences",        "Attapur", R, 45,  950,  2, 3.1, 6, 6, 0.68, "G", 9.5,  M, _APT,   0),
    ("Attapur Green Park",                "Attapur", R, 58,  1180, 3, 3.4, 6, 6, 0.69, "G", 10.8, M, _APT,   1),
    ("Attapur Premium Villas",            "Attapur", R, 118, 2000, 4, 3.0, 6, 6, 0.67, "G", 11.2, M, _VILLA, 2),
    ("Attapur Smart Homes",               "Attapur", R, 48,  1000, 2, 3.2, 6, 6, 0.68, "G", 9.8,  M, _APT,   2),

    # ── KOMPALLY (7) ─────────────────────────────────────────────────────────
    ("Kompally Sunrise Township",         "Kompally", R, 42,  900,  2, 3.0, 6, 6, 0.70, "G", 9.5,  M, _APT,   3),
    ("Kompally North Heights",            "Kompally", R, 58,  1150, 3, 3.4, 6, 6, 0.72, "G", 10.8, M, _APT,   4),
    ("Kompally Green City",               "Kompally", R, 45,  950,  2, 3.1, 6, 6, 0.70, "G", 9.8,  M, _APT,   5),
    ("Kompally Grandeur Villas",          "Kompally", R, 115, 1980, 4, 2.9, 6, 6, 0.68, "G", 11.5, M, _VILLA, 3),
    ("Kompally Premium Heights",          "Kompally", R, 62,  1230, 3, 3.5, 6, 6, 0.72, "G", 11.0, M, _APT,   6),
    ("Kompally Garden Enclave",           "Kompally", R, 48,  1000, 2, 3.2, 6, 6, 0.70, "G", 10.2, M, _APT,   7),
    ("Kompally Smart City Towers",        "Kompally", R, 65,  1280, 3, 3.6, 6, 6, 0.73, "G", 11.2, M, _APT,   8),

    # ── SHAMSHABAD (7) ───────────────────────────────────────────────────────
    ("Shamshabad Airport Boulevard",      "Shamshabad", C, 96,  1650, 0, 6.0, 7, 7, 0.80, "G", 13.5, M, _OFFICE,3),
    ("Shamshabad IT Zone Offices",        "Shamshabad", O, 128, 2150, 0, 6.5, 7, 7, 0.82, "G", 13.8, M, _OFFICE,4),
    ("Shamshabad Township Apts",          "Shamshabad", R, 38,  820,  2, 2.9, 6, 7, 0.75, "G", 9.2,  M, _APT,   9),
    ("Shamshabad Metro Heights",          "Shamshabad", R, 52,  1050, 3, 3.3, 6, 7, 0.78, "G", 10.5, M, _APT,   0),
    ("Shamshabad Logistics Hub",          "Shamshabad", C, 148, 2500, 0, 6.8, 7, 7, 0.83, "G", 14.2, M, _OFFICE,5),
    ("Shamshabad Aeropolis Residences",   "Shamshabad", R, 42,  900,  2, 3.0, 6, 7, 0.76, "G", 9.5,  M, _APT,   1),
    ("Shamshabad Premium Homes",          "Shamshabad", R, 58,  1180, 3, 3.4, 6, 7, 0.78, "G", 10.8, M, _APT,   2),

    # ── BACHUPALLY (7) ───────────────────────────────────────────────────────
    ("Bachupally Meadow Enclave",         "Bachupally", R, 40,  870,  2, 2.9, 6, 6, 0.68, "G", 9.2,  M, _APT,   3),
    ("Bachupally North Heights",          "Bachupally", R, 56,  1120, 3, 3.3, 6, 6, 0.70, "G", 10.5, M, _APT,   4),
    ("Bachupally Township Residences",    "Bachupally", R, 44,  930,  2, 3.0, 6, 6, 0.68, "G", 9.5,  M, _APT,   5),
    ("Bachupally Green City Apts",        "Bachupally", R, 60,  1200, 3, 3.4, 6, 6, 0.70, "G", 10.8, M, _APT,   6),
    ("Bachupally Grandeur Villas",        "Bachupally", R, 108, 1870, 4, 2.8, 6, 6, 0.67, "G", 11.2, M, _VILLA, 0),
    ("Bachupally Smart Homes",            "Bachupally", R, 46,  970,  2, 3.1, 6, 6, 0.68, "G", 9.8,  M, _APT,   7),
    ("Bachupally Premier Towers",         "Bachupally", R, 62,  1250, 3, 3.5, 6, 6, 0.70, "G", 11.0, M, _APT,   8),
]

_AT_MAP = {"G": 0.80, "S": 0.55, "D": 0.30}


def write_sample_pdf(path: Path, title: str) -> None:
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 44>>stream\n"
        + f"BT /F1 12 Tf 10 100 Td ({title}) Tj ET".encode("utf-8")
        + b"\nendstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f \n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n300\n%%EOF"
    )
    path.write_bytes(content)


def main() -> None:
    db = get_database()
    uploads = Path("uploads")
    uploads.mkdir(exist_ok=True)

    # Delete in FK-safe order and reset sequences
    db.investment_transactions.delete_many({})
    db.share_listings.delete_many({})
    db.ownerships.delete_many({})
    db.documents.delete_many({})
    db.properties.delete_many({})
    db.users.delete_many({})
    db.counters.delete_many({})

    admin_id = get_next_sequence(db, "users")
    owner_id = get_next_sequence(db, "users")
    investor_id = get_next_sequence(db, "users")

    admin = {
        "_id": admin_id,
        "email": "admin@estatex.in",
        "full_name": "EstateX Hyderabad Admin",
        "hashed_password": hash_password("Admin@123"),
        "role": UserRole.ADMIN.value,
        "wallet_address": "0x000000000000000000000000000000000000dEaD",
        "wallet_balance": 0.0,
        "is_active": True,
        "created_at": utc_now(),
    }
    owner = {
        "_id": owner_id,
        "email": "owner@estatex.in",
        "full_name": "Priya Property Owner",
        "hashed_password": hash_password("Owner@123"),
        "role": UserRole.PROPERTY_OWNER.value,
        "wallet_address": "0x1111111111111111111111111111111111111111",
        "wallet_balance": 0.0,
        "is_active": True,
        "created_at": utc_now(),
    }
    investor = {
        "_id": investor_id,
        "email": "investor@estatex.in",
        "full_name": "Arjun Investor",
        "hashed_password": hash_password("Investor@123"),
        "role": UserRole.INVESTOR.value,
        "wallet_address": "0x2222222222222222222222222222222222222222",
        "wallet_balance": 0.0,
        "is_active": True,
        "created_at": utc_now(),
    }
    db.users.insert_many([admin, owner, investor])

    type_desc = {
        PropertyType.RESIDENTIAL: "Premium residential asset in {loc}, Hyderabad with high rental demand and strong appreciation potential.",
        PropertyType.COMMERCIAL:  "Grade-A commercial space in {loc}, Hyderabad — ideal for fractional investors seeking steady rental income.",
        PropertyType.OFFICE:      "Modern IT-grade office park in {loc}, Hyderabad offering institutional-quality returns with low vacancy.",
        PropertyType.RETAIL:      "High-footfall retail asset in {loc}, Hyderabad with long-term anchor tenant leases.",
    }

    approved_props: list[dict] = []

    for idx, row in enumerate(HYDERABAD_PROPERTIES):
        (title, locality, ptype, price_lakh, area_sqft, beds,
         rental_yield, loc_score, conn_score, infra_growth, at_code,
         roi, risk, img_pool, img_idx) = row

        price_inr     = price_lakh * 100_000
        total_shares  = max(100, int(price_inr / 1_000))
        demand_index  = round((loc_score + conn_score) / 20.0, 3)
        market_trend  = _AT_MAP.get(at_code, 0.55)

        property_id = get_next_sequence(db, "properties")
        prop = {
            "_id": property_id,
            "owner_id": owner_id,
            "title": title,
            "description": type_desc[ptype].format(loc=locality),
            "city": locality,
            "state": "Telangana",
            "location": f"{locality}, Hyderabad, Telangana",
            "property_type": ptype.value,
            "image_url": _img(img_pool, img_idx),
            "property_price": price_inr,
            "total_shares": total_shares,
            "available_shares": int(total_shares * 0.88),
            "price_per_share": 1_000.0,
            "rental_yield": rental_yield,
            "demand_index": demand_index,
            "market_trend": market_trend,
            "ai_predicted_roi": roi,
            "risk_level": risk.value,
            "listing_status": ListingStatus.APPROVED.value if idx < 148 else ListingStatus.PENDING.value,
            "is_verified": idx < 148,
            "rejection_reason": None,
            "contract_property_id": None,
            "created_at": utc_now(),
        }
        db.properties.insert_one(prop)

        if len(approved_props) < 15 and idx < 148:
            approved_props.append(prop)

        document_docs = []
        for doc_type in [
            DocumentType.SALE_DEED,
            DocumentType.ENCUMBRANCE_CERTIFICATE,
            DocumentType.PROPERTY_TAX_RECEIPT,
            DocumentType.IDENTITY_PROOF,
        ]:
            file_path = uploads / f"seed_{property_id}_{doc_type.value}.pdf"
            write_sample_pdf(file_path, f"{title} {doc_type.value}")
            document_docs.append(
                {
                    "_id": get_next_sequence(db, "documents"),
                    "property_id": property_id,
                    "document_type": doc_type.value,
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "sha256_hash": sha256_file(file_path),
                    "mime_type": "application/pdf",
                    "is_verified": idx < 148,
                    "verified_by_admin_id": admin_id if idx < 148 else None,
                    "created_at": utc_now(),
                }
            )
        if document_docs:
            db.documents.insert_many(document_docs)

    # ── Demo investment transactions (investor portfolio) ─────────────────────
    _demo_buys = [
        (approved_props[0],   50),   # 50 shares in property 1
        (approved_props[3],  100),   # 100 shares in property 4
        (approved_props[9],   30),   # 30 shares in property 10
        (approved_props[12],  20),   # 20 shares in property 13
        (approved_props[14],  15),   # 15 shares in property 15
    ]
    for prop, n_shares in _demo_buys:
        db.properties.update_one({"_id": prop["_id"]}, {"$inc": {"available_shares": -n_shares}})
        db.ownerships.insert_one(
            {
                "_id": get_next_sequence(db, "ownerships"),
                "property_id": prop["_id"],
                "investor_id": investor_id,
                "shares": n_shares,
                "updated_at": utc_now(),
            }
        )
        db.investment_transactions.insert_one(
            {
                "_id": get_next_sequence(db, "investment_transactions"),
                "property_id": prop["_id"],
                "buyer_id": investor_id,
                "seller_id": owner_id,
                "shares": n_shares,
                "amount": float(prop["price_per_share"]) * n_shares,
                "tx_type": TransactionType.PRIMARY_BUY.value,
                "onchain_tx_hash": f"0x{'0' * 40}{prop['_id']:06x}",
                "created_at": utc_now(),
            }
        )

    # ── Secondary market listings (liquidity demo) ────────────────────────────
    db.share_listings.insert_many(
        [
            {
                "_id": get_next_sequence(db, "share_listings"),
                "property_id": approved_props[0]["_id"],
                "seller_id": investor_id,
                "shares_for_sale": 10,
                "price_per_share": 1_100.0,
                "is_active": True,
                "created_at": utc_now(),
            },
            {
                "_id": get_next_sequence(db, "share_listings"),
                "property_id": approved_props[3]["_id"],
                "seller_id": investor_id,
                "shares_for_sale": 20,
                "price_per_share": 1_050.0,
                "is_active": True,
                "created_at": utc_now(),
            },
        ]
    )
    print(
        f"✓ Seeded {len(HYDERABAD_PROPERTIES)} Hyderabad properties, "
        f"{len(_demo_buys)} investor holdings, 2 secondary listings across 20 localities."
    )


if __name__ == "__main__":
    main()

