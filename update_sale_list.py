import argparse
import json
import os
from datetime import datetime
from pathlib import Path


def read_json(path: Path, default):
    if not path.exists():
        return default
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return default
    return json.loads(raw)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_photo_id(photo_id: str) -> str:
    photo_id = (photo_id or "").strip()
    if not photo_id:
        raise ValueError("photo_id is empty")
    for ch in photo_id:
        if not (ch.isalnum() or ch in "_-"):
            raise ValueError(f"invalid photo_id: {photo_id}")
    return photo_id


def load_manifest_photo_ids(manifest_path: Path) -> list[str]:
    manifest = read_json(manifest_path, {})
    photos = manifest.get("photos")
    if not isinstance(photos, dict):
        return []
    return sorted(list(photos.keys()))


def ensure_record(sale_list: dict, photo_id: str):
    sales = sale_list.setdefault("sales", {})
    if photo_id not in sales:
        sales[photo_id] = {"sold": False, "updatedAt": ""}


def cmd_init(args, sale_list_path: Path, manifest_path: Path):
    sale_list = read_json(sale_list_path, {"version": "1.0", "updatedAt": "", "sales": {}})

    ids = load_manifest_photo_ids(manifest_path)
    for pid in ids:
        ensure_record(sale_list, pid)

    sale_list["version"] = sale_list.get("version") or "1.0"
    sale_list["updatedAt"] = datetime.now().isoformat()
    write_json(sale_list_path, sale_list)

    print(f"Initialized/updated: {sale_list_path}")
    print(f"Photos tracked: {len(sale_list.get('sales', {}))}")


def cmd_set(args, sale_list_path: Path):
    photo_id = normalize_photo_id(args.photo_id)
    sold = args.sold

    sale_list = read_json(sale_list_path, {"version": "1.0", "updatedAt": "", "sales": {}})
    ensure_record(sale_list, photo_id)

    sale_list["sales"][photo_id]["sold"] = bool(sold)
    sale_list["sales"][photo_id]["updatedAt"] = datetime.now().isoformat()
    sale_list["updatedAt"] = datetime.now().isoformat()

    write_json(sale_list_path, sale_list)
    print(f"Set {photo_id} sold={bool(sold)}")


def cmd_sync(args, sale_list_path: Path, manifest_path: Path):
    sale_list = read_json(sale_list_path, {"version": "1.0", "updatedAt": "", "sales": {}})

    ids = load_manifest_photo_ids(manifest_path)
    for pid in ids:
        ensure_record(sale_list, pid)

    sale_list["updatedAt"] = datetime.now().isoformat()
    write_json(sale_list_path, sale_list)

    print(f"Synced from manifest: {manifest_path}")
    print(f"Photos tracked: {len(sale_list.get('sales', {}))}")


def cmd_list(args, sale_list_path: Path):
    sale_list = read_json(sale_list_path, {"version": "1.0", "updatedAt": "", "sales": {}})
    sales = sale_list.get("sales", {})
    if not isinstance(sales, dict):
        sales = {}

    items = []
    for pid, rec in sales.items():
        if isinstance(rec, bool):
            items.append((pid, rec))
        elif isinstance(rec, dict):
            items.append((pid, bool(rec.get("sold", False))))
        else:
            items.append((pid, False))

    if args.sold_only:
        items = [it for it in items if it[1] is True]

    for pid, sold in sorted(items, key=lambda x: x[0]):
        print(f"{pid}\t{'SOLD' if sold else 'AVAILABLE'}")


def main():
    root = Path(__file__).resolve().parent
    data_dir = root / "data"
    sale_list_path = data_dir / "sale-list.json"
    manifest_path = root / "static" / "imgs" / "manifest.json"

    parser = argparse.ArgumentParser(description="Update data/sale-list.json sold status for photos")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Create sale-list.json if missing and track all manifest photo IDs")
    p_init.set_defaults(func=lambda a: cmd_init(a, sale_list_path, manifest_path))

    p_sync = sub.add_parser("sync", help="Ensure all manifest photo IDs exist in sale-list.json (does not remove entries)")
    p_sync.set_defaults(func=lambda a: cmd_sync(a, sale_list_path, manifest_path))

    p_set = sub.add_parser("set", help="Set sold status for a photo ID")
    p_set.add_argument("photo_id")
    p_set.add_argument("sold", choices=["true", "false"], help="true or false")
    p_set.set_defaults(func=lambda a: cmd_set(a, sale_list_path))

    p_list = sub.add_parser("list", help="List sale statuses")
    p_list.add_argument("--sold-only", action="store_true")
    p_list.set_defaults(func=lambda a: cmd_list(a, sale_list_path))

    args = parser.parse_args()

    if args.cmd == "set":
        args.sold = True if args.sold == "true" else False

    args.func(args)


if __name__ == "__main__":
    main()
