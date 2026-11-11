from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import csv
import io
import json
import unittest

from temperature_pipeline.metadata import (
    FILENAMES, Inventory, cached_source, parse_country, parse_inventory,
    parse_station, qualifying_stations, read_records, run, sha256,
)

FIXTURES = Path(__file__).parent / 'fixtures'


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.stations = list(read_records(FIXTURES / FILENAMES[0], parse_station))
        self.inventory = list(read_records(FIXTURES / FILENAMES[1], parse_inventory))
        self.countries = dict(read_records(FIXTURES / FILENAMES[2], parse_country))

    def test_fixed_width_station(self):
        station = self.stations[0]
        self.assertEqual(station.station_id, 'US000000001')
        self.assertEqual(station.station_name, 'ALPHA, TEST')
        self.assertEqual(station.country_code, 'US')
        self.assertEqual((station.latitude, station.longitude, station.elevation), (-12.3456, -123.4567, 123.4))
        self.assertIsNone(self.stations[1].elevation)

    def test_fixed_width_inventory_and_country(self):
        self.assertEqual(self.inventory[0], Inventory('US000000001', 'TMAX', 1926, 2040))
        self.assertEqual(self.countries, {'US': 'United States', 'CA': 'Canada'})

    def test_malformed_records_fail(self):
        for parser in (parse_station, parse_inventory, parse_country):
            with self.subTest(parser=parser), self.assertRaises(ValueError):
                parser('bad')
        line = (FIXTURES / FILENAMES[1]).read_text().splitlines()[0]
        with self.assertRaises(ValueError):
            parse_inventory(line[:36] + '2041 2040')

    def test_both_elements_inclusive_boundaries_and_country_join(self):
        rows = qualifying_stations(self.stations, self.inventory, self.countries, 2040)
        self.assertEqual([r.station_id for r in rows], ['US000000001'])
        self.assertEqual(rows[0].country_name, 'United States')
        self.assertEqual((rows[0].tmax_first_year, rows[0].tmin_first_year), (1926, 1900))
        self.assertEqual(qualifying_stations(self.stations, self.inventory, self.countries, 2041), [])

    def test_each_element_required_and_each_endpoint_checked(self):
        for element in ('TMAX', 'TMIN'):
            with self.subTest(element=element):
                records = [r for r in self.inventory if r.element != element]
                self.assertEqual(qualifying_stations(self.stations, records, self.countries, 2040), [])
                for changes in ({'first_year': 1927}, {'last_year': 2039}):
                    records = [replace(r, **changes) if r.element == element else r for r in self.inventory]
                    self.assertEqual(qualifying_stations(self.stations, records, self.countries, 2040), [])

    def test_duplicate_and_missing_joins_fail(self):
        for stations, inventory, countries in (
            (self.stations, self.inventory + [self.inventory[0]], self.countries),
            (self.stations + [self.stations[0]], self.inventory, self.countries),
            (self.stations[1:], self.inventory, self.countries),
            (self.stations, self.inventory, {}),
        ):
            with self.subTest(), self.assertRaises(ValueError):
                qualifying_stations(stations, inventory, countries, 2040)

    def seed_cache(self, cache):
        for filename in FILENAMES:
            path = cache / filename
            path.write_bytes((FIXTURES / filename).read_bytes())
            metadata = {'url': 'https://example.invalid/' + filename,
                        'retrieved_at': 'fixture', 'sha256': sha256(path), 'cache_file': filename}
            (cache / (filename + '.json')).write_text(json.dumps(metadata))

    def test_offline_outputs_provenance_and_repeatability(self):
        with TemporaryDirectory() as directory, patch('temperature_pipeline.metadata.urlopen') as network:
            cache = Path(directory)
            self.seed_cache(cache)
            output = cache / 'output'
            summary = run(cache, output, year=2040, offline=True)
            self.assertEqual(summary['total_qualifying_stations'], 1)
            self.assertEqual(summary['by_country'], [{'country_code': 'US', 'country_name': 'United States', 'count': 1}])
            with (output / 'qualifying-stations.csv').open() as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(rows[0]['station_name'], 'ALPHA, TEST')
            original = (output / 'qualifying-stations.csv').read_bytes()
            run(cache, output, year=2040, offline=True)
            self.assertEqual((output / 'qualifying-stations.csv').read_bytes(), original)
            provenance = json.loads((output / 'provenance.json').read_text())
            self.assertEqual(provenance['output_sha256'], sha256(output / 'qualifying-stations.csv'))
            self.assertEqual(len(provenance['sources']), 3)
            network.assert_not_called()

    def test_default_year_is_current_utc_year(self):
        with TemporaryDirectory() as directory:
            cache = Path(directory)
            self.seed_cache(cache)
            summary = run(cache, cache / 'out', offline=True)
            self.assertEqual(summary['target_year'], datetime.now(timezone.utc).year)

    def test_download_refresh_preserves_snapshots_and_cache_reuses_bytes(self):
        with TemporaryDirectory() as directory:
            cache = Path(directory)
            response = io.BytesIO(b'first snapshot')
            response.headers = {'ETag': 'version-1'}
            with patch('temperature_pipeline.metadata.urlopen', return_value=response) as network:
                first, metadata = cached_source(cache, FILENAMES[0])
                self.assertEqual(metadata['sha256'], sha256(first))
                self.assertEqual(metadata['http_headers']['ETag'], 'version-1')
                self.assertTrue(metadata['retrieved_at'])
                same, _ = cached_source(cache, FILENAMES[0])
                self.assertEqual(same, first)
                network.assert_called_once()
            response = io.BytesIO(b'second snapshot')
            response.headers = {}
            with patch('temperature_pipeline.metadata.urlopen', return_value=response):
                second, _ = cached_source(cache, FILENAMES[0], refresh=True)
            self.assertNotEqual(first, second)
            self.assertEqual(first.read_bytes(), b'first snapshot')
            with patch('temperature_pipeline.metadata.urlopen', side_effect=OSError('network failed')):
                with self.assertRaisesRegex(OSError, 'network failed'):
                    cached_source(cache, FILENAMES[0], refresh=True)
            self.assertEqual(cached_source(cache, FILENAMES[0], offline=True)[0], second)

    def test_missing_and_corrupted_cache_fail_without_network(self):
        with TemporaryDirectory() as directory, patch('temperature_pipeline.metadata.urlopen') as network:
            cache = Path(directory)
            with self.assertRaises(ValueError):
                cached_source(cache, FILENAMES[0], offline=True)
            self.seed_cache(cache)
            (cache / FILENAMES[0]).write_text('corrupted')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                cached_source(cache, FILENAMES[0], offline=True)
            network.assert_not_called()


if __name__ == '__main__':
    unittest.main()
