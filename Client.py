import socket
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Khởi tạo socket client
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(10)
server_address = ('192.168.1.9', 12320)

# Đăng ký tên người dùng
root = tk.Tk()
root.withdraw()

USER_NAME = simpledialog.askstring("User Registration/Login", "Enter your username:")
PASSWORD = simpledialog.askstring("Password", "Enter your password:", show='*')
IS_NEW_USER = messagebox.askyesno("User Type", "Are you a new user?")

if not USER_NAME or not PASSWORD:
    messagebox.showerror("Error", "Username and Password are required!")
    exit()

if IS_NEW_USER:
    # Đăng ký người dùng mới
    request = json.dumps({'action': 'register_user', 'username': USER_NAME, 'password': PASSWORD})
else:
    # Đăng nhập người dùng
    request = json.dumps({'action': 'login_user', 'username': USER_NAME, 'password': PASSWORD})

client_socket.sendto(request.encode(), server_address)

try:
    response, _ = client_socket.recvfrom(4096)
    response = json.loads(response.decode())

    if response.get('type') in ['registration', 'login']:
        messagebox.showinfo("Info", response['message'])
    else:
        messagebox.showerror("Error", response.get('message'))
        exit()
except socket.timeout:
    messagebox.showerror("Error", "Server is not responding.")
    exit()

# Tạo giao diện chính sau khi đăng nhập thành công
root = tk.Tk()
root.title(f"Gmail Clone - {USER_NAME}'s Inbox")
root.geometry("600x800")

notebook = ttk.Notebook(root)
notebook.pack(pady=10, expand=True)

# Frame cho Inbox
frame_inbox = ttk.Frame(notebook, width=600, height=400)
frame_inbox.pack(fill='both', expand=True)

# Frame cho Send Email
frame_send_email = ttk.Frame(notebook, width=600, height=400)
frame_send_email.pack(fill='both', expand=True)

notebook.add(frame_inbox, text='Inbox')
notebook.add(frame_send_email, text='Send Email')

# Inbox Frame Widgets
email_list = []
listbox = tk.Listbox(frame_inbox, width=80, height=15)
listbox.pack(pady=10)

def fetch_emails():
    request = json.dumps({'action': 'get_emails', 'user': USER_NAME})
    client_socket.sendto(request.encode(), server_address)

    try:
        data, _ = client_socket.recvfrom(4096)
        response = json.loads(data.decode())

        if response.get('type') == 'email_list':
            global email_list
            email_list = response.get('emails', [])
            listbox.delete(0, tk.END)

            for i, email in enumerate(email_list):
                listbox.insert(tk.END, f"{i+1}. {email}")
    except socket.timeout:
        messagebox.showerror("Error", "Server is not responding.")

btn_fetch = ttk.Button(frame_inbox, text="Fetch Emails", command=fetch_emails)
btn_fetch.pack()

def show_email_detail():
    selected_index = listbox.curselection()
    if selected_index:
        index = selected_index[0]
        email_filename = email_list[index]
        
        request = json.dumps({'action': 'get_email_content', 'user': USER_NAME, 'filename': email_filename})
        client_socket.sendto(request.encode(), server_address)
        
        try:
            data, _ = client_socket.recvfrom(4096)
            response = json.loads(data.decode())
            if response.get('type') == 'email_content':
                email = response['email']
                timestamp = email.get('timestamp', 'No timestamp available')
                # Hiển thị nội dung email ngay trên Frame Inbox
                detail_text.delete("1.0", tk.END)
                detail_text.insert(tk.END, f"From: {email['from']}\nTo: {email['to']}\nSubject: {email['subject']}\nSent Time: {timestamp}\n\n{email['content']}")
            else:
                messagebox.showerror("Error", response.get('message'))

        except socket.timeout:
            messagebox.showerror("Error", "Server is not responding.")

btn_detail = ttk.Button(frame_inbox, text="Show Email Detail", command=show_email_detail)
btn_detail.pack()

# Text widget to show email details directly in the inbox frame
detail_text = tk.Text(frame_inbox, width=80, height=10, wrap='word')
detail_text.pack(pady=10)

# Send Email Frame Widgets
tk.Label(frame_send_email, text="To:").grid(row=0, column=0, pady=5, padx=5, sticky='e')
entry_to = ttk.Entry(frame_send_email, width=50)
entry_to.grid(row=0, column=1, pady=5, padx=5)

tk.Label(frame_send_email, text="Subject:").grid(row=1, column=0, pady=5, padx=5, sticky='e')
entry_subject = ttk.Entry(frame_send_email, width=50)
entry_subject.grid(row=1, column=1, pady=5, padx=5)

tk.Label(frame_send_email, text="Content:").grid(row=2, column=0, pady=5, padx=5, sticky='ne')
text_content = tk.Text(frame_send_email, width=50, height=10)
text_content.grid(row=2, column=1, pady=5, padx=5)

def send_email():
    recipient = entry_to.get()
    subject = entry_subject.get()
    content = text_content.get("1.0", tk.END).strip()

    if not recipient or not subject or not content:
        messagebox.showerror("Error", "All fields are required.")
        return

    email = {
        'from': USER_NAME,
        'to': recipient,
        'subject': subject,
        'content': content
    }

    request = json.dumps({'action': 'send_email', 'email': email})
    client_socket.sendto(request.encode(), server_address)

    try:
        response, _ = client_socket.recvfrom(4096)
        response = json.loads(response.decode())

        if response.get('type') == 'status':
            messagebox.showinfo("Info", response['message'])
    except socket.timeout:
        messagebox.showerror("Error", "Server is not responding.")

btn_send = ttk.Button(frame_send_email, text="Send", command=send_email)
btn_send.grid(row=3, column=1, pady=10)

root.mainloop()
