"""Explicitly funded closeout ledger; reservations are not measured usage."""
from datetime import datetime, timedelta, timezone
from evaluation.runtime import RequestBudget, BudgetStop


class FundedBudget(RequestBudget):
    def __init__(self, requests, tokens, manifest):
        super().__init__(requests, tokens)
        plan = manifest['funded_budget']
        if plan['total_usd'] != 15 or plan['model_limit_usd'] > 8:
            raise ValueError('This closeout is authorized only within the USD 15 envelope')
        self.limit = plan['model_limit_usd']
        self.reserve_usd = plan['missing_usage_reserve_usd']
        if not 0 < self.reserve_usd <= self.limit:
            raise ValueError('Positive explicit missing-usage reserve required')
        now = datetime.now(timezone.utc)
        manifest.setdefault('model_deadline_utc', (now + timedelta(minutes=90)).isoformat())
        self.deadline = datetime.fromisoformat(manifest['model_deadline_utc'])
        self.prior = dict(manifest.get('spend_ledger', {}))
        self.known = self.unknown = 0.0
        self.unknown_responses = self.pending = 0

    def snapshot(self):
        known = self.prior.get('known_usage_usd', 0) + self.known
        reserve = self.prior.get('unknown_usage_reserve_usd', 0) + self.unknown + self.pending*self.reserve_usd
        return {'known_usage_usd': round(known, 8), 'unknown_usage_reserve_usd': round(reserve, 8),
                'accounted_model_usd': round(known+reserve, 8),
                'responses_reserved': self.prior.get('responses_reserved', 0)+self.requests,
                'responses_with_unknown_usage': self.prior.get('responses_with_unknown_usage', 0)+self.unknown_responses+self.pending,
                'reported_tokens': self.prior.get('reported_tokens', 0)+self.reported_tokens,
                'note': 'Unknown usage reserve is an allowance, not a billed or observed cost; internal retries are not exposed.'}

    def reserve(self):
        ledger = self.snapshot()
        if (datetime.now(timezone.utc) >= self.deadline or ledger['responses_reserved'] >= 73
                or ledger['accounted_model_usd'] + self.reserve_usd > self.limit):
            self.stopped = True
            raise BudgetStop('Funded model allowance, 73-request bound or 90-minute deadline reached')
        super().reserve()
        self.pending += 1

    def observe(self, response):
        usage = response.get('usage') or {}
        self.pending -= 1
        if all(usage.get(key) is not None for key in ('input_tokens', 'output_tokens', 'total_tokens')):
            # Ignore cache discounts: conservative public GlobalStandard price.
            self.known += (usage['input_tokens']*0.25 + usage['output_tokens']*2)/1_000_000
            self.reported_tokens += usage['total_tokens']
        else:
            self.unknown += self.reserve_usd
            self.unknown_responses += 1
            if usage.get('total_tokens') is not None:
                self.reported_tokens += usage['total_tokens']
        self.stopped |= self.reported_tokens >= self.maximum_tokens or self.snapshot()['accounted_model_usd'] >= self.limit


def request_budget(manifest, requests, tokens):
    if manifest.get('funded_budget'):
        return FundedBudget(requests, tokens, manifest)
    return RequestBudget(requests, tokens)
