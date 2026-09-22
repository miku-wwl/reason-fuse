"""Funded budget accounting without any cloud/model access."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from cloud_budget import request_budget
from evaluation.runtime import BudgetStop


class CloudBudgetTests(unittest.TestCase):
    def manifest(self):
        return {'funded_budget': {'total_usd': 15, 'model_limit_usd': 8, 'missing_usage_reserve_usd': 0.1}}

    def test_missing_usage_reserves_cost_without_fabricating_tokens(self):
        m=self.manifest();b=request_budget(m,3,1000)
        b.reserve();b.observe({'status':'completed','usage':None})
        self.assertFalse(b.stopped)
        self.assertEqual(b.reported_tokens,0)
        self.assertEqual(b.snapshot()['unknown_usage_reserve_usd'],0.1)
        m['spend_ledger']=b.snapshot()
        next_budget=request_budget(m,2,1000)
        next_budget.reserve();next_budget.observe({'usage':{'input_tokens':100,'output_tokens':10,'total_tokens':110}})
        ledger=next_budget.snapshot()
        self.assertEqual(ledger['responses_reserved'],2)
        self.assertEqual(ledger['responses_with_unknown_usage'],1)
        self.assertEqual(ledger['reported_tokens'],110)
        self.assertAlmostEqual(ledger['accounted_model_usd'],0.100045)

    def test_inflight_reserve_and_deadline_stop_new_requests(self):
        m=self.manifest();m['spend_ledger']={'known_usage_usd':7.85}
        b=request_budget(m,3,1000);b.reserve()
        with self.assertRaises(BudgetStop):b.reserve()
        self.assertEqual(b.snapshot()['unknown_usage_reserve_usd'],0.1)
        m=self.manifest();m['model_deadline_utc']=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
        with self.assertRaises(BudgetStop):request_budget(m,2,1000).reserve()

    def test_unfunded_default_remains_fail_closed(self):
        b=request_budget({},2,1000);b.reserve();b.observe({'status':'failed','usage':None})
        with self.assertRaises(BudgetStop):b.reserve()
