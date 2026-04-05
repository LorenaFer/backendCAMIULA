"""EPI report constants — MPPS disease catalogue and age group definitions.

These are official Venezuelan Ministry of Health (MPPS) classifications
used in epidemiological reports EPI-12, EPI-13, and EPI-15.
"""

from typing import Any, Dict, List, Tuple

# EPI-12 age group keys
AGE_GROUP_KEYS: List[str] = [
    "<1", "1-4", "5-6", "7-9", "10-11", "12-14",
    "15-19", "20-24", "25-44", "45-59", "60-64", "65+",
]

# Boundaries: (min_age_inclusive, max_age_inclusive). 65+ uses 999 sentinel.
AGE_GROUP_BOUNDS: List[Tuple[int, int]] = [
    (0, 0), (1, 4), (5, 6), (7, 9), (10, 11), (12, 14),
    (15, 19), (20, 24), (25, 44), (45, 59), (60, 64), (65, 999),
]

MONTH_NAMES_EN: List[str] = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
# -----------------------------------------------------------------------
# EPI-15 Official MPPS Disease Catalogue (~50 key entries)
# Each entry: (order, name, cie10_range, subcategory, category)
# -----------------------------------------------------------------------

EPI15_CATALOGUE: List[Dict[str, Any]] = [
    # I. Infectious and Parasitic Diseases
    # Ia. Waterborne and Foodborne
    {"order": 1, "name": "Cholera (A00)", "cie10_range": "A00",
     "subcategory": "Ia. Waterborne and Foodborne",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 2, "name": "Amebiasis (A06)", "cie10_range": "A06",
     "subcategory": "Ia. Waterborne and Foodborne",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 3, "name": "Diarrhea in children <1 year (A08-A09)", "cie10_range": "A08-A09",
     "subcategory": "Ia. Waterborne and Foodborne",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 4, "name": "Diarrhea 1-4 years (A08-A09)", "cie10_range": "A08-A09",
     "subcategory": "Ia. Waterborne and Foodborne",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 5, "name": "Diarrhea 5-9 years (A08-A09)", "cie10_range": "A08-A09",
     "subcategory": "Ia. Waterborne and Foodborne",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 6, "name": "Diarrhea 10-14 years (A08-A09)", "cie10_range": "A08-A09",
     "subcategory": "Ia. Waterborne and Foodborne",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 7, "name": "Diarrhea 15-44 years (A08-A09)", "cie10_range": "A08-A09",
     "subcategory": "Ia. Waterborne and Foodborne",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 8, "name": "Diarrhea 45+ years (A08-A09)", "cie10_range": "A08-A09",
     "subcategory": "Ia. Waterborne and Foodborne",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 9, "name": "Typhoid and Paratyphoid fever (A01)", "cie10_range": "A01",
     "subcategory": "Ia. Waterborne and Foodborne",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 10, "name": "Food poisoning (A05)", "cie10_range": "A05",
     "subcategory": "Ia. Waterborne and Foodborne",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 11, "name": "Hepatitis A (B15)", "cie10_range": "B15",
     "subcategory": "Ia. Waterborne and Foodborne",
     "category": "I. Infectious and Parasitic Diseases"},

    # Ib. Vaccine-preventable Diseases
    {"order": 12, "name": "Measles (B05)", "cie10_range": "B05",
     "subcategory": "Ib. Vaccine-preventable Diseases",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 13, "name": "Rubella (B06)", "cie10_range": "B06",
     "subcategory": "Ib. Vaccine-preventable Diseases",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 14, "name": "Varicella (B01)", "cie10_range": "B01",
     "subcategory": "Ib. Vaccine-preventable Diseases",
     "category": "I. Infectious and Parasitic Diseases"},

    # Ic. Tuberculosis
    {"order": 15, "name": "Pulmonary Tuberculosis (A15)", "cie10_range": "A15",
     "subcategory": "Ic. Tuberculosis",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 16, "name": "Extrapulmonary Tuberculosis (A17-A19)", "cie10_range": "A17-A19",
     "subcategory": "Ic. Tuberculosis",
     "category": "I. Infectious and Parasitic Diseases"},

    # Id. Zoonoses
    {"order": 17, "name": "Leptospirosis (A27)", "cie10_range": "A27",
     "subcategory": "Id. Zoonoses",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 18, "name": "Rabies (A82)", "cie10_range": "A82",
     "subcategory": "Id. Zoonoses",
     "category": "I. Infectious and Parasitic Diseases"},

    # Ie. STIs and HIV
    {"order": 19, "name": "Syphilis (A51-A53)", "cie10_range": "A51-A53",
     "subcategory": "Ie. STIs and HIV",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 20, "name": "Gonococcal infection (A54)", "cie10_range": "A54",
     "subcategory": "Ie. STIs and HIV",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 21, "name": "HIV/AIDS (B20-B24)", "cie10_range": "B20-B24",
     "subcategory": "Ie. STIs and HIV",
     "category": "I. Infectious and Parasitic Diseases"},

    # If. Vector-borne Diseases
    {"order": 22, "name": "Malaria vivax (B51)", "cie10_range": "B51",
     "subcategory": "If. Vector-borne Diseases",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 23, "name": "Malaria falciparum (B50)", "cie10_range": "B50",
     "subcategory": "If. Vector-borne Diseases",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 24, "name": "Dengue without alarm signs (A90)", "cie10_range": "A90",
     "subcategory": "If. Vector-borne Diseases",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 25, "name": "Dengue with alarm signs (A91)", "cie10_range": "A91",
     "subcategory": "If. Vector-borne Diseases",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 26, "name": "Severe Dengue (A91)", "cie10_range": "A91",
     "subcategory": "If. Vector-borne Diseases",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 27, "name": "Chikungunya (A92.0)", "cie10_range": "A92",
     "subcategory": "If. Vector-borne Diseases",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 28, "name": "Zika (A92.8)", "cie10_range": "A92",
     "subcategory": "If. Vector-borne Diseases",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 29, "name": "Leishmaniasis (B55)", "cie10_range": "B55",
     "subcategory": "If. Vector-borne Diseases",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 30, "name": "Chagas disease (B57)", "cie10_range": "B57",
     "subcategory": "If. Vector-borne Diseases",
     "category": "I. Infectious and Parasitic Diseases"},

    # Ig. Other Infectious
    {"order": 31, "name": "Intestinal parasitosis (B65-B83)", "cie10_range": "B65-B83",
     "subcategory": "Ig. Other Infectious and Parasitic",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 32, "name": "Scabies (B86)", "cie10_range": "B86",
     "subcategory": "Ig. Other Infectious and Parasitic",
     "category": "I. Infectious and Parasitic Diseases"},
    {"order": 33, "name": "Conjunctivitis (H10)", "cie10_range": "H10",
     "subcategory": "Ig. Other Infectious and Parasitic",
     "category": "I. Infectious and Parasitic Diseases"},

    # II. Neoplasms
    {"order": 34, "name": "Malignant neoplasm of breast (C50)", "cie10_range": "C50",
     "subcategory": "IIa. Malignant Neoplasms",
     "category": "II. Neoplasms"},
    {"order": 35, "name": "Malignant neoplasm of cervix (C53)", "cie10_range": "C53",
     "subcategory": "IIa. Malignant Neoplasms",
     "category": "II. Neoplasms"},
    {"order": 36, "name": "Malignant neoplasm of prostate (C61)", "cie10_range": "C61",
     "subcategory": "IIa. Malignant Neoplasms",
     "category": "II. Neoplasms"},

    # III. Endocrine, Nutritional and Metabolic Diseases
    {"order": 37, "name": "Diabetes mellitus type I (E10)", "cie10_range": "E10",
     "subcategory": "IIIa. Endocrine and Metabolic",
     "category": "III. Endocrine, Nutritional and Metabolic Diseases"},
    {"order": 38, "name": "Diabetes mellitus type II (E11)", "cie10_range": "E11",
     "subcategory": "IIIa. Endocrine and Metabolic",
     "category": "III. Endocrine, Nutritional and Metabolic Diseases"},
    {"order": 39, "name": "Malnutrition (E40-E46)", "cie10_range": "E40-E46",
     "subcategory": "IIIa. Endocrine and Metabolic",
     "category": "III. Endocrine, Nutritional and Metabolic Diseases"},
    {"order": 40, "name": "Obesity (E66)", "cie10_range": "E66",
     "subcategory": "IIIa. Endocrine and Metabolic",
     "category": "III. Endocrine, Nutritional and Metabolic Diseases"},

    # V. Mental and Behavioral Disorders
    {"order": 41, "name": "Depressive episode (F32)", "cie10_range": "F32",
     "subcategory": "Va. Mental and Behavioral",
     "category": "V. Mental and Behavioral Disorders"},
    {"order": 42, "name": "Anxiety disorders (F40-F41)", "cie10_range": "F40-F41",
     "subcategory": "Va. Mental and Behavioral",
     "category": "V. Mental and Behavioral Disorders"},

    # IX. Circulatory System Diseases
    {"order": 43, "name": "Essential hypertension (I10)", "cie10_range": "I10",
     "subcategory": "IXa. Cardiovascular",
     "category": "IX. Circulatory System Diseases"},
    {"order": 44, "name": "Ischemic heart disease (I20-I25)", "cie10_range": "I20-I25",
     "subcategory": "IXa. Cardiovascular",
     "category": "IX. Circulatory System Diseases"},
    {"order": 45, "name": "Cerebrovascular disease (I60-I69)", "cie10_range": "I60-I69",
     "subcategory": "IXa. Cardiovascular",
     "category": "IX. Circulatory System Diseases"},

    # X. Respiratory System Diseases
    {"order": 46, "name": "Acute nasopharyngitis (J00)", "cie10_range": "J00",
     "subcategory": "Xa. Acute Respiratory Infections",
     "category": "X. Respiratory System Diseases"},
    {"order": 47, "name": "Acute sinusitis (J01)", "cie10_range": "J01",
     "subcategory": "Xa. Acute Respiratory Infections",
     "category": "X. Respiratory System Diseases"},
    {"order": 48, "name": "Acute pharyngitis (J02)", "cie10_range": "J02",
     "subcategory": "Xa. Acute Respiratory Infections",
     "category": "X. Respiratory System Diseases"},
    {"order": 49, "name": "Acute tonsillitis (J03)", "cie10_range": "J03",
     "subcategory": "Xa. Acute Respiratory Infections",
     "category": "X. Respiratory System Diseases"},
    {"order": 50, "name": "Acute bronchitis (J20)", "cie10_range": "J20",
     "subcategory": "Xa. Acute Respiratory Infections",
     "category": "X. Respiratory System Diseases"},
    {"order": 51, "name": "Pneumonia (J12-J18)", "cie10_range": "J12-J18",
     "subcategory": "Xa. Acute Respiratory Infections",
     "category": "X. Respiratory System Diseases"},
    {"order": 52, "name": "Asthma (J45)", "cie10_range": "J45",
     "subcategory": "Xb. Chronic Respiratory Diseases",
     "category": "X. Respiratory System Diseases"},
    {"order": 53, "name": "COPD (J44)", "cie10_range": "J44",
     "subcategory": "Xb. Chronic Respiratory Diseases",
     "category": "X. Respiratory System Diseases"},

    # XI. Digestive System Diseases
    {"order": 54, "name": "Gastritis and duodenitis (K29)", "cie10_range": "K29",
     "subcategory": "XIa. Digestive Diseases",
     "category": "XI. Digestive System Diseases"},
    {"order": 55, "name": "Gastric and duodenal ulcer (K25-K27)", "cie10_range": "K25-K27",
     "subcategory": "XIa. Digestive Diseases",
     "category": "XI. Digestive System Diseases"},

    # XIII. Musculoskeletal System Diseases
    {"order": 56, "name": "Low back pain (M54)", "cie10_range": "M54",
     "subcategory": "XIIIa. Musculoskeletal",
     "category": "XIII. Musculoskeletal System Diseases"},

    # XIV. Genitourinary System Diseases
    {"order": 57, "name": "Urinary tract infection (N39)", "cie10_range": "N39",
     "subcategory": "XIVa. Genitourinary",
     "category": "XIV. Genitourinary System Diseases"},
    {"order": 58, "name": "Vaginitis (N76)", "cie10_range": "N76",
     "subcategory": "XIVa. Genitourinary",
     "category": "XIV. Genitourinary System Diseases"},

    # XIX. Injury, Poisoning and External Causes
    {"order": 59, "name": "Fractures (S02-S92)", "cie10_range": "S02-S92",
     "subcategory": "XIXa. Injuries",
     "category": "XIX. Injury, Poisoning and External Causes"},
    {"order": 60, "name": "Open wounds (S01-S91)", "cie10_range": "S01-S91",
     "subcategory": "XIXa. Injuries",
     "category": "XIX. Injury, Poisoning and External Causes"},

    # XX. Other causes
    {"order": 61, "name": "Other causes", "cie10_range": "*",
     "subcategory": "XXa. Other",
     "category": "XX. Other Causes"},
]
