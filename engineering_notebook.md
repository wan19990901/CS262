Engineering Notebook: Chat Application Implementation Redesign

Date: 04/09/2023

Implementation Details:

Initial Implementation:

The initial implementation of the chat application was a simple client-server architecture, where the server was responsible for receiving messages from clients and broadcasting them to all connected clients. However, the implementation lacked persistence, meaning that if the server was stopped or restarted, all messages sent during that time were lost.

Design Changes:

To make the implementation persistent and 2-fault tolerant, we decided to use a key-value store in the form of a CSV as the database, and use a master-slave architecture to handle 2-fault tolerant.

Key-value Store: We used a CSV file as our database to store all messages sent by clients. This ensures that even if the server is stopped or restarted, all messages sent during that time can be recovered from the CSV file. Since the file is a flat text file, we can easily replicate it across all server instances.

Master-Slave Architecture: To achieve 2-fault tolerant, we used a master-slave architecture. The master server is responsible for accepting all messages from clients, and it replicates the messages to all slave servers. If the master server fails, one of the slave servers takes over as the new master server. If a slave server fails, the other slave servers continue to function normally.

Specific functionality:

The notify_backup_servers() function takes two parameters: file_name, a string representing the name of the file that has been updated.
data, a string representing the data that has been updated. This function sends an update message to all backup servers that are registered with the current server. The function is used by the master server when there is an update to the CSV files, so that the backup servers can synchronize their data with the master. The function checks if the current server is the master server. If it is, then the function proceeds with notifying the backup servers. Otherwise, it does nothing. For each backup server that is registered with the current server, the function creates a socket connection to the server. It then sends an "update" message to the backup server, which includes the file name and the updated data. If the message is successfully sent to the backup server, the function receives a confirmation message. If there is an error while sending the message, the function prints an error message with the server ID that caused the error.

The start_server() function starts the chat room server and listens for incoming connections from clients. It also handles incoming messages and initiates threads for handling the messages. The function creates a new socket object and binds it to the host and port specified in the ChatServer object. It then puts the socket into listening mode, and waits for incoming connections from clients. If the current server is not the master server, it receives incoming messages from clients and processes them accordingly. If the message is a "health check" message, it sends a response with instructions for connecting to the chat room. If the message is a "master" message, it sets the current server as the master server and initiates a new thread for handling incoming messages. If the message is an "update" message, it calls the update_csv_file() function to update the corresponding CSV file. If the current server is the master server, it receives incoming messages from clients and sends a response with instructions for connecting to the chat room. It also initiates a new thread for handling incoming messages.

The check_server_health() function is used to check the status of a given server by sending a message to the server's socket. If the server is the master server, the message sent is 'master'. If the server is not the master server, the message sent is HEALTH_CHECK_MSG. The method returns True if the server responds with a message that indicates it is functioning properly. Otherwise, the method returns False.

The monitor_servers() function is used to monitor the health of all servers in the chat room system. The method first identifies the primary server and the backup servers in the system. Then, the method enters a loop that sleeps for 5 seconds and checks the health of the primary server using the check_server_health method. If the primary server fails, the method promotes a backup server to the primary server. If no backup servers are available, the method prints a message indicating that there are no available backup servers to promote. If the primary server is functioning properly, the method checks the health of each backup server in the system using the check_server_health method and prints a message indicating whether each backup server is functioning properly or has failed.

Demo:

To demonstrate that the new implementation works as intended, we performed the following steps:

We ran the master server and multiple slave servers on different machines and connected clients to the master server.

We sent messages from different clients to the master server and verified that the messages were broadcast to all connected clients through the slave servers.

We stopped the master server and sent messages from different clients to the slave servers. We verified that the messages were still broadcast to all connected clients, even with the master server down.

Conclusion:

The redesigned implementation of the chat application is both persistent and 2-fault tolerant, and can handle crash/failstop failures. The use of a CSV file as our key-value store ensures that all messages sent by clients are stored even if the server is stopped or restarted. The use of a master-slave architecture ensures that even if the master server fails, one of the slave servers can take over as the new master server, and if a slave server fails, the other slave servers can continue to function normally. Overall, the new implementation is more reliable and resilient than the initial implementation, and can be used in production environments where uptime and data integrity are critical.