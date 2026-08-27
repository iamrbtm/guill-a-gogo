"""Seed the initial Dallas, OR -> Clarksville, TN move trip.

Repeatable: re-running updates the same entities in place (deterministic UUIDs).

Usage (inside the api container or with DATABASE_URL set):
    python scripts/seed_tennessee.py --email owner@example.com
"""
from __future__ import annotations

import argparse
import sys

from app.config import get_settings
from app.db.session import _create_engine, get_sessionmaker, init_db
from app.models.accounts import User
from app.seed.tennessee import seed_tennessee


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True, help="Existing owner account email")
    args = parser.parse_args()

    settings = get_settings()
    engine = _create_engine(settings)
    init_db(engine)
    Session = get_sessionmaker(engine)
    session = Session()

    owner = session.query(User).filter_by(email=args.email, deleted_at=None).first()
    if owner is None:
        print(f"No owner user with email {args.email}. Create one via scripts/create_owner.py first.", file=sys.stderr)
        return 1

    trip = seed_tennessee(session, owner)
    session.commit()
    print(f"Seeded Tennessee trip: {trip.id} ({trip.title})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
