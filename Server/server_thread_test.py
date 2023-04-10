import unittest
import socket
import pandas as pd
import time
from unittest.mock import MagicMock
from server import Server, check_server_health, monitor_servers
from threading import Thread

class TestServerThreaded(unittest.TestCase):
    def setUp(self):
        self.server = Server(server_id=0)
        self.server.active_connections = {}

        # Mock read_accounts_csv and write_accounts_csv methods
        self.server.read_accounts_csv = MagicMock(return_value=pd.DataFrame({
            'Username': ['user1'],
            'ID': [1],
            'Active_Status': [True],
            'Connection': ["('127.0.0.1', 12345)"],
            'Queue': ['[]']
        }))
        self.server.write_accounts_csv = MagicMock()

    def test_threaded(self):
        # Create a pair of connected sockets
        client_sock, server_sock = socket.socketpair()

        # Start the threaded method in a separate thread
        server_thread = Thread(target=self.server.threaded, args=(server_sock,))
        server_thread.start()

        # Send opcode 1 (account creation) from the client
        client_sock.sendall("1|user2".encode())
        response = client_sock.recv(1024).decode()
        self.assertEqual(response, "Success New Account Creation! Your new Account ID: 2\n")

        # Send opcode 2 (list accounts) from the client
        client_sock.sendall("2|".encode())
        response = client_sock.recv(1024).decode()
        self.assertTrue("Showing all accounts" in response)

        # Send opcode 4 (pop undelivered) from the client
        client_sock.sendall("4|1".encode())
        response = client_sock.recv(1024).decode()
        self.assertEqual(response, "No new messages\n")

        # Send opcode 5 (delete account) from the client
        client_sock.sendall("5|1".encode())
        response = client_sock.recv(1024).decode()
        self.assertEqual(response, "Your account has been deleted\n")

        # Close the client socket to simulate client disconnection
        client_sock.close()

        # Wait for the server thread to finish
        server_thread.join()

if __name__ == '__main__':
    unittest.main()
