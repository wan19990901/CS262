#Ref: https://www.geeksforgeeks.org/socket-programming-multi-threading-python/

import socket
import re
from _thread import *
import pandas as pd
import os
import time
class Server:
    err_msg = 'Please give a valid input as instructed in the documentation'
    def __init__(self):
        self.account_file = 'accounts.csv'
        self.message_file = 'messages.csv'
        self.host = "127.0.0.1"
        self.port = 2023
        self.active_connections = {}
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

    def read_messages_csv(self):
        return pd.read_csv(self.message_file)

    def write_messages_csv(self, data):
        data.to_csv(self.message_file, index=False)
    def get_connection_by_socket_string(self, socket_string):
        if socket_string in self.active_connections:
            return self.active_connections[socket_string]

    def close_connection(self, connection):
        # socket_string = str(connection.getpeername())
        # if socket_string in self.active_connections:
        #     del self.active_connections[socket_string]
        connection.close()


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
            print('Connected to :', addr[0], ':', addr[1])
            data = "To get started on this chat room, please create or login your account first and type command as instructed in the documentation \n"
            c.send(data.encode('ascii'))
            # Start a new thread and return its identifier
            start_new_thread(self.threaded, (c,))
    # def close_server(self):        
    #     """
    #     Stop the chat room server.
    #     """
    #     try:
    #         self.s.shutdown(socket.SHUT_RDWR)
    #         self.s.close()
    #         print ("Server closed")
    #     except:
    #         print("Server not started")
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
            messages_df = pd.read_csv('messages.csv')
            new_message = {'Sender': sender, 'Receiver': receiver, 'Message': msg, 'Time': time.time()}
            messages_df = messages_df.append(new_message, ignore_index=True)
            messages_df.to_csv('messages.csv', index=False)

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
            # Log out
            if not data:
                socket_string = str(c.getpeername())
                # Find the row in the accounts DataFrame corresponding to the socket_string
                account_df = self.read_accounts_csv()
                row = account_df.loc[account_df['Connection'] == socket_string]
                print(row)
                if not row.empty:
                    # Set the Active_Status to False
                    account_df.loc[account_df['Connection'] == socket_string, 'Active_Status'] = False
                    self.write_accounts_csv(account_df)
                    # Log the user logout
                    username = row.iloc[0]['Username']
                    print(username + " has logged out of the system\n")
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
        except Exception as e:
            print(e)
            print("hellohello")
        self.close_connection(c)
def Main():
    server = Server()
    server.start_server()
    # s.close()
if __name__ == '__main__':
    Main()
