from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import Any

from .exceptions import (
    CronBackendError,
    CronDuplicateJobError,
    CronJobNotFoundError,
    CronValidationError,
)
from .manager import CronManager
from .models import CronJob, UpsertResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cron-manager")
    parser.add_argument("--json", action="store_true", dest="as_json")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list")

    get_parser = sub.add_parser("get")
    get_parser.add_argument("job_id")

    exists_parser = sub.add_parser("exists")
    exists_parser.add_argument("job_id")

    upsert_parser = sub.add_parser("upsert")
    upsert_parser.add_argument("--id", dest="job_id", required=True)
    upsert_parser.add_argument("--schedule", required=True)
    upsert_parser.add_argument("--command", dest="shell_command", required=True)
    enabled_group = upsert_parser.add_mutually_exclusive_group()
    enabled_group.add_argument("--enabled", action="store_true")
    enabled_group.add_argument("--disabled", action="store_true")

    pause_parser = sub.add_parser("pause")
    pause_parser.add_argument("job_id")

    resume_parser = sub.add_parser("resume")
    resume_parser.add_argument("job_id")

    delete_parser = sub.add_parser("delete")
    delete_parser.add_argument("job_id")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manager = CronManager()

    try:
        if args.command == "list":
            jobs = manager.list_managed_jobs()
            _print_output([asdict(job) for job in jobs], args.as_json)
            return 0

        if args.command == "get":
            job = manager.get_job(args.job_id)
            _print_output(asdict(job), args.as_json)
            return 0

        if args.command == "exists":
            exists = manager.exists(args.job_id)
            if args.as_json:
                _print_output({"job_id": args.job_id, "exists": exists}, True)
            else:
                print("yes" if exists else "no")
            return 0

        if args.command == "upsert":
            enabled = not args.disabled
            result = manager.upsert_job(
                job_id=args.job_id,
                schedule=args.schedule,
                command=args.shell_command,
                enabled=enabled,
            )
            _print_upsert(result, args.as_json)
            return 0

        if args.command == "pause":
            job = manager.pause_job(args.job_id)
            _print_output(asdict(job), args.as_json)
            return 0

        if args.command == "resume":
            job = manager.resume_job(args.job_id)
            _print_output(asdict(job), args.as_json)
            return 0

        if args.command == "delete":
            manager.delete_job(args.job_id)
            if args.as_json:
                _print_output({"deleted": True, "job_id": args.job_id}, True)
            else:
                print(f"Deleted: {args.job_id}")
            return 0

        parser.print_help()
        return 1

    except CronValidationError as exc:
        _print_error(str(exc), args.as_json)
        return 2
    except CronJobNotFoundError as exc:
        _print_error(str(exc), args.as_json)
        return 3
    except (CronBackendError, CronDuplicateJobError) as exc:
        _print_error(str(exc), args.as_json)
        return 4


def _print_upsert(result: UpsertResult, as_json: bool) -> None:
    payload = {"status": result.status.value, "job": asdict(result.job)}
    _print_output(payload, as_json)


def _print_output(payload: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, list):
        for item in payload:
            print(
                f"{item['job_id']} | {item['schedule']} | "
                f"enabled={item['enabled']} | {item['command']}"
            )
        if not payload:
            print("No managed cron jobs found.")
        return
    if isinstance(payload, dict):
        if {"job_id", "schedule", "command", "enabled"}.issubset(payload.keys()):
            print(
                f"{payload['job_id']} | {payload['schedule']} | "
                f"enabled={payload['enabled']} | {payload['command']}"
            )
            return
        if "status" in payload and "job" in payload:
            job = payload["job"]
            print(
                f"{payload['status']}: {job['job_id']} | {job['schedule']} | "
                f"enabled={job['enabled']} | {job['command']}"
            )
            return
    print(payload)


def _print_error(message: str, as_json: bool) -> None:
    if as_json:
        print(json.dumps({"error": message}))
    else:
        print(f"Error: {message}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
