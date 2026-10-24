"""Offline execution invariants; no generation or scheduler calls."""
import base64
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest

from dream_runs import finish, location, reserve


class RunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def test_concurrent_occurrence_is_claimed_once(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: reserve(self.root, 'daily-2026-01-01'), range(8)))
        self.assertEqual(sum(r['claimed'] for r in results), 1)

    def test_untrusted_key_cannot_escape_output(self):
        result = reserve(self.root, '../../outside/2026-01-01+08:00')
        self.assertTrue(Path(result['directory']).is_relative_to(self.root / 'runs'))

    def test_interrupted_reservation_is_not_reclaimed(self):
        location(self.root, 'slot').mkdir(parents=True)
        result = reserve(self.root, 'slot')
        self.assertFalse(result['claimed'])
        self.assertEqual(result['record']['status'], 'interrupted')

    def test_blocked_remains_deduplicated(self):
        reserve(self.root, 'slot')
        finish(self.root, 'slot', 'blocked', 'Library unavailable')
        self.assertFalse(reserve(self.root, 'slot')['claimed'])
        with self.assertRaises(ValueError):
            finish(self.root, 'slot', 'failed', 'Attempt to overwrite a terminal result')

    def test_complete_requires_local_raster_and_provenance(self):
        run = Path(reserve(self.root, 'slot')['directory'])
        with self.assertRaises(ValueError):
            finish(self.root, 'slot', 'complete', 'Missing artifacts')
        image = run / 'image.png'
        image.write_text('<html>not an image</html>')
        prompt = run / 'prompt.md'; prompt.write_text('Synthetic test prompt')
        brief = run / 'brief.md'; brief.write_text('Synthetic test source')
        with self.assertRaises(ValueError):
            finish(self.root, 'slot', 'complete', 'Wrong media', image, prompt, brief)
        image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aH1sAAAAASUVORK5CYII='))
        result = finish(self.root, 'slot', 'complete', 'Synthetic fixture; not a generation test', image, prompt, brief)
        self.assertEqual(result['record']['image'], 'image.png')
        self.assertFalse(reserve(self.root, 'slot')['claimed'])

    def test_external_artifact_cannot_complete_run(self):
        reserve(self.root, 'slot')
        outside = self.root / 'outside.png'; outside.write_text('unrelated')
        with self.assertRaises(ValueError):
            finish(self.root, 'slot', 'complete', 'Wrong source', outside, outside, outside)


if __name__ == '__main__':
    unittest.main()
