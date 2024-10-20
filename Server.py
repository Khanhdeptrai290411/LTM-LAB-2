import socket
import json
import os
import threading
from datetime import datetime
import tkinter as tk
from tkinter import Listbox, Scrollbar, VERTICAL, LEFT, RIGHT, BOTH, Y

# Server details
SERVER_ADDRESS = ('192.168.1.9', 12320)
BUFFER_SIZE = 4096

# Create UDP server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(SERVER_ADDRESS)

# Create "User" directory if not exists
if not os.path.exists('User'):
    os.mkdir('User')

# List to keep track of log activities for the admin GUI
log_activities = []

def log_activity(activity):
    """Logs the activity with a timestamp and add it to the admin GUI log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {activity}"
    print(log_message)  # Optional: print to terminal for debugging
    log_activities.append(log_message)

    # Update the admin GUI log if it exists
    if admin_app and hasattr(admin_app, 'log_listbox'):
        admin_app.update_log()

def handle_client_requests():
    """Function that continuously handles incoming client requests."""
    while True:
        try:
            # Receive data from clients
            data, address = server_socket.recvfrom(BUFFER_SIZE)
            message = json.loads(data.decode())

            if message['action'] == 'register_user':
                username = message['username']
                password = message['password']
                user_dir = os.path.join('User', username)

                if not os.path.exists(user_dir):
                    os.mkdir(user_dir)
                    with open(os.path.join(user_dir, 'password.txt'), 'w') as file:
                        file.write(password)

                    # Create initial email with timestamp
                    initial_email = {
                        "from": "Admin",
                        "to": username,
                        "subject": "Welcome",
                        "content": "Thank you for using this service, we hope you enjoy this service",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    with open(os.path.join(user_dir, 'new_email.txt'), 'w') as file:
                        file.write(json.dumps(initial_email))

                    response = {'type': 'registration', 'message': f"User {username} registered successfully."}
                    log_activity(f"User {username} registered successfully.")
                else:
                    response = {'type': 'error', 'message': f"User {username} already exists."}
                    log_activity(f"Failed to register {username}: User already exists.")

                server_socket.sendto(json.dumps(response).encode(), address)

            elif message['action'] == 'login_user':
                username = message['username']
                password = message['password']
                user_dir = os.path.join('User', username)

                if os.path.exists(user_dir):
                    with open(os.path.join(user_dir, 'password.txt'), 'r') as file:
                        saved_password = file.read().strip()

                    if saved_password == password:
                        response = {'type': 'login', 'message': f"User {username} logged in successfully."}
                        log_activity(f"User {username} logged in successfully.")
                    else:
                        response = {'type': 'error', 'message': "Incorrect password."}
                        log_activity(f"Failed login attempt for {username}: Incorrect password.")
                else:
                    response = {'type': 'error', 'message': f"User {username} not found."}
                    log_activity(f"Failed login attempt: User {username} not found.")

                server_socket.sendto(json.dumps(response).encode(), address)

            elif message['action'] == 'send_email':
                email = message['email']
                recipient = email['to']
                recipient_dir = os.path.join('User', recipient)

                if os.path.exists(recipient_dir):
                    # Add timestamp to the email
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    email['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Generate unique filename using subject and timestamp
                    email_filename = f"{email['subject'].replace(' ', '_')}_{timestamp}_{email['from']}.txt"
                    email_path = os.path.join(recipient_dir, email_filename)

                    # Write email to file
                    with open(email_path, 'w') as file:
                        file.write(json.dumps(email))

                    response = {'type': 'status', 'message': "Email sent successfully."}
                    log_activity(f"User {email['from']} sent an email to {recipient} with subject '{email['subject']}'.")
                else:
                    response = {'type': 'error', 'message': f"User {recipient} not found."}
                    log_activity(f"Failed to send email from {email['from']} to {recipient}: User not found.")

                server_socket.sendto(json.dumps(response).encode(), address)

            elif message['action'] == 'get_emails':
                username = message['user']
                user_dir = os.path.join('User', username)

                if os.path.exists(user_dir):
                    emails = [f for f in os.listdir(user_dir) if f.endswith('.txt') and f != 'password.txt']
                    response = {'type': 'email_list', 'emails': emails}
                    log_activity(f"User {username} fetched email list.")
                else:
                    response = {'type': 'email_list', 'emails': []}
                    log_activity(f"User {username} attempted to fetch email list but no user directory found.")

                server_socket.sendto(json.dumps(response).encode(), address)

            elif message['action'] == 'get_email_content':
                username = message['user']
                filename = message['filename']
                user_dir = os.path.join('User', username)
                email_path = os.path.join(user_dir, filename)

                if os.path.exists(email_path):
                    with open(email_path, 'r') as file:
                        email = json.loads(file.read())
                    response = {'type': 'email_content', 'email': email}
                    log_activity(f"User {username} viewed email '{filename}'.")
                else:
                    response = {'type': 'error', 'message': "Email not found."}
                    log_activity(f"User {username} attempted to view email '{filename}' but it was not found.")

                server_socket.sendto(json.dumps(response).encode(), address)

        except json.JSONDecodeError:
            log_activity("Failed to decode JSON from client.")
        except Exception as e:
            log_activity(f"Unexpected error: {e}")

# Start the server thread
server_thread = threading.Thread(target=handle_client_requests, daemon=True)
server_thread.start()

# Create Admin GUI to view users and log activities
class AdminApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Admin - User Management and Activity Log")
        self.geometry("600x400")

        # User listbox
        self.user_listbox = Listbox(self, width=50, height=10)
        self.user_listbox.pack(pady=10)

        self.refresh_button = tk.Button(self, text="Refresh User List", command=self.refresh_user_list)
        self.refresh_button.pack(pady=5)

        # Log Listbox with scrollbar
        self.log_frame = tk.Frame(self)
        self.log_frame.pack(fill=BOTH, expand=True)

        self.log_scrollbar = Scrollbar(self.log_frame, orient=VERTICAL)
        self.log_listbox = Listbox(self.log_frame, yscrollcommand=self.log_scrollbar.set, width=100, height=15)
        self.log_scrollbar.config(command=self.log_listbox.yview)

        self.log_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self.log_scrollbar.pack(side=RIGHT, fill=Y)

        # Initial population of the user list and log
        self.refresh_user_list()
        self.update_log()

    def refresh_user_list(self):
        self.user_listbox.delete(0, tk.END)
        users = [user for user in os.listdir('User') if os.path.isdir(os.path.join('User', user))]
        for user in users:
            self.user_listbox.insert(tk.END, user)
    
    def update_log(self):
        self.log_listbox.delete(0, tk.END)
        for log in log_activities:
            self.log_listbox.insert(tk.END, log)

# Create and run the Admin GUI
admin_app = AdminApp()
admin_app.mainloop()

Admin
import socket
import json
import os
import threading
from datetime import datetime
import tkinter as tk
from tkinter import Listbox, messagebox, Text, Scrollbar, VERTICAL, END

# Server details
SERVER_ADDRESS = ('192.168.1.3', 12326)
BUFFER_SIZE = 4096

# Create UDP server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(SERVER_ADDRESS)

# Create "User" directory if not exists
if not os.path.exists('User'):
    os.mkdir('User')

class AdminApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Admin - User Management")
        self.geometry("600x500")

        # User Listbox
        self.user_listbox = Listbox(self, width=50, height=10)
        self.user_listbox.pack(pady=10)

        self.refresh_button = tk.Button(self, text="Refresh User List", command=self.refresh_user_list)
        self.refresh_button.pack(pady=5)

        # Log Area
        self.log_text = Text(self, wrap='word', height=15, width=70)
        self.log_text.pack(pady=10)

        # Scrollbar for Log Area
        self.scrollbar = Scrollbar(self, orient=VERTICAL, command=self.log_text.yview)
        self.scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=self.scrollbar.set)

        self.refresh_user_list()

    def refresh_user_list(self):
        self.user_listbox.delete(0, tk.END)
        users = [user for user in os.listdir('User') if os.path.isdir(os.path.join('User', user))]
        for user in users:
            self.user_listbox.insert(tk.END, user)

    def log_activity(self, activity):
        """Logs the activity in the GUI log area with a timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {activity}\n"
        self.log_text.insert(END, log_message)
        self.log_text.see(END)  # Scroll to the end of the text area

# Initialize Admin GUI
admin_app = AdminApp()

def handle_client_requests():
    """Function that continuously handles incoming client requests."""
    while True:
        try:
            # Receive data from clients
            data, address = server_socket.recvfrom(BUFFER_SIZE)
            message = json.loads(data.decode())

            if message['action'] == 'register_user':
                username = message['username']
                password = message['password']
                user_dir = os.path.join('User', username)

                if not os.path.exists(user_dir):
                    os.mkdir(user_dir)
                    with open(os.path.join(user_dir, 'password.txt'), 'w') as file:
                        file.write(password)
                    
                    # Create initial email with timestamp
                    initial_email = {
                        "from": "Admin",
                        "to": username,
                        "subject": "Welcome",
                        "content": "Thank you for using this service, we hope you enjoy this service",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    with open(os.path.join(user_dir, 'new_email.txt'), 'w') as file:
                        file.write(json.dumps(initial_email))

                    response = {'type': 'registration', 'message': f"User {username} registered successfully."}
                    admin_app.log_activity(f"User {username} registered successfully.")
                else:
                    response = {'type': 'error', 'message': f"User {username} already exists."}
                    admin_app.log_activity(f"Failed to register {username}: User already exists.")

                server_socket.sendto(json.dumps(response).encode(), address)

            elif message['action'] == 'login_user':
                username = message['username']
                password = message['password']
                user_dir = os.path.join('User', username)

                if os.path.exists(user_dir):
                    with open(os.path.join(user_dir, 'password.txt'), 'r') as file:
                        saved_password = file.read().strip()

                    if saved_password == password:
                        response = {'type': 'login', 'message': f"User {username} logged in successfully."}
                        admin_app.log_activity(f"User {username} logged in successfully.")
                    else:
                        response = {'type': 'error', 'message': "Incorrect password."}
                        admin_app.log_activity(f"Failed login attempt for {username}: Incorrect password.")
                else:
                    response = {'type': 'error', 'message': f"User {username} not found."}
                    admin_app.log_activity(f"Failed login attempt: User {username} not found.")

                server_socket.sendto(json.dumps(response).encode(), address)

            elif message['action'] == 'send_email':
                email = message['email']
                recipient = email['to']
                recipient_dir = os.path.join('User', recipient)

                if os.path.exists(recipient_dir):
                    # Add timestamp to the email
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    email['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Generate unique filename using subject and timestamp
                    email_filename = f"{email['subject'].replace(' ', '_')}_{timestamp}_{email['from']}.txt"
                    email_path = os.path.join(recipient_dir, email_filename)

                    # Write email to file
                    with open(email_path, 'w') as file:
                        file.write(json.dumps(email))

                    response = {'type': 'status', 'message': "Email sent successfully."}
                    admin_app.log_activity(f"User {email['from']} sent an email to {recipient} with subject '{email['subject']}'.")
                else:
                    response = {'type': 'error', 'message': f"User {recipient} not found."}
                    admin_app.log_activity(f"Failed to send email from {email['from']} to {recipient}: User not found.")

                server_socket.sendto(json.dumps(response).encode(), address)

            elif message['action'] == 'get_emails':
                username = message['user']
                user_dir = os.path.join('User', username)
                
                if os.path.exists(user_dir):
                    emails = [f for f in os.listdir(user_dir) if f.endswith('.txt') and f != 'password.txt']
                    response = {'type': 'email_list', 'emails': emails}
                    admin_app.log_activity(f"User {username} fetched email list.")
                else:
                    response = {'type': 'email_list', 'emails': []}
                    admin_app.log_activity(f"User {username} attempted to fetch email list but no user directory found.")

                server_socket.sendto(json.dumps(response).encode(), address)

            elif message['action'] == 'get_email_content':
                username = message['user']
                filename = message['filename']
                user_dir = os.path.join('User', username)
                email_path = os.path.join(user_dir, filename)

                if os.path.exists(email_path):
                    with open(email_path, 'r') as file:
                        email = json.loads(file.read())
                    response = {'type': 'email_content', 'email': email}
                    admin_app.log_activity(f"User {username} viewed email '{filename}'.")
                else:
                    response = {'type': 'error', 'message': "Email not found."}
                    admin_app.log_activity(f"User {username} attempted to view email '{filename}' but it was not found.")

                server_socket.sendto(json.dumps(response).encode(), address)

        except json.JSONDecodeError:
            admin_app.log_activity("Failed to decode JSON from client.")
        except Exception as e:
            admin_app.log_activity(f"Unexpected error: {e}")

# Start the server thread
server_thread = threading.Thread(target=handle_client_requests, daemon=True)
server_thread.start()

# Run the Admin GUI
admin_app.mainloop()