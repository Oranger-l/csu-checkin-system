from datetime import datetime
import os
import unittest
from unittest.mock import Mock, patch

import local_runner as runner


class LocalRunnerTests(unittest.TestCase):
    def test_plan_covers_full_window_and_reuses_chosen_time(self):
        current = datetime(2026, 10, 23, 9, 0, tzinfo=runner.ZONE)
        first = runner.make_plan(current, {}, choose=lambda n: 0)
        last = runner.make_plan(current, {}, choose=lambda n: n - 1)
        self.assertEqual(first['planned_at'], '2026-10-23T20:13:00+08:00')
        self.assertEqual(last['planned_at'], '2026-10-23T20:23:00+08:00')
        self.assertEqual(runner.make_plan(current, last), last)

    def test_late_wakeup_never_schedules_in_past(self):
        current = datetime(2026, 10, 23, 20, 18, 3, 500000, tzinfo=runner.ZONE)
        plan = runner.make_plan(current, {}, choose=lambda n: 0)
        self.assertGreaterEqual(datetime.fromisoformat(plan['planned_at']), current)

    def test_closed_window_is_skipped_and_success_is_preserved(self):
        current = datetime(2026, 10, 23, 23, 0, tzinfo=runner.ZONE)
        self.assertEqual(runner.make_plan(current, {})['phase'], 'window_closed')
        done = {'date': '2026-10-23', 'phase': 'submitted'}
        self.assertEqual(runner.make_plan(current, done), done)

    def invoke(self, *, submit=False, can=True, kdk=True, already=0):
        client = Mock()
        client.query_dkbc.return_value = {'code': '200', 'data': {'dkbc': 'test-shift', 'kdk': kdk, 'sfydk': already}}
        client.check_range.return_value = {'code': '200', 'data': {'canDk': can}}
        client.submit.return_value = {'code': '200'}
        with patch.dict(os.environ, {'CHECKIN_LNG': '112.947959', 'CHECKIN_LAT': '28.144836', 'CHECKIN_COORD': 'gcj02'}), \
                patch.object(runner, 'load_environment'), patch.object(runner, 'get_auth', return_value=('test', 'test')), \
                patch.object(runner, 'CheckinClient', return_value=client):
            result = runner.run_once(submit=submit)
        return result, client

    def test_dry_run_checks_supplied_coordinates_and_never_submits(self):
        result, client = self.invoke()
        self.assertEqual(result['phase'], 'dry_run')
        client.check_range.assert_called_once_with(112.947959, 28.144836, 'PA')
        client.submit.assert_not_called()

    def test_range_failure_never_submits(self):
        result, client = self.invoke(submit=True, can=False)
        self.assertEqual(result['phase'], 'out_of_range')
        client.submit.assert_not_called()

    def test_already_checked_never_submits(self):
        result, client = self.invoke(submit=True, already='1')
        self.assertEqual(result['phase'], 'already_checked')
        client.submit.assert_not_called()

    def test_string_false_does_not_allow_checkin(self):
        result, client = self.invoke(submit=True, kdk='false')
        self.assertEqual(result['phase'], 'outside_period')
        client.submit.assert_not_called()

    def test_success_submits_once_at_supplied_location(self):
        result, client = self.invoke(submit=True)
        self.assertEqual(result['phase'], 'submitted')
        client.submit.assert_called_once_with(112.947959, 28.144836, 'test-shift', dkdz='')


if __name__ == '__main__':
    unittest.main()
