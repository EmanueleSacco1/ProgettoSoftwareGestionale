import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal

# --- Module Import Handling ---
try:
    from .. import ledger
    from .. import persistence as db
    from .. import documents as db_docs
except ImportError:
    import ledger
    import persistence as db
    import documents as db_docs

class TestLedger(unittest.TestCase):
    """
    Test suite for the 'ledger' (Prima Nota) module.
    Focuses on the interaction between financial movements and invoice statuses.
    """

    @patch('ledger.db_docs.update_document_status')
    @patch('ledger.db_docs.find_document_by_id')
    @patch('ledger.db.save_data')
    @patch('ledger.db.load_data')
    def test_create_movimento_from_invoice(
        self, mock_load_data, mock_save_data, mock_find_invoice, mock_update_status
    ):
        """
        Tests that creating a payment from an invoice correctly:
        1. Updates the invoice status to 'Pagato'.
        2. Creates a new 'Entrata' (Income) movement with the correct financial data.
        """
        # 1. Setup Mocks
        # Start with an empty ledger
        mock_load_data.return_value = [] 
        
        # Define the mock invoice that will be "paid"
        mock_invoice = {
            'id': 'inv123',
            'number': 'F2025/001',
            'status': 'In sospeso', # Key: starts as unpaid
            'client_id': 'client1',
            'taxable_amount': Decimal('1000'),
            'vat_amount': Decimal('220'),
            'ritenuta_amount': Decimal('200'),
            'total_da_pagare': Decimal('1020') # (1000 + 220) - 200
        }
        mock_find_invoice.return_value = mock_invoice
        
        # Simulate a successful status update
        mock_update_status.return_value = (True, "OK")
        
        payment_date = '2025-11-05'
        
        # 2. Execute Function
        success, msg = ledger.create_movimento_from_invoice('inv123', payment_date)
        
        # 3. Assertions
        self.assertTrue(success)
        
        # Verify the invoice status was changed to 'Pagato'
        mock_update_status.assert_called_once_with('inv123', 'Pagato')
        
        # Verify that the ledger was saved
        mock_save_data.assert_called_once()
        # Retrieve the list of movements that was passed to save_data
        saved_movimenti = mock_save_data.call_args[0][1]
        self.assertEqual(len(saved_movimenti), 1)
        
        # Inspect the new movement to ensure all data was copied correctly
        new_movimento = saved_movimenti[0]
        self.assertEqual(new_movimento['type'], 'Entrata')
        self.assertEqual(new_movimento['date'], payment_date)
        self.assertEqual(new_movimento['description'], "Incasso Fattura N. F2025/001")
        self.assertEqual(new_movimento['linked_invoice_id'], 'inv123')
        # Check that financial data matches the invoice
        self.assertEqual(new_movimento['amount_netto'], Decimal('1000'))
        self.assertEqual(new_movimento['amount_iva'], Decimal('220'))
        self.assertEqual(new_movimento['amount_ritenuta'], Decimal('200'))
        self.assertEqual(new_movimento['amount_totale'], Decimal('1020'))

    @patch('ledger.db_docs.update_document_status')
    @patch('ledger.db.save_data')
    @patch('ledger.db.load_data')
    def test_delete_movimento_reverts_invoice_status(
        self, mock_load_data, mock_save_data, mock_update_status
    ):
        """
        Tests the "undo" logic: deleting a linked payment movement
        must automatically revert the invoice's status back to 'In sospeso'.
        """
        # 1. Setup Mocks
        # Define a mock payment movement that is linked to an invoice
        mock_movimento = {
            'id': 'mov1',
            'description': 'Payment for invoice F2025/001',
            'linked_invoice_id': 'inv123' # The link
        }
        # Simulate the database containing this one movement
        mock_load_data.return_value = [mock_movimento]
        
        # 2. Execute Function
        success, msg = ledger.delete_movimento('mov1')
        
        # 3. Assertions
        self.assertTrue(success)
        
        # Critical: Verify that the linked invoice ('inv123') was
        # found and its status was reset to 'In sospeso'.
        mock_update_status.assert_called_once_with('inv123', 'In sospeso')
        
        # Verify that the movement was removed from the database
        # (save_data is called with an empty list)
        mock_save_data.assert_called_once_with(db.PRIMANOTA_DB, [])

    @patch('ledger.db_docs.update_document_status')
    @patch('ledger.db.save_data')
    @patch('ledger.db.load_data')
    def test_delete_movimento_no_link(
        self, mock_load_data, mock_save_data, mock_update_status
    ):
        """
        Tests that deleting a manual (un-linked) movement does NOT
        attempt to update any invoice status.
        """
        # 1. Setup Mocks
        mock_movimento = {
            'id': 'mov2',
            'description': 'Office supplies',
            'linked_invoice_id': None # No link
        }
        mock_load_data.return_value = [mock_movimento]
        
        # 2. Execute Function
        success, msg = ledger.delete_movimento('mov2')
        
        # 3. Assertions
        self.assertTrue(success)
        
        # Critical: Verify that the document status function was NOT called
        mock_update_status.assert_not_called()
        
        # Verify the movement was still deleted
        mock_save_data.assert_called_once_with(db.PRIMANOTA_DB, [])

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)