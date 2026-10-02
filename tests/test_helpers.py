import unittest

from main import is_hex_address, is_tx_hash, slug_for_filename


class ValidationTests(unittest.TestCase):
    def test_valid_address(self):
        self.assertTrue(is_hex_address("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"))

    def test_invalid_address_length(self):
        self.assertFalse(is_hex_address("0xabc"))

    def test_valid_tx_hash(self):
        self.assertTrue(
            is_tx_hash(
                "0x" + "a" * 64,
            )
        )

    def test_invalid_tx_hash(self):
        self.assertFalse(is_tx_hash("0x" + "a" * 62))


class SlugTests(unittest.TestCase):
    def test_strips_prefix(self):
        self.assertEqual(slug_for_filename("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"), "d8da6bf26964")


if __name__ == "__main__":
    unittest.main()
