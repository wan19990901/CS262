import socket
import re
from _thread import *
import pandas as pd
import os
import time
import io
import multiprocessing

HEALTH_CHECK_MSG = "HEALTH_CHECK"
class Server:
    err_msg = 'Please give a valid input as instructed in the documentation'
    def __init__(self,server_id, is_master = True, backup_servers=[]):
        self.master = is_master
        self.server_id = server_id
        self.account_file = f'accounts_{self.server_id}.csv'
        self.message_file = f'messages_{self.server_id}.csv'
        self.host = 'localhost'
        self.port = 6666 + self.server_id
        self.active_connections = {}
        self.backup_servers = backup_servers
        if not os.path.exists(self.account_file):
            columns = ['Username', 'ID', 'Active_Status', 'Connection','Queue']
            pd.DataFrame(columns=columns).to_csv(self.account_file, index=False)
        if not os.path.exists(self.message_file):
            columns = ['Sender', 'Receiver', 'Message', 'Time']
            pd.DataFrame(columns=columns).to_csv(self.message_file, index=False)
        # p_lock = threading.Lock()
    def read_accounts_csv(self):
        return pd.read_csv(self.account_file)
    def write_accounts_csv(self, data):
        data.to_csv(self.account_file, index=False)
    def read_message_csv(self):
        return pd.read_csv(self.message_file)
    def write_message_csv(self, data):
        data.to_csv(self.message_file, index=False)
    def update_csv_file(self, file_name, data):
        data = pd.read_csv(data)
        if(file_name == 'message'):
            self.write_message_csv(data)
        else:
            self.write_accounts_csv(data)
    def get_connection_by_socket_string(self, socket_string):
        if socket_string in self.active_connections:
            return self.active_connections[socket_string]
    def close_connection(self, connection):
        connection.close()
    def notify_backup_servers(self, file_name, data):
        if self.master:
            for backup_server in self.backup_servers:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((backup_server.host, backup_server.port))
                        print('checking notify')
                        print(type(data))
                        s.send(f"update,{file_name},{data}".encode('ascii'))
                        s.recv(1024)
                except Exception as e:
                    print(f"Error notifying backup server {backup_server['id']}: {e}")

    def start_server(self):
        """
        Start the chat room server, listening on the given host and port.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        print("socket binded to port", self.port)
        # put the socket into listening mode
        s.listen(5)
        print("socket is listening")
    # a forever loop until client wants to exit
        while True:
            # establish connection with client
            c, addr = s.accept()
            if(not self.master):
                data = c.recv(1024).decode('ascii')
                try: # For update
                    if(data == HEALTH_CHECK_MSG):
                        data = "To get started on this chat room, please create or login your account first and type command as instructed in the documentation \n"
                        c.send(data.encode('ascii'))
                    elif(data == 'master'):
                        self.master = True
                        # print('Becoming the master')
                        data = "To get started on this chat room, please create or login your account first and type command as instructed in the documentation \n"
                        c.send(data.encode('ascii'))
                        # Start a new thread and return its identifier
                        start_new_thread(self.threaded, (c,))
                    else:
                        tokens = data.split(',')
                        cmd = tokens[0]
                        if cmd == "update":
                            file_name, data = tokens[1], tokens[2]
                            self.update_csv_file(file_name, data)
                except Exception as e: # For check health
                    print(e)
                    print('checking backup server health failed')

            else:
                # print('In the master')
                data = "To get started on this chat room, please create or login your account first and type command as instructed in the documentation \n"
                c.send(data.encode('ascii'))
                # Start a new thread and return its identifier
                start_new_thread(self.threaded, (c,))
    def account_creation(self, username, c):
        """
        Create a new account with the given username and connection.

        Parameters:
        username (str): The username for the new account.
        c (socket): The connection to the client.
        addr (tuple): The client address.

        Returns:
        str: A message indicating the status of the account creation.
        """
        account_data = self.read_accounts_csv()
        if username in account_data['Username'].values:
            return f"Username {username} already exists. Please try a different username."

        new_id = account_data['ID'].max() + 1 if not account_data.empty else 1
        new_id = str(new_id)
        socket_string = str(c.getpeername())
        self.active_connections[socket_string] = c
        new_user = {'Username': username, 'ID': new_id, 'Connection': socket_string, 'Active_Status': True, 'Queue': '[]'}
        account_data = account_data.append(new_user, ignore_index=True)
        self.write_accounts_csv(account_data)
        self.notify_backup_servers("account", self.account_file)
        print(f"New User created. key: {new_id}\n")
        data = f"Success New Account Creation! Your new Account ID: {new_id}\n"
        return data
    def list_accounts(self, pattern):
        """
        List the accounts whose usernames match the given pattern.

        Parameters:
        pattern (str): The pattern to match usernames against.

        Returns:
        str: A message listing the accounts whose usernames match the pattern.
        """
        account_data = self.read_accounts_csv()
        account_pre = str(pattern)
        rematch = "^" + account_pre + "$"
        print("key: " + str(pattern) + "\n")
        regex = re.compile(rematch)

        matches = [username for username in account_data['Username'] if re.match(regex, username)]

        if len(matches):
            for m in range(len(matches)):
                print("Account matched: " + matches[m] + "\n")

            data = "Account matched: " + ','.join(matches) + "\n"
        else:
            print("Account matched doesn't exist: " + str(account_pre) + "\n")
            data = "Account matched to: " + str(account_pre) + " doesn't exist \n"
        return data

    def send_message(self, name, msg, c):
        """
        Send message to a specific account with a given username.

        Parameters:
        name (str): The name (NOT ID) of the recipient
        msg (str): the message sent from the host client
        c (socket): The connection to the client.

        Returns:
        str: A message showing whether the message is delivered successfully; 
        """
        account_data = self.read_accounts_csv()
        receiver = name

        if receiver in account_data['Username'].values:
            receiver_row = account_data[account_data['Username'] == receiver].iloc[0]
            rscv_ID = str(receiver_row['ID'])
            sender_socket_string = str(c.getpeername())
            sender_row = account_data[account_data['Connection'] == sender_socket_string].iloc[0]
            sender = sender_row['Username']
            message = str(sender) + " sends: " + str(msg) + "\n"

            # Save the message in messages.csv
            messages_df = pd.read_csv(self.message_file)
            new_message = {'Sender': sender, 'Receiver': receiver, 'Message': msg, 'Time': time.time()}
            messages_df = messages_df.append(new_message, ignore_index=True)
            self.write_message_csv(messages_df)
            self.notify_backup_servers("message", self.message_file)

            if (receiver_row['Active_Status'] == True):
                client = self.get_connection_by_socket_string(receiver_row['Connection'])
                data = "Sender " + str(sender) + " sends a new message: " + str(msg) + " to " + str(receiver) + "\n"
                client.send((str(sender) + ": " + str(msg)).encode('ascii'))
                print(data)
            else:
                data = "Message from " + sender + " has been delivered to " + receiver + "'s mailbox\n"
                queue = eval(receiver_row['Queue'])
                queue.append(message)
                account_data.loc[account_data['ID'] == int(rscv_ID), 'Queue'] = str(queue)
                self.write_accounts_csv(account_data)
                self.notify_backup_servers("account", self.account_file)
                print(data)
        else:
            print("Receiver doesn't exist: " + str(receiver) + "\n")
            data = "Receiver: " + str(receiver) + " doesn't exist \n"
        return data

    def pop_undelivered(self, id):
        """
        Deliver queued messages to a particular user.

        Parameters:
        id (str): The user ID to be delivered.

        Returns:
        str: A message showing the status of the action.
        """
        account_data = self.read_accounts_csv()

        try:
            accountID = str(id)
            user_row = account_data[account_data['ID'] == int(accountID)].iloc[0]
        except:
            data = 'User not Found '
            return data

        q = eval(user_row['Queue'])

        if q:
            data = f"Undelivered messages for user ID {accountID}: \n"
            while q:
                new_msg = q.pop(0)
                data += new_msg + "\n"

            # Update the queue in the accounts CSV
            account_data.loc[account_data['ID'] == int(accountID), 'Queue'] = str(q)
            self.write_accounts_csv(account_data)
            self.notify_backup_servers("account", self.account_file)
        else:
            data = "No new messages\n"

        return data

    def delete_account(self, id):
        """
        Delete a particular user from the sever permanently

        Parameters:
        id (str): The user ID to be delivered

        Returns:
        str: A message showing the status of the actions
        """
        accountID = int(id)
        accounts_df = self.read_accounts_csv()

        user_row = accounts_df.loc[accounts_df['ID'] == accountID]

        if user_row.empty:
            return "User Not Found! "

        q = eval(user_row.iloc[0]['Queue'])
        if q:
            data = "Please check your mailbox before deleting your account! \n"
            return data
        else:
            # Delete user from the accounts DataFrame
            accounts_df = accounts_df[accounts_df['ID'] != accountID]
            self.write_accounts_csv(accounts_df)
            self.notify_backup_servers("account", self.account_file)
        print(f"Account ID: {accountID} has been deleted\n")
        data = "Your account has been deleted\n"
        return data
    # thread function
    def threaded(self,c):
        """
        This method is used to handle communication between the server and a client in a separate thread. It receives data from the client,
        parses the data, and sends the appropriate response back to the client. It also manages the login status of users and keeps track of
        undelivered messages.

        Parameters:
            c (socket): A socket object representing the connection with a client.

        Returns:
            None

        Raises:
            No exceptions are explicitly raised, but if an error occurs during the execution of the method, an error message is sent back to the client.
        """
        userid = None
        while True:
            data_list=[]
            # data received from client
            data = c.recv(1024)

            data_str = data.decode('UTF-8')
            if data_str == 'master':
                break
            # Log out
            if not data:
                socket_string = str(c.getpeername())
                # Find the row in the accounts DataFrame corresponding to the socket_string
                account_df = self.read_accounts_csv()
                row = account_df.loc[account_df['Connection'] == socket_string]
                
                if not row.empty:
                    # Set the Active_Status to False
                    account_df.loc[account_df['Connection'] == socket_string, 'Active_Status'] = False
                    self.write_accounts_csv(account_df)
                    self.notify_backup_servers("account", self.account_file)
                    # Log the user logout
                    username = row.iloc[0]['Username']
                    print(username + " has logged out of the system\n")
                else:
                    print(f"Machine with {self.server_id} Becoming the new Master")
                break
            # print user input
            print(data_str+"\n")
            # parse user input
            data_list = data_str.split('|')
            opcode = data_list[0]
            print("Opcode:" + str(opcode))
            # Login
            if opcode == '0':
                try: 
                    user_id = int(data_list[1])
                    account_data = self.read_accounts_csv()
                    if (user_id in account_data['ID'].values):
                        print(account_data.loc[account_data['ID'] == user_id])
                        user_name = account_data.loc[account_data['ID'] == user_id]['Username'].values[0]
                        socket_string = str(c.getpeername())
                        account_data.loc[account_data['ID'] == user_id, 'Active_Status'] = True
                        account_data.loc[account_data['ID'] == user_id, 'Connection'] = socket_string
                        self.write_accounts_csv(account_data)
                        self.active_connections[socket_string] = c
                        print(f'user : {user_name} is now logged in\n')
                        data = f'user : {user_name} is now logged in\n'
                    else:
                        print(account_data['ID'])
                        data = f'user with ID : {data_list[1]} is not recognized in the system, please try a different ID or create a new one\n'
                    c.send(data.encode('ascii'))
                except Exception as e:
                    print(e)
                    c.send(self.err_msg.encode('ascii'))

            elif opcode == '1':
                #account creation
                try:
                    username = str(data_list[1])
                    data = self.account_creation(username,c)
                    c.send(data.encode('ascii'))
                except Exception as e:
                    print(e)
                    c.send(self.err_msg.encode('ascii'))
            elif opcode == '2':
                try:
                    if(len(data_list) == 1):
                        data = "Showing all accounts: " + ','.join(self.name_list) +"\n"
                        print("Output all accounts name: " + "\n")
                    else:
                        data = self.list_accounts(data_list[1])
                except Exception as e:
                    print(e)
                    c.send(self.err_msg.encode('ascii'))
                #list accounts
                c.send(data.encode('ascii')) 
            elif opcode == '3':
                #Send a message to a recipient
                try:
                    username = str(data_list[1])
                    msg = str(data_list[2])
                    data = self.send_message(username,msg,c)
                    c.send(data.encode('ascii'))
                except Exception as e: 
                    print(e)
                    c.send(self.err_msg.encode('ascii'))
                #list accounts
            elif opcode == '4':
                try:
                    userid = str(data_list[1])
                    data = self.pop_undelivered(userid)
                    c.send(data.encode('ascii'))
                except Exception as e:
                    print(e)
                    c.send(self.err_msg.encode('ascii'))
            elif opcode == '5':
                #Delete an account
                try:
                    userid = str(data_list[1])
                    data = self.delete_account(userid)
                    c.send(data.encode('ascii'))
                except Exception as e: 
                    print(e)
                    c.send(self.err_msg.encode('ascii'))
            else:
                c.send(self.err_msg.encode('ascii'))
        # connection closed
        # When no user was attached to the current connection
        try:
            socket_string = c.getpeername()
            row = account_df.loc[account_df['Connection'] == socket_string]
            if not row.empty:
                # Set the Active_Status to False
                account_df.loc[account_df['Connection'] == socket_string, 'Active_Status'] = False
                self.write_accounts_csv(account_df)
                self.notify_backup_servers("account", self.account_file)
        except Exception as e:
            pass
        self.close_connection(c)

def check_server_health(server):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            data = HEALTH_CHECK_MSG
            if(server.master):
                data = 'master'
            sock.connect((server.host,server.port))
            sock.sendall(data.encode())
            response = sock.recv(1024).decode()
            if response == "To get started on this chat room, please create or login your account first and type command as instructed in the documentation \n":
                try:
                    sock.close()
                except:
                    pass
                return True
    except Exception as e:
        print(f"Error checking server status: {e}")
        try:
            sock.close()
        except:
            pass
        return False
def monitor_servers(servers):
    primary_server = servers[0]
    backup_servers = servers[1:]

    while True:
        time.sleep(5)
        if not check_server_health(primary_server):
            print("Primary server failed, promoting a backup server.")
            
            # Find the first available backup server and promote it
            for backup_server in backup_servers:
                if check_server_health(backup_server):
                    primary_server = backup_server
                    primary_server.master = True
                    backup_servers.remove(backup_server)
                    primary_server.backup_servers = backup_servers
                    print(f"Promoted server {backup_server.server_id} to primary server.")
                    break
            else:
                print("No available backup servers to promote.")
        else:
            print("Primary server is still alive.")
        
        # Check the health of backup servers
        for backup_server in backup_servers:
            if not check_server_health(backup_server):
                print(f"Backup server {backup_server.server_id} failed.")
            else:
                print(f"Backup server {backup_server.server_id} is still alive.")


def main():
    backup_server2 = Server(server_id=2, is_master=False)
    backup_server1 = Server(server_id=1, is_master=False, backup_servers=[backup_server2])
    primary_server = Server(server_id=0, backup_servers=[backup_server1, backup_server2])
    
    primary_process = multiprocessing.Process(target=primary_server.start_server)
    backup_process1 = multiprocessing.Process(target=backup_server1.start_server)
    backup_process2 = multiprocessing.Process(target=backup_server2.start_server)
    monitor_process = multiprocessing.Process(target=monitor_servers, args=([primary_server, backup_server1, backup_server2],))

    primary_process.start()
    backup_process1.start()
    backup_process2.start()
    monitor_process.start()

    primary_process.join()
    backup_process1.join()
    backup_process2.join()
    monitor_process.join()

if __name__ == "__main__":
    main()

