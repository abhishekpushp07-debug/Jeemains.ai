"""Authenticated read-only baseline; no runtime readiness or capacity claims."""
from typing import Literal
from fastapi import APIRouter, Depends, Request
from .auth import staff
from .capacity import CapacityProfile, calculate
from .command_contracts import StrictContract
from .safety import Capability, held

router = APIRouter(prefix='/api/internal', tags=['Staff engineering baseline'])


class CapabilityState(StrictContract):
    capability: str
    held: bool


class SafetyStatus(StrictContract):
    packet: Literal[1] = 1
    packet_status: Literal['IN_PROGRESS_BLOCKED_EXIT'] = 'IN_PROGRESS_BLOCKED_EXIT'
    capacity_status: Literal['UNQUALIFIED'] = 'UNQUALIFIED'
    credential_rotation: Literal['PENDING_AUTHORIZED_OPERATOR'] = 'PENDING_AUTHORIZED_OPERATOR'
    capabilities: list[CapabilityState]
    note: str


@router.get('/capacity/profile', response_model=CapacityProfile, operation_id='internal_capacity_profile_v1')
async def capacity_profile(u=Depends(staff)):
    return calculate()


@router.get('/runtime/status')
async def runtime_status(request: Request, u=Depends(staff)):
    from .packs import cache_stats
    from .jobs import _active, _draining
    from .runtime import DB_POOL, DB_WAIT_MS, LANE_LIMITS, JOB_DRAIN_QUANTUM
    return {'capacity_status': 'UNQUALIFIED', 'admission': request.app.state.admission.snapshot(),
            'pack_cache': cache_stats(), 'database': {'max_pool_per_process': DB_POOL, 'wait_ms': DB_WAIT_MS},
            'jobs': {'active': {k: len(v) for k, v in _active.items()}, 'limits': LANE_LIMITS,
                     'draining_lanes': sorted(_draining), 'drain_quantum': JOB_DRAIN_QUANTUM},
            'note': 'Bounded process-local counters, not fleet metrics or a load-test certificate.'}


@router.get('/safety/status', response_model=SafetyStatus, operation_id='internal_safety_status_v1')
async def safety_status(u=Depends(staff)):
    return SafetyStatus(capabilities=[CapabilityState(capability=c.value, held=held(c)) for c in Capability],
        note='Containment only. Historical correctness defects remain open; atomic source review, full contracts, approvals and credential rotation still block Packet 1 exit.')
