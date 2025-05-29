from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QSpinBox, QMessageBox, QScrollArea, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import json
from datetime import datetime

class TicketRefundDialog(QDialog):
    def __init__(self, ticket_group, parent=None):
        super().__init__(parent)
        self.ticket_group = ticket_group
        self.parent = parent
        self.setWindowTitle("Ακύρωση Εισιτηρίων")
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QLabel {
                color: #333333;
                font-family: 'Helvetica';
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Cancel Ticket")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        title.setStyleSheet("color: #D91656; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Ticket selection section
        ticket_section = QGroupBox("Select Tickets to Cancel")
        ticket_section.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #D91656;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        ticket_layout = QVBoxLayout(ticket_section)

        # Add ticket type selections
        self.ticket_selections = {}
        for ticket_type, type_info in self.ticket_group['ticket_types'].items():
            type_layout = QHBoxLayout()
            
            # Ticket type label
            type_label = QLabel(f"{ticket_type}:")
            type_label.setStyleSheet("font-weight: bold; color: #333; min-width: 120px;")
            type_layout.addWidget(type_label)
            
            # Available quantity label
            available_label = QLabel(f"Available: {type_info['quantity']}")
            available_label.setStyleSheet("color: #666; min-width: 100px;")
            type_layout.addWidget(available_label)
            
            # Quantity selector
            qty_label = QLabel("Cancel:")
            qty_label.setStyleSheet("color: #333;")
            type_layout.addWidget(qty_label)
            
            qty_spinbox = QSpinBox()
            qty_spinbox.setMinimum(0)
            qty_spinbox.setMaximum(type_info['quantity'])
            qty_spinbox.setValue(0)
            qty_spinbox.setStyleSheet("""
                QSpinBox {
                    padding: 5px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    min-width: 60px;
                }
            """)
            type_layout.addWidget(qty_spinbox)
            
            type_layout.addStretch()
            ticket_layout.addLayout(type_layout)
            
            self.ticket_selections[ticket_type] = {
                'spinbox': qty_spinbox,
                'price': type_info['price'],
                'max_quantity': type_info['quantity']
            }

        layout.addWidget(ticket_section)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Back button
        back_button = QPushButton("Πίσω")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        back_button.clicked.connect(self.reject)
        button_layout.addWidget(back_button)
        
        button_layout.addStretch()
        
        # Refund button
        refund_button = QPushButton("Refund")
        refund_button.setStyleSheet("""
            QPushButton {
                background-color: #D91656;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #640D5F;
            }
            QPushButton:pressed {
                background-color: #4a0a47;
            }
        """)
        refund_button.clicked.connect(lambda: self.process_refund("refund"))
        button_layout.addWidget(refund_button)

        # Credit button
        credit_button = QPushButton("Credit")
        credit_button.setStyleSheet("""
            QPushButton {
                background-color: #D91656;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #640D5F;
            }
            QPushButton:pressed {
                background-color: #4a0a47;
            }
        """)
        credit_button.clicked.connect(lambda: self.process_refund("credit"))
        button_layout.addWidget(credit_button)

        layout.addLayout(button_layout)

    def process_refund(self, refund_type):
        total_selected = 0
        total_refund = 0
        selected_tickets = {}

        # Calculate totals and validate selections
        for ticket_type, selection_data in self.ticket_selections.items():
            quantity = selection_data['spinbox'].value()
            if quantity > 0:
                total_selected += quantity
                total_refund += quantity * selection_data['price']
                selected_tickets[ticket_type] = quantity

        if total_selected == 0:
            QMessageBox.warning(self, "No Selection", "Please select at least one ticket to cancel.")
            return

        try:
            # Update tickets.json - remove or update tickets
            with open("tickets.json", "r", encoding="utf-8") as f:
                tickets = json.load(f)

            # Keep track of tickets to update
            tickets_to_update = []
            
            # Find tickets to update
            for ticket in tickets:
                if (ticket["user_id"] == self.parent.current_user["user_id"] and 
                    ticket["event_id"] == self.ticket_group["event"]["event_id"] and
                    ticket["status"] == "valid"):
                    
                    ticket_type = ticket["ticket_type"]
                    if ticket_type in selected_tickets and selected_tickets[ticket_type] > 0:
                        tickets_to_update.append(ticket)

            # Update or remove tickets
            for ticket in tickets_to_update:
                ticket_type = ticket["ticket_type"]
                if selected_tickets[ticket_type] >= ticket["quantity_bought"]:
                    # Remove the entire ticket
                    tickets.remove(ticket)
                    selected_tickets[ticket_type] -= ticket["quantity_bought"]
                else:
                    # Update the quantity
                    ticket["quantity_bought"] -= selected_tickets[ticket_type]
                    selected_tickets[ticket_type] = 0

            # Save updated tickets
            with open("tickets.json", "w", encoding="utf-8") as f:
                json.dump(tickets, f, indent=4, ensure_ascii=False)

            # Update event ticket availability
            with open("events.json", "r", encoding="utf-8") as f:
                events = json.load(f)

            # Find the event and update ticket quantities
            for event in events:
                if event["event_id"] == self.ticket_group["event"]["event_id"]:
                    for ticket_type in event["ticket_types"]:
                        if ticket_type["type"] in selected_tickets:
                            # Get the original selected quantity for this ticket type
                            original_selected = 0
                            for selection_data in self.ticket_selections.items():
                                if selection_data[0] == ticket_type["type"]:
                                    original_selected = selection_data[1]['spinbox'].value()
                                    break
                            # Add back the selected quantity
                            ticket_type["total_quantity"] += original_selected

            # Save updated events
            with open("events.json", "w", encoding="utf-8") as f:
                json.dump(events, f, indent=4, ensure_ascii=False)

            # Update user credit if credit option selected
            if refund_type == "credit":
                with open("users.json", "r", encoding="utf-8") as f:
                    users = json.load(f)

                for user in users:
                    if user["user_id"] == self.parent.current_user["user_id"]:
                        current_credit = float(user.get("credit", 0))
                        user["credit"] = str(current_credit + total_refund)  # Store as string
                        # Update in memory
                        self.parent.current_user["credit"] = str(current_credit + total_refund)
                        break

                with open("users.json", "w", encoding="utf-8") as f:
                    json.dump(users, f, indent=4, ensure_ascii=False)

                success_msg = QMessageBox()
                success_msg.setIcon(QMessageBox.Information)
                success_msg.setWindowTitle("Success")
                success_msg.setText("The value of the cancelled tickets has been saved to your account for future purchases.")
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
            else:  # refund option
                success_msg = QMessageBox()
                success_msg.setIcon(QMessageBox.Information)
                success_msg.setWindowTitle("Success")
                success_msg.setText("The money will be deposited immediately to the organization with which you made the purchase.")
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

            # Refresh the parent's ticket display and credit display
            if hasattr(self.parent, 'display_my_tickets'):
                self.parent.display_my_tickets()
            if hasattr(self.parent, 'update_credit_display'):
                self.parent.update_credit_display()

            # Get updated event data
            updated_event = None
            for event in events:
                if event["event_id"] == self.ticket_group["event"]["event_id"]:
                    updated_event = event
                    break

            # Try to refresh the event details view - try different possible view methods
            if updated_event:
                if hasattr(self.parent, 'show_attendee_event_details_in_stack'):
                    try:
                        self.parent.show_attendee_event_details_in_stack(updated_event)
                    except AttributeError:
                        pass  # View not available
                
                if hasattr(self.parent, 'show_event_details_in_stack'):
                    try:
                        self.parent.show_event_details_in_stack(updated_event)
                    except AttributeError:
                        pass  # View not available

            self.accept()

        except Exception as e:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText(f"An error occurred: {str(e)}")
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