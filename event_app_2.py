import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class EventManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Event Hub")
        self.root.geometry("1000x800")
        self.root.configure(bg="#2c3e50")  # Dark blue background

        # Custom style for modern design
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#2c3e50")
        self.style.configure("TLabel", background="#2c3e50", foreground="#333333", font=("Helvetica", 12))  # Dark gray text
        self.style.configure("TButton", background="#34495e", foreground="#333333", font=("Helvetica", 12), padding=10)  # Dark gray text
        self.style.map("TButton", background=[("active", "#1abc9c")], foreground=[("active", "#333333")])  # Teal on hover, dark gray text
        self.style.configure("TCombobox", background="white", foreground="#333333", font=("Helvetica", 12))  # Dark gray text
        self.style.configure("TEntry", background="white", foreground="#333333", font=("Helvetica", 12))  # Dark gray text
        self.style.configure("TNotebook", background="#2c3e50")
        self.style.configure("TNotebook.Tab", background="#34495e", foreground="#333333", font=("Helvetica", 12), padding=10)  # Dark gray text
        self.style.map("TNotebook.Tab", background=[("selected", "#1abc9c")], foreground=[("selected", "#333333")])  # Teal when selected, dark gray text

        # Create a notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        # Create tabs
        self.create_home_tab()
        self.create_events_tab()
        self.create_login_tab()

    def create_home_tab(self):
        home_tab = ttk.Frame(self.notebook)
        self.notebook.add(home_tab, text="Αρχική")

        label = ttk.Label(home_tab, text="Καλώς ήρθατε στο Event Hub!", font=("Helvetica", 16))
        label.pack(pady=20)

        button_frame = ttk.Frame(home_tab)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Δημιουργία Εκδήλωσης", command=self.open_create_event_modal).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Προβολή Εκδηλώσεων", command=self.show_events_tab).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Σύνδεση/Εγγραφή", command=self.show_login_tab).pack(side="left", padx=10)

    def create_events_tab(self):
        events_tab = ttk.Frame(self.notebook)
        self.notebook.add(events_tab, text="Εκδηλώσεις")

        label = ttk.Label(events_tab, text="Διαθέσιμες Εκδηλώσεις", font=("Helvetica", 16))
        label.pack(pady=20)

        # Filters
        filter_frame = ttk.Frame(events_tab)
        filter_frame.pack(pady=10)

        ttk.Label(filter_frame, text="Ημερομηνία:").pack(side="left", padx=5)
        self.date_filter_entry = ttk.Entry(filter_frame, width=15)
        self.date_filter_entry.pack(side="left", padx=5)

        ttk.Label(filter_frame, text="Τοποθεσία:").pack(side="left", padx=5)
        self.location_filter_combobox = ttk.Combobox(filter_frame, values=["Όλες", "Αθήνα", "Θεσσαλονίκη", "Πάτρα", "Ηράκλειο"], width=15)
        self.location_filter_combobox.pack(side="left", padx=5)

        ttk.Label(filter_frame, text="Είδος:").pack(side="left", padx=5)
        self.type_filter_combobox = ttk.Combobox(filter_frame, values=["Όλα", "Δημόσιο", "Ιδιωτικό"], width=15)
        self.type_filter_combobox.pack(side="left", padx=5)

        ttk.Button(filter_frame, text="Εφαρμογή Φίλτρων", command=self.apply_filters).pack(side="left", padx=5)

        # Event list
        self.events_list_frame = ttk.Frame(events_tab)
        self.events_list_frame.pack(fill="both", expand=True)

        # Demo events (similar to events.js)
        self.events = [
            {"id": 1, "title": "Συναυλία Rock", "date": "2025-04-10", "location": "Αθήνα", "type": "Δημόσιο", "description": "Μια συναυλία rock με διάσημους καλλιτέχνες."},
            {"id": 2, "title": "Γάμος - Μαρία & Γιάννης", "date": "2025-04-15", "location": "Θεσσαλονίκη", "type": "Ιδιωτικό", "description": "Γάμος στο Ξενοδοχοείο Ακρόπολις."},
            {"id": 3, "title": "Ομιλία - Τέχνη της Επικοινωνίας", "date": "2025-04-20", "location": "Πάτρα", "type": "Δημόσιο", "description": "Ομιλία για την τέχνη της επικοινωνίας."},
            {"id": 4, "title": "Βάφτιση - Μικρή Ελένη", "date": "2025-04-25", "location": "Ηράκλειο", "type": "Ιδιωτικό", "description": "Βάφτιση στην Εκκλησία Αγίου Νικολάου."},
            {"id": 5, "title": "Φεστιβάλ Κινηματογράφου", "date": "2025-05-05", "location": "Αθήνα", "type": "Δημόσιο", "description": "Διεθνές φεστιβάλ κινηματογράφου."},
            {"id": 6, "title": "Συναυλία Jazz", "date": "2025-05-10", "location": "Θεσσαλονίκη", "type": "Δημόσιο", "description": "Συναυλία jazz με διάσημους μουσικούς."},
            {"id": 7, "title": "Γιορτή Ανοιξης", "date": "2025-05-15", "location": "Πάτρα", "type": "Δημόσιο", "description": "Γιορτή για την άνοιξη στο κέντρο της πόλης."},
            {"id": 8, "title": "Πάρτυ Πρωτοχρονιάς", "date": "2025-12-31", "location": "Ηράκλειο", "type": "Δημόσιο", "description": "Πάρτυ Πρωτοχρονιάς με ζωντανή μουσική."},
            {"id": 9, "title": "Σεμινάριο Ψυχολογίας", "date": "2026-01-10", "location": "Αθήνα", "type": "Δημόσιο", "description": "Σεμινάριο για την ψυχολογία της ευτυχίας."},
            {"id": 10, "title": "Γάμος - Άννα & Νίκος", "date": "2026-01-20", "location": "Θεσσαλονίκη", "type": "Ιδιωτικό", "description": "Γάμος στο Ξενοδοχείο Μεγάλο Αλέξανδρο."},
        ]

        self.display_events(self.events)

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

    def display_events(self, events):
        for widget in self.events_list_frame.winfo_children():
            widget.destroy()

        for event in events:
            event_card = ttk.Frame(self.events_list_frame, padding=10, style="TFrame")
            event_card.pack(fill="x", pady=5)

            ttk.Label(event_card, text=event["title"], font=("Helvetica", 14, "bold")).pack(anchor="w")
            ttk.Label(event_card, text=f"Ημερομηνία: {event['date']}").pack(anchor="w")
            ttk.Label(event_card, text=f"Τοποθεσία: {event['location']}").pack(anchor="w")
            ttk.Label(event_card, text=f"Είδος: {event['type']}").pack(anchor="w")
            ttk.Label(event_card, text=event["description"]).pack(anchor="w")

            ttk.Button(event_card, text="Περισσότερες Πληροφορίες", command=lambda e=event: self.view_event_details(e)).pack(anchor="w")

    def apply_filters(self):
        date_filter = self.date_filter_entry.get()
        location_filter = self.location_filter_combobox.get()
        type_filter = self.type_filter_combobox.get()

        filtered_events = [event for event in self.events if
                           (not date_filter or event["date"] == date_filter) and
                           (location_filter == "Όλες" or event["location"] == location_filter) and
                           (type_filter == "Όλα" or event["type"] == type_filter)]

        self.display_events(filtered_events)

    def view_event_details(self, event):
        messagebox.showinfo("Λεπτομέρειες Εκδήλωσης", f"Τίτλος: {event['title']}\nΗμερομηνία: {event['date']}\nΤοποθεσία: {event['location']}\nΕίδος: {event['type']}\nΠεριγραφή: {event['description']}")

    def open_create_event_modal(self):
        # Create a new top-level window (modal-like)
        self.modal = tk.Toplevel(self.root)
        self.modal.title("Δημιουργία Νέας Εκδήλωσης")
        self.modal.geometry("500x400")
        self.modal.configure(bg="#2c3e50")  # Dark blue background
        self.modal.grab_set()  # Make the modal window modal (blocks interaction with the main window)

        # Event creation form
        ttk.Label(self.modal, text="Όνομα Εκδήλωσης:").pack()
        self.event_name_entry = ttk.Entry(self.modal, width=40)
        self.event_name_entry.pack(pady=5)

        ttk.Label(self.modal, text="Ημερομηνία:").pack()
        self.event_date_entry = ttk.Entry(self.modal, width=40)
        self.event_date_entry.pack(pady=5)

        ttk.Label(self.modal, text="Τοποθεσία:").pack()
        self.event_location_entry = ttk.Entry(self.modal, width=40)
        self.event_location_entry.pack(pady=5)

        ttk.Label(self.modal, text="Τύπος Εκδήλωσης:").pack()
        self.event_type_combobox = ttk.Combobox(self.modal, values=["Δημόσιο", "Ιδιωτικό"], width=37)
        self.event_type_combobox.pack(pady=5)

        ttk.Label(self.modal, text="Περιγραφή:").pack()
        self.event_description_entry = ttk.Entry(self.modal, width=40)
        self.event_description_entry.pack(pady=5)

        ttk.Label(self.modal, text="Εικόνα Εκδήλωσης (URL):").pack()
        self.event_image_entry = ttk.Entry(self.modal, width=40)
        self.event_image_entry.pack(pady=5)

        # Buttons
        button_frame = ttk.Frame(self.modal)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Κλείσιμο", command=self.modal.destroy).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Δημιουργία", command=self.create_event).pack(side="left", padx=10)

    def create_event(self):
        event_name = self.event_name_entry.get()
        event_date = self.event_date_entry.get()
        event_location = self.event_location_entry.get()
        event_type = self.event_type_combobox.get()
        event_description = self.event_description_entry.get()
        event_image = self.event_image_entry.get()

        if event_name and event_date and event_location and event_type and event_description and event_image:
            new_event = {
                "id": len(self.events) + 1,
                "title": event_name,
                "date": event_date,
                "location": event_location,
                "type": event_type,
                "description": event_description,
                "image": event_image
            }
            self.events.append(new_event)
            self.apply_filters()  # Refresh the event list
            messagebox.showinfo("Επιτυχία", "Η εκδήλωση δημιουργήθηκε με επιτυχία!")
            self.modal.destroy()  # Close the modal
        else:
            messagebox.showerror("Σφάλμα", "Παρακαλώ συμπληρώστε όλα τα πεδία.")

    def show_events_tab(self):
        self.notebook.select(1)  # Switch to the "Events" tab

    def show_login_tab(self):
        self.notebook.select(2)  # Switch to the "Login" tab

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
    root = tk.Tk()
    app = EventManagementApp(root)
    root.mainloop()