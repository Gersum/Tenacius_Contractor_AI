from __future__ import annotations

import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from huggingface_hub import HfApi


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = ROOT / "tenacious_bench_v0_1"


def _read_dotenv() -> dict[str, str]:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value and len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def _env_get(name: str, default: str = "") -> str:
    raw = os.getenv(name)
    if raw is not None and raw.strip():
        return raw.strip()
    return _read_dotenv().get(name, default).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish the Tenacious-Bench dataset package to Hugging Face Hub."
    )
    parser.add_argument(
        "--repo-id",
        default=_env_get("HF_DATASET_REPO_ID"),
        help="Dataset repo id in the form username/repo_name. Defaults to HF_DATASET_REPO_ID.",
    )
    parser.add_argument(
        "--token",
        default=_env_get("HF_TOKEN"),
        help="Hugging Face token. Defaults to HF_TOKEN.",
    )
    parser.add_argument(
        "--dataset-dir",
        default=str(DEFAULT_DATASET_DIR),
        help="Local dataset directory to upload.",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Create the dataset repo as private.",
    )
    parser.add_argument(
        "--include-held-out",
        action="store_true",
        help="Include the held_out split in the published dataset. Off by default to preserve a sealed slice.",
    )
    return parser.parse_args()


def require(value: str, message: str) -> str:
    if value:
        return value
    raise SystemExit(message)


def main() -> None:
    args = parse_args()
    repo_id = require(
        args.repo_id,
        "Missing dataset repo id. Set HF_DATASET_REPO_ID or pass --repo-id username/repo_name.",
    )
    token = require(
        args.token,
        "Missing Hugging Face token. Set HF_TOKEN or pass --token hf_xxx.",
    )
    dataset_dir = Path(args.dataset_dir).resolve()
    if not dataset_dir.exists():
        raise SystemExit(f"Dataset directory does not exist: {dataset_dir}")

    api = HfApi(token=token)
    api.create_repo(repo_id=repo_id, repo_type="dataset", private=args.private, exist_ok=True)

    with TemporaryDirectory() as tmp_dir:
        publish_dir = _prepare_publish_dir(
            dataset_dir=dataset_dir,
            target_dir=Path(tmp_dir) / "tenacious_bench_v0_1",
            include_held_out=args.include_held_out,
        )

        uploads: list[tuple[Path, str]] = [
        (publish_dir, ""),
        (ROOT / "datasheet.md", "datasheet.md"),
        (ROOT / "methodology.md", "methodology.md"),
        (ROOT / "audit_memo.md", "audit_memo.md"),
        (ROOT / "evidence_graph.json", "evidence_graph.json"),
        (ROOT / "README.md", "repo_readme_snapshot.md"),
        ]

        for source_path, path_in_repo in uploads:
            if not source_path.exists():
                continue
            if source_path.is_dir():
                api.upload_folder(
                    repo_id=repo_id,
                    repo_type="dataset",
                    folder_path=str(source_path),
                    path_in_repo=path_in_repo,
                )
            else:
                api.upload_file(
                    repo_id=repo_id,
                    repo_type="dataset",
                    path_or_fileobj=str(source_path),
                    path_in_repo=path_in_repo or source_path.name,
                )

    print(f"Published dataset scaffold to https://huggingface.co/datasets/{repo_id}")


def _prepare_publish_dir(*, dataset_dir: Path, target_dir: Path, include_held_out: bool) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    for child in dataset_dir.iterdir():
        if child.name == "held_out" and not include_held_out:
            continue
        if child.is_dir():
            _copy_tree(child, target_dir / child.name)
        else:
            (target_dir / child.name).write_bytes(child.read_bytes())
    return target_dir


def _copy_tree(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        if child.is_dir():
            _copy_tree(child, target / child.name)
        else:
            (target / child.name).write_bytes(child.read_bytes())


if __name__ == "__main__":
    main()
