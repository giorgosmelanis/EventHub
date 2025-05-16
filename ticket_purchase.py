from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QComboBox,
    QLineEdit, QPushButton, QMessageBox, QHBoxLayout, QSpacerItem, QSizePolicy, QDialog,
    QGroupBox, QListWidget, QListWidgetItem, QDialogButtonBox, QListView
)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt
import os

class TicketPurchaseModal(QWidget):
    def __init__(self, event, user):
        super().__init__()
        self.event = event
        self.user = user
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

        title = QLabel(f"Εκδήλωση: {event['title']}")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        title.setStyleSheet("color: #ff6f61;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

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
            QMessageBox.warning(self, "Καλάθι Άδειο", "Δεν έχετε επιλέξει εισιτήρια.")
            return
        QMessageBox.information(self, "Επιτυχία", "Η αγορά ολοκληρώθηκε!")
        self.close()
