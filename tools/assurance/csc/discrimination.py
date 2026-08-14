from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import tempfile

from .adapters import run_command_gate
from .config import CommandGateSpec, ProjectProfile, load_profile
from .discovery import discover
from .gates import doctrine_surface, lineage_presence, project_contract
from .rule_registry import RuleSpec, load_rule_registry


CaseClass = str


@dataclass(frozen=True)
class DiscriminationCase:
    rule_id: str
    case_id: str
    case_class: CaseClass
    expected_clean: bool
    actual_clean: bool
    evidence: str

    @property
    def discriminated(self) -> bool:
        return self.expected_clean == self.actual_clean


@dataclass(frozen=True)
class RuleDiscrimination:
    rule_id: str
    family: str
    authority_status: str
    enforcement_eligible: bool
    case_count: int
    case_classes: tuple[str, ...]
    discriminated: bool
    cases: tuple[DiscriminationCase, ...]


@dataclass(frozen=True)
class DiscriminationReport:
    format: str
    authority_mode: str
    veto_authority: str
    enforcement_authority: str
    all_discriminated: bool
    rules: tuple[RuleDiscrimination, ...]


def run_discrimination(registry_path: Path) -> DiscriminationReport:
    rules = load_rule_registry(registry_path)
    by_id = {rule.rule_id: rule for rule in rules}

    known = {
        'authority_mode_guard': _authority_cases,
        'command_gate_exit_contract': _command_cases,
        'lineage_anchor_presence': _lineage_cases,
        'doctrine_surface_presence': _doctrine_cases,
        'project_contract_source_roots': _project_contract_cases,
    }
    if set(by_id) != set(known):
        raise ValueError(
            'CSC rule registry/fixture universe mismatch: '
            f'registry={sorted(by_id)} fixtures={sorted(known)}'
        )

    results: list[RuleDiscrimination] = []
    for rule_id in sorted(by_id):
        rule = by_id[rule_id]
        cases = tuple(known[rule_id]())
        classes = tuple(sorted({case.case_class for case in cases}))
        expected_classes = tuple(sorted(rule.required_case_classes))
        discriminated = (
            classes == expected_classes
            and len(cases) >= len(rule.required_case_classes)
            and all(case.discriminated for case in cases)
        )
        results.append(RuleDiscrimination(
            rule_id=rule.rule_id,
            family=rule.family,
            authority_status=rule.authority_status,
            enforcement_eligible=rule.enforcement_eligible,
            case_count=len(cases),
            case_classes=classes,
            discriminated=discriminated,
            cases=cases,
        ))

    return DiscriminationReport(
        format='personal-cic.csc-discrimination.v1',
        authority_mode='audit_only',
        veto_authority='NONE',
        enforcement_authority='NONE',
        all_discriminated=all(result.discriminated for result in results),
        rules=tuple(results),
    )


def write_discrimination_report(report: DiscriminationReport, output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    path = output_root / 'CIC_CSC_DISCRIMINATION_REPORT.json'
    path.write_text(
        json.dumps(_jsonable(report), indent=2) + '\n',
        encoding='utf-8',
    )
    return path


def _authority_cases() -> list[DiscriminationCase]:
    cases: list[DiscriminationCase] = []
    with tempfile.TemporaryDirectory(prefix='cic-csc-authority-fixtures-') as td:
        root = Path(td)
        _fixture_layout(root)

        good = _profile_data()
        cases.append(_profile_case(root, 'authority-good', 'known_good', good, True))

        bad = _profile_data()
        bad['authority_mode'] = 'enforce'
        cases.append(_profile_case(root, 'authority-enforce', 'known_bad', bad, False))

        near = _profile_data()
        near['authority_mode'] = 'audit-only'
        cases.append(_profile_case(root, 'authority-near-spelling', 'near_miss', near, False))

        harmless = _profile_data()
        harmless['comment'] = 'harmless extra metadata'
        cases.append(_profile_case(root, 'authority-harmless-extra', 'false_positive', harmless, True))
    return cases


def _command_cases() -> list[DiscriminationCase]:
    with tempfile.TemporaryDirectory(prefix='cic-csc-command-fixtures-') as td:
        root = Path(td)
        specs = [
            ('command-zero', 'known_good', CommandGateSpec(
                'fixture', ('{python}', '-c', 'raise SystemExit(0)')
            ), True),
            ('command-seven', 'known_bad', CommandGateSpec(
                'fixture', ('{python}', '-c', 'raise SystemExit(7)')
            ), False),
            ('command-allowed-seven', 'near_miss', CommandGateSpec(
                'fixture', ('{python}', '-c', 'raise SystemExit(7)'),
                clean_exit_codes=(0, 7),
            ), True),
            ('command-word-fail', 'false_positive', CommandGateSpec(
                'fixture', ('{python}', '-c', "print('FAIL is only output text'); raise SystemExit(0)")
            ), True),
        ]
        return [
            DiscriminationCase(
                rule_id='command_gate_exit_contract',
                case_id=case_id,
                case_class=case_class,
                expected_clean=expected,
                actual_clean=run_command_gate(root, spec).clean,
                evidence=f'clean_exit_codes={list(spec.clean_exit_codes)}',
            )
            for case_id, case_class, spec, expected in specs
        ]


def _lineage_cases() -> list[DiscriminationCase]:
    cases: list[DiscriminationCase] = []
    for case_id, case_class, layout, expected in [
        ('lineage-present', 'known_good', 'exact', True),
        ('lineage-absent', 'known_bad', 'absent', False),
        ('lineage-backup-only', 'near_miss', 'backup', False),
        ('lineage-extra-neighbors', 'false_positive', 'extra', True),
    ]:
        with tempfile.TemporaryDirectory(prefix='cic-csc-lineage-fixture-') as td:
            root = Path(td)
            _fixture_layout(root)
            anchor = root / 'engineering/lineage/csc/MANIFEST.json'
            if layout in {'exact', 'extra'}:
                anchor.write_text('{}\n', encoding='utf-8')
            if layout == 'backup':
                anchor.with_suffix('.json.bak').write_text('{}\n', encoding='utf-8')
            if layout == 'extra':
                (anchor.parent / 'README.md').write_text('extra neighbor\n', encoding='utf-8')
            profile = _profile_object()
            actual = lineage_presence(root, profile).clean
            cases.append(DiscriminationCase(
                rule_id='lineage_anchor_presence',
                case_id=case_id,
                case_class=case_class,
                expected_clean=expected,
                actual_clean=actual,
                evidence=f'layout={layout}',
            ))
    return cases


def _doctrine_cases() -> list[DiscriminationCase]:
    cases: list[DiscriminationCase] = []
    for case_id, case_class, layout, expected in [
        ('doctrine-markdown', 'known_good', 'markdown', True),
        ('doctrine-empty', 'known_bad', 'empty', False),
        ('doctrine-binary-only', 'near_miss', 'binary', False),
        ('doctrine-word-fail', 'false_positive', 'fail_text', True),
    ]:
        with tempfile.TemporaryDirectory(prefix='cic-csc-doctrine-fixture-') as td:
            root = Path(td)
            _fixture_layout(root)
            docs = root / 'docs'
            if layout == 'markdown':
                (docs / 'LAW.md').write_text('verification law\n', encoding='utf-8')
            elif layout == 'binary':
                (docs / 'diagram.png').write_bytes(b'not actually an image')
            elif layout == 'fail_text':
                (docs / 'LAW.md').write_text('The word FAIL is not itself a defect.\n', encoding='utf-8')
            actual = doctrine_surface(root, _profile_object()).clean
            cases.append(DiscriminationCase(
                rule_id='doctrine_surface_presence',
                case_id=case_id,
                case_class=case_class,
                expected_clean=expected,
                actual_clean=actual,
                evidence=f'layout={layout}',
            ))
    return cases


def _project_contract_cases() -> list[DiscriminationCase]:
    cases: list[DiscriminationCase] = []
    for case_id, case_class, layout, expected in [
        ('source-root-present', 'known_good', 'exact', True),
        ('source-root-missing', 'known_bad', 'missing', False),
        ('source-root-similar', 'near_miss', 'similar', False),
        ('source-root-extra', 'false_positive', 'extra', True),
    ]:
        with tempfile.TemporaryDirectory(prefix='cic-csc-contract-fixture-') as td:
            root = Path(td)
            (root / 'docs').mkdir(parents=True)
            (root / 'engineering/lineage/csc').mkdir(parents=True)
            if layout in {'exact', 'extra'}:
                (root / 'src').mkdir()
            if layout == 'similar':
                (root / 'source').mkdir()
            if layout == 'extra':
                (root / 'scratch').mkdir()
            profile = _profile_object()
            found = discover(root, profile)
            actual = project_contract(root, profile, found).clean
            cases.append(DiscriminationCase(
                rule_id='project_contract_source_roots',
                case_id=case_id,
                case_class=case_class,
                expected_clean=expected,
                actual_clean=actual,
                evidence=f'layout={layout}',
            ))
    return cases


def _profile_case(
    root: Path,
    case_id: str,
    case_class: str,
    data: dict[str, object],
    expected: bool,
) -> DiscriminationCase:
    path = root / f'{case_id}.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    try:
        load_profile(path)
    except ValueError as exc:
        actual = False
        evidence = f'rejected: {exc}'
    else:
        actual = True
        evidence = 'accepted'
    return DiscriminationCase(
        rule_id='authority_mode_guard',
        case_id=case_id,
        case_class=case_class,
        expected_clean=expected,
        actual_clean=actual,
        evidence=evidence,
    )


def _profile_data() -> dict[str, object]:
    return {
        'project_name': 'fixture',
        'authority_mode': 'audit_only',
        'source_roots': ['src'],
        'doctrine_roots': ['docs'],
        'lineage_anchor': 'engineering/lineage/csc/MANIFEST.json',
        'command_gates': [],
    }


def _profile_object() -> ProjectProfile:
    return ProjectProfile(
        project_name='fixture',
        authority_mode='audit_only',
        source_roots=('src',),
        doctrine_roots=('docs',),
        lineage_anchor='engineering/lineage/csc/MANIFEST.json',
        command_gates=(),
    )


def _fixture_layout(root: Path) -> None:
    (root / 'src').mkdir(parents=True, exist_ok=True)
    (root / 'docs').mkdir(parents=True, exist_ok=True)
    (root / 'engineering/lineage/csc').mkdir(parents=True, exist_ok=True)


def _jsonable(value: object) -> object:
    if hasattr(value, '__dataclass_fields__'):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value
