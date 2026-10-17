// Only editable fields cross the Studio write boundary. Never echo approval,
// private source paths, job payloads, audit records or persisted IDs as inputs.
const pick = (value, fields) => Object.fromEntries(
  fields.filter((key) => Object.prototype.hasOwnProperty.call(value, key))
    .map((key) => [key, value[key]])
);

export const questionPayload = (question) => pick(question, [
  'number', 'solution_number', 'subject', 'section', 'type', 'text', 'options',
  'answer', 'solution', 'topic', 'difficulty', 'render_mode', 'q_refs', 's_refs',
  'accessible_text', 'solution_accessible_text', 'review_note', 'disposition', 'accepted_answers',
]);

export const settingsPayload = (settings) => pick(settings, [
  'title', 'exam', 'year', 'source', 'attribution', 'audience', 'allowed_emails',
  'allowed_phones', 'profile_mode', 'expires', 'rights_upload', 'rights_publish',
  'rights_report', 'rules', 'change_reason',
]);
