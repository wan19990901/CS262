import unittest
import socket
import pandas as pd
from unittest.mock import MagicMock
from server import Server, HEALTH_CHECK_MSG

class TestServer(unittest.TestCase):
    def setUp(self):
        self.server = Server(server_id=0)
        self.server.active_connections = {}

    def test_account_creation(self):
        self.server.read_accounts_csv = MagicMock(return_value=pd.DataFrame({
            'Username': ['user1'],
            'ID': [1],
            'Active_Status': [True],
            'Connection': ["('127.0.0.1', 12345)"],
            'Queue': ['[]']
        }))
        self.server.write_accounts_csv = MagicMock()
        self.server.notify_backup_servers = MagicMock()

        connection = MagicMock()
        connection.getpeername.return_value = ('127.0.0.1', 12346)

        result = self.server.account_creation("user2", connection)
        self.assertEqual(result, "Success New Account Creation! Your new Account ID: 2\n")

        result_duplicate = self.server.account_creation("user1", connection)
        self.assertEqual(result_duplicate, "Username user1 already exists. Please try a different username.")

    def test_list_accounts(self):
        self.server.read_accounts_csv = MagicMock(return_value=pd.DataFrame({'Username': ['user1', 'user2', 'user3']}))

        result = self.server.list_accounts("user.")
        self.assertEqual(result, "Account matched: user1,user2,user3\n")

    def test_pop_undelivered(self):
        self.server.read_accounts_csv = MagicMock(return_value=pd.DataFrame({
            'Username': ['user1'],
            'ID': [1],
            'Active_Status': [True],
            'Connection': ["('127.0.0.1', 12345)"],
            'Queue': ["['msg1', 'msg2']"]
        }))
        self.server.write_accounts_csv = MagicMock()
        self.server.notify_backup_servers = MagicMock()

        result = self.server.pop_undelivered(1)
        self.assertEqual(result, "Undelivered messages for user ID 1: \nmsg1\nmsg2\n")

    def test_delete_account(self):
        self.server.read_accounts_csv = MagicMock(return_value=pd.DataFrame({
            'Username': ['user1'],
            'ID': [1],
            'Active_Status': [True],
            'Connection': ["('127.0.0.1', 12345)"],
            'Queue': ['[]']
        }))
        self.server.write_accounts_csv = MagicMock()
        self.server.notify_backup_servers = MagicMock()

        result = self.server.delete_account(1)
        self.assertEqual(result, "Your account has been deleted\n")

if __name__ == '__main__':
    unittest.main()


