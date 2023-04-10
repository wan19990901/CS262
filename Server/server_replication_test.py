import unittest
from unittest.mock import MagicMock, patch
from server import Server, monitor_servers, check_server_health

class TestServerHealthFunctions(unittest.TestCase):
    def setUp(self):
        self.primary_server = Server(server_id=0)
        self.backup_server1 = Server(server_id=1)
        self.backup_server2 = Server(server_id=2)

        self.servers = [self.primary_server, self.backup_server1, self.backup_server2]

    @patch('socket.socket')
    def test_check_server_health_success(self, mock_socket):
        mock_socket.return_value.__enter__.return_value.recv.return_value = \
            "To get started on this chat room, please create or login your account first and type command as instructed in the documentation \n".encode()
        result = check_server_health(self.primary_server)
        self.assertTrue(result)

    @patch('socket.socket')
    def test_check_server_health_failure(self, mock_socket):
        mock_socket.return_value.__enter__.return_value.recv.return_value = \
            "Invalid response".encode()
        result = check_server_health(self.primary_server)
        self.assertFalse(result)

    @patch('socket.socket')
    def test_check_server_health_exception(self, mock_socket):
        mock_socket.return_value.__enter__.return_value.recv.side_effect = Exception("Socket error")
        result = check_server_health(self.primary_server)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
