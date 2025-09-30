import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
from datetime import datetime
from decimal import Decimal
import re
import hashlib
import bcrypt
import random
# Check if email is valid
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

# Function to send email
def send_email(subject, body, to_email):
    try:
        sender_email = "velliangiriniranjan2002@gmail.com"  # Replace with your own email
        sender_password = "bgif cefo lice ztzf"  # Replace with your own email password
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())

        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Create connection to MySQL
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',  
            user='root',  
            password='*********',  
            database='bank_system'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        messagebox.showerror("Error", f"Error connecting to MySQL: {e}")
        return None

# Hash password using SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_password(password):
    # Check length
    
    if len(password) < 8:
        return "Password must be at least 8 characters long."

    # Check for uppercase letters
    if not re.search(r"[A-Z]", password):
        return "Password must include at least one uppercase letter."

    # Check for lowercase letters
    if not re.search(r"[a-z]", password):
        return "Password must include at least one lowercase letter."

    # Check for digits
    if not re.search(r"\d", password):
        return "Password must include at least one digit."

    # Check for special characters
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must include at least one special character."

    return "Password is valid."

# BankAccount class
class BankAccount:
    def __init__(self, account_number, account_holder, email, password, balance=0):
        self.account_number = account_number
        self.account_holder = account_holder
        self.email = email
        self.password = password  # Hashed password
        self.balance = Decimal(balance)

    def verify_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)
        

    def deposit(self, amount):
        amount = Decimal(amount)
        if amount > 0:
            self.balance += amount
            self.record_transaction("Deposit", amount)
            return f"Deposited ${amount:.2f} into your account.\n New Balance: ${self.balance:.2f}"
        return "Deposit amount must be positive."

    def withdraw(self, amount):
        amount = Decimal(amount)
        if 0 < amount <= self.balance:
            self.balance -= amount
            self.record_transaction("Withdrawal", amount)
            return f"Withdrew ${amount:.2f} from your account.\n New Balance: ${self.balance:.2f}"
        return "Insufficient balance or invalid amount."

    def transfer(self, target_account, amount):
        amount = Decimal(amount)
        if 0 < amount <= self.balance:
            self.withdraw(amount)
            target_account.deposit(amount)
            self.record_transaction("Transfer", amount, target_account.account_number)
            return f"Transferred ${amount:.2f} to account {target_account.account_number}."
        return "Insufficient balance or invalid amount."

    def record_transaction(self, transaction_type, amount, target_account_number=None):
        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""INSERT INTO transactions (account_number, transaction_type, amount, transaction_date)
                            VALUES (%s, %s, %s, %s)""",
                           (self.account_number, transaction_type, amount, transaction_date))
            connection.commit()
            cursor.close()
            connection.close()

    def get_transactions(self):
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""SELECT transaction_type, amount, transaction_date 
                            FROM transactions 
                            WHERE account_number = %s 
                            ORDER BY transaction_date DESC""", (self.account_number,))
            rows = cursor.fetchall()
            transactions = [f"{txn['transaction_date']} - {txn['transaction_type']}: ${txn['amount']:.2f}" for txn in rows]
            cursor.close()
            connection.close()
            return transactions

# Save accounts to MySQL database
def save_accounts(accounts):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            for account in accounts:
                account_data = (account.account_number, account.account_holder, account.email, account.password, account.balance)
                cursor.execute("""INSERT INTO accounts (account_number, account_holder, email, password, balance)
                                  VALUES (%s, %s, %s, %s, %s)
                                  ON DUPLICATE KEY UPDATE
                                      account_holder = VALUES(account_holder),
                                      email = VALUES(email),
                                      password = VALUES(password),
                                      balance = VALUES(balance);""", account_data)
            connection.commit()
            messagebox.showinfo("Success", "Accounts saved successfully.")
        except Error as e:
            messagebox.showerror("Error", f"Error saving accounts: {e}")
        finally:
            cursor.close()
            connection.close()

# Load accounts from MySQL database
def load_accounts():
    connection = create_connection()
    accounts = []
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT account_number, account_holder, email, password, balance FROM accounts")
            rows = cursor.fetchall()
            for row in rows:
                account = BankAccount(
                    account_number=row['account_number'],
                    account_holder=row['account_holder'],
                    email=row['email'],
                    password=row['password'].encode('utf-8'),
                    balance=row['balance']
                )
                accounts.append(account)
            print("Loaded accounts from DB:", accounts) 
        except Error as e:
            messagebox.showerror("Error", f"Error loading accounts: {e}")
        finally:
            cursor.close()
            connection.close()
    return accounts

# Login screen function
def login_screen(root, accounts):
    def attempt_login():
        acc_number = login_acc_number_entry.get().strip()
        acc_holder = login_name_entry.get().strip().lower()
        password = login_password_entry.get().strip()

        account = next((acc for acc in accounts if str(acc.account_number) == acc_number and acc.account_holder.strip().lower() == acc_holder and acc.verify_password(password)), None)
        if account and account.verify_password(password):
            root.destroy()
            main_window(accounts, account)
        else:
            messagebox.showerror("Login Failed", "Invalid account number, account holder name, or password.")

    def generate_account_number():
        while True:
            account_number=random.randint(10000,999999)
            if not any (acc.account_number==account_number for acc in accounts):
                return account_number
                
    def create_account():
        account_number = generate_account_number()
        account_holder = simpledialog.askstring("Input", "Enter Account Holder Name:")
        if account_holder is None:  
            return
        email = simpledialog.askstring("Input", "Enter your email:")
        if email is None:  
            return
        password = simpledialog.askstring("Input", "Enter your password:")
        validate_password()
        if password is None:  
            return
        confirm_password=simpledialog.askstring("Input","Confirm your password:")
        validate_password()
        if confirm_password is None:
            return
        if password!=confirm_password:
            messagebox.showerror("Error","Password doesn't match \n Please try again.")
        # Check if account number already exists
        if any(acc.account_number == account_number for acc in accounts):
            messagebox.showerror("Error", f"Account number {account_number} already exists.")
            return

        # Validate email1 format
        if not is_valid_email(email):
            messagebox.showerror("Error", "Invalid email format. Please try again.")
            return
         
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        if account_number and account_holder and email:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            new_account = BankAccount(account_number, account_holder, email,hashed_password, balance=0)
            accounts.append(new_account)
            #save_accounts(accounts)
            messagebox.showinfo("Success", "Account created successfully.")
        else:
            messagebox.showerror("Error", "Account creation failed.")


        if account_number and account_holder and email and password:
            new_account = BankAccount(account_number, account_holder, email,hashed_password, balance=0)  # Set initial balance to 0
            accounts.append(new_account)
            save_accounts(accounts)  # Save to MySQL
            #messagebox.showinfo("Success", "Account created successfully.")

            # Send email after account creation
            subject = "Thank You for Creating Your Account-E Bank"
            body = f"""Dear {account_holder},\n\nYour account with number {account_number} has been successfully created.\n\nThank you for choosing our banking service.
We are delighted to welcome you as a valued customer. Your new account has been successfully created, and we are excited to be part of your financial journey.\n
Your account details:\n\n Name: {account_holder}\nAccount number: {account_number}\nPassword:{password}\n\nYou can now access your account anytime through the Bank's online banking portal/mobile app.
We encourage you to explore the various services and features we offer to help you manage your finances with ease. \n\nThank you again for choosing our bank. We look forward to serving you."""

            send_email(subject, body, email)
        else:
            messagebox.showerror("Error", "Account creation failed. Please provide both account number and account holder name.")

    login_frame = tk.Frame(root, bg="lightblue")
    login_frame.pack(fill="both", expand=True)

    # Load background image into a Label
    image_path = r"C:\Users\niran\Downloads\SL-121021-47240-11.jpg" 
    img = Image.open(image_path)
    img_tk = ImageTk.PhotoImage(img.resize((800, 800), Image.Resampling.LANCZOS))

    background_label = tk.Label(login_frame, image=img_tk)
    background_label.place(relwidth=1, relheight=1)  # Make label fill the entire window
    background_label.image = img_tk  # Keep a reference to the image to prevent garbage collection


    login_label = tk.Label(login_frame, text="Login to Your Account", font=("Arial", 18, "bold"), bg="#043361", fg="#01d9e8")
    login_label.place(relx=0.5, rely=0.3, anchor="center")

    tk.Label(login_frame, text="Enter your Account Number", bg="#043361", font=("Arial",12,"bold"),fg="#01d9e8").place(relx=0.5, rely=0.35, anchor="center")
    login_acc_number_entry = tk.Entry(login_frame,width=30,bd=5)
    login_acc_number_entry.place(relx=0.5, rely=0.4, anchor="center")

    tk.Label(login_frame, text="Account Holder Name", bg="#043361", font=("Arial",12,"bold"),fg="#01d9e8").place(relx=0.5, rely=0.45, anchor="center")
    login_name_entry = tk.Entry(login_frame,width=30,bd=5)
    login_name_entry.place(relx=0.5, rely=0.5, anchor="center")
    
    tk.Label(login_frame, text="Password", bg="#043361", font=("Arial", 12, "bold"), fg="#01d9e8").place(relx=0.5, rely=0.55, anchor="center")
    login_password_entry = tk.Entry(login_frame,show="*" ,width=30, bd=5)
    login_password_entry.place(relx=0.5, rely=0.6, anchor="center")

    eye_open = Image.open(r"C:\Users\niran\Downloads\Eye open.png")
    eye_open = eye_open.resize((20, 20), Image.Resampling.LANCZOS)
    eye_open_tk = ImageTk.PhotoImage(eye_open)

    eye_closed = Image.open(r"C:\Users\niran\Downloads\Eye closed.png")
    eye_closed = eye_closed.resize((20, 20), Image.Resampling.LANCZOS)
    eye_closed_tk = ImageTk.PhotoImage(eye_closed)

    # Function to toggle password visibility
    def toggle_password():
        if login_password_entry.cget("show") == "*":
            login_password_entry.config(show="")
            eye_button.config(image=eye_open_tk)
        else:
            login_password_entry.config(show="*")
            eye_button.config(image=eye_closed_tk)

    # Create the eye icon button
    eye_button = tk.Button(login_frame, image=eye_closed_tk, bg="#043361",fg="#01d9e8", bd=0, command=toggle_password)
    eye_button.place(relx=0.65, rely=0.6, anchor="center")

    login_button = tk.Button(login_frame, text="Submit", bg="#043361", font=("Arial",12,"bold"),width=12, fg="#01d9e8", command=attempt_login)
    login_button.place(relx=0.6, rely=0.66, anchor="center")

    create_button = tk.Button(login_frame, text="Create Account", bg="#043361", font=("Arial",12,"bold"),width=12, fg="#01d9e8", command=create_account)
    create_button.place(relx=0.4, rely=0.66, anchor="center")

# Main banking window
def main_window(accounts,selected_account):
    
    #print(f"Welcome {current_account.account_holder}!")

    root = tk.Tk()
    root.title("Banking Application")
    root.geometry("800x600")
    root.configure(bg='lightblue')

    canvas = tk.Canvas(root, width=800, height=600)
    canvas.pack(fill="both", expand=True)

    # Load image and set it as background
    image_path = r"C:\Users\niran\Downloads\sl_121021_47240_16.jpg"  # Update path to your image
    img = Image.open(image_path)

   

    def update_image(event):
        resized_img = img.resize((event.width, event.height), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(resized_img)
        canvas.create_image(0, 0, image=img_tk, anchor="nw")
        canvas.image = img_tk  # Keep a reference to avoid garbage collection

    canvas.bind("<Configure>", update_image)
    

    # Frame for buttons with same color as background
    button_frame = tk.Frame(root, bg="#000040")
    button_frame.place(relx=0.05, rely=0.5, anchor="w", relwidth=0.3)

    def deposit_action():
        amount = simpledialog.askfloat("Input", "Enter deposit amount:")
        if selected_account and amount:
            result = selected_account.deposit(amount)
            messagebox.showinfo("Deposit", result)
        save_accounts(accounts)
    
    def withdraw_action():
        amount = simpledialog.askfloat("Input", "Enter withdrawal amount:")
        if selected_account and amount:
            result = selected_account.withdraw(amount)
            messagebox.showinfo("Withdrawal", result)
        save_accounts(accounts)
    def transfer_action():
        target_account_number = simpledialog.askstring("Input", "Enter target account number for transfer:")
        amount = simpledialog.askfloat("Input", "Enter transfer amount:")
        if selected_account and amount:
            target_account = next((acc for acc in accounts if str(acc.account_number) == target_account_number), None)
            if target_account:
                result = selected_account.transfer(target_account, amount)
                messagebox.showinfo("Transfer", result)
            else:
                messagebox.showerror("Error", "Target account not found.")
        save_accounts(accounts)

    
    def show_user_details():
        details = f"Account Number: {selected_account.account_number}\n"
        details += f"Account Holder: {selected_account.account_holder}\n"
        details += f"Email: {selected_account.email}\n"
        details += f"Balance: ${selected_account.balance:.2f}\n"
        messagebox.showinfo("User Details", details)
    
    def reset_password():
        acc_number = simpledialog.askinteger("Input", "Enter your Account Number:")
        if acc_number is None:
            return
    
        current_password = simpledialog.askstring("Input", "Enter your current password:")
        if current_password is None:
            return
    
        account = next((acc for acc in accounts if acc.account_number == acc_number), None)
        if account and account.verify_password(current_password):
            new_password = simpledialog.askstring("Input", "Enter your new password:")
            if new_password:
                hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                account.password =hashed_new_password  # Update the in-memory account password
            
            # Update the password in the database
                connection = create_connection()
                if connection:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE accounts SET password = %s WHERE account_number = %s", 
                                   (new_password, acc_number))
                    connection.commit()
                    cursor.close()
                    connection.close()
            
                messagebox.showinfo("Success", "Password has been reset successfully.")
            else:
                messagebox.showerror("Error", "New password cannot be empty.")
        else:
            messagebox.showerror("Error", "Account number or current password is incorrect.")

    def check_balance_action():
        if selected_account:
            messagebox.showinfo("Balance", f"Account Balance: ${selected_account.balance:.2f}")
    
    def save_and_exit_action():
        save_accounts(accounts)  # Save all accounts to MySQL
        root.destroy()  # Close the application

    def delete_account_from_db(account_number):
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
            
            # First, delete the transactions associated with this account
                cursor.execute("DELETE FROM transactions WHERE account_number = %s", (account_number,))
                connection.commit()
            
            # Now delete the account from the accounts table
                cursor.execute("DELETE FROM accounts WHERE account_number = %s", (account_number,))
                if cursor.rowcount == 0:
                    messagebox.showerror("Error", f"Account number {account_number} not found.")
                    return False
                connection.commit()
                cursor.close()
                connection.close()
                return True
            except Error as e:
                messagebox.showerror("Error", f"Error deleting account from database: {e}")
                connection.rollback()  # Rollback if error occurs
                return False
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    connection.close()
        else:
            messagebox.showerror("Error", "Failed to connect to the database.")
            return False

    def delete_account():
    # Ensure the account selected for deletion is the same as the logged-in account
        if selected_account:  # Ensure that an account is selected
        # Ask for account confirmation
            acc_number = simpledialog.askinteger("Input", f"Enter Account Number to delete (Current: {selected_account.account_number}):")
        
        # Check if the entered account number matches the selected account number
            if acc_number == selected_account.account_number:
            # Confirm deletion with the user
                confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete account {selected_account.account_number}? This action cannot be undone.")
                if confirm:
                # Proceed with deletion logic
                    email = selected_account.email  # Get the email of the selected account
                
                # Remove from the accounts list (in-memory)
                    accounts.remove(selected_account)
                
                # Remove from the database
                    if delete_account_from_db(acc_number):  # Now it deletes from the database
                        messagebox.showinfo("Success", f"Account {acc_number} deleted successfully.")
                    
                    # Send email confirmation for account deletion
                        subject = "Confirmation of Account Deletion-E Bank"
                        body = f"""Dear {selected_account.account_holder},\n\nWe are writing to confirm that your request to delete your account {acc_number} has been successfully processed. Your account with number {acc_number} has now been closed.
                    \n\nPlease note that once an account is deleted, it is no longer accessible and any remaining balance has been handled according to your instructions.
                    \n\nIf you did not request this, please contact us immediately.\n\nThank you for banking with us."""
                    
                        send_email(subject, body, email)  # Send the email confirmation
                    
                    # Log the user out after account deletion
                        logout()
                    else:
                        messagebox.showerror("Error", "Error deleting account from database.")
                else:
                    messagebox.showinfo("Info", "Account deletion canceled.")
            else:
                messagebox.showerror("Error", "You can only delete your own account. The account number entered does not match your selected account.")
        else:
            messagebox.showerror("Error", "No account is currently selected.")


    def logout():
        root.destroy()  # Close the current window
        login_window = tk.Tk()
        login_window.title("Banking Login")
        login_window.geometry("800x800")
        login_screen(login_window, accounts)
        login_window.mainloop()

    def contact_us():
        contact_message = """For any assistance, please contact us at:
    Phone: 123-456-7890
    Email: esupport@bank.com
    Address: 123 vivekanda Street, Banking City, India"""
        messagebox.showinfo("Contact Us", contact_message)
    
    def show_transaction_history(account):
        transactions = account.get_transactions()
        if transactions:
            history = "\n".join(transactions)
            messagebox.showinfo("Transaction History", history)
        else:
            messagebox.showinfo("Transaction History", "No transactions found.")
        
    menu_bar = tk.Menu(root)
    user_menu = tk.Menu(menu_bar, tearoff=0)
    user_menu.add_command(label="User Details", command=show_user_details)
    user_menu.add_command(label="Logout", command=logout)
    user_menu.add_command(label="Reset password",command=reset_password)
    user_menu.add_command(label="Delete account",command=delete_account)
    menu_bar.add_cascade(label="Menu", menu=user_menu)

    # Transactions Menu
    transaction_menu = tk.Menu(menu_bar, tearoff=0)
    transaction_menu.add_command(label="Transaction History", command=lambda: show_transaction_history(selected_account))
    menu_bar.add_cascade(label="Transactions", menu=transaction_menu)

    # Help Menu
    help_menu = tk.Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="Contact Us", command=contact_us)
    menu_bar.add_cascade(label="Help", menu=help_menu)
    root.config(menu=menu_bar)

    # Buttons for Deposit, Withdraw, Transfer, Check Balance and Save & Exit with new colors
    deposit_button = tk.Button(button_frame, text="Deposit", command=deposit_action, font=("Arial", 12), relief="flat", bg="#025696", activebackground="#043361", activeforeground="#01d9e8", bd=5, fg="#3ab9da")
    deposit_button.pack(fill="x", pady=10)

    withdraw_button = tk.Button(button_frame, text="Withdraw", command=withdraw_action, font=("Arial", 12), relief="flat", bg="#025696", activebackground="#043361", activeforeground="#01d9e8", bd=5, fg="#3ab9da")
    withdraw_button.pack(fill="x", pady=10)

    transfer_button = tk.Button(button_frame, text="Transfer", command=transfer_action, font=("Arial", 12), relief="flat", bg="#025696", activebackground="#043361", activeforeground="#01d9e8", bd=5, fg="#3ab9da")
    transfer_button.pack(fill="x", pady=10)

    check_balance_button = tk.Button(button_frame, text="Check Balance", command=check_balance_action, font=("Arial", 12), relief="flat", bg="#025696", activebackground="#043361", activeforeground="#01d9e8", bd=5, fg="#3ab9da")
    check_balance_button.pack(fill="x", pady=10)

    save_and_exit_button = tk.Button(button_frame, text="Save & Exit", command=save_and_exit_action, font=("Arial", 12), relief="flat", bg="#025696", activebackground="#043361", activeforeground="#01d9e8", bd=5, fg="#3ab9da")
    save_and_exit_button.pack(fill="x", pady=10)

    messagebox.showinfo("Successfully Logged In", f"Welcome {selected_account.account_holder}!")

    root.mainloop()
    


# Main function
if __name__ == "__main__":
    accounts = load_accounts()
    root = tk.Tk()
    root.title("Banking Application")
    root.geometry("800x800")
    login_screen(root, accounts)
    root.mainloop()

