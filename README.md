# cs262-HW1 Guangya Wan & Zongjun Liu

## About
This is a simple chat room application (Extended from Design Problem 1) implemented using Python and sockets. The application supports account creation, user login, sending messages, listing available accounts, and deleting accounts. The system is built with a primary server and multiple backup servers to ensure high availability and fault tolerance.

## Features

- Account creation
- User login
- Send messages to other users
- List available accounts
- Retrieve undelivered messages
- Delete an account
- Primary and backup servers for fault tolerance

### Download

1. Ensure that you have Python 3.6 or later installed on your system.
2. Clone the repository or download the source code:

Run the following command in your terminal to save the repository in your system
> $ git clone https://github.com/wan19990901/CS262.git
> $ git switch replication

Then install the necssary dependecy, which is just pandas

> $ pip install -r requirment.txt

### Run
Once you are in the directory where `server.py` or `client.py` file exists, run by typing the following commands in your terminal.

### Server
> $ python server.py

  
### Client
> $ python client.py 6666 (By default the primary port is 6666, and 6667/6668 are the ports for backup servers. You can customize the port number, but you also need to change accordingly in the server)

You can run multiple clients ay the same time by creating multiple processes. 

### Wire Protocol:


Op '0' = Account Login, e.g. 0|wayne123 --> User with ID wayne123 logged in (need to be created at first)

Op '1' = Account Creation, e.g. 1|John --> Creates an account with username John, and an ID will be supplemented. (Avoid same user name, and such format has to be followed and try to aviod adding '|' in the name)

Op '2' = List User, e.g., 2|J.hn --> returns list of user whose name is J*hn. Or 2 --> Returns list of all users

Op '3'  = Send Message to a particular user, e.g., 3|accountID|message --> Send a new message immediately to another account if online (send to mailbox if the other account is offline)

Op '4' = View underlivered message, e.g. 4|accountID --> View all undelivery message for a user with id accountID when he/she is logged off (will return a note if user does not exist)

Op '5' = Delete Account, e.g. 5|accountID --> Delete Account with accountID (will return a note if user does not exist)

Op 'bye' = Logged off. Similar to delete account but the information is kept in the server so that people can still message you in the mailbox, and you can use Op '0' to relogin.

### Test

We tested (With Python's unittest module) the basic functionality of our server, thread, helper function, and replication code. Due to time limit it's certainly not inclusive, and You can play around and add your own tests in the respectively python scripts.

In the Server folder, Simply run the server scripts:

> $ bash test.sh

This script runs Python unit tests, installs the coverage package, measures code coverage during test execution, and generates an HTML coverage report. It helps ensure the code is well-tested and identifies areas where more tests may be needed.

### Example

Note that here is an example of basic funcionality. For advanced features such as server replication/2-fault-tolerance/Clients connections from external machine, we will show them in the demo day!
**Server**
> $ python server.py
<pre>
				SERVER WORKING 
socket binded to port 6666
socket is listening
Connected to : 127.0.0.1 : 49032
Connected to : 127.0.0.1 : 49034
1|wayne

Opcode:1
New User created. key: wayne123

1|mason

Opcode:1
New User created. key: mason123

2|w.yne

Opcode:2
key: w.yne

Account matched: wayne

2|.ason

Opcode:2
key: .ason

Account matched: mason

3|wayne|hello

Opcode:3
Sender mason sends a new message hello to wayne

5|mason123

Opcode:5
Account ID: mason123 has been deleted

4|wayne123

Opcode:4
3|mason123|hello too!

Opcode:3
Receiver doesnt exist: mason123

5|wayne1234

Opcode:5
wayne has logged out of the system
</pre>



**Client 1**
> $ python client.py 

<pre>
To get started on this chat room, please create or login your account first and type command as instructed in the documentation 

1|mason
Success New Account Creation! Your new Account ID: mason123


2|.ason
Account matched: mason


3|wayne|hello
Sender mason sends a new message hello to wayne


5|mason123
Your account has been deleted


bye
</pre>

**Client 2**
> $ python client.py 
<pre>
To get started on this chat room, please create or login your account first and type command as instructed in the documentation 

1|wayne
Success New Account Creation! Your new Account ID: wayne123


2|w.yne
Account matched: wayne


mason: hello
4|wayne123
No new messages


3|mason123|hello too!
Receiver: mason123 doesn't exist 


5|wayne1234
User Not Found! 

bye
</pre>
