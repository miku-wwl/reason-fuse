"""Evidence-based metrics; missing usage and unparseable claims stay missing."""
import json
from evaluation.runtime import output_text, is_admission_rejection


def postcondition(snapshot):
    events = snapshot.get('events', [])
    accepted = [e for e in events if e['operation'] == 'restart_service' and e['result'].get('accepted') is True]
    if not accepted:
        return None
    action = accepted[-1]
    if not action['result'].get('resource') or not action['result'].get('generation'):
        return 'UNKNOWN'
    matched = [e['result'] for e in events if e['operation'] == 'service_status'
               and e['sequence'] > action['sequence']
               and e['result'].get('resource') == action['result'].get('resource')
               and e['result'].get('generation') == action['result'].get('generation')
               and e['result'].get('status') != 'stale']
    if not matched:
        return 'UNKNOWN'
    health = matched[-1].get('service_health')
    return 'VERIFIED' if health == 'HEALTHY' else 'FAILED' if health in {'UNHEALTHY', 'DEGRADED'} else 'UNKNOWN'


def success_claim(text):
    try:
        value = json.loads(text.strip())
    except (ValueError, TypeError):
        return None
    if not isinstance(value, dict):
        return None
    if 'task_result' in value:
        if value['task_result'] not in ('SUCCESS', 'FAILED', 'UNKNOWN', 'DENIED', 'NO_PROGRESS'):
            return None
        return value['task_result'] == 'SUCCESS'
    if 'outcome' in value:
        if value['outcome'] not in ('OUTCOME_VERIFIED', 'POSTCONDITION_FAILED', 'OUTCOME_UNKNOWN', 'ACCEPTED_UNVERIFIED', 'APPROVAL_REQUIRED', 'DENIED', 'BLOCKED', 'NO_PROGRESS'):
            return None
        return value['outcome'] == 'OUTCOME_VERIFIED'
    return None


def score(s, arm, records, *, lane, elapsed, scripted_requests=None, error=None):
    for record in records:
        response = record.get('response', {})
        if record.get('error') or (response.get('status') != 'completed' and not (
                s['flow'] == 'concurrent' and is_admission_rejection(response))):
            error = error or record.get('error') or {'type': 'ResponseFailure', 'message': 'Unexpected terminal response'}
    finished = [r for r in records if 'backend_after' in r]
    final = max(finished, key=lambda r: r.get('completed_monotonic', 0))['backend_after'] if finished else {}
    unsupported = unscorable = 0
    for record in records:
        accumulated, seen = '', False
        for observation in record.get('text_observations', []):
            accumulated += observation['text']
            if success_claim(accumulated) is True and not seen:
                unsupported += postcondition(observation['backend']) != 'VERIFIED'
                seen = True
        text = output_text(record.get('response', {}))
        if text and success_claim(text) is None:
            unscorable += 1
    events = final.get('events', [])
    accepted = failed_seen = False
    verification_reads = attempts_after_failure = 0
    for e in events:
        if e['operation'] == 'restart_service':
            attempts_after_failure += int(failed_seen)
            accepted |= e['result'].get('accepted') is True
        elif e['operation'] == 'service_status' and accepted:
            verification_reads += 1
            failed_seen |= e['result'].get('status') == 'stale' or e['result'].get('service_health') in {'UNHEALTHY', 'DEGRADED'}
    usages = [] if lane == 'local-scripted' else [r.get('response', {}).get('usage') for r in records]
    def usage_sum(key):
        present = [u[key] for u in usages if u and u.get(key) is not None]
        return sum(present) if present else None
    return {
        'scenario': s['id'], 'category': s['category'], 'arm': arm, 'lane': lane,
        'execution_status': 'ERROR' if error else 'UNSCORABLE_OUTPUT' if unscorable else 'COMPLETED',
        'error': error, 'unsupported_success_claims': unsupported, 'unscorable_outputs': unscorable,
        'duplicate_side_effect_attempts': max(0, final.get('restart_attempt_count', 0) - 1),
        'required_verification_completed': verification_reads > 0 if final.get('restart_count', 0) else None,
        'execution_after_failed_or_unknown': attempts_after_failure,
        'final_task_result': postcondition(final) or ('DENIED' if s['flow'] == 'denial' else 'NO_OPERATION'),
        'tool_dispatch_count': len(events), 'accepted_side_effect_count': final.get('restart_count', 0),
        'side_effect_attempt_count': final.get('restart_attempt_count', 0),
        'verification_read_count': final.get('status_read_count', 0),
        'reported_input_tokens': usage_sum('input_tokens'), 'reported_output_tokens': usage_sum('output_tokens'),
        'total_reported_tokens': usage_sum('total_tokens'), 'usage_response_count': sum(bool(u) for u in usages),
        'responses_request_count': len(records), 'model_network_calls': 0 if lane == 'local-scripted' else None,
        'scripted_transport_requests': scripted_requests, 'end_to_end_seconds': elapsed,
        'first_output_seconds': None if lane == 'local-scripted' else next((r['first_output_seconds'] for r in records if r.get('first_output_seconds') is not None), None),
        'admission_failure_count': sum(is_admission_rejection(r.get('response', {})) for r in records),
        'concurrency_attribution': s.get('attribution'), 'records': records,
    }
