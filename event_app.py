import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import ttkbootstrap as tb

class EventManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Event Hub")
        self.root.geometry("800x600")

        # Create a notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        # Create tabs
        self.create_home_tab()
        self.create_events_tab()
        self.create_create_event_tab()
        self.create_login_tab()

    def create_home_tab(self):
        home_tab = ttk.Frame(self.notebook)
        self.notebook.add(home_tab, text="Αρχική")

        label = ttk.Label(home_tab, text="Καλώς ήρθατε στο Event Hub!", font=("Helvetica", 16))
        label.pack(pady=20)

        button_frame = ttk.Frame(home_tab)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Δημιουργία Εκδήλωσης", command=self.show_create_event_tab).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Προβολή Εκδηλώσεων", command=self.show_events_tab).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Σύνδεση/Εγγραφή", command=self.show_login_tab).pack(side="left", padx=10)

    def create_events_tab(self):
        events_tab = ttk.Frame(self.notebook)
        self.notebook.add(events_tab, text="Εκδηλώσεις")

        label = ttk.Label(events_tab, text="Διαθέσιμες Εκδηλώσεις", font=("Helvetica", 16))
        label.pack(pady=20)

        # Example events list
        self.events_listbox = tk.Listbox(events_tab, width=50, height=10)
        self.events_listbox.pack(pady=10)

        # Add some example events
        self.events_listbox.insert(tk.END, "Συναυλία στην Αθήνα - 2023-12-15")
        self.events_listbox.insert(tk.END, "Φεστιβάλ Θεσσαλονίκης - 2023-12-20")

        ttk.Button(events_tab, text="Εγγραφή σε Εκδήλωση", command=self.register_for_event).pack(pady=10)

    def create_create_event_tab(self):
        create_event_tab = ttk.Frame(self.notebook)
        self.notebook.add(create_event_tab, text="Δημιουργία Εκδήλωσης")

        label = ttk.Label(create_event_tab, text="Δημιουργία Νέας Εκδήλωσης", font=("Helvetica", 16))
        label.pack(pady=20)

        # Event creation form
        ttk.Label(create_event_tab, text="Όνομα Εκδήλωσης:").pack()
        self.event_name_entry = ttk.Entry(create_event_tab, width=40)
        self.event_name_entry.pack(pady=5)

        ttk.Label(create_event_tab, text="Ημερομηνία:").pack()
        self.event_date_entry = ttk.Entry(create_event_tab, width=40)
        self.event_date_entry.pack(pady=5)

        ttk.Label(create_event_tab, text="Τοποθεσία:").pack()
        self.event_location_entry = ttk.Entry(create_event_tab, width=40)
        self.event_location_entry.pack(pady=5)

        ttk.Label(create_event_tab, text="Τύπος Εκδήλωσης:").pack()
        self.event_type_combobox = ttk.Combobox(create_event_tab, values=["Δημόσιο", "Ιδιωτικό"], width=37)
        self.event_type_combobox.pack(pady=5)

        ttk.Label(create_event_tab, text="Περιγραφή:").pack()
        self.event_description_entry = ttk.Entry(create_event_tab, width=40)
        self.event_description_entry.pack(pady=5)

        ttk.Button(create_event_tab, text="Δημιουργία", command=self.create_event).pack(pady=10)

    def create_login_tab(self):
        login_tab = ttk.Frame(self.notebook)
        self.notebook.add(login_tab, text="Σύνδεση/Εγγραφή")

        label = ttk.Label(login_tab, text="Σύνδεση/Εγγραφή", font=("Helvetica", 16))
        label.pack(pady=20)

        ttk.Label(login_tab, text="Email:").pack()
        self.email_entry = ttk.Entry(login_tab, width=40)
        self.email_entry.pack(pady=5)

        ttk.Label(login_tab, text="Κωδικός:").pack()
        self.password_entry = ttk.Entry(login_tab, width=40, show="*")
        self.password_entry.pack(pady=5)

        ttk.Button(login_tab, text="Σύνδεση", command=self.login).pack(pady=10)
        ttk.Button(login_tab, text="Εγγραφή", command=self.signup).pack(pady=10)

    def show_create_event_tab(self):
        self.notebook.select(2)  # Switch to the "Create Event" tab

    def show_events_tab(self):
        self.notebook.select(1)  # Switch to the "Events" tab

    def show_login_tab(self):
        self.notebook.select(3)  # Switch to the "Login" tab

    def create_event(self):
        event_name = self.event_name_entry.get()
        event_date = self.event_date_entry.get()
        event_location = self.event_location_entry.get()
        event_type = self.event_type_combobox.get()
        event_description = self.event_description_entry.get()

        if event_name and event_date and event_location and event_type and event_description:
            self.events_listbox.insert(tk.END, f"{event_name} - {event_date} - {event_location}")
            messagebox.showinfo("Επιτυχία", "Η εκδήλωση δημιουργήθηκε με επιτυχία!")
        else:
            messagebox.showerror("Σφάλμα", "Παρακαλώ συμπληρώστε όλα τα πεδία.")

    def register_for_event(self):
        selected_event = self.events_listbox.get(tk.ACTIVE)
        if selected_event:
            messagebox.showinfo("Εγγραφή", f"Εγγραφήκατε στην εκδήλωση: {selected_event}")
        else:
            messagebox.showerror("Σφάλμα", "Παρακαλώ επιλέξτε μια εκδήλωση.")

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()

        if email and password:
            messagebox.showinfo("Σύνδεση", "Συνδεθήκατε με επιτυχία!")
        else:
            messagebox.showerror("Σφάλμα", "Παρακαλώ συμπληρώστε email και κωδικό.")

    def signup(self):
        email = self.email_entry.get()
        password = self.password_entry.get()

        if email and password:
            messagebox.showinfo("Εγγραφή", "Εγγραφήκατε με επιτυχία!")
        else:
            messagebox.showerror("Σφάλμα", "Παρακαλώ συμπληρώστε email και κωδικό.")

if __name__ == "__main__":
    root = tb.Window(themename="cosmo")  # Use ttkbootstrap for a modern look
    app = EventManagementApp(root)
    root.mainloop()