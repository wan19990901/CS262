import unittest
import os
import pandas as pd
from unittest.mock import MagicMock
from server import Server
import socket

class TestServerMethods(unittest.TestCase):
    def setUp(self):
        self.server = Server(server_id=0)
        self.accounts_df = pd.DataFrame({
            'Username': ['user1'],
            'ID': [1],
            'Active_Status': [True],
            'Connection': ["('127.0.0.1', 12345)"],
            'Queue': ['[]']
        })

        self.messages_df = pd.DataFrame({
            'Sender': ['user1'],
            'Receiver': ['user2'],
            'Message': ['Hello, user2!']
        })

    def test_read_and_write_accounts_csv(self):
        self.server.write_accounts_csv(self.accounts_df)
        read_accounts_df = self.server.read_accounts_csv()
        pd.testing.assert_frame_equal(read_accounts_df, self.accounts_df)

    def test_read_and_write_message_csv(self):
        self.server.write_message_csv(self.messages_df)
        read_messages_df = self.server.read_message_csv()
        pd.testing.assert_frame_equal(read_messages_df, self.messages_df)

    def test_get_connection_by_socket_string(self):
        self.server.active_connections = { "('127.0.0.1', 12345)": 'connection_object' }
        connection = self.server.get_connection_by_socket_string("('127.0.0.1', 12345)")
        self.assertEqual(connection, 'connection_object')

    def test_close_connection(self):
        # Create a pair of connected sockets
        client_sock, server_sock = socket.socketpair()
        self.server.close_connection(client_sock)
        with self.assertRaises(Exception):
            client_sock.sendall("test".encode())


if __name__ == '__main__':
    unittest.main()
