import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import config
from session_manager.mongo_session_repository import MongoSessionRepository


def delete_sessions_by_prefix(repo: MongoSessionRepository, prefix: str, dry_run: bool = False) -> list[str]:
    sessions = repo.list_sessions()
    matched = [s["id"] for s in sessions if s["id"].startswith(prefix)]
    if not matched:
        print(f"  No sessions found matching prefix '{prefix}'")
        return []
    print(f"  Found {len(matched)} session(s) matching '{prefix}':")
    for sid in matched:
        title = next((s["title"] for s in sessions if s["id"] == sid), "")
        print(f"    - {sid}  ({title[:60]})")
    if not dry_run:
        for sid in matched:
            repo.delete_session(sid)
        print(f"  Deleted {len(matched)} session(s)")
    return matched


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Delete test sessions from MongoDB")
    parser.add_argument("prefix", nargs="?", default="", help="Session ID prefix to match (default: prompts for input)")
    parser.add_argument("--dry-run", action="store_true", help="List sessions without deleting")
    args = parser.parse_args()

    mongo_uri = config.get("mongo_uri")
    mongo_db = config.get("mongo_db")
    if not mongo_uri or not mongo_db:
        print("Error: MONGO_URI and MONGO_DB must be set in .env")
        return 1

    repo = MongoSessionRepository(uri=mongo_uri, db_name=mongo_db)

    sessions = repo.list_sessions()
    all_ids = [s["id"] for s in sessions]

    prefix = args.prefix
    if not prefix:
        print("Matching all test sessions...")
        matched = []
        for sid in all_ids:
            if sid == "default":
                continue
            if re.match(r'^[a-z]{2,10}_', sid):
                matched.append(sid)
        if not matched:
            print("  No test sessions found")
        else:
            print(f"  Found {len(matched)} test session(s):")
            for sid in matched:
                title = next((s["title"] for s in sessions if s["id"] == sid), "")
                print(f"    - {sid}  ({title[:60]})")
            if not args.dry_run:
                for sid in matched:
                    repo.delete_session(sid)
                print(f"  Deleted {len(matched)} session(s)")
        print(f"\n  Total: {len(matched)} unique session(s) {'would be' if args.dry_run else ''} deleted")
    else:
        delete_sessions_by_prefix(repo, prefix, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    exit(main())
