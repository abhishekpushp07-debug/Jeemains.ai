"""Executable route catalogue built from actual FastAPI routes/dependencies.

No per-request database/global-catalogue dependency. Every mounted API operation
must have a reviewed local contract entry; unknown operations fail startup.
"""
from dataclasses import dataclass
from fastapi.routing import APIRoute
from .request_contracts import MODELS, EmptyPayload

# owner boundary, workload tier, current idempotency behavior
SPEC = {
    'exam_navigation.catalogue': ('current_profile_exam_metadata', 'normal', 'read'),
    'mock_books.list_mock_books': ('staff_mock_metadata', 'normal', 'read'),
    'mock_solutions.attempt_solutions': ('attempt_owner_completed_released', 'normal', 'read'),
    'mock_solutions.review_list': ('staff_ai_review_metadata', 'normal', 'read'),
    'mock_solutions.review_action': ('staff_ai_review_tag', 'normal', 'tag_update_audited'),
    'attempts.unlock_bonus': ('attempt_owner_active_deadline_all_main_answered', 'live', 'set_once_server_seq_CAS'),
    'cohorts.read': ('attempt_owner_released_original_peer_comparison', 'normal', 'read_with_materialization'),
    'cohorts.air_scenario': ('attempt_owner_released_full_jee_scenario', 'normal', 'pure_calculation'),
    'ai_solutions.read': ('attempt_owner_released_question', 'normal', 'read'),
    'ai_solutions.request_solution': ('attempt_owner_released_question', 'bulk', 'deterministic_question_solution_job'),
    'smart_imports.listing': ('owner_only', 'normal', 'read'),
    'smart_imports.set_daily_budget': ('owner_only_explicit_ai_usage_consent', 'critical', 'idempotent_budget_setting'),
    'smart_imports.upload': ('owner_only_rights_confirmed', 'bulk', 'owner_idempotency_key_and_source_hash'),
    'smart_imports.read': ('upload_owner_only', 'normal', 'read_with_bounded_dispatch'),
    'smart_imports.question_list': ('upload_owner_only', 'normal', 'read'),
    'smart_imports.source': ('upload_owner_only', 'bulk', 'read'),
    'smart_imports.clarify': ('upload_owner_only_private_paper', 'critical', 'explicit_rule_clarification'),
    'smart_imports.repair': ('upload_owner_only_private_paper', 'critical', 'source_repair_requires_note_and_recheck'),
    'smart_imports.budget': ('upload_owner_only_ai_work_consent', 'critical', 'idempotent_work_budget'),
    'smart_imports.retry': ('upload_owner_only', 'bulk', 'resume_existing_job_progress'),
    'exam_navigation.history': ('attempt_owner_exam_history', 'normal', 'read_with_expiry_side_effect'),
    'chapter_books.list_books': ('staff_chapter_metadata', 'normal', 'read'),
    'chapter_books.upload_book': ('owner_private_chapter_source', 'batch', 'source_hash_and_request_receipt'),
    'chapter_books.read_book': ('staff_chapter_metadata', 'normal', 'read'),
    'chapter_books.retry_book': ('owner_chapter_processing', 'batch', 'lease_CAS'),
    'chapter_books.preview_chapter': ('staff_chapter_content', 'normal', 'read'),
    'chapter_books.chapter_asset': ('staff_private_chapter_source', 'normal', 'read'),
    'chapter_books.publish_book': ('owner_verified_chapter_publication', 'control', 'per_set_once_same_validity'),
    'chapter_books.chapter_live': ('owner_chapter_admission', 'control', 'revision_CAS'),
    'chapter_books.public_exams': ('public_chapter_metadata', 'normal', 'read'),
    'chapter_books.my_exams': ('current_profile_chapter_metadata', 'normal', 'read'),
    'imports.template': ('staff_template', 'normal', 'read'),
    'imports.list_imports': ('staff_imports', 'normal', 'read'),
    'imports.create_import': ('owner_private_sources', 'batch', 'request_uuid_fingerprint'),
    'imports.read_import': ('staff_imports', 'normal', 'read'),
    'imports.retry_import': ('owner_imports', 'batch', 'lease_CAS'),
    'imports.error_report': ('staff_imports', 'normal', 'read'),
    'imports.import_asset': ('staff_imports', 'normal', 'read'),
    'imports.schedule_import': ('owner_immutable_import_publication', 'control', 'insert_or_revision_CAS'),
    'imports.toggle_live': ('owner_import_admission', 'control', 'revision_CAS'),
    'reviews.save_review': ('attempt_owner_private_post_release_notes', 'normal', 'question_version_revision_CAS_body_receipt'),
    'reviews.expected_value': ('attempt_owner_released_rules_only', 'normal', 'stateless_hypothetical'),
    'attempts.solution_consulted': ('attempt_owner_released_solutions', 'normal', 'set_membership_idempotent'),
    'competitions.catalogue': ('authenticated_competition_metadata', 'normal', 'read'),
    'competitions.leaderboard': ('anonymous_cohort_after_close', 'normal', 'read'),
    'server.health': ('public_liveness_only', 'normal', 'read'),
    'auth.register': ('removed_endpoint', 'normal', 'gone'),
    'auth.login': ('staff_password_session', 'normal', 'new_session'),
    'auth.session': ('cookie_identity', 'normal', 'read_refresh_side_effect'),
    'auth.me': ('current_identity', 'normal', 'read'),
    'auth.refresh': ('current_refresh_session', 'normal', 'session_refresh'),
    'auth.logout': ('current_cookie_sessions_only', 'normal', 'repeatable_delete'),
    'auth.preferences': ('current_profile_only', 'normal', 'replace_field'),
    'phone.access': ('unverified_phone_profile_only', 'normal', 'profile_upsert_new_session'),
    'content.catalogue': ('public_published_audience', 'normal', 'read'),
    'content.set_detail': ('public_published_audience', 'normal', 'read'),
    'content.studio_sets': ('authorized_editorial_workspace', 'control', 'read'),
    'content.create_set': ('authorized_editorial_workspace', 'control', 'not_idempotent'),
    'content.studio_set': ('authorized_editorial_workspace', 'control', 'read'),
    'content.update_set': ('authorized_editorial_workspace', 'control', 'legacy_unfenced_edit'),
    'content.upload': ('authorized_private_source', 'batch', 'HELD'),
    'content.source_page': ('authorized_private_source', 'batch', 'HELD'),
    'content.source_text': ('authorized_private_source', 'batch', 'HELD'),
    'content.source_download': ('authorized_private_source', 'normal', 'read'),
    'content.extract': ('authorized_editorial_workspace', 'batch', 'HELD'),
    'content.add_question': ('authorized_editorial_workspace', 'control', 'not_idempotent'),
    'content.edit_question': ('authorized_editorial_workspace', 'control', 'legacy_unfenced_edit'),
    'content.approve_question': ('authorized_editorial_workspace', 'control', 'revision_CAS'),
    'content.publish': ('owner_publication_rights', 'control', 'HELD'),
    'content.withdraw': ('owner_publication_rights', 'control', 'repeatable_state_change_audit_each_call'),
    'content.subset': ('authorized_editorial_workspace', 'control', 'not_idempotent'),
    'content.preview_asset': ('authorized_private_source', 'batch', 'HELD'),
    'answers.save_answer': ('attempt_owner_active_deadline', 'live', 'stored_request_receipt_CAS'),
    'attempts.my_sets': ('current_profile_audience', 'normal', 'read'),
    'attempts.my_set': ('current_profile_audience', 'normal', 'read'),
    'attempts.preflight': ('current_profile_audience_or_staff_preview', 'normal', 'upsert_preflight'),
    'attempts.start': ('current_profile_audience_or_staff_preview', 'live', 'start_key_receipt_legacy'),
    'attempts.history': ('attempt_owner', 'normal', 'read_with_expiry_side_effect'),
    'attempts.read_attempt': ('attempt_owner', 'live', 'read_with_expiry_side_effect'),
    'attempts.visit_question': ('attempt_owner_active_deadline', 'live', 'set_membership'),
    'attempts.submit': ('attempt_owner', 'live', 'atomic_seal_receipt'),
    'attempts.results': ('attempt_owner_and_solution_release', 'normal', 'read_grade_enqueue_side_effect'),
    'attempts.asset': ('attempt_owner_and_solution_release', 'normal', 'read_with_expiry_side_effect'),
    'attempts.retry': ('attempt_owner_frozen_grade', 'normal', 'KNOWN_A01_alias_gap'),
    'attempts.report': ('attempt_owner_and_report_rights', 'batch', 'versioned_report_job'),
    'jobs.status': ('job_owner_or_staff_set_scope', 'normal', 'read_dispatch_side_effect'),
    'jobs.retry_job': ('job_owner_or_staff_set_scope', 'batch', 'job_state_retry'),
    'jobs.download': ('job_owner_and_report_rights', 'normal', 'read'),
    'jobs.cron': ('cron_secret_dependency', 'batch', 'maintenance_replay'),
    'reviewers.update_access': ('owner_reviewer_administration', 'control', 'role_replace'),
    'profiles.profiles': ('authorized_editorial_workspace', 'control', 'read'),
    'corrections.regrade': ('owner_scoring_successor', 'batch', 'HELD'),
    'engineering.capacity_profile': ('staff_engineering_only', 'normal', 'read'),
    'engineering.safety_status': ('staff_engineering_only', 'normal', 'read'),
}


@dataclass(frozen=True)
class RouteContract:
    route: APIRoute
    key: str
    owner: str
    tier: str
    idempotency: str
    roles: tuple[str, ...]
    body_limit: int
    model: type | None
    json_body: bool


def roles(dependant):
    names = set()
    def visit(dep):
        names.add(getattr(dep.call, '__name__', ''))
        for child in dep.dependencies:
            visit(child)
    visit(dependant)
    if 'owner' in names:
        return ('owner',)
    if 'staff' in names:
        return ('owner', 'reviewer')
    if 'current' in names:
        return ('authenticated_profile',)
    return ('public_or_handler_checked',)


def install_contracts(app):
    from fastapi.routing import iter_route_contexts
    registry = []
    for ctx in iter_route_contexts(app.routes):
        route = ctx.route
        if not isinstance(route, APIRoute) or not route.path.startswith('/api/'):
            continue
        module = route.endpoint.__module__.split('.')[-1]
        key = module + '.' + route.endpoint.__name__
        if key not in SPEC:
            raise RuntimeError('API route lacks an explicit local contract: ' + key)
        owner, tier, idem = SPEC[key]
        writes = bool(route.methods & {'POST', 'PUT', 'PATCH', 'DELETE'})
        upload = key in ('content.upload', 'imports.create_import', 'chapter_books.upload_book', 'smart_imports.upload')
        model = (MODELS.get(key, EmptyPayload) if writes and not upload else None)
        if writes and not upload and route.body_field and key not in MODELS:
            raise RuntimeError('Body-bearing route lacks an explicit input model: ' + key)
        limit = 64 * 1024 if key in ('smart_imports.repair', 'smart_imports.clarify') else 256 * 1024 if key == 'content.edit_question' else 64 * 1024 if key in ('content.create_set', 'content.update_set', 'content.subset') else 4096
        if not writes or upload:
            limit = 0
        registry.append(RouteContract(route, key, owner, tier, idem, roles(route.dependant), limit, model, writes and not upload))
    app.state.route_contracts = tuple(registry)
    original = app.openapi
    def openapi():
        spec = original()
        components = spec.setdefault('components', {}).setdefault('schemas', {})
        for c in registry:
            for method in c.route.methods:
                operation = spec['paths'].get(c.route.path, {}).get(method.lower())
                if not operation:
                    continue
                operation.update({'x-owner-policy': c.owner, 'x-role-scope': list(c.roles),
                    'x-workload-tier': c.tier, 'x-idempotency-mode': c.idempotency,
                    'x-body-limit-bytes': c.body_limit, 'x-contract-stage': 'pilot_ingress_not_qualified_live_cell'})
                if c.model:
                    schema = c.model.model_json_schema(ref_template='#/components/schemas/{model}')
                    components.update(schema.pop('$defs', {}))
                    components[c.model.__name__] = schema
                    operation['requestBody'] = {'required': bool(c.route.body_field and getattr(c.route.body_field, 'required', True)),
                        'content': {'application/json': {'schema': {'$ref': '#/components/schemas/' + c.model.__name__}}}}
                operation['x-known-gaps'] = ['Target SQL authority, field-level response DTOs and cross-resource transaction proof are separate qualification requirements']
        return spec
    app.openapi = openapi
    return tuple(registry)
