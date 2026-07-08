"""Seed the database with sample HCPs so search_hcp has data to work with."""
from .database import SessionLocal, engine, Base
from .models import HCP

SAMPLE_HCPS = [
    {"name": "Dr. Smith", "specialty": "Oncology", "institution": "City General Hospital", "email": "smith@citygeneral.example"},
    {"name": "Dr. John Miller", "specialty": "Cardiology", "institution": "St. Mary's Medical Center", "email": "jmiller@stmarys.example"},
    {"name": "Dr. Sharma", "specialty": "Neurology", "institution": "Apollo Institute", "email": "sharma@apollo.example"},
    {"name": "Dr. Emily Chen", "specialty": "Endocrinology", "institution": "Metro Health", "email": "echen@metro.example"},
    {"name": "Dr. Rodriguez", "specialty": "Immunology", "institution": "University Hospital", "email": "rodriguez@univ.example"},
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(HCP).count() == 0:
            db.add_all([HCP(**h) for h in SAMPLE_HCPS])
            db.commit()
            print(f"Seeded {len(SAMPLE_HCPS)} HCPs.")
        else:
            print("HCPs already present — skipping seed.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
