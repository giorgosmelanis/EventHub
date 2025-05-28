import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QComboBox,
    QLineEdit, QPushButton, QMessageBox, QHBoxLayout, QSpacerItem, QSizePolicy, QDialog,
    QGroupBox, QListWidget, QListWidgetItem, QDialogButtonBox, QListView
)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt
import os
import json

class TicketPurchaseModal(QWidget):
    def __init__(self, event, user, parent=None):
        super().__init__()
        self.event = event
        self.user = user
        self.parent_app = parent
        self.setWindowTitle("Αγορά Εισιτηρίου")
        self.setGeometry(300, 300, 600, 600)
        self.setStyleSheet("""
            background-color: #f0f0f0;
            color: #333333;
            font-family: 'Helvetica';
        """)

        self.cart = []
        self.ticket_availability = {
            ticket ['type']: ticket['total_quantity'] for ticket in self.event.get("ticket_types", [])
        }

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Event Title
        title = QLabel(f"Εκδήλωση: {event['title']}")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        title.setStyleSheet("color: #ff6f61;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # Credit display (if user has credit)
        user_credit = float(self.user.get("credit", 0))
        if user_credit > 0:
            credit_label = QLabel(f"Έχετε πιστωτικό αξίας {user_credit:.2f} € για αγορές εισιτηρίων")
            credit_label.setFont(QFont("Helvetica", 12))
            credit_label.setStyleSheet("color: #D91656; padding: 5px;")
            credit_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(credit_label)

        image_label = QLabel()
        pixmap = QPixmap(event['image'])
        if not pixmap.isNull():
            pixmap = pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(image_label)

        layout.addSpacing(80)

        form = QFormLayout()
        form.setSpacing(20)

        self.ticket_type_combo = QComboBox()
        self.refresh_ticket_dropdown()
        self.ticket_type_combo.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.ticket_type_combo.currentIndexChanged.connect(self.update_price_and_quantity)
        form.addRow("Τύπος Εισιτηρίου:", self.ticket_type_combo)

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Ποσότητα")
        self.quantity_input.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.quantity_input.textChanged.connect(self.update_total_price)
        form.addRow("Ποσότητα:", self.quantity_input)

        self.total_price_label = QLabel("Σύνολο: 0€")
        self.total_price_label.setStyleSheet("font-size: 14px; color: #333;")
        form.addRow("", self.total_price_label)

        layout.addLayout(form)
        layout.addSpacing(10)

        button_layout = QHBoxLayout()

        cart_btn = QPushButton()
        cart_btn.setIcon(QIcon.fromTheme("basket"))
        cart_btn.setText("Καλάθι")
        cart_btn.clicked.connect(self.show_cart)
        cart_btn.setStyleSheet("""
            QPushButton {
                background-color: #4AA4C8;
                color: white;
                padding: 8px 15px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3786a8;
            }
        """)
        button_layout.addWidget(cart_btn)

        button_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding))

        cancel_btn = QPushButton("Ακύρωση")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b5b95;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #524778;
            }
        """)
        cancel_btn.clicked.connect(self.close)

        add_to_cart_btn = QPushButton("Προσθήκη στο Καλάθι")
        add_to_cart_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #EB5B00;
            }
        """)
        add_to_cart_btn.clicked.connect(self.add_to_cart)

        purchase_btn = QPushButton("Ολοκλήρωση Αγοράς")
        purchase_btn.setStyleSheet("""
            QPushButton {
                background-color: #88b04b;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #6d8b3a;
            }
        """)
        purchase_btn.clicked.connect(self.purchase_ticket)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(add_to_cart_btn)
        button_layout.addWidget(purchase_btn)

        layout.addLayout(button_layout)
        self.update_price_and_quantity()

    def refresh_ticket_dropdown(self):
        self.ticket_type_combo.clear()
        for ticket in self.event.get("ticket_types", []):
            available = self.ticket_availability[ticket['type']]
            display_text = f"{ticket['type']} - {ticket['price']}€ ({available} διαθέσιμα)"
            self.ticket_type_combo.addItem(display_text, ticket)

    def update_price_and_quantity(self):
        data = self.ticket_type_combo.currentData()
        if data:
            self.selected_price = data["price"]
            self.available_quantity = self.ticket_availability[data["type"]]
            self.update_total_price()

    def update_total_price(self):
        try:
            qty = int(self.quantity_input.text())
            new_total = self.selected_price * qty
            cart_total = sum(item["price"] * item["quantity"] for item in self.cart)
            full_total = new_total + cart_total

            if qty > self.available_quantity:
                self.total_price_label.setText("Υπέρβαση διαθεσιμότητας!")
            else:
                self.total_price_label.setText(f"Σύνολο: {full_total:.2f}€")
        except ValueError:
            cart_total = sum(item["price"] * item["quantity"] for item in self.cart)
            self.total_price_label.setText(f"Σύνολο: {cart_total:.2f}€")

    def add_to_cart(self):
        try:
            qty = int(self.quantity_input.text())
            data = self.ticket_type_combo.currentData()
            ticket_type = data["type"]
            if qty <= 0 or qty > self.ticket_availability[ticket_type]:
                QMessageBox.warning(self, "Σφάλμα", "Μη έγκυρη ποσότητα.")
                return

            found = False
            for item in self.cart:
                if item["type"] == ticket_type:
                    item["quantity"] += qty
                    found = True
                    break

            if not found:
                self.cart.append({"type": ticket_type, "price": data["price"], "quantity": qty})

            self.ticket_availability[ticket_type] -= qty
            QMessageBox.information(self, "Προστέθηκε", "Το εισιτήριο προστέθηκε στο καλάθι.")
            self.quantity_input.clear()
            self.refresh_ticket_dropdown()
            self.update_price_and_quantity()
        except ValueError:
            QMessageBox.warning(self, "Σφάλμα", "Εισάγετε έγκυρη ποσότητα.")

    def show_cart(self):
        if hasattr(self, 'cart_dialog') and self.cart_dialog.isVisible():
            return  # already open

        self.cart_dialog = QDialog(self)
        self.cart_dialog.setWindowTitle("Καλάθι Εισιτηρίων")
        self.cart_dialog.setMinimumWidth(400)

        self.cart_layout = QVBoxLayout(self.cart_dialog)
        self.update_cart_display()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.cart_dialog.accept)
        self.cart_layout.addWidget(button_box)

        self.cart_dialog.exec_()

    def update_cart_display(self):
        for i in reversed(range(self.cart_layout.count() - 1)):
            widget = self.cart_layout.itemAt(i).layout()
            if widget:
                while widget.count():
                    child = widget.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                self.cart_layout.removeItem(widget)

        for index, item in enumerate(self.cart):
            line = QHBoxLayout()
            label = QLabel(f"{item['type']} x {item['quantity']} = {item['price'] * item['quantity']:.2f}€")
            remove_btn = QPushButton("Αφαίρεση")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #88b04b;
                    color: white;
                    padding: 6px 12px;
                    font-size: 12px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #6d8b3a;
                }
            """)
            remove_btn.clicked.connect(lambda _, idx=index: self.remove_one_from_cart(idx))
            line.addWidget(label)
            line.addWidget(remove_btn)
            self.cart_layout.insertLayout(index, line)

    def remove_one_from_cart(self, index):
        if index >= len(self.cart):
            return

        item = self.cart[index]
        item['quantity'] -= 1
        self.ticket_availability[item['type']] += 1

        if item['quantity'] <= 0:
            self.cart.pop(index)

        self.refresh_ticket_dropdown()
        self.update_price_and_quantity()
        self.update_cart_display()

    def purchase_ticket(self):
        if not self.cart:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Καλάθι Άδειο")
            msg.setText("Δεν έχετε επιλέξει εισιτήρια.")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #f0f0f0;
                    color: #333333;
                }
                QPushButton {
                    background-color: #D91656;
                    color: white;
                    padding: 6px 20px;
                    border-radius: 3px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #B31145;
                }
            """)
            msg.exec_()
            return
        
        try:
            total_cost = sum(item['price'] * item['quantity'] for item in self.cart)
            user_credit = float(self.user.get('credit', '0'))
            
            # If user has credit, ask if they want to use it
            if user_credit > 0:
                use_credit_msg = QMessageBox()
                use_credit_msg.setWindowTitle("Χρήση Πιστωτικού")
                use_credit_msg.setText(f"Έχετε {user_credit:.2f}€ πιστωτικό, θα θέλατε να πραγματοποιήσετε την αγορά με το υπόλοιπό σας;")
                use_credit_msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #f0f0f0;
                        color: #333333;
                    }
                    QPushButton {
                        padding: 6px 20px;
                        border-radius: 3px;
                        min-width: 80px;
                    }
                    QPushButton[text="Ναι"] {
                        background-color: #D91656;
                        color: white;
                    }
                    QPushButton[text="Ναι"]:hover {
                        background-color: #B31145;
                    }
                    QPushButton[text="Όχι"] {
                        background-color: #6b5b95;
                        color: white;
                    }
                    QPushButton[text="Όχι"]:hover {
                        background-color: #524778;
                    }
                """)
                
                yes_button = QPushButton("Ναι")
                no_button = QPushButton("Όχι")
                use_credit_msg.addButton(yes_button, QMessageBox.YesRole)
                use_credit_msg.addButton(no_button, QMessageBox.NoRole)
                
                reply = use_credit_msg.exec_()
                
                if reply == 0:  # Yes was clicked
                    if user_credit >= total_cost:
                        # Full payment with credit
                        remaining_credit = user_credit - total_cost
                        self.update_user_credit(remaining_credit)
                    else:
                        # Partial payment with credit
                        info_msg = QMessageBox()
                        info_msg.setIcon(QMessageBox.Information)
                        info_msg.setWindowTitle("Μερική Χρήση Πιστωτικού")
                        info_msg.setText("Θα χρησιμοποιηθεί όλο το πιστωτικό σας και η διαφορά θα καλυφθεί από εσάς.")
                        info_msg.setStyleSheet("""
                            QMessageBox {
                                background-color: #f0f0f0;
                                color: #333333;
                            }
                            QPushButton {
                                background-color: #D91656;
                                color: white;
                                padding: 6px 20px;
                                border-radius: 3px;
                                min-width: 80px;
                            }
                            QPushButton:hover {
                                background-color: #B31145;
                            }
                        """)
                        info_msg.exec_()
                        
                        self.update_user_credit(0)  # Set credit to 0
            
            # Save tickets to tickets.json
            if self.save_tickets_to_file():
                # Update event ticket availability
                self.update_event_ticket_availability()
                
                success_msg = QMessageBox()
                success_msg.setIcon(QMessageBox.Information)
                success_msg.setWindowTitle("Επιτυχία")
                success_msg.setText("Η αγορά ολοκληρώθηκε επιτυχώς!")
                success_msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #f0f0f0;
                        color: #333333;
                    }
                    QPushButton {
                        background-color: #D91656;
                        color: white;
                        padding: 6px 20px;
                        border-radius: 3px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #B31145;
                    }
                """)
                success_msg.exec_()
                
                # Get updated event data
                try:
                    with open("events.json", "r", encoding="utf-8") as f:
                        events = json.load(f)
                        for e in events:
                            if e["event_id"] == self.event["event_id"]:
                                updated_event = e
                                break
                except Exception as e:
                    print(f"Error loading updated event data: {str(e)}")
                    updated_event = self.event
                
                # Notify parent app to reload events data and update views
                if self.parent_app:
                    if hasattr(self.parent_app, 'reload_events_data'):
                        self.parent_app.reload_events_data()
                    if hasattr(self.parent_app, 'update_credit_display'):
                        self.parent_app.update_credit_display()
                    # Force refresh of event details with updated data
                    if hasattr(self.parent_app, 'show_attendee_event_details_in_stack'):
                        self.parent_app.show_attendee_event_details_in_stack(updated_event)
                
                self.close()
            else:
                raise Exception("Failed to save tickets")
                
        except Exception as e:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Σφάλμα")
            error_msg.setText(f"Σφάλμα κατά την αγορά: {str(e)}")
            error_msg.setStyleSheet("""
                QMessageBox {
                    background-color: #f0f0f0;
                    color: #333333;
                }
                QPushButton {
                    background-color: #D91656;
                    color: white;
                    padding: 6px 20px;
                    border-radius: 3px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #B31145;
                }
            """)
            error_msg.exec_()

    def update_user_credit(self, new_credit):
        """Update user's credit in users.json"""
        try:
            with open("users.json", "r", encoding="utf-8") as f:
                users = json.load(f)
            
            for user in users:
                if user["user_id"] == self.user["user_id"]:
                    user["credit"] = str(new_credit)  # Store as string
                    self.user["credit"] = str(new_credit)  # Update in memory
                    break
            
            with open("users.json", "w", encoding="utf-8") as f:
                json.dump(users, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            raise Exception(f"Failed to update user credit: {str(e)}")

    def save_tickets_to_file(self):
        """Save purchased tickets to tickets.json."""
        try:
            # Load existing tickets
            try:
                with open("tickets.json", "r", encoding="utf-8") as f:
                    tickets = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                tickets = []

            # Get the next ticket ID
            next_ticket_id = max([t.get("ticket_id", 0) for t in tickets], default=0) + 1

            # For each item in cart
            for item in self.cart:
                # Check if user already has tickets of this type for this event
                existing_ticket = None
                for ticket in tickets:
                    if (ticket["event_id"] == self.event["event_id"] and 
                        ticket["user_id"] == self.user["user_id"] and 
                        ticket["ticket_type"] == item["type"] and
                        ticket["status"] == "valid"):
                        existing_ticket = ticket
                        break

                if existing_ticket:
                    # Update existing ticket quantity
                    existing_ticket["quantity_bought"] += item["quantity"]
                else:
                    # Create new ticket
                    new_ticket = {
                        "ticket_id": next_ticket_id,
                        "event_id": self.event["event_id"],
                        "user_id": self.user["user_id"],
                        "ticket_type": item["type"],
                        "quantity_bought": item["quantity"],
                        "price": item["price"],
                        "purchase_date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "status": "valid",
                        "qr_code": f"TKT-{next_ticket_id}-{self.event['event_id']}-{self.user['user_id']}"
                    }
                    tickets.append(new_ticket)
                    next_ticket_id += 1

            # Save updated tickets
            with open("tickets.json", "w", encoding="utf-8") as f:
                json.dump(tickets, f, indent=4, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error saving tickets: {str(e)}")
            return False

    def update_event_ticket_availability(self):
        """Update the event's ticket availability in events.json."""
        # Load events
        try:
            with open("events.json", "r", encoding="utf-8") as f:
                events = json.load(f)
        except FileNotFoundError:
            return
        
        # Find and update the event
        for event in events:
            if event["event_id"] == self.event["event_id"]:
                # Update ticket quantities based on cart
                for cart_item in self.cart:
                    for ticket_type in event.get("ticket_types", []):
                        if ticket_type["type"] == cart_item["type"]:
                            ticket_type["total_quantity"] -= cart_item["quantity"]
                            # Ensure quantity doesn't go below 0
                            if ticket_type["total_quantity"] < 0:
                                ticket_type["total_quantity"] = 0
                break
        
        # Save updated events
        with open("events.json", "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=4)
