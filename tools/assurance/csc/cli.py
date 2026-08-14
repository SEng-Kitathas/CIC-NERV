from __future__ import annotations

import argparse
import os
from pathlib import Path

from .audit import run_audit
from .self_audit import run_self_audit


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog='cic-csc')
    sub = root.add_subparsers(dest='command', required=True)

    audit = sub.add_parser('audit')
    audit.add_argument('--project', default='.')
    audit.add_argument('--profile', default='engineering/assurance/csc/CIC_CSC_PROFILE.json')
    audit.add_argument('--output-root')

    sub.add_parser('self-audit')
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == 'self-audit':
        failures = run_self_audit()
        if failures:
            print('FAIL: CIC CSC self-audit')
            for failure in failures:
                print(f'- {failure}')
            return 1
        print('PASS: CIC CSC self-audit')
        print('veto_authority=NONE')
        return 0

    project = Path(args.project).resolve()
    profile = (project / args.profile).resolve() if not Path(args.profile).is_absolute() else Path(args.profile)
    output = Path(args.output_root).expanduser().resolve() if args.output_root else _default_output()
    report, clean = run_audit(project, profile, output)
    print(report)
    print(f'final_clean={str(clean).lower()}')
    print('veto_authority=NONE')
    # Audit-only by construction: findings are evidence, not process veto authority.
    return 0


def _default_output() -> Path:
    state = os.environ.get('XDG_STATE_HOME')
    base = Path(state).expanduser() if state else Path.home() / '.local/state'
    return (base / 'personal-cic-assurance/csc').resolve()


if __name__ == '__main__':
    raise SystemExit(main())
