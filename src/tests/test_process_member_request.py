import unittest
from unittest.mock import patch, MagicMock
import super_admin

class TestProcessTravellerRequest(unittest.TestCase):

    @patch('builtins.input', side_effect=[
        "John", "Doe",                  # First and last name
        "1995-05-20",                   # Birthday
        "Male",                         # Gender
        "Main Street",                  # Street
        "123",                          # House number
        "1234AB",                       # Zip code
        "Rotterdam",                    # City
        "john.doe@example.com",         # Email
        "12345678",                     # Mobile (8 digits)
        "AB1234567"                     # Driving license
    ])
    @patch('builtins.print')
    @patch('sqlite3.connect')
    def test_process_traveller_request(self, mock_connect, mock_print, mock_input):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = None
        mock_cursor.execute.return_value = mock_cursor

        super_admin.add_traveller("super_admin")

        self.assertTrue(mock_cursor.execute.called)
        self.assertTrue(mock_connection.commit.called)
        self.assertTrue(mock_connection.close.called)

        mock_print.assert_any_call("Traveller registered successfully")

if __name__ == '__main__':
    unittest.main()
