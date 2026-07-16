"""
Pharma Analytics - Realistic Data Regeneration Script
=====================================================
Regenerates all 6 CSV datasets with realistic Indian pharmaceutical market behavior.
Preserves exact schema, column names, data types, IDs, and relationships.
"""
import os
import sys
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

np.random.seed(42)
random.seed(42)

OUTPUT_DIR = "data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# REFERENCE DATA - Indian Pharma Market
# ============================================================================

DRUG_CATALOG = {
    # drug_name: (therapeutic_class, base_price_inr, price_std, monthly_base_demand)
    "Lipitor":    ("Cardiovascular",    350,   80,  180),
    "Crestor":    ("Cardiovascular",    420,   90,  150),
    "Januvia":    ("Diabetes",          580,  120,  160),
    "Lantus":     ("Diabetes",          950,  180,  120),
    "Advair":     ("Respiratory",       680,  140,  110),
    "Nexium":     ("Gastroenterology",  280,   60,  200),
    "Humira":     ("Immunology",       3200,  500,   45),
    "Enbrel":     ("Immunology",       2800,  450,   50),
    "Remicade":   ("Immunology",       2500,  400,   55),
    "Copaxone":   ("Neurology",        1200,  250,   70),
    "Lyrica":     ("Neurology",         450,  100,   140),
    "Tecfidera":  ("Neurology",        1800,  350,   60),
    "Keytruda":   ("Oncology",         8500, 1500,   25),
    "Opdivo":     ("Oncology",         7200, 1200,   28),
    "Herceptin":  ("Oncology",         6500, 1100,   30),
    "Avastin":    ("Oncology",         5800, 1000,   32),
    "Gleevec":    ("Oncology",         4500,  800,   35),
    "Rituxan":    ("Oncology",         5200,  900,   33),
    "Revlimid":   ("Oncology",         6800, 1100,   27),
    "Neulasta":   ("Oncology",         3800,  700,   40),
}

TERRITORY_DATA = [
    ("TER-01", "Maharashtra",      "West",    "Maharashtra",                                3, 36, 12500000),
    ("TER-02", "Delhi",            "North",   "Delhi, Haryana",                              3, 31, 11000000),
    ("TER-03", "Karnataka",        "South",   "Karnataka",                                   3, 33,  9800000),
    ("TER-04", "Tamil Nadu",       "South",   "Tamil Nadu",                                  3, 29,  9500000),
    ("TER-05", "Gujarat",          "West",    "Gujarat",                                     2, 27,  8200000),
    ("TER-06", "Telangana",        "South",   "Telangana",                                   3, 14,  6500000),
    ("TER-07", "West Bengal",      "East",    "West Bengal",                                 2, 20,  7000000),
    ("TER-08", "Rajasthan",        "North",   "Rajasthan",                                   2, 28,  6800000),
    ("TER-09", "Punjab",           "North",   "Punjab",                                      3, 23,  6200000),
    ("TER-10", "Kerala",           "South",   "Kerala",                                      2, 32,  7500000),
    ("TER-11", "Uttar Pradesh",    "North",   "Uttar Pradesh",                               2, 22,  7800000),
    ("TER-12", "Haryana",          "North",   "Haryana",                                     2, 21,  5500000),
    ("TER-13", "Madhya Pradesh",   "Central", "Madhya Pradesh",                              2, 26,  5800000),
    ("TER-14", "Bihar",            "East",    "Bihar",                                       3, 24,  5000000),
    ("TER-15", "Odisha",           "East",    "Odisha",                                      2, 29,  4800000),
    ("TER-16", "Andhra Pradesh",   "South",   "Andhra Pradesh",                              3, 20,  6000000),
    ("TER-17", "Chhattisgarh",     "Central", "Chhattisgarh",                                3, 19,  4200000),
    ("TER-18", "Jharkhand",        "East",    "Jharkhand",                                   2, 23,  4500000),
    ("TER-19", "Assam",            "East",    "Assam",                                       2, 22,  3800000),
    ("TER-20", "Uttarakhand",      "North",   "Uttarakhand",                                 3, 21,  4000000),
]

INDIAN_FIRST_NAMES_M = [
    "Rajesh", "Suresh", "Amit", "Vikram", "Sanjay", "Arun", "Deepak", "Manoj",
    "Rohit", "Ashok", "Nikhil", "Anand", "Vivek", "Rahul", "Pranav", "Gaurav",
    "Kiran", "Siddharth", "Harsh", "Ajay", "Ravi", "Naveen", "Pradeep", "Sameer",
    "Arjun", "Mohan", "Gopal", "Tarun", "Vinay", "Sachin", "Pankaj", "Mukesh",
    "Ramesh", "Sunil", "Vijay", "Kamal", "Dhruv", "Aniket", "Varun", "Nitin",
    "Hemant", "Yogesh", "Manish", "Dinesh", "Raghav", "Dev", "Shyam", "Akash",
    "Tushar", "Vishal", "Kapil", "Sandeep", "Nilesh", "Jatin", "Kunal", "Lalit",
]

INDIAN_FIRST_NAMES_F = [
    "Priya", "Anita", "Sunita", "Kavita", "Neha", "Pooja", "Meera", "Rekha",
    "Deepa", "Shalini", "Anjali", "Swati", "Nisha", "Ritu", "Seema", "Archana",
    "Divya", "Sneha", "Shweta", "Preeti", "Aarti", "Jyoti", "Pallavi", "Rashmi",
    "Smita", "Geeta", "Komal", "Shruti", "Tanvi", "Varsha", "Madhuri", "Sapna",
    "Aparna", "Bhavna", "Chitra", "Devi", "Ekta", "Heena", "Isha", "Kalpana",
    "Lakshmi", "Mamta", "Nandini", "Padma", "Radha", "Sarita", "Usha", "Vandana",
]

INDIAN_LAST_NAMES = [
    "Sharma", "Patel", "Gupta", "Singh", "Kumar", "Reddy", "Nair", "Iyer",
    "Verma", "Joshi", "Agarwal", "Mehta", "Rao", "Pillai", "Banerjee", "Das",
    "Mishra", "Chauhan", "Yadav", "Bhat", "Kulkarni", "Deshmukh", "Shetty",
    "Menon", "Tiwari", "Dubey", "Pandey", "Saxena", "Malhotra", "Kapoor",
    "Chopra", "Bose", "Mukherjee", "Chatterjee", "Sen", "Roy", "Ghosh",
    "Patil", "Deshpande", "Jain", "Shah", "Thakur", "Rajan", "Krishnan",
    "Subramaniam", "Venkatesh", "Narayan", "Prasad", "Srivastava", "Khanna",
]

INDIAN_CITIES = {
    "Maharashtra":      ["Mumbai", "Pune", "Nagpur", "Nashik", "Thane"],
    "Delhi":            ["New Delhi", "Dwarka", "Rohini", "Saket", "Noida"],
    "Karnataka":        ["Bengaluru", "Mysuru", "Hubli", "Mangaluru", "Belgaum"],
    "Tamil Nadu":       ["Chennai", "Coimbatore", "Madurai", "Salem", "Trichy"],
    "Gujarat":          ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar"],
    "Telangana":        ["Hyderabad", "Secunderabad", "Warangal"],
    "West Bengal":      ["Kolkata", "Howrah", "Durgapur", "Siliguri"],
    "Rajasthan":        ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer"],
    "Punjab":           ["Chandigarh", "Ludhiana", "Amritsar", "Jalandhar"],
    "Kerala":           ["Kochi", "Thiruvananthapuram", "Kozhikode", "Thrissur", "Kannur"],
    "Uttar Pradesh":    ["Lucknow", "Varanasi", "Kanpur", "Agra", "Allahabad"],
    "Haryana":          ["Gurugram", "Faridabad", "Karnal", "Panipat"],
    "Madhya Pradesh":   ["Bhopal", "Indore", "Gwalior", "Jabalpur"],
    "Bihar":            ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur"],
    "Odisha":           ["Bhubaneswar", "Cuttack", "Rourkela", "Puri"],
    "Andhra Pradesh":   ["Visakhapatnam", "Vijayawada", "Tirupati", "Guntur"],
    "Chhattisgarh":     ["Raipur", "Bhilai", "Bilaspur", "Korba"],
    "Jharkhand":        ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro"],
    "Assam":            ["Guwahati", "Dibrugarh", "Silchar", "Jorhat"],
    "Uttarakhand":      ["Dehradun", "Haridwar", "Rishikesh", "Haldwani"],
}

HOSPITAL_PREFIXES = [
    "Apollo", "Fortis", "Max", "Medanta", "Manipal", "Narayana", "KIMS",
    "Columbia Asia", "Aster", "Lilavati", "Hinduja", "Kokilaben", "Wockhardt",
    "Breach Candy", "Ruby Hall", "Sterling", "Sagar", "Global", "Metro",
    "City", "Care", "Star", "Rainbow", "Sunshine", "Continental",
]

HOSPITAL_SUFFIXES = [
    "Hospital", "Medical Centre", "Multispecialty Hospital", "Clinic",
    "Healthcare", "Institute of Medical Sciences", "Super Specialty Hospital",
]

SPECIALTIES = [
    "Cardiology", "Dermatology", "Endocrinology", "Gastroenterology",
    "Nephrology", "Neurology", "Oncology", "Psychiatry", "Pulmonology", "Rheumatology",
]

# Specialty-drug affinity: which specialties are more likely to prescribe which therapeutic classes
SPECIALTY_DRUG_AFFINITY = {
    "Cardiology":        {"Cardiovascular": 0.55, "Diabetes": 0.20, "Gastroenterology": 0.05, "Immunology": 0.02, "Neurology": 0.05, "Oncology": 0.03, "Respiratory": 0.10},
    "Dermatology":       {"Cardiovascular": 0.05, "Diabetes": 0.05, "Gastroenterology": 0.05, "Immunology": 0.40, "Neurology": 0.10, "Oncology": 0.05, "Respiratory": 0.30},
    "Endocrinology":     {"Cardiovascular": 0.20, "Diabetes": 0.50, "Gastroenterology": 0.05, "Immunology": 0.05, "Neurology": 0.05, "Oncology": 0.05, "Respiratory": 0.10},
    "Gastroenterology":  {"Cardiovascular": 0.05, "Diabetes": 0.05, "Gastroenterology": 0.50, "Immunology": 0.15, "Neurology": 0.05, "Oncology": 0.10, "Respiratory": 0.10},
    "Nephrology":        {"Cardiovascular": 0.25, "Diabetes": 0.25, "Gastroenterology": 0.05, "Immunology": 0.15, "Neurology": 0.05, "Oncology": 0.05, "Respiratory": 0.20},
    "Neurology":         {"Cardiovascular": 0.05, "Diabetes": 0.05, "Gastroenterology": 0.05, "Immunology": 0.05, "Neurology": 0.60, "Oncology": 0.05, "Respiratory": 0.15},
    "Oncology":          {"Cardiovascular": 0.03, "Diabetes": 0.02, "Gastroenterology": 0.05, "Immunology": 0.10, "Neurology": 0.05, "Oncology": 0.65, "Respiratory": 0.10},
    "Psychiatry":        {"Cardiovascular": 0.10, "Diabetes": 0.10, "Gastroenterology": 0.05, "Immunology": 0.05, "Neurology": 0.45, "Oncology": 0.05, "Respiratory": 0.20},
    "Pulmonology":       {"Cardiovascular": 0.10, "Diabetes": 0.05, "Gastroenterology": 0.05, "Immunology": 0.10, "Neurology": 0.05, "Oncology": 0.10, "Respiratory": 0.55},
    "Rheumatology":      {"Cardiovascular": 0.05, "Diabetes": 0.05, "Gastroenterology": 0.05, "Immunology": 0.50, "Neurology": 0.10, "Oncology": 0.05, "Respiratory": 0.20},
}

REP_NAMES = [
    "Rajesh Sharma", "Priya Patel", "Amit Kumar", "Neha Gupta", "Vikram Singh",
    "Sunita Reddy", "Sanjay Verma", "Kavita Nair", "Deepak Joshi", "Anjali Mehta",
    "Arun Rao", "Pooja Iyer", "Rohit Banerjee", "Meera Das", "Nikhil Mishra",
    "Swati Chauhan", "Anand Yadav", "Divya Bhat", "Vivek Kulkarni", "Sneha Deshmukh",
    "Rahul Shetty", "Shreya Menon", "Pranav Tiwari", "Komal Dubey", "Gaurav Pandey",
    "Shruti Saxena", "Kiran Malhotra", "Pallavi Kapoor", "Siddharth Chopra", "Rashmi Bose",
    "Harsh Mukherjee", "Aparna Chatterjee", "Ajay Sen", "Varsha Roy", "Ravi Ghosh",
    "Tanvi Patil", "Naveen Deshpande", "Smita Jain", "Pradeep Shah", "Bhavna Thakur",
    "Sameer Rajan", "Chitra Krishnan", "Arjun Subramaniam", "Heena Venkatesh", "Mohan Narayan",
    "Isha Prasad", "Gopal Srivastava", "Kalpana Khanna", "Tarun Agarwal", "Lakshmi Pillai",
]

# ============================================================================
# 1. GENERATE territory_mapping.csv
# ============================================================================
def generate_territories():
    print("[1/6] Generating territory_mapping.csv...")
    rows = []
    for tid, tname, region, state_cov, rep_count, hcp_count, quota in TERRITORY_DATA:
        rows.append({
            "territory_id": tid,
            "territory_name": tname,
            "region": region,
            "state_coverage": state_cov,
            "assigned_rep_count": rep_count,
            "target_hcp_count": hcp_count,
            "annual_quota": round(quota + np.random.uniform(-500000, 500000), 2),
        })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "territory_mapping.csv"), index=False)
    print(f"  -> {len(df)} territories generated.")
    return df


# ============================================================================
# 2. GENERATE hcp_master.csv
# ============================================================================
def generate_hcps(territories_df):
    print("[2/6] Generating hcp_master.csv...")
    rows = []
    hcp_id = 1
    
    # Distribute HCPs across territories according to target counts
    for _, terr in territories_df.iterrows():
        tid = terr["territory_id"]
        tname = terr["territory_name"]
        n_hcps = terr["target_hcp_count"]
        
        cities = INDIAN_CITIES.get(tname, ["Unknown City"])
        
        for _ in range(n_hcps):
            is_female = random.random() < 0.35
            if is_female:
                first = random.choice(INDIAN_FIRST_NAMES_F)
            else:
                first = random.choice(INDIAN_FIRST_NAMES_M)
            last = random.choice(INDIAN_LAST_NAMES)
            
            # Tier distribution: 10% Tier 1, 30% Tier 2, 60% Tier 3
            tier_roll = random.random()
            if tier_roll < 0.10:
                tier = "Tier 1"
            elif tier_roll < 0.40:
                tier = "Tier 2"
            else:
                tier = "Tier 3"
            
            specialty = random.choice(SPECIALTIES)
            city = random.choice(cities)
            
            # Years experience: Tier 1 -> more experienced
            if tier == "Tier 1":
                yrs = random.randint(15, 40)
            elif tier == "Tier 2":
                yrs = random.randint(8, 30)
            else:
                yrs = random.randint(2, 20)
            
            hosp_prefix = random.choice(HOSPITAL_PREFIXES)
            hosp_suffix = random.choice(HOSPITAL_SUFFIXES)
            hospital = f"{hosp_prefix} {hosp_suffix}"
            
            # MCI registration number format
            npi = random.randint(1000000000, 9999999999)
            
            rows.append({
                "hcp_id": f"HCP-{hcp_id:04d}",
                "first_name": first,
                "last_name": last,
                "specialty": specialty,
                "tier": tier,
                "years_experience": yrs,
                "hospital_affiliation": hospital,
                "city": city,
                "state": tname,
                "territory_id": tid,
                "npi_number": npi,
            })
            hcp_id += 1
    
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "hcp_master.csv"), index=False)
    print(f"  -> {len(df)} HCPs generated.")
    return df


# ============================================================================
# 3. GENERATE pharma_sales.csv
# ============================================================================
def generate_sales(territories_df):
    print("[3/6] Generating pharma_sales.csv...")
    
    # Date range: Jan 2024 to Dec 2025
    start = datetime(2024, 1, 1)
    end = datetime(2025, 12, 31)
    
    # Generate all dates in range
    all_dates = pd.date_range(start, end, freq="D")
    
    # Territory demand multipliers (based on market size)
    terr_multipliers = {}
    for _, t in territories_df.iterrows():
        quota = t["annual_quota"]
        # Normalize around 1.0
        terr_multipliers[t["territory_id"]] = 0.5 + (quota / 12500000) * 0.8
    
    rows = []
    
    for drug_name, (ther_class, base_price, price_std, base_demand) in DRUG_CATALOG.items():
        for _, terr in territories_df.iterrows():
            tid = terr["territory_id"]
            t_mult = terr_multipliers[tid]
            
            # Generate monthly aggregated data, then distribute across days
            months = pd.date_range(start, end, freq="MS")
            
            for month_start in months:
                month_num = month_start.month
                year = month_start.year
                
                # Seasonal multiplier (Indian pharma patterns)
                seasonal = 1.0
                if month_num in [1, 2]:      # Post-new-year, new budgets
                    seasonal = 1.10 + np.random.uniform(-0.05, 0.05)
                elif month_num == 3:          # Financial year end (Q4 push)
                    seasonal = 1.25 + np.random.uniform(-0.05, 0.10)
                elif month_num in [4, 5]:     # New fiscal year start
                    seasonal = 1.05 + np.random.uniform(-0.05, 0.05)
                elif month_num == 6:          # Q1 end push
                    seasonal = 1.15 + np.random.uniform(-0.05, 0.05)
                elif month_num in [7, 8]:     # Monsoon slowdown
                    seasonal = 0.85 + np.random.uniform(-0.05, 0.05)
                elif month_num == 9:          # Q2 end push
                    seasonal = 1.12 + np.random.uniform(-0.05, 0.05)
                elif month_num in [10, 11]:   # Festival season boost
                    seasonal = 1.08 + np.random.uniform(-0.05, 0.05)
                elif month_num == 12:         # Year-end, Q3 push
                    seasonal = 1.18 + np.random.uniform(-0.05, 0.08)
                
                # Year-over-year growth (non-linear)
                yoy_growth = 1.0
                if year == 2025:
                    yoy_growth = 1.06 + np.random.uniform(-0.03, 0.05)
                
                # Monthly noise (increased to make forecasting more realistic/difficult)
                noise = np.random.uniform(0.65, 1.35)
                
                # Calculate monthly demand for this drug-territory
                monthly_demand = int(base_demand * t_mult * seasonal * yoy_growth * noise)
                monthly_demand = max(monthly_demand, 1)
                
                # Distribute across random days in the month
                month_end = (month_start + pd.offsets.MonthEnd(0)).date()
                month_days = pd.date_range(month_start, month_end, freq="D")
                month_days = [d for d in month_days if d <= end]
                
                if not month_days:
                    continue
                
                # 1-4 transactions per drug-territory-month (restores ~24k row count)
                n_transactions = random.randint(1, 4)
                
                # Distribute demand across transactions
                if n_transactions > 1:
                    splits = np.random.dirichlet(np.ones(n_transactions)) * monthly_demand
                    splits = np.maximum(splits.astype(int), 1)
                else:
                    splits = [monthly_demand]
                
                for units in splits:
                    sale_date = random.choice(month_days).strftime("%Y-%m-%d")
                    # Price with realistic variation
                    unit_price = round(max(base_price + np.random.normal(0, price_std * 0.3), base_price * 0.6), 2)
                    revenue = round(units * unit_price, 2)
                    
                    rows.append({
                        "sale_date": sale_date,
                        "drug_name": drug_name,
                        "territory_id": tid,
                        "units_sold": int(units),
                        "unit_price": unit_price,
                        "revenue": revenue,
                    })
    
    df = pd.DataFrame(rows)
    df = df.sort_values("sale_date").reset_index(drop=True)
    print(f"  -> {len(df)} sales records generated.")
    df.to_csv(os.path.join(OUTPUT_DIR, "pharma_sales.csv"), index=False)
    return df


# ============================================================================
# 4. GENERATE prescription_data.csv
# ============================================================================
def generate_prescriptions(hcp_df):
    print("[4/6] Generating prescription_data.csv...")
    
    # Date range: Jan 2024 to Dec 2025
    start = datetime(2024, 1, 1)
    end = datetime(2025, 12, 28)
    all_dates = pd.date_range(start, end, freq="D")
    
    # Build drug lists by therapeutic class
    drugs_by_class = {}
    for drug, (tc, _, _, _) in DRUG_CATALOG.items():
        drugs_by_class.setdefault(tc, []).append(drug)
    
    rows = []
    rx_id = 1
    target_count = 15000
    
    # Assign prescription counts based on tier
    # Tier 1: 50-80 prescriptions, Tier 2: 25-45, Tier 3: 8-20
    hcp_rx_counts = {}
    for _, hcp in hcp_df.iterrows():
        hid = hcp["hcp_id"]
        tier = hcp["tier"]
        if tier == "Tier 1":
            hcp_rx_counts[hid] = random.randint(50, 80)
        elif tier == "Tier 2":
            hcp_rx_counts[hid] = random.randint(25, 45)
        else:
            hcp_rx_counts[hid] = random.randint(8, 20)
    
    # Scale to hit target
    total_planned = sum(hcp_rx_counts.values())
    scale = target_count / total_planned
    for hid in hcp_rx_counts:
        hcp_rx_counts[hid] = max(1, int(hcp_rx_counts[hid] * scale))
    
    # Adjust to get exactly 15000
    current_total = sum(hcp_rx_counts.values())
    diff = target_count - current_total
    hcp_ids_list = list(hcp_rx_counts.keys())
    while diff > 0:
        hid = random.choice(hcp_ids_list)
        hcp_rx_counts[hid] += 1
        diff -= 1
    while diff < 0:
        hid = random.choice(hcp_ids_list)
        if hcp_rx_counts[hid] > 1:
            hcp_rx_counts[hid] -= 1
            diff += 1
    
    for _, hcp in hcp_df.iterrows():
        hid = hcp["hcp_id"]
        specialty = hcp["specialty"]
        n_rx = hcp_rx_counts[hid]
        
        # Get drug affinity for this specialty
        affinity = SPECIALTY_DRUG_AFFINITY.get(specialty, {})
        
        for _ in range(n_rx):
            # Pick therapeutic class based on specialty affinity
            classes = list(affinity.keys())
            weights = list(affinity.values())
            chosen_class = random.choices(classes, weights=weights, k=1)[0]
            
            # Pick a drug from that class
            available_drugs = drugs_by_class.get(chosen_class, list(DRUG_CATALOG.keys()))
            drug_name = random.choice(available_drugs)
            ther_class = DRUG_CATALOG[drug_name][0]
            base_price = DRUG_CATALOG[drug_name][1]
            price_std = DRUG_CATALOG[drug_name][2]
            
            rx_date = random.choice(all_dates).strftime("%Y-%m-%d")
            quantity = random.randint(5, 180)
            
            # Tier 1 HCPs tend to prescribe higher quantities
            if hcp["tier"] == "Tier 1":
                quantity = random.randint(30, 250)
            elif hcp["tier"] == "Tier 2":
                quantity = random.randint(15, 150)
            
            unit_price = round(max(base_price + np.random.normal(0, price_std * 0.3), base_price * 0.5), 2)
            total_value = round(quantity * unit_price, 2)
            
            rows.append({
                "prescription_id": f"RX-{rx_id:06d}",
                "hcp_id": hid,
                "drug_name": drug_name,
                "therapeutic_class": ther_class,
                "prescription_date": rx_date,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_value": total_value,
            })
            rx_id += 1
    
    df = pd.DataFrame(rows)
    df = df.sort_values("prescription_date").reset_index(drop=True)
    print(f"  -> {len(df)} prescriptions generated.")
    df.to_csv(os.path.join(OUTPUT_DIR, "prescription_data.csv"), index=False)
    return df


# ============================================================================
# 5. GENERATE rep_activity.csv
# ============================================================================
def generate_rep_activity(territories_df, hcp_df):
    print("[5/6] Generating rep_activity.csv...")
    
    # Date range: Jan 2024 to Dec 2025
    start = datetime(2024, 1, 1)
    end = datetime(2025, 12, 28)
    all_dates = pd.date_range(start, end, freq="D")
    # Remove Sundays
    work_dates = [d for d in all_dates if d.dayofweek < 6]
    
    # Assign reps to territories
    rep_assignments = []
    rep_id = 1
    for _, terr in territories_df.iterrows():
        tid = terr["territory_id"]
        n_reps = terr["assigned_rep_count"]
        for _ in range(n_reps):
            rep_name = REP_NAMES[rep_id - 1] if rep_id <= len(REP_NAMES) else f"Rep {rep_id}"
            rep_assignments.append({
                "rep_id": f"REP-{rep_id:03d}",
                "rep_name": rep_name,
                "territory_id": tid,
            })
            rep_id += 1
    
    # Performance tiers for reps
    n_reps = len(rep_assignments)
    perf_order = list(range(n_reps))
    random.shuffle(perf_order)
    
    top_reps = set(perf_order[:10])       # Top performers
    mid_reps = set(perf_order[10:40])      # Average
    bottom_reps = set(perf_order[40:])     # Underperformers
    
    activity_types = ["Visit", "Phone Call", "Sample Drop", "Virtual Meeting", "Conference"]
    activity_weights_top = [0.38, 0.25, 0.18, 0.12, 0.07]
    activity_weights_mid = [0.32, 0.28, 0.15, 0.15, 0.10]
    activity_weights_bot = [0.25, 0.30, 0.12, 0.18, 0.15]
    
    outcomes = ["Positive", "Neutral", "Follow-up Required", "No Show", "Declined Meeting"]
    outcome_weights_top = [0.58, 0.22, 0.12, 0.05, 0.03]
    outcome_weights_mid = [0.42, 0.28, 0.15, 0.10, 0.05]
    outcome_weights_bot = [0.28, 0.25, 0.15, 0.18, 0.14]
    
    rows = []
    
    for idx, rep in enumerate(rep_assignments):
        rid = rep["rep_id"]
        rname = rep["rep_name"]
        tid = rep["territory_id"]
        
        # Get HCPs in this territory
        territory_hcps = hcp_df[hcp_df["territory_id"] == tid]["hcp_id"].tolist()
        
        if idx in top_reps:
            n_activities = random.randint(350, 450)
            coverage_pct = random.uniform(0.70, 0.85)
            act_weights = activity_weights_top
            out_weights = outcome_weights_top
            dur_range = (25, 75)
            sample_range = (0, 15)
        elif idx in bottom_reps:
            n_activities = random.randint(80, 190)
            coverage_pct = random.uniform(0.20, 0.40)
            act_weights = activity_weights_bot
            out_weights = outcome_weights_bot
            dur_range = (10, 50)
            sample_range = (0, 8)
        else:
            n_activities = random.randint(200, 340)
            coverage_pct = random.uniform(0.45, 0.65)
            act_weights = activity_weights_mid
            out_weights = outcome_weights_mid
            dur_range = (15, 60)
            sample_range = (0, 12)
        
        # Select HCPs this rep will cover
        n_covered = max(1, int(len(territory_hcps) * coverage_pct))
        covered_hcps = random.sample(territory_hcps, min(n_covered, len(territory_hcps)))
        
        # Tier 1 HCPs get more visits
        tier1_hcps = hcp_df[(hcp_df["hcp_id"].isin(covered_hcps)) & (hcp_df["tier"] == "Tier 1")]["hcp_id"].tolist()
        tier2_hcps = hcp_df[(hcp_df["hcp_id"].isin(covered_hcps)) & (hcp_df["tier"] == "Tier 2")]["hcp_id"].tolist()
        tier3_hcps = hcp_df[(hcp_df["hcp_id"].isin(covered_hcps)) & (hcp_df["tier"] == "Tier 3")]["hcp_id"].tolist()
        
        for _ in range(n_activities):
            # Weighted HCP selection: Tier 1 gets 3x, Tier 2 gets 2x
            hcp_pool = tier1_hcps * 3 + tier2_hcps * 2 + tier3_hcps
            if not hcp_pool:
                hcp_pool = covered_hcps
            hcp_id = random.choice(hcp_pool)
            
            act_type = random.choices(activity_types, weights=act_weights, k=1)[0]
            outcome = random.choices(outcomes, weights=out_weights, k=1)[0]
            act_date = random.choice(work_dates).strftime("%Y-%m-%d")
            duration = random.randint(*dur_range)
            
            samples = 0
            if act_type in ["Visit", "Sample Drop"]:
                samples = random.randint(*sample_range)
            
            rows.append({
                "rep_id": rid,
                "rep_name": rname,
                "territory_id": tid,
                "hcp_id": hcp_id,
                "activity_type": act_type,
                "activity_date": act_date,
                "duration_minutes": duration,
                "samples_left": samples,
                "outcome": outcome,
            })
    
    df = pd.DataFrame(rows)
    df = df.sort_values("activity_date").reset_index(drop=True)
    print(f"  -> {len(df)} rep activities generated ({len(rep_assignments)} reps).")
    df.to_csv(os.path.join(OUTPUT_DIR, "rep_activity.csv"), index=False)
    return df


# ============================================================================
# 6. GENERATE promotion_campaigns.csv
# ============================================================================
def generate_promotions():
    print("[6/6] Generating promotion_campaigns.csv...")
    
    channels = ["Email", "Rep Visit", "Conference", "Digital", "Journal Ad"]
    drugs = ["Keytruda", "Humira", "Lipitor", "Januvia", "Advair",
             "Nexium", "Enbrel", "Lyrica", "Herceptin", "Crestor",
             "Opdivo", "Lantus", "Copaxone", "Remicade", "Avastin"]
    
    # Campaign outcomes: 3 great, 5 moderate, 4 neutral, 3 failed
    outcome_profiles = [
        # (rx_lift_factor, revenue_lift_factor, reach_pct) 
        # Great
        (1.45, 1.55, 0.88), (1.38, 1.42, 0.82), (1.52, 1.60, 0.91),
        # Moderate  
        (1.18, 1.22, 0.72), (1.12, 1.15, 0.68), (1.25, 1.28, 0.75),
        (1.15, 1.18, 0.70), (1.20, 1.25, 0.73),
        # Neutral
        (1.02, 1.05, 0.55), (0.98, 1.01, 0.50), (1.05, 1.08, 0.58), (0.95, 0.98, 0.48),
        # Failed
        (0.82, 0.78, 0.35), (0.88, 0.85, 0.40), (0.75, 0.72, 0.30),
    ]
    random.shuffle(outcome_profiles)
    
    rows = []
    # Spread campaigns across 2024-2025
    base_dates = [
        "2024-01-15", "2024-02-20", "2024-04-01", "2024-05-15", "2024-07-01",
        "2024-08-15", "2024-10-01", "2024-11-15", "2025-01-10", "2025-02-20",
        "2025-04-01", "2025-05-15", "2025-07-01", "2025-08-15", "2025-10-01",
    ]
    
    for i in range(15):
        drug = drugs[i]
        channel = channels[i % len(channels)]
        rx_lift, rev_lift, reach_pct = outcome_profiles[i]
        
        start_date = base_dates[i]
        # Campaign duration: 45-120 days
        duration = random.randint(45, 120)
        end_date = (pd.to_datetime(start_date) + timedelta(days=duration)).strftime("%Y-%m-%d")
        
        budget = round(random.uniform(150000, 500000), 2)
        hcps_targeted = random.randint(80, 250)
        hcps_reached = max(10, int(hcps_targeted * reach_pct))
        
        rx_before = random.randint(400, 1200)
        rx_after = max(100, int(rx_before * rx_lift))
        
        rev_before = round(rx_before * random.uniform(800, 3500), 2)
        rev_after = round(rev_before * rev_lift, 2)
        
        campaign_name = f"{channel} Campaign - {drug}"
        
        rows.append({
            "campaign_id": f"CAMP-{i+1:03d}",
            "campaign_name": campaign_name,
            "drug_name": drug,
            "channel": channel,
            "start_date": start_date,
            "end_date": end_date,
            "budget": budget,
            "hcps_targeted": hcps_targeted,
            "hcps_reached": hcps_reached,
            "prescriptions_before": rx_before,
            "prescriptions_after": rx_after,
            "revenue_before": rev_before,
            "revenue_after": rev_after,
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "promotion_campaigns.csv"), index=False)
    print(f"  -> {len(df)} campaigns generated.")
    return df


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("=" * 60)
    print("  PHARMA DATA REGENERATION - Indian Market Realistic Data")
    print("=" * 60)
    
    territories = generate_territories()
    hcps = generate_hcps(territories)
    sales = generate_sales(territories)
    prescriptions = generate_prescriptions(hcps)
    rep_activity = generate_rep_activity(territories, hcps)
    promotions = generate_promotions()
    
    print("\n" + "=" * 60)
    print("  ALL 6 DATASETS REGENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"  territory_mapping.csv:    {len(territories):>8,} rows")
    print(f"  hcp_master.csv:           {len(hcps):>8,} rows")
    print(f"  pharma_sales.csv:         {len(sales):>8,} rows")
    print(f"  prescription_data.csv:    {len(prescriptions):>8,} rows")
    print(f"  rep_activity.csv:         {len(rep_activity):>8,} rows")
    print(f"  promotion_campaigns.csv:  {len(promotions):>8,} rows")


if __name__ == "__main__":
    main()
