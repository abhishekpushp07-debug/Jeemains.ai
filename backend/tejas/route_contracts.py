"""Executable route catalogue built from actual FastAPI routes/dependencies.

No per-request database/global-catalogue dependency. Every mounted API operation
must have a reviewed local contract entry; unknown operations fail startup.
"""
from dataclasses import dataclass
from fastapi.routing import APIRoute
from .request_contracts import MODELS, EmptyPayload

# owner boundary, workload tier, current idempotency behavior
SPEC = {
    **{f'book_imports.{name}': ('book_owner_private_source', tier, mode) for name,tier,mode in (
        ('listing','normal','read'),('create','control','owner_source_hash_edition'),('read','normal','read'),
        ('part','control','immutable_part_hash'),('complete','control','leased_completion'),
        ('page_list','normal','read'),('page_detail','normal','read'),('page_image','batch','read'),
        ('repair_page','control','lease_page_revision'),('mock_detail','normal','read'),('rules','control','lease_mock_revision'),
        ('control','control','lease_book_revision'),('allowance','control','owner_explicit_bounded_request_receipt'),
        ('preview_crop','batch','owner_source_region_only'),('map_range','control','lease_range_mapping'))},
    'book_imports.series_list': ('current_released_series_metadata_only','normal','read'),
    'structure.student_exams': ('current_profile_visible_exam_metadata','normal','read'),
    'structure.student_exam': ('current_profile_visible_section_metadata','normal','read'),
    'structure.admin_catalog': ('owner_only_catalogue_structure','normal','read'),
    'structure.create_exam': ('owner_only_hidden_new_exam','control','unique_exam_name'),
    'structure.update_exam': ('owner_only_custom_exam_settings','control','replace_fields_audited'),
    'structure.create_section': ('owner_only_new_section','control','not_idempotent_audited'),
    'structure.update_section': ('owner_only_section_settings','control','replace_fields_audited'),
    'structure.order_sections': ('owner_only_section_order','control','full_set_replace'),
    'structure.admin_section_tests': ('owner_only_section_test_metadata','normal','read'),
    'structure.admin_unplaced': ('owner_only_unplaced_test_metadata','normal','read'),
    'structure.order_tests': ('owner_only_test_order','control','full_set_replace'),
    'structure.update_test': ('owner_only_test_placement_no_content_change','control','replace_fields_audited'),
    'structure.overview': ('owner_only_publishing_overview','normal','read'),
    'integrity.report': ('owner_only_integrity_counts_no_personal_data','normal','read'),
    'integrity.start_run': ('owner_only_integrity_run','control','single_flight_audited'),
    'structure.held_mocks': ('staff_held_mock_reasons_only','normal','read'),
    'structure.waiting': ('owner_only_ready_to_publish_metadata','normal','read'),
    'structure.publish_ready_items': ('owner_only_publish_ready_items','control','per_mock_request_flag_audited'),
    'book_imports.mock_problems': ('owner_any_reviewer_held_mocks_only','normal','read'),
    'book_imports.fix_question': ('owner_any_reviewer_held_mocks_only','control','lease_mock_revision'),
    'library.library': ('owner_only_library_metadata','normal','read'),
    'master.summary': ('owner_only_publishing_counts','normal','read'),
    'master.fix_list': ('staff_mocks_to_fix_metadata','normal','read'),
    'master.type_mocks': ('owner_only_type_mock_metadata','normal','read'),
    'master.change_status': ('owner_only_mock_status','control','per_item_state_audited'),
    'master.dismiss_upload': ('owner_only_upload_to_library','control','idempotent_flag_audited'),
    'written.create_written': ('owner_only_new_draft_mock','control','not_idempotent_audited'),
    'written.read_written': ('owner_any_reviewer_flagged_drafts_only','normal','read'),
    'written.update_written': ('owner_only_written_mock_details','control','revision_CAS_audited'),
    'written.save_question': ('staff_written_question','control','revision_CAS_audited'),
    'written.delete_question': ('staff_written_question','control','revision_CAS_audited'),
    'written.upload_image': ('staff_written_mock_photo','control','new_file_each_upload'),
    'written.read_image': ('staff_written_mock_photo','batch','read'),
    'written.paste': ('staff_written_mock_paste','control','revision_CAS_audited'),
    'written.excel': ('owner_only_written_mock_excel_rows','control','revision_CAS_audited'),
    'series_admin.public_list': ('public_series_schedule_metadata_only','normal','read'),
    'series_admin.public_schedule': ('public_series_schedule_metadata_only','normal','read'),
    'series_admin.public_history': ('own_series_attempts_only','normal','read'),
    'series_admin.owner_view': ('owner_series_schedule_only','normal','read'),
    'series_admin.update_config': ('owner_future_days_only','control','opened_days_unchanged_audited'),
    'series_admin.assign': ('owner_future_day_only','control','unique_series_day'),
    'series_admin.unassign': ('owner_future_day_only','control','idempotent_clear'),
    'series_admin.fill': ('owner_future_days_only','control','free_days_in_order_audited'),
    'series_admin.clear': ('owner_future_days_only','control','idempotent_clear'),
    'library.archive': ('owner_only_library_move','control','idempotent_flag_audited'),
    'library.restore': ('owner_only_library_restore','control','idempotent_flag_audited'),
    'library.export': ('owner_only_library_export','batch','read'),
    'live_series.fill': ('owner_future_days_only','control','free_days_in_order_audited'),
    'live_series.clear': ('owner_future_days_only','control','revision_CAS'),
    'live_series.unassign_book_mock': ('owner_future_day_only','control','idempotent_clear'),
    'structure.timed_tests': ('owner_only_schedule_metadata','normal','read'),
    'structure.preview_link_status': ('owner_only_section_preview_link_metadata','normal','read'),
    'structure.create_preview_link': ('owner_only_section_preview_link','control','rotates_previous_link_audited'),
    'structure.revoke_preview_link': ('owner_only_section_preview_link','control','idempotent_revoke_audited'),
    'structure.section_preview': ('public_unguessable_expiring_token_titles_order_status_only','normal','read'),
    'reviewers.list_reviewers': ('owner_reviewer_administration','normal','read'),
    'book_imports.series_detail': ('current_released_series_metadata_only','normal','read'),
    'pyq.catalogue': ('authenticated_pyq_metadata_own_attempts_only', 'normal', 'read'),
    'pyq_import.import_status': ('owner_only_pyq_import_status', 'normal', 'read'),
    'pyq_import.import_step': ('owner_only_verified_insert_only_pyq_import', 'heavy', 'leased_resumable_content_append'),
    'attempt_status.status_attempt': ('attempt_owner_header_only', 'live', 'read_conditional_database_time_expiry'),
    'engineering.runtime_status': ('staff_bounded_process_metrics_no_identifiers', 'normal', 'read'),
    'server.ready': ('public_database_readiness_only', 'normal', 'read'),
    'jee_transfer.transfer_status': ('owner_scoped_transfer_counts_only', 'normal', 'read'),
    'jee_transfer.transfer_step': ('owner_fixed_verified_bundle_only', 'batch', 'insert_only_hash_conflict_stop_durable_lease'),
    'series_streak.progress': ('own_live_series_streak_only', 'normal', 'read'),
    'live_series.catalogue': ('public_schedule_metadata_only', 'normal', 'read'),
    'live_series.history': ('own_series_attempts_only', 'normal', 'read'),
    'live_series.studio_schedule': ('owner_schedule_only', 'normal', 'read'),
    'live_series.assign': ('owner_published_fresh_paper_future_day', 'control', 'revision_CAS_unique_date'),
    'live_series.unassign': ('owner_future_day_only', 'control', 'revision_CAS'),
    'learning_progress.journey': ('attempt_owner_original_released_progress', 'normal', 'read'),
    'bitsat_branches.branch_matches': ('authenticated_score_lookup_no_private_record', 'normal', 'read_official_cutoff_snapshot'),
    'historical_rank.historical_rank': ('attempt_owner_released_evidence_gate', 'normal', 'read_no_invented_rank'),
    'my_tests.save_state': ('own_saved_paper_only', 'normal', 'read'),
    'my_tests.save_paper': ('current_published_visible_test_own_bookmark', 'normal', 'unique_user_set_no_attempt'),
    'my_tests.remove_saved': ('own_saved_paper_only', 'normal', 'idempotent_delete'),
    'my_tests.my_tests': ('private_user_filtered_history_and_saves', 'normal', 'read_no_start'),
    'my_tests.compare': ('both_attempts_owned_released_identical_paper_basis', 'normal', 'read'),
    'question_reports.report_priorities': ('staff_distinct_profile_issue_priority', 'normal', 'read'),
    'question_reports.report_group': ('staff_same_question_version_issue_details', 'normal', 'read'),
    'manual_solutions.solve_tests': ('owner_test_selection_only', 'normal', 'read'),
    'manual_solutions.solve_status': ('owner_test_solution_progress', 'normal', 'read_no_dispatch'),
    'manual_solutions.request_solve': ('owner_explicit_selected_test_only', 'bulk', 'request_receipt_and_question_content_identity'),
    'question_reports.my_reports': ('attempt_owner_private_report_receipts', 'normal', 'read'),
    'question_reports.report_wrong': ('attempt_owner_available_question_only', 'normal', 'one_report_per_attempt_question'),
    'question_reports.report_list': ('staff_editorial_issue_review', 'normal', 'read'),
    'question_reports.review_report': ('staff_issue_triage_no_regrade', 'normal', 'idempotent_status_update_audited'),
    'exam_navigation.catalogue': ('current_profile_exam_metadata', 'normal', 'read'),
    'mock_books.list_mock_books': ('staff_mock_metadata', 'normal', 'read'),
    'mock_solutions.attempt_solutions': ('attempt_owner_completed_released', 'normal', 'read'),
    'mock_solutions.review_list': ('staff_ai_review_metadata', 'normal', 'read'),
    'mock_solutions.review_image': ('staff_ai_review_source_crop', 'normal', 'read'),
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
    'phone.access': ('student_phone_pin_credentials', 'normal', 'verified_pin_new_session'),
    'phone.signup': ('new_student_phone_pin_only', 'normal', 'unique_phone_no_existing_profile_claim'),
    'phone.change_pin': ('authenticated_own_student_only', 'normal', 'pin_version_CAS_session_revocation'),
    'phone.owner_reset_pin': ('owner_only_existing_student_pin_reset', 'normal', 'pin_version_CAS_audited_no_student_session'),
    'students.list_students': ('owner_only_student_phone_projection', 'normal', 'read'),
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
    'attempts.start': ('current_profile_audience_or_staff_preview', 'live', 'start_key_and_body_receipt_resume_alias'),
    'attempts.history': ('attempt_owner', 'normal', 'read_with_expiry_side_effect'),
    'attempts.read_attempt': ('attempt_owner', 'live', 'read_with_expiry_side_effect'),
    'attempts.visit_question': ('attempt_owner_active_deadline', 'live', 'set_membership'),
    'attempts.submit': ('attempt_owner', 'live', 'atomic_seal_receipt'),
    'attempts.results': ('attempt_owner_and_solution_release', 'normal', 'read_grade_enqueue_side_effect'),
    'attempts.asset': ('attempt_owner_and_solution_release', 'normal', 'read_with_expiry_side_effect'),
    'attempts.retry': ('attempt_owner_frozen_grade', 'normal', 'retry_body_receipt_resume_alias'),
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
        upload = key in ('content.upload', 'imports.create_import', 'chapter_books.upload_book', 'smart_imports.upload', 'book_imports.part', 'written.upload_image', 'written.excel')
        model = (MODELS.get(key, EmptyPayload) if writes and not upload else None)
        if writes and not upload and route.body_field and key not in MODELS:
            raise RuntimeError('Body-bearing route lacks an explicit input model: ' + key)
        limit = 64 * 1024 if key in ('smart_imports.repair', 'smart_imports.clarify') else 256 * 1024 if key == 'content.edit_question' else 64 * 1024 if key in ('content.create_set', 'content.update_set', 'content.subset') else 4096
        if key == 'book_imports.repair_page':
            limit = 512 * 1024
        elif key in ('book_imports.rules', 'book_imports.allowance'):
            limit = 128 * 1024
        elif key in ('structure.order_tests', 'structure.order_sections', 'master.change_status'):
            limit = 128 * 1024
        elif key in ('written.save_question', 'written.paste'):
            limit = 512 * 1024
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
                operation['x-known-gaps'] = ['MongoDB is canonical; replica/failover/load evidence and remaining legacy response DTO coverage are unqualified']
        return spec
    app.openapi = openapi
    return tuple(registry)
