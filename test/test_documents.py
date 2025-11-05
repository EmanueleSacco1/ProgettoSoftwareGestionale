import unittest
from unittest.mock import patch, MagicMock, ANY
from decimal import Decimal

# --- Module Import Handling ---
# This allows tests to run whether the 'Test' folder is treated
# as a package (e.g., 'python -m unittest') or as a simple script.
try:
    # Attempt package-relative imports
    from .. import documents
    from .. import persistence as db
    from .. import inventory as db_magazzino
    from .. import address_book as db_rubrica
except ImportError:
    # Fallback to direct imports for script-based execution
    import documents
    import persistence as db
    import inventory as db_magazzino
    import address_book as db_rubrica

class TestDocuments(unittest.TestCase):
    """
    Test suite for the 'documents' module.
    Focuses on financial calculations and interactions with other modules
    like inventory and persistence.
    """

    def test_calculate_totals_complex(self):
        """
        Tests the _calculate_totals function with all financial components:
        discount, VAT (IVA), and withholding tax (ritenuta).
        
        This is a pure logic test, ensuring the math is correct.
        """
        # Define line items. Subtotal should be 200.
        items = [
            {'qty': '2', 'unit_price': '50'},  # 100
            {'qty': '1', 'unit_price': '100'}  # 100
        ]
        
        # Expected calculation flow:
        # Subtotal: 200
        # Discount (10%): 20
        # Taxable Amount: 180
        # VAT (22% on 180): 39.60
        # Gross Total: 219.60
        # Withholding Tax (20% on 180): 36
        # Final Amount Due (Net): 219.60 - 36 = 183.60
        
        totals = documents._calculate_totals(
            items,
            discount_perc=Decimal('10'),
            vat_perc=Decimal('22'),
            ritenuta_perc=Decimal('20')
        )
        
        # Verify each step of the calculation
        self.assertEqual(totals['subtotal'], Decimal('200.00'))
        self.assertEqual(totals['discount_amount'], Decimal('20.00'))
        self.assertEqual(totals['taxable_amount'], Decimal('180.00'))
        self.assertEqual(totals['vat_amount'], Decimal('39.60'))
        self.assertEqual(totals['total'], Decimal('219.60'))
        self.assertEqual(totals['ritenuta_amount'], Decimal('36.00'))
        self.assertEqual(totals['total_da_pagare'], Decimal('183.60'))

    @patch('documents.db.save_data')
    @patch('documents.db_magazzino.update_stock')
    @patch('documents.db_rubrica.find_contact_by_id')
    @patch('documents.db.get_next_document_number')
    @patch('documents.db.load_data')
    def test_create_invoice_updates_stock(
        self, mock_load_data, mock_get_next_num, mock_find_client, 
        mock_update_stock, mock_save_data
    ):
        """
        Tests the interaction between 'documents' and 'inventory'.
        Verifies that creating an invoice successfully calls 'update_stock'
        with the correct (negative) quantity.
        """
        # 1. Setup Mocks
        # Simulate an empty database to start
        mock_load_data.return_value = []
        # Provide a document number
        mock_get_next_num.return_value = "F2025/001"
        # Simulate a valid client
        mock_find_client.return_value = {'id': 'client1', 'name': 'Test Client'}
        # Simulate a successful stock update
        mock_update_stock.return_value = (True, "Stock updated successfully")
        
        # Define invoice items linked to an inventory item
        items = [{
            'qty': '2', 
            'unit_price': '50', 
            'description': 'Test Item', 
            'articolo_id': 'item_id_123' # This item ID links to inventory
        }]
        
        # 2. Execute Function
        invoice = documents.create_invoice(
            client_id='client1',
            project_id=None,
            items=items,
            discount_perc=Decimal('0'),
            vat_perc=Decimal('22'),
            ritenuta_perc=Decimal('0'),
            due_date='2025-12-31',
            notes=""
        )
        
        # 3. Assertions
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice['number'], "F2025/001")
        
        # Critical: Verify that update_stock was called EXACTLY once,
        # with the item ID and a NEGATIVE quantity.
        mock_update_stock.assert_called_once_with('item_id_123', Decimal('-2'))
        
        # Verify that the new invoice was saved to the database
        mock_save_data.assert_called_once_with(db.DOCUMENTI_DB, [invoice])

    @patch('documents.db.save_data')
    @patch('documents.db_magazzino.update_stock')
    @patch('documents.db_rubrica.find_contact_by_id')
    def test_create_invoice_fails_on_stock_error(
        self, mock_find_client, mock_update_stock, mock_save_data
    ):
        """
        Tests the "sad path" (failure case).
        Verifies that the invoice creation is aborted and an exception is raised
        if the inventory 'update_stock' function reports a failure.
        """
        # 1. Setup Mocks
        # Simulate a valid client
        mock_find_client.return_value = {'id': 'client1', 'name': 'Test Client'}
        # Simulate a FAILED stock update (e.g., insufficient stock)
        mock_update_stock.return_value = (False, "Stock insufficiente")
        
        items = [{'qty': '2', 'unit_price': '50', 'articolo_id': 'item_id_123'}]
        
        # 2. Execute and Assert Exception
        # Use assertRaises to catch the expected error
        with self.assertRaises(ValueError) as context:
            documents.create_invoice(
                client_id='client1', project_id=None, items=items,
                discount_perc=Decimal('0'), vat_perc=Decimal('0'), 
                ritenuta_perc=Decimal('0'), due_date='2025-12-31'
            )
        
        # Check that the exception message contains the stock error
        self.assertIn("Stock update failed", str(context.exception))
        
        # Critical: Verify that NO data was saved to the database
        mock_save_data.assert_not_called()

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)