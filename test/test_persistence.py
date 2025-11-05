import unittest
from unittest.mock import patch
from datetime import datetime

# --- Module Import Handling ---
try:
    from .. import persistence
except ImportError:
    import persistence

class TestPersistence(unittest.TestCase):
    """
    Test suite for the 'persistence' module.
    Focuses on testing the business logic within the persistence layer,
    specifically the document numbering and year-end rollover.
    """

    @patch('persistence.save_settings')
    @patch('persistence.load_settings')
    @patch('persistence.datetime') # Mock the datetime module
    def test_get_next_document_number_simple_increment(
        self, mock_datetime, mock_load_settings, mock_save_settings
    ):
        """
        Tests the standard increment of a document number within the same year.
        """
        # 1. Setup Mocks
        # Simulate that we are currently in 2025
        mock_datetime.now.return_value = datetime(2025, 6, 15)
        
        # Simulate the settings loaded from disk
        mock_settings = {
            'last_invoice_num': 41,
            'invoice_prefix': "F2025/",
            'last_quote_num': 10,
            'quote_prefix': "P2025/",
        }
        mock_load_settings.return_value = mock_settings
        
        # 2. Execute Function
        next_num = persistence.get_next_document_number(doc_type="invoice")
        
        # 3. Assertions
        # The number should be the last number (41) + 1, formatted
        self.assertEqual(next_num, "F2025/042")
        
        # Verify that the settings were saved
        mock_save_settings.assert_called_once()
        # Inspect the dictionary that was passed to save_settings
        saved_settings = mock_save_settings.call_args[0][0]
        
        # Check that the number was incremented in the saved data
        self.assertEqual(saved_settings['last_invoice_num'], 42)
        # Check that the quote number was left untouched
        self.assertEqual(saved_settings['last_quote_num'], 10)

    @patch('persistence.save_settings')
    @patch('persistence.load_settings')
    @patch('persistence.datetime') # Mock the datetime module
    def test_get_next_document_number_year_rollover(
        self, mock_datetime, mock_load_settings, mock_save_settings
    ):
        """
        Tests the critical "year-end rollover" logic.
        Verifies that when the year changes, the prefix is updated
        and the document counter is reset to 1.
        """
        # 1. Setup Mocks
        # Simulate that we are now in 2026
        mock_datetime.now.return_value = datetime(2026, 1, 1)
        
        # Simulate settings loaded from disk, which are from the *previous* year
        mock_settings = {
            'last_invoice_num': 99,
            'invoice_prefix': "F2025/", # Old prefix
            'last_quote_num': 50,
            'quote_prefix': "P2025/",
        }
        mock_load_settings.return_value = mock_settings
        
        # 2. Execute Function
        next_num = persistence.get_next_document_number(doc_type="invoice")
        
        # 3. Assertions
        # The number should reset to 1 and the prefix should update to 2026
        self.assertEqual(next_num, "F2026/001")
        
        # Verify that the settings were saved
        mock_save_settings.assert_called_once()
        saved_settings = mock_save_settings.call_args[0][0]
        
        # Check that the number was reset to 1 in the saved data
        self.assertEqual(saved_settings['last_invoice_num'], 1)
        # Check that the prefix was updated
        self.assertEqual(saved_settings['invoice_prefix'], "F2026/")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)