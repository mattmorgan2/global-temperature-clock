import csv
from datetime import date
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from temperature_pipeline.completeness import (
    START, END, QC_FLAGS, analyze_daily, coverage_metrics, daily_source,
    parse_daily, passes_threshold, run_completeness,
)
from temperature_pipeline.metadata import sha256

FIXTURE = Path(__file__).parent / 'fixtures' / 'daily.dly'


class CompletenessTests(unittest.TestCase):
    def test_daily_fixed_width_and_leap_centuries(self):
        lines = FIXTURE.read_text().splitlines()
        station, year, month, element, values = parse_daily(lines[0], 'US000000001')
        self.assertEqual((station, year, month, element), ('US000000001', 2000, 2, 'TMAX'))
        self.assertEqual(len(values), 29)
        self.assertEqual(values[2], (100, ' ', 'X', '0'))
        self.assertEqual(values[3], (100, 'H', ' ', 'S'))
        self.assertEqual(len(parse_daily(lines[2])[4]), 28)  # 1900 is not leap
        self.assertEqual((END - START).days + 1, 36525)

    def test_missing_and_qflags_with_measurement_and_source_allowed(self):
        metrics, flags = analyze_daily(FIXTURE, 'US000000001', date(2000, 2, 1), date(2000, 2, 29))
        self.assertEqual(metrics['total_calendar_days'], 29)
        self.assertEqual(metrics['valid_tmax_days'], 28)
        self.assertEqual(metrics['valid_tmin_days'], 27)
        self.assertEqual(metrics['both_valid_days'], 26)
        self.assertEqual(metrics['incomplete_days'], 3)
        self.assertEqual(metrics['longest_incomplete_run_days'], 2)
        self.assertEqual(flags, {'?': 1, 'X': 1})

    def test_all_documented_and_unknown_qflags_rejected(self):
        line = FIXTURE.read_text().splitlines()[0]
        for flag in QC_FLAGS + '?':
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as directory:
                content = line[:27] + flag + line[28:]
                path = Path(directory) / 'test.dly'
                path.write_text(content + '\n')
                metrics, flags = analyze_daily(path, 'US000000001', date(2000, 2, 1), date(2000, 2, 1))
                self.assertEqual(metrics['valid_tmax_days'], 0)
                self.assertEqual(flags, {flag: 1})

    def test_absent_element_and_absent_month_are_incomplete(self):
        metrics, _ = analyze_daily(FIXTURE, 'US000000001', date(2001, 1, 1), date(2001, 2, 28))
        self.assertEqual(metrics['valid_tmax_days'], 30)  # one QC rejection
        self.assertEqual(metrics['valid_tmin_days'], 0)
        self.assertEqual(metrics['both_valid_days'], 0)
        self.assertEqual(metrics['longest_incomplete_run_days'], 59)

    def test_longest_gap_including_edges_and_across_month_boundary(self):
        metrics = coverage_metrics([0, 0, 1, 1, 0, 0, 0], [1] * 7)
        self.assertEqual(metrics['longest_incomplete_run_days'], 3)
        self.assertEqual(coverage_metrics([1] * 7, [1] * 7)['longest_incomplete_run_days'], 0)
        with tempfile.TemporaryDirectory() as directory:
            line = FIXTURE.read_text().splitlines()[3]
            path = Path(directory) / 'gap.dly'
            # Last days of December are absent; January 1 is complete, January 2 missing TMIN.
            tmin = line[:17] + 'TMIN' + line[21:29] + f'{-9999:5d}   ' + line[37:]
            path.write_text(line+'\n'+tmin+'\n')
            metrics, _ = analyze_daily(path, 'US000000001', date(2000, 12, 29), date(2001, 1, 2))
            self.assertEqual(metrics['longest_incomplete_run_days'], 3)

    def test_exact_threshold_uses_counts_not_rounded_percentages(self):
        self.assertTrue(passes_threshold(95, 100))
        self.assertFalse(passes_threshold(94, 100))
        self.assertTrue(passes_threshold(34699, 36525))
        self.assertFalse(passes_threshold(34698, 36525))
        self.assertFalse(passes_threshold(949999, 1000000))

    def test_malformed_and_duplicate_months_fail(self):
        line = FIXTURE.read_text().splitlines()[0]
        with self.assertRaises(ValueError): parse_daily(line[:-1])
        with self.assertRaises(ValueError): parse_daily(line, 'CA000000002')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'duplicate.dly'
            path.write_text(line+'\n'+line+'\n')
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                analyze_daily(path, 'US000000001')

    def test_cache_download_reuse_revalidation_and_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            response = io.BytesIO(FIXTURE.read_bytes())
            response.headers = {'ETag': 'v1'}
            with patch('temperature_pipeline.completeness.urlopen', return_value=response) as network:
                path, metadata = daily_source(directory, 'US000000001')
                self.assertEqual(metadata['sha256'], sha256(path))
                daily_source(directory, 'US000000001')
                network.assert_called_once()
            with patch('temperature_pipeline.completeness.urlopen', side_effect=HTTPError('url',304,'Not Modified',{},None)) as network:
                self.assertEqual(daily_source(directory, 'US000000001', refresh=True)[0], path)
                self.assertEqual(network.call_args.args[0].get_header('If-none-match'), 'v1')
            path.write_text('corrupted')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                daily_source(directory, 'US000000001', offline=True)

    def test_failed_station_retains_cache_without_publishing_partial_results(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.csv'
            source.write_text('station_id,country_code,country_name\nUS000000001,US,United States\n')
            output = root / 'out'
            with self.assertRaisesRegex(ValueError, '1 stations failed'):
                run_completeness(source, root / 'cache', output, offline=True)
            self.assertIn('US000000001', json.loads((output / 'failures.json').read_text()))
            self.assertFalse((output / 'station-completeness.csv').exists())
            self.assertFalse((output / 'summary.json').exists())

    def test_offline_pipeline_outputs_resume_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_csv = root / 'input.csv'
            input_csv.write_text('station_id,station_name,country_code,country_name\nUS000000001,TEST,US,United States\n')
            cache = root / 'cache'
            cache.mkdir()
            path = cache / 'fixture.dly'
            path.write_bytes(FIXTURE.read_bytes())
            (cache / 'US000000001.json').write_text(json.dumps({'cache_file': path.name, 'sha256': sha256(path), 'url': 'fixture', 'retrieved_at': 'fixture'}))
            with patch('temperature_pipeline.completeness.urlopen') as network:
                summary = run_completeness(input_csv, cache, root / 'out', offline=True)
                network.assert_not_called()
            self.assertEqual(summary['first_pass_station_count'], 1)
            self.assertEqual(summary['second_stage_qualifying_count'], 0)
            self.assertIsNone(summary['minimum_completeness_percent_passing_stations'])
            with patch('temperature_pipeline.completeness.analyze_daily') as analyze:
                run_completeness(input_csv, cache, root / 'out', offline=True)
                analyze.assert_not_called()
            with (root / 'out/station-completeness.csv').open() as source:
                row = next(csv.DictReader(source))
            self.assertEqual(row['station_name'], 'TEST')
            provenance = json.loads((root / 'out/provenance.json').read_text())
            self.assertEqual(provenance['input_csv']['sha256'], sha256(input_csv))
            self.assertEqual(provenance['output_sha256']['station-completeness.csv'], sha256(root / 'out/station-completeness.csv'))


if __name__ == '__main__':
    unittest.main()
