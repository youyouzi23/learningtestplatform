"""Import BugsInPy buggy/fixed comparisons into the test platform."""

import argparse
import json
from pathlib import Path

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--task-id", type=int, required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    endpoint = f"{args.base_url.rstrip('/')}/test-tasks/{args.task_id}/bugsinpy-results"

    with httpx.Client(timeout=30) as client:
        for case in manifest["cases"]:
            response = client.post(
                endpoint,
                headers={"X-API-Key": args.api_key},
                json=case,
            )
            response.raise_for_status()
            result = response.json()
            print(
                f"{result['project']}#{result['bug_id']}: "
                f"regression_passed={result['regression_passed']} "
                f"category={result['category']}"
            )


if __name__ == "__main__":
    main()
