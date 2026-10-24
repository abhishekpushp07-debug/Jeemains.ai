"""Exact workload arithmetic; planning evidence, never measured capacity."""
from fractions import Fraction
from typing import Literal
from pydantic import Field
from .command_contracts import StrictContract


class Workload(StrictContract):
    active_attempts: int = Field(default=500000, ge=1, le=500000)
    steady_seconds: int = Field(default=10800, ge=1, le=86400)
    cell_count: int = Field(default=20, ge=1, le=100)
    commit_interval_seconds: int = Field(default=30, ge=1, le=3600)
    dirty_percentage: int = Field(default=20, ge=0, le=100)
    draft_interval_seconds: int = Field(default=10, ge=1, le=3600)
    lease_interval_seconds: int = Field(default=60, ge=1, le=3600)
    telemetry_interval_seconds: int = Field(default=30, ge=1, le=3600)
    start_window_seconds: int = Field(default=120, ge=1, le=3600)
    submit_window_seconds: int = Field(default=30, ge=1, le=3600)
    candidate_package_bytes: int = Field(default=2000000, ge=1, le=100000000)
    items_per_attempt: int = Field(default=75, ge=1, le=1000)
    grade_window_seconds: int = Field(default=120, ge=1, le=3600)


class ExactQuantity(StrictContract):
    numerator: int
    denominator: int = Field(ge=1)
    unit: str
    display: str


def quantity(value, unit):
    exact = Fraction(value)
    return ExactQuantity(numerator=exact.numerator, denominator=exact.denominator,
                         unit=unit, display=f'{float(exact):,.4f}')


class Stage(StrictContract):
    actors: int
    steady_minutes: int


class Slo(StrictContract):
    id: str
    unit: str
    limit: int
    percentile: Literal['p95', 'p99', 'maximum']
    measurement: str


class CapacityProfile(StrictContract):
    schema_version: Literal['capacity-profile-v1'] = 'capacity-profile-v1'
    evidence_status: Literal['PLANNING_ONLY_UNQUALIFIED'] = 'PLANNING_ONLY_UNQUALIFIED'
    workload: Workload
    rates: dict[str, ExactQuantity]
    volumes: dict[str, ExactQuantity]
    stages: list[Stage]
    slos: list[Slo]
    qualified_active_attempts: int | None = None
    mounted_runtime: dict = Field(default_factory=dict)
    reference_model: Literal['UNMOUNTED_V5_DESIGN'] = 'UNMOUNTED_V5_DESIGN'
    warnings: list[str]


def mounted_workload(w):
    c = w.active_attempts
    saves = Fraction(c, w.commit_interval_seconds)
    visits = Fraction(c * w.items_per_attempt, w.steady_seconds)
    crops = visits * 2
    retries = saves / 10
    rates = {'answer_save': saves, 'question_visit': visits, 'question_asset': crops,
             'answer_retry_allowance': retries, 'steady_total': saves + visits + crops + retries,
             'deadline_confirmation_burst': Fraction(c, 6),
             'start_burst': Fraction(c, w.start_window_seconds),
             'submit_burst': Fraction(c, w.submit_window_seconds)}
    return {'status': 'PLANNING_ONLY_UNQUALIFIED',
            'protocol': 'Mounted PUT answers with revision and body-bound request receipt; no remote draft/lease/telemetry heartbeat',
            'assumptions': {'answer_interval_seconds': w.commit_interval_seconds,
                            'visits_per_student': w.items_per_attempt, 'crop_requests_per_visit': 2,
                            'answer_retry_percentage': 10, 'deadline_retry_seconds': 6,
                            'asset_bytes_and_database_amplification': 'MUST_BE_MEASURED'},
            'rates': {key: quantity(value, 'requests/second').model_dump() for key, value in rates.items()},
            'notes': ['Dirty answers debounce around 350ms; 30s average edits is an assumption, not an enforced interval.',
                      'Each dirty question is a separate request; navigation, revisits, auth, results and storage misses add load.',
                      'Deadline checks are small and conditional, not a steady full-attempt poll.',
                      'All caches, pools and admission budgets multiply by process/pod count; no fleet size is certified.',
                      'The 15-minute repair cron and in-process grade lanes cannot guarantee a 120-second mass grading SLA.']}



def calculate(w: Workload | None = None) -> CapacityProfile:
    w = w or Workload()
    c = w.active_attempts
    commit = Fraction(c, w.commit_interval_seconds)
    draft = Fraction(c * w.dirty_percentage, 100 * w.draft_interval_seconds)
    lease = Fraction(c, w.lease_interval_seconds)
    telemetry = Fraction(c, w.telemetry_interval_seconds)
    live = commit + draft + lease
    start = Fraction(c, w.start_window_seconds)
    submit = Fraction(c, w.submit_window_seconds)
    pathological = Fraction(c, 5) + commit + lease
    rates = {k: quantity(v, 'requests/second') for k, v in {
        'commit': commit, 'draft': draft, 'lease': lease, 'live': live,
        'telemetry': telemetry, 'combined': live + telemetry,
        'double_live': live * 2, 'double_combined': (live + telemetry) * 2,
        'per_cell_live': live / w.cell_count,
        'start_overlay': start, 'submit_overlay': submit,
        'start_live_overlap': live + start,
        'submit_live_overlap': live + submit,
        'submit_combined_overlap': live + telemetry + submit,
        'pathological_live': pathological, 'pathological_combined': pathological + telemetry,
    }.items()}
    rates['grade_item_demand'] = quantity(Fraction(c * w.items_per_attempt, w.grade_window_seconds), 'items/second')
    rates['candidate_egress'] = quantity(Fraction(c * w.candidate_package_bytes * 8, w.start_window_seconds), 'bits/second')
    volumes = {k: quantity(v * w.steady_seconds, 'operations') for k, v in {
        'commits': commit, 'drafts': draft, 'leases': lease, 'live': live, 'telemetry': telemetry,
    }.items()}
    volumes['candidate_wave'] = quantity(c * w.candidate_package_bytes, 'bytes')
    return CapacityProfile(workload=w, rates=rates, volumes=volumes, mounted_runtime=mounted_workload(w),
        stages=[Stage(actors=a, steady_minutes=m) for a, m in [(1000, 15), (10000, 30), (50000, 45), (100000, 60), (250000, 90), (500000, 180)]],
        slos=[
            Slo(id='commit-p95', unit='milliseconds', limit=300, percentile='p95', measurement='Server ingress through durable acknowledgement, including queueing and database commit'),
            Slo(id='commit-p99', unit='milliseconds', limit=1000, percentile='p99', measurement='Server ingress through durable acknowledgement'),
            Slo(id='submit-p99', unit='milliseconds', limit=2000, percentile='p99', measurement='Ingress to durable terminal receipt under declared submit burst'),
            Slo(id='grade-p95', unit='milliseconds', limit=60000, percentile='p95', measurement='Durable receipt to correct frozen core grade, including queue wait'),
            Slo(id='grade-p99', unit='milliseconds', limit=120000, percentile='p99', measurement='Durable receipt to correct frozen core grade'),
            Slo(id='server-errors', unit='parts-per-million', limit=1000, percentile='maximum', measurement='Overall AND every predeclared critical window; admitted overload failures count'),
            Slo(id='integrity-violations', unit='violations', limit=0, percentile='maximum', measurement='Covered failures: lost acknowledged commits, wrong grades, duplicate effects, key leakage'),
        ], warnings=[
            'Top-level commit/draft/lease/telemetry rates describe the UNMOUNTED V5 reference, not current app traffic; see mounted_runtime.',
            'These are exact planning equations and proposed guide SLOs, NOT load-test results.',
            'Independent database cells, operator-approved budgets and failure tests are not provisioned here.',
            'Retries, reads, auth, exports, asset requests and connection demand must be added explicitly.',
            'Two-times normal traffic does not qualify pathological draft traffic or failover.',
            'No actor, browser, connection, AZ-loss or regional-restore qualification has passed.',
        ])
