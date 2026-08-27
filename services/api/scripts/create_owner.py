"""Bootstrap the first owner account.

Accounts are invitation-only, so this out-of-band script creates the initial
owner and prints an invitation token they use to register their passkey via the
WebAuthn register flow.

Usage (inside the api container or with DATABASE_URL set):
    python scripts/create_owner.py --email owner@example.com --name "Trip Owner"
"""
from __future__ import annotations

import argparse
import sys
import uuid

from app.config import get_settings
from app.db.session import _create_engine, get_sessionmaker, init_db
from app.models.accounts import Invitation, User
from app.services import auth_service


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--role", default="owner")
    args = parser.parse_args()

    settings = get_settings()
    engine = _create_engine(settings)
    init_db(engine)
    Session = get_sessionmaker(engine)
    session = Session()

    existing = session.query(User).filter_by(email=args.email).first()
    if existing:
        print(f"User {args.email} already exists (id={existing.id})", file=sys.stderr)
        return 1

    user = User(email=args.email, display_name=args.name, status="active")
    session.add(user)
    session.flush()

    invitation = auth_service.create_invitation(
        session,
        issuer_id=user.id,
        role=args.role,
        email=args.email,
        trip_id=None,
        settings=settings,
    )
    session.commit()

    link = f"{settings.invitation_base_url}?token={invitation.token}"
    print("Owner created:")
    print(f"  user_id : {user.id}")
    print(f"  token   : {invitation.token}")
    print(f"  link    : {link}")
    print("Share the link with the owner device to register a passkey.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
