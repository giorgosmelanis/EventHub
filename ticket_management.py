from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QScrollArea, QGroupBox, QMessageBox, QDialog, QLineEdit, QDialogButtonBox,
    QGraphicsDropShadowEffect, QComboBox, QSpinBox, QFormLayout, QFileDialog
)
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.QtCore import Qt
from datetime import datetime
import json
import os
import tempfile
import subprocess
import platform

# Import reportlab for PDF generation
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib.colors import black, blue, red
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from ticket_refund import TicketRefundDialog

class TicketManagementMixin:
    """Mixin class to add ticket management functionality to the main UI."""
    
    def show_my_tickets_tab(self):
        """Show the My Tickets tab and display user's tickets."""
        i = self.get_tab_index("My Tickets")
        if i is not None:
            self.tabs.setCurrentIndex(i)
            self.display_my_tickets()

    def display_my_tickets(self):
        """Display user's tickets categorized by upcoming vs past events."""
        # Get the My Tickets tab layout
        my_tickets_tab = self.private_tabs.get("My Tickets")
        if not my_tickets_tab:
            return
            
        # Clear existing content except the title
        layout = my_tickets_tab.layout()
        while layout.count() > 1:  # Keep the title (first item)
            item = layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            # Load tickets and events
            with open("tickets.json", "r", encoding="utf-8") as f:
                tickets = json.load(f)
            
            # Filter tickets for current user
            user_tickets = [t for t in tickets if t["user_id"] == self.current_user["user_id"]]
            
            if not user_tickets:
                no_tickets_label = QLabel("You don't have any tickets yet.")
                no_tickets_label.setStyleSheet("font-size: 14px; color: #666; padding: 20px;")
                layout.addWidget(no_tickets_label)
                return
            
            # Create a stacked widget to hold both the tickets list and ticket details
            self.tickets_stack = QStackedWidget()
            layout.addWidget(self.tickets_stack)

            # Create the tickets list widget
            tickets_list_widget = QWidget()
            tickets_list_layout = QHBoxLayout(tickets_list_widget)  # Changed to horizontal layout
            tickets_list_layout.setSpacing(20)
            tickets_list_layout.setContentsMargins(20, 20, 20, 20)

            # Create the ticket details widget
            self.ticket_details_widget = QWidget()
            self.ticket_details_layout = QVBoxLayout(self.ticket_details_widget)

            # Add both widgets to the stack
            self.tickets_stack.addWidget(tickets_list_widget)
            self.tickets_stack.addWidget(self.ticket_details_widget)
            
            # Categorize tickets by event date
            current_date = datetime.now().date()
            upcoming_tickets = []
            past_tickets = []
            
            print(f"Debug - Current date: {current_date}")
            
            for ticket in user_tickets:
                # Get event information
                event = next((e for e in self.events if e["event_id"] == ticket["event_id"]), None)
                if event:
                    try:
                        event_date = datetime.strptime(event["start_date"], "%d/%m/%Y").date()
                        print(f"Debug - Ticket {ticket['ticket_id']}: Event {event['event_id']} ({event['title']}) on {event_date}, Status: {ticket['status']}")
                        if event_date >= current_date:
                            upcoming_tickets.append(ticket)
                            print(f"Debug - Added to upcoming tickets")
                        else:
                            past_tickets.append(ticket)
                            print(f"Debug - Added to past tickets")
                    except ValueError as e:
                        print(f"Debug - Date parsing error for event {event['event_id']}: {e}")
                        # If date parsing fails, put in upcoming by default
                        upcoming_tickets.append(ticket)
                else:
                    print(f"Debug - No event found for ticket {ticket['ticket_id']} (event_id: {ticket['event_id']})")
            
            # Create left column for upcoming tickets
            left_column = QWidget()
            left_layout = QVBoxLayout(left_column)
            left_layout.setSpacing(20)
            left_layout.setContentsMargins(0, 0, 10, 0)
            
            # Create right column for past tickets
            right_column = QWidget()
            right_layout = QVBoxLayout(right_column)
            right_layout.setSpacing(20)
            right_layout.setContentsMargins(10, 0, 0, 0)
            
            # Create sections for each category
            self.create_ticket_category_section(left_layout, "Ενεργά Εισιτήρια", upcoming_tickets, "#28a745")
            self.create_ticket_category_section(right_layout, "Παλιά Εισιτήρια", past_tickets, "#ff0000")
            
            # Add columns to the main layout
            tickets_list_layout.addWidget(left_column)
            tickets_list_layout.addWidget(right_column)
            
            # Show the tickets list
            self.tickets_stack.setCurrentIndex(0)
            
        except FileNotFoundError:
            error_label = QLabel("No ticket information found.")
            error_label.setStyleSheet("font-size: 14px; color: #666; padding: 20px;")
            layout.addWidget(error_label)
        except json.JSONDecodeError:
            error_label = QLabel("Error loading ticket information.")
            error_label.setStyleSheet("font-size: 14px; color: #666; padding: 20px;")
            layout.addWidget(error_label)

    def create_ticket_category_section(self, parent_layout, title, tickets, color):
        """Create a section for a specific ticket category."""
        # Always show category title, even if no tickets
        category_label = QLabel(title)
        category_label.setFont(QFont("Helvetica", 16, QFont.Bold))
        category_label.setStyleSheet(f"color: {color}; padding: 10px 0;")
        parent_layout.addWidget(category_label)
        
        # Create a scroll area for tickets
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none; background-color: transparent;")
        scroll_area.setMinimumHeight(400)  # Set minimum height
        
        tickets_container = QWidget()
        tickets_layout = QVBoxLayout(tickets_container)
        tickets_layout.setSpacing(10)
        tickets_layout.setContentsMargins(0, 0, 0, 0)
        tickets_layout.setAlignment(Qt.AlignTop)  # Align tickets to top
        
        if not tickets:
            # Show "No tickets" message if empty
            no_tickets_label = QLabel("No tickets in this category")
            no_tickets_label.setStyleSheet("color: #999; font-style: italic; padding: 20px;")
            no_tickets_label.setAlignment(Qt.AlignCenter)
            tickets_layout.addWidget(no_tickets_label)
        else:
            # Group tickets by event
            grouped_tickets = self.group_tickets_by_event(tickets)
            
            # Add grouped tickets to this category
            for event_id, ticket_group in grouped_tickets.items():
                self.create_grouped_ticket_widget(tickets_layout, ticket_group)
        
        # Add stretch to push content to top
        tickets_layout.addStretch()
        
        scroll_area.setWidget(tickets_container)
        parent_layout.addWidget(scroll_area)
        
        # Add spacing between categories
        parent_layout.addSpacing(10)

    def group_tickets_by_event(self, tickets):
        """Group tickets by event ID and combine ticket types and quantities."""
        grouped = {}
        
        for ticket in tickets:
            event_id = ticket["event_id"]
            
            if event_id not in grouped:
                # Get event information
                event = next((e for e in self.events if e["event_id"] == event_id), None)
                grouped[event_id] = {
                    'event': event,
                    'tickets': [],
                    'ticket_types': {},
                    'total_quantity': 0,
                    'total_price': 0,
                    'purchase_date': ticket['purchase_date'],  # Use first ticket's purchase date
                    'status': ticket['status']  # Assume all tickets for same event have same status
                }
            
            # Add ticket to the group
            grouped[event_id]['tickets'].append(ticket)
            
            # Group by ticket type
            ticket_type = ticket['ticket_type']
            if ticket_type not in grouped[event_id]['ticket_types']:
                grouped[event_id]['ticket_types'][ticket_type] = {
                    'quantity': 0,
                    'price': ticket['price']
                }
            
            grouped[event_id]['ticket_types'][ticket_type]['quantity'] += ticket['quantity_bought']
            grouped[event_id]['total_quantity'] += ticket['quantity_bought']
            grouped[event_id]['total_price'] += ticket['price'] * ticket['quantity_bought']
        
        return grouped

    def create_grouped_ticket_widget(self, parent_layout, ticket_group):
        """Create a widget for displaying grouped tickets for a single event."""
        event = ticket_group['event']
        if not event:
            return
            
        # Ticket Container
        ticket_widget = QWidget()
        ticket_widget.setStyleSheet("""
            QWidget#ticketContainer {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
            QWidget#ticketContainer:hover {
                border: 2px solid #D91656;
                cursor: pointer;
            }
        """)
        ticket_widget.setObjectName("ticketContainer")
        ticket_layout = QHBoxLayout(ticket_widget)
        ticket_layout.setContentsMargins(15, 15, 15, 15)
        
        # Left: Event Image
        image_container = QWidget()
        image_container.setFixedSize(80, 80)  # Smaller image for better layout
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        image_label = QLabel()
        pixmap = QPixmap(event.get("image", "event_images/default_event.jpg"))
        scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(image_label)
        ticket_layout.addWidget(image_container)
        
        # Right: Ticket Details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setSpacing(3)
        
        # Event title
        title_label = QLabel(event["title"])
        title_label.setFont(QFont("Helvetica", 12, QFont.Bold))
        title_label.setStyleSheet("color: #D91656;")
        details_layout.addWidget(title_label)
        
        # Event date and location
        date_location = QLabel(f"{event['start_date']} • {event['location']}")
        date_location.setStyleSheet("color: #666; font-size: 11px;")
        details_layout.addWidget(date_location)
        
        # Ticket types and quantities (combined)
        ticket_types_text = []
        for ticket_type, type_info in ticket_group['ticket_types'].items():
            ticket_types_text.append(f"{ticket_type} (x{type_info['quantity']})")
        
        ticket_info = QLabel(f"Ticket Types: {', '.join(ticket_types_text)}")
        ticket_info.setStyleSheet("color: #333; font-size: 11px;")
        ticket_info.setWordWrap(True)
        details_layout.addWidget(ticket_info)
        
        # Total quantity and price
        total_info = QLabel(f"Total Quantity: {ticket_group['total_quantity']} • Total Price: €{ticket_group['total_price']}")
        total_info.setStyleSheet("color: #333; font-size: 11px; font-weight: bold;")
        details_layout.addWidget(total_info)
        
        # Status
        status_label = QLabel(f"Status: {ticket_group['status'].title()}")
        status_color = "#28a745" if ticket_group['status'] == "valid" else "#6c757d"
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold; font-size: 11px;")
        details_layout.addWidget(status_label)
        
        # Purchase date
        purchase_date = QLabel(f"Purchased: {ticket_group['purchase_date']}")
        purchase_date.setStyleSheet("color: #666; font-size: 10px;")
        details_layout.addWidget(purchase_date)
        
        ticket_layout.addWidget(details_widget)
        
        # Make the ticket clickable - pass the first ticket for compatibility
        first_ticket = ticket_group['tickets'][0]
        ticket_widget.mousePressEvent = lambda event, t=first_ticket: self.show_grouped_ticket_details(ticket_group)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        ticket_widget.setGraphicsEffect(shadow)
        
        parent_layout.addWidget(ticket_widget)

    def show_grouped_ticket_details(self, ticket_group):
        """Show detailed information about grouped tickets with action buttons."""
        # Clear previous content
        while self.ticket_details_layout.count():
            item = self.ticket_details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        event = ticket_group['event']
        if not event:
            return

        # Create a scroll area for the content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Ticket Title
        title = QLabel(f"Ticket Details - {event['title']}")
        title.setFont(QFont("Helvetica", 24, QFont.Bold))
        title.setStyleSheet("color: #D91656;")
        content_layout.addWidget(title, alignment=Qt.AlignCenter)
        
        # Event Image
        image_label = QLabel()
        pixmap = QPixmap(event.get("image", "event_images/default_event.jpg"))
        scaled_pixmap = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        content_layout.addWidget(image_label, alignment=Qt.AlignCenter)
        
        # Event Details Section
        event_details_group = QGroupBox("Event Information")
        event_details_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #D91656;
                padding: 0 10px;
            }
        """)
        event_details_layout = QVBoxLayout()
        
        event_details = [
            ("📅 Ημερομηνία:", f"{event['start_date']} - {event['end_date']}"),
            ("🕐 Ώρα:", event['start_time']),
            ("📍 Τοποθεσία:", event['location']),
            ("👤 Διοργανωτής:", event.get('organizer', 'N/A'))
        ]
        
        for label, value in event_details:
            detail_widget = QWidget()
            detail_layout = QHBoxLayout(detail_widget)
            detail_layout.setContentsMargins(10, 5, 10, 5)
            
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 12, QFont.Bold))
            label_widget.setStyleSheet("color: #333; min-width: 120px;")
            detail_layout.addWidget(label_widget)
            
            value_widget = QLabel(value)
            value_widget.setFont(QFont("Arial", 12))
            value_widget.setStyleSheet("color: #555;")
            value_widget.setWordWrap(True)
            detail_layout.addWidget(value_widget)
            
            event_details_layout.addWidget(detail_widget)
        
        event_details_group.setLayout(event_details_layout)
        content_layout.addWidget(event_details_group)
        
        # Ticket Details Section (showing all ticket types)
        tickets_details_group = QGroupBox("Ticket Information")
        tickets_details_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #D91656;
                padding: 0 10px;
            }
        """)
        tickets_details_layout = QVBoxLayout()
        
        # Show details for each ticket type
        for ticket_type, type_info in ticket_group['ticket_types'].items():
            type_details_text = f"""
            <div style='background-color: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 5px;'>
            <p style='font-size: 14px; margin: 0;'>
            <b>Ticket Type:</b> {ticket_type}<br>
            <b>Quantity:</b> {type_info['quantity']}<br>
            <b>Price per Ticket:</b> €{type_info['price']}<br>
            <b>Subtotal:</b> €{type_info['price'] * type_info['quantity']}
            </p>
            </div>
            """
            
            type_details_label = QLabel(type_details_text)
            type_details_label.setWordWrap(True)
            type_details_label.setStyleSheet("color: #333;")
            tickets_details_layout.addWidget(type_details_label)
        
        # Total information
        total_text = f"""
        <p style='font-size: 16px; font-weight: bold; color: #D91656;'>
        <b>Total Quantity:</b> {ticket_group['total_quantity']}<br>
        <b>Total Price:</b> €{ticket_group['total_price']}<br>
        <b>Status:</b> {ticket_group['status'].title()}<br>
        <b>Purchase Date:</b> {ticket_group['purchase_date']}
        </p>
        """
        
        total_label = QLabel(total_text)
        total_label.setWordWrap(True)
        total_label.setStyleSheet("color: #333;")
        tickets_details_layout.addWidget(total_label)
        
        tickets_details_group.setLayout(tickets_details_layout)
        content_layout.addWidget(tickets_details_group)
        
        # QR Code Section (for valid tickets)
        if ticket_group['status'] == 'valid':
            qr_group = QGroupBox("QR Codes for Check-in")
            qr_group.setStyleSheet("""
                QGroupBox {
                    font-size: 16px;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    margin-top: 10px;
                }
                QGroupBox::title {
                    color: #D91656;
                    padding: 0 10px;
                }
            """)
            qr_layout = QVBoxLayout()
            
            # Show QR codes for all tickets
            for i, ticket in enumerate(ticket_group['tickets']):
                qr_label = QLabel(f"QR Code {i+1}: {ticket['qr_code']}")
                qr_label.setFont(QFont("Courier", 14, QFont.Bold))
                qr_label.setStyleSheet("color: #333; background-color: #f8f9fa; padding: 10px; border: 1px solid #ddd; margin: 2px 0;")
                qr_label.setAlignment(Qt.AlignCenter)
                qr_layout.addWidget(qr_label)
            
            qr_group.setLayout(qr_layout)
            content_layout.addWidget(qr_group)
        
        # Action Buttons
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 20, 0, 0)
        
        # Back Button
        back_btn = QPushButton("Πίσω")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 12px 30px;
                font-size: 16px;
                border-radius: 5px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        back_btn.clicked.connect(lambda: self.tickets_stack.setCurrentIndex(0))
        buttons_layout.addWidget(back_btn)
        
        # Action buttons based on ticket status and event date
        if ticket_group['status'] == 'valid':
            # Check if event has passed
            try:
                event_date = datetime.strptime(event["start_date"], "%d/%m/%Y").date()
                current_date = datetime.now().date()
                event_passed = event_date < current_date
                
                # Download Ticket Button (always available for valid tickets)
                download_btn = QPushButton("Download Tickets")
                download_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #D91656;
                        color: white;
                        padding: 12px 30px;
                        font-size: 16px;
                        border-radius: 5px;
                        min-width: 120px;
                    }
                    QPushButton:hover {
                        background-color: #640D5F;
                    }
                """)
                if event_passed:
                    download_btn.clicked.connect(lambda: self.show_event_passed_message())
                else:
                    # Pass the first ticket for compatibility with existing PDF generation
                    download_btn.clicked.connect(lambda: self.download_ticket_pdf(ticket_group['tickets'][0], event))
                buttons_layout.addWidget(download_btn)
                
                # Cancel Tickets Button (only if event hasn't passed)
                if not event_passed:
                    cancel_btn = QPushButton("Cancel Tickets")
                    cancel_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #D91656;
                            color: white;
                            padding: 12px 30px;
                            font-size: 16px;
                            border-radius: 5px;
                            min-width: 120px;
                        }
                        QPushButton:hover {
                            background-color: #640D5F;
                        }
                    """)
                    cancel_btn.clicked.connect(lambda: self.cancel_grouped_tickets(ticket_group))
                    buttons_layout.addWidget(cancel_btn)
                
                # Transfer Tickets Button (only if event hasn't passed)
                if not event_passed:
                    transfer_btn = QPushButton("Transfer Tickets")
                    transfer_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #D91656;
                            color: white;
                            padding: 12px 30px;
                            font-size: 16px;
                            border-radius: 5px;
                            min-width: 120px;
                        }
                        QPushButton:hover {
                            background-color: #640D5F;
                        }
                    """)
                    # Pass the first ticket for compatibility with existing transfer dialog
                    transfer_btn.clicked.connect(lambda: self.transfer_ticket(ticket_group['tickets'][0]))
                    buttons_layout.addWidget(transfer_btn)
                    
            except ValueError as e:
                # If date parsing fails, show download button but disable other actions
                download_btn = QPushButton("Download Tickets")
                download_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #D91656;
                        color: white;
                        padding: 12px 30px;
                        font-size: 16px;
                        border-radius: 5px;
                        min-width: 120px;
                    }
                    QPushButton:hover {
                        background-color: #640D5F;
                    }
                """)
                download_btn.clicked.connect(lambda: self.download_ticket_pdf(ticket_group['tickets'][0], event))
                buttons_layout.addWidget(download_btn)
        
        elif ticket_group['status'] == 'used':
            # For used tickets, only show download button
            download_btn = QPushButton("Download Tickets")
            download_btn.setStyleSheet("""
                QPushButton {
                    background-color: #D91656;
                    color: white;
                    padding: 12px 30px;
                    font-size: 16px;
                    border-radius: 5px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #640D5F;
                }
            """)
            # For used tickets, always allow download (no event date check)
            download_btn.clicked.connect(lambda: self.download_ticket_pdf(ticket_group['tickets'][0], event))
            buttons_layout.addWidget(download_btn)
        
        content_layout.addWidget(buttons_container)
        
        # Set the content widget to the scroll area
        scroll.setWidget(content_widget)
        self.ticket_details_layout.addWidget(scroll)

        # Switch to the details view
        self.tickets_stack.setCurrentIndex(1)

    def cancel_grouped_tickets(self, ticket_group):
        """Show the refund dialog for ticket cancellation."""
        try:
            # Check if cancellation is allowed
            event = ticket_group['event']
            if not event:
                return
            
            cancel_date_str = event.get("ticket_cancel_availability")
            if cancel_date_str:
                try:
                    cancel_date = datetime.strptime(cancel_date_str, "%d/%m/%Y %H:%M")
                    current_date = datetime.now()
                    
                    if current_date > cancel_date:
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setWindowTitle("Cancellation Not Allowed")
                        msg.setText("Η περιοδος ακυρωσης των εισιτηριων εχει περασει")
                        msg.exec_()
                        return
                except ValueError:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("Error")
                    msg.setText("Error checking cancellation date.")
                    msg.exec_()
                    return

            # Show the refund dialog
            dialog = TicketRefundDialog(ticket_group, self)
            dialog.exec_()
            
            # After dialog closes, update the credit display if it exists
            self.update_credit_display()
            
            # Refresh event data and UI
            self.refresh_event_data()

        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"An error occurred: {str(e)}")
            msg.exec_()

    def update_credit_display(self):
        """Update the credit display in the UI."""
        try:
            if hasattr(self, 'credit_label'):
                self.credit_label.deleteLater()
                
            if self.current_user and self.current_user.get("type") == "attendee":
                credit = self.current_user.get("credit", 0)
                if credit > 0:
                    # Create credit label if it doesn't exist
                    self.credit_label = QLabel(f"Credit: €{credit:.2f}")
                    self.credit_label.setStyleSheet("""
                        QLabel {
                            color: #D91656;
                            font-size: 14px;
                            font-weight: bold;
                            padding: 5px;
                        }
                    """)
                    
                    # Add the label next to the logout button
                    if hasattr(self, 'toolbar'):
                        self.toolbar.insertWidget(self.toolbar.actions()[-1], self.credit_label)
        except Exception as e:
            print(f"Error updating credit display: {str(e)}")

    def show_event_passed_message(self):
        """Show message when trying to download ticket for passed event."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Event Completed")
        msg.setText("Το Event έχει ολοκληρωθεί, τα εισιτήρια δεν είναι διαθέσιμα για download.")
        msg.exec_()

    def download_ticket_pdf(self, ticket, event):
        """Show PDF preview dialog before download."""
        self.pdf_preview_dialog = TicketPDFPreviewDialog(ticket, event, self)
        self.pdf_preview_dialog.show()

    def download_ticket_text(self, ticket, event):
        """Fallback method to generate text file if reportlab is not available."""
        try:
            # Create a temporary text file
            temp_dir = tempfile.gettempdir()
            filename = f"ticket_{ticket['ticket_id']}_{event['title'].replace(' ', '_')}.txt"
            file_path = os.path.join(temp_dir, filename)
            
            # Generate text content
            content = f"""
🎫 EVENT TICKET 🎫

{event['title']}

Event Details:
Date: {event['start_date']} - {event['end_date']}
Time: {event['start_time']}
Location: {event['location']}
Organizer: {event.get('organizer', 'N/A')}

Ticket Information:
Ticket Type: {ticket['ticket_type']}
Quantity: {ticket['quantity_bought']}
Price per Ticket: €{ticket['price']}
Total Price: €{ticket['price'] * ticket['quantity_bought']}
Purchase Date: {ticket['purchase_date']}
QR Code: {ticket['qr_code']}

Please present this ticket at the event entrance
            """
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Open the file
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', file_path))
            elif platform.system() == 'Windows':  # Windows
                os.startfile(file_path)
            else:  # Linux
                subprocess.call(('xdg-open', file_path))
            
            # Show success message
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Ticket Downloaded")
            msg.setText(f"Ticket has been saved and opened:\n{file_path}")
            msg.exec_()
            
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"An error occurred while generating the ticket: {str(e)}")
            msg.exec_()

    def transfer_ticket(self, ticket):
        """Transfer a ticket to another user."""
        self.transfer_dialog = TicketTransferDialog(ticket, self)
        self.transfer_dialog.show()

    def handle_transfer_response(self, notification, response):
        """Handle recipient's response to a ticket transfer request."""
        try:
            # Get transfer request data
            with open("ticket_transfer_requests.json", "r", encoding="utf-8") as f:
                transfer_data = json.load(f)
            
            request_id = notification.get("transfer_request_id")
            if not request_id:
                raise ValueError("Transfer request ID not found in notification")
            
            # Find the transfer request
            request = next((req for req in transfer_data["transfer_requests"] 
                          if req["request_id"] == request_id), None)
            
            if not request:
                raise ValueError("Transfer request not found")
            
            # Update request status
            request["status"] = "accepted" if response else "rejected"
            request["response_date"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # If accepted, update ticket ownership
            if response:
                with open("tickets.json", "r", encoding="utf-8") as f:
                    tickets_data = json.load(f)
                
                # Update each transferred ticket
                for transfer_item in request["tickets"]:
                    ticket_data = transfer_item["ticket"]
                    quantity = transfer_item["quantity"]
                    
                    # Find and update the ticket
                    ticket = next((t for t in tickets_data if t["ticket_id"] == ticket_data["ticket_id"]), None)
                    if ticket:
                        if ticket["quantity_bought"] == quantity:
                            # Transfer entire ticket
                            ticket["user_id"] = request["recipient"]["user_id"]
                        else:
                            # Split ticket and create new one for recipient
                            new_ticket = ticket.copy()
                            new_ticket["ticket_id"] = max(t["ticket_id"] for t in tickets_data) + 1
                            new_ticket["user_id"] = request["recipient"]["user_id"]
                            new_ticket["quantity_bought"] = quantity
                            tickets_data.append(new_ticket)
                            
                            # Update original ticket quantity
                            ticket["quantity_bought"] -= quantity
                
                # Save updated tickets
                with open("tickets.json", "w", encoding="utf-8") as f:
                    json.dump(tickets_data, f, ensure_ascii=False, indent=4)
            
            # Save updated transfer requests
            with open("ticket_transfer_requests.json", "w", encoding="utf-8") as f:
                json.dump(transfer_data, f, ensure_ascii=False, indent=4)
            
            # Send notification to original sender
            status_text = "accepted" if response else "rejected"
            self.parent_app.add_notification(
                request["sender"]["user_id"],
                f"Ticket Transfer {status_text.title()}",
                f"Your ticket transfer request for '{request['event']['title']}' has been {status_text} by {request['recipient']['email']}.",
                "Ticket Transfers",
                {
                    "type": "transfer_response",
                    "transfer_request_id": request_id,
                    "status": status_text
                }
            )
            
            # Show success message
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Transfer Request Response")
            msg.setText(f"You have successfully {status_text} the ticket transfer request.")
            msg.exec_()
            
            # Refresh tickets display and event data
            self.display_my_tickets()
            self.refresh_event_data()
            
        except Exception as e:
            print(f"Error handling transfer response: {str(e)}")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Error handling transfer response: {str(e)}")
            msg.exec_()

    def refresh_event_data(self):
        """Refresh event data and update UI."""
        try:
            # Reload events from file
            with open("events.json", "r", encoding="utf-8") as f:
                self.events = json.load(f)
            
            # Update UI if we're in the events tab
            current_tab = self.tabs.tabText(self.tabs.currentIndex())
            if current_tab == "Events":
                self.display_events()
            elif current_tab == "My Tickets":
                self.display_my_tickets()
                
        except Exception as e:
            print(f"Error refreshing event data: {str(e)}")


class TicketTransferDialog(QDialog):
    """Enhanced dialog for transferring tickets to another user with multi-ticket support."""
    
    def __init__(self, ticket, parent=None):
        super().__init__(parent)
        self.ticket = ticket
        self.parent_app = parent
        self.user_tickets = []
        self.setWindowTitle("Transfer Ticket")
        self.setGeometry(300, 300, 500, 400)
        self.load_user_tickets()
        self.setup_ui()
    
    def load_user_tickets(self):
        """Load all tickets for the current user for the same event."""
        try:
            with open("tickets.json", "r", encoding="utf-8") as f:
                tickets = json.load(f)
            
            # Get all tickets for this user and event
            self.user_tickets = [
                t for t in tickets 
                if t["user_id"] == self.parent_app.current_user["user_id"] 
                and t["event_id"] == self.ticket["event_id"]
                and t["status"] == "valid"  # Only valid tickets can be transferred
            ]
            
        except (FileNotFoundError, json.JSONDecodeError):
            self.user_tickets = []
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Transfer Ticket")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        title.setStyleSheet("color: #D91656; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Εισάγετε το email ή το όνομα χρήστη του χρήστη στον οποίο θέλετε να στείλετε τα εισιτήρια.")
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-size: 14px; color: #333; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Email input
        email_layout = QHBoxLayout()
        email_label = QLabel("Email/Username:")
        email_label.setStyleSheet("font-weight: bold; color: #333;")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Other user's email")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #D91656;
            }
        """)
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        layout.addLayout(email_layout)
        
        # Ticket selection section
        if len(self.user_tickets) > 1:
            ticket_section = QGroupBox("Select Tickets to Transfer")
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
            
            # Group tickets by type
            ticket_types = {}
            for ticket in self.user_tickets:
                ticket_type = ticket['ticket_type']
                if ticket_type not in ticket_types:
                    ticket_types[ticket_type] = []
                ticket_types[ticket_type].append(ticket)
            
            self.ticket_selections = {}
            
            for ticket_type, tickets in ticket_types.items():
                type_layout = QHBoxLayout()
                
                # Ticket type label
                type_label = QLabel(f"{ticket_type}:")
                type_label.setStyleSheet("font-weight: bold; color: #333; min-width: 120px;")
                type_layout.addWidget(type_label)
                
                # Available quantity label
                available_qty = sum(t['quantity_bought'] for t in tickets)
                available_label = QLabel(f"Available: {available_qty}")
                available_label.setStyleSheet("color: #666; min-width: 100px;")
                type_layout.addWidget(available_label)
                
                # Quantity selector
                qty_label = QLabel("Transfer:")
                qty_label.setStyleSheet("color: #333;")
                type_layout.addWidget(qty_label)
                
                qty_spinbox = QSpinBox()
                qty_spinbox.setMinimum(0)
                qty_spinbox.setMaximum(available_qty)
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
                
                # Store the selection for later use
                self.ticket_selections[ticket_type] = {
                    'tickets': tickets,
                    'spinbox': qty_spinbox,
                    'available': available_qty
                }
            
            layout.addWidget(ticket_section)
        else:
            # Single ticket transfer
            ticket_section = QGroupBox("Select Quantity to Transfer")
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
            
            type_layout = QHBoxLayout()
            
            # Ticket type label
            type_label = QLabel(f"{self.ticket['ticket_type']}:")
            type_label.setStyleSheet("font-weight: bold; color: #333; min-width: 120px;")
            type_layout.addWidget(type_label)
            
            # Available quantity label
            available_qty = self.ticket['quantity_bought']
            available_label = QLabel(f"Available: {available_qty}")
            available_label.setStyleSheet("color: #666; min-width: 100px;")
            type_layout.addWidget(available_label)
            
            # Quantity selector
            qty_label = QLabel("Transfer:")
            qty_label.setStyleSheet("color: #333;")
            type_layout.addWidget(qty_label)
            
            self.single_ticket_spinbox = QSpinBox()
            self.single_ticket_spinbox.setMinimum(1)
            self.single_ticket_spinbox.setMaximum(available_qty)
            self.single_ticket_spinbox.setValue(1)
            self.single_ticket_spinbox.setStyleSheet("""
                QSpinBox {
                    padding: 5px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    min-width: 60px;
                }
            """)
            type_layout.addWidget(self.single_ticket_spinbox)
            
            type_layout.addStretch()
            ticket_layout.addLayout(type_layout)
            
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
        
        # Transfer button
        transfer_button = QPushButton("Transfer")
        transfer_button.setStyleSheet("""
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
        transfer_button.clicked.connect(self.transfer_tickets)
        button_layout.addWidget(transfer_button)
        
        layout.addLayout(button_layout)
    
    def transfer_tickets(self):
        """Process the ticket transfer with support for multiple tickets."""
        try:
            print("Debug - Starting transfer_tickets method")
            recipient_email = self.email_input.text().strip()
            print(f"Debug - Recipient email: '{recipient_email}'")
            
            if not recipient_email:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Invalid Email")
                msg.setText("Please enter a valid email address.")
                msg.exec_()
                return
            
            print("Debug - Starting ticket collection")
            # Collect selected tickets
            tickets_to_transfer = []
            
            if len(self.user_tickets) > 1:
                print("Debug - Multiple ticket types detected")
                # Multiple ticket types - check selections
                total_selected = 0
                for ticket_type, selection_data in self.ticket_selections.items():
                    quantity = selection_data['spinbox'].value()
                    if quantity > 0:
                        total_selected += quantity
                        # Add tickets of this type to transfer list
                        tickets = selection_data['tickets']
                        remaining_qty = quantity
                        
                        for ticket in tickets:
                            if remaining_qty <= 0:
                                break
                            
                            ticket_qty = ticket['quantity_bought']
                            transfer_qty = min(remaining_qty, ticket_qty)
                            
                            tickets_to_transfer.append({
                                'ticket': ticket,
                                'quantity': transfer_qty
                            })
                            
                            remaining_qty -= transfer_qty
                
                if total_selected == 0:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("No Tickets Selected")
                    msg.setText("Please select at least one ticket to transfer.")
                    msg.exec_()
                    return
            else:
                print("Debug - Single ticket transfer")
                # Single ticket transfer
                tickets_to_transfer.append({
                    'ticket': self.ticket,
                    'quantity': self.single_ticket_spinbox.value()
                })
            
            print(f"Debug - Tickets to transfer: {len(tickets_to_transfer)}")
            
        except Exception as e:
            print(f"Debug - Error in ticket collection: {str(e)}")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Error in ticket collection: {str(e)}")
            msg.exec_()
            return
        
        try:
            print("Debug - Starting user lookup")
            # Check if recipient exists and is an attendee
            with open("users.json", "r", encoding="utf-8") as f:
                users = json.load(f)
            
            # Debug: Print the email we're looking for
            print(f"Debug - Looking for email: '{recipient_email}'")
            print(f"Debug - Available emails: {[u.get('email', 'NO_EMAIL') for u in users]}")
            
            recipient = next((u for u in users if u.get("email", "").strip().lower() == recipient_email.strip().lower()), None)
            
            if not recipient:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("User Not Found")
                msg.setText(f"Ο χρήστης με email '{recipient_email}' δεν βρέθηκε ή δεν έχει ρόλο θεατή!")
                msg.exec_()
                return
            
            # Debug: Print recipient data
            print(f"Debug - Found recipient: {recipient}")
            
            if recipient.get("type") != "Attendee":
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Invalid User Type")
                msg.setText(f"Ο χρήστης '{recipient_email}' δεν έχει ρόλο θεατή!")
                msg.exec_()
                return
                
        except Exception as e:
            print(f"Debug - Error in user lookup: {str(e)}")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Error in user lookup: {str(e)}")
            msg.exec_()
            return
        
        try:
            print("Debug - Starting event lookup")
            # Create transfer notification
            event = next((e for e in self.parent_app.events if e["event_id"] == self.ticket["event_id"]), None)
            
            if not event:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Error")
                msg.setText("Event not found for this ticket.")
                msg.exec_()
                return
            
            print(f"Debug - Found event: {event.get('title', 'NO_TITLE')}")
            
        except Exception as e:
            print(f"Debug - Error in event lookup: {str(e)}")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Error in event lookup: {str(e)}")
            msg.exec_()
            return
        
        try:
            print("Debug - Creating transfer summary")
            # Create summary of tickets being transferred
            transfer_summary = []
            for item in tickets_to_transfer:
                ticket = item['ticket']
                quantity = item['quantity']
                transfer_summary.append(f"{ticket['ticket_type']} (Qty: {quantity})")
            
            summary_text = ", ".join(transfer_summary)
            print(f"Debug - Summary text: {summary_text}")
            
        except Exception as e:
            print(f"Debug - Error creating summary: {str(e)}")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Error creating summary: {str(e)}")
            msg.exec_()
            return
        
        try:
            print("Debug - Validating current user")
            # Check if current_user data is valid
            if not isinstance(self.parent_app.current_user, dict):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Error")
                msg.setText("Invalid user data.")
                msg.exec_()
                return
            
            # Debug: Print current user data
            print(f"Debug - Current user: {self.parent_app.current_user}")
            print(f"Debug - Recipient: {recipient}")
            
            # Safely access user data with fallbacks
            sender_name = self.parent_app.current_user.get('name', 'Unknown')
            sender_surname = self.parent_app.current_user.get('surname', 'User')
            sender_id = self.parent_app.current_user.get('user_id', 0)
            recipient_id = recipient.get('user_id', 0)
            
            print(f"Debug - Sender: {sender_name} {sender_surname} (ID: {sender_id})")
            print(f"Debug - Recipient ID: {recipient_id}")
            
        except Exception as e:
            print(f"Debug - Error validating user data: {str(e)}")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Error validating user data: {str(e)}")
            msg.exec_()
            return
        
        try:
            print("Debug - Creating notification data")
            # Generate a unique transfer request ID
            transfer_request_id = self.generate_transfer_request_id()
            
            # Create transfer request data
            transfer_request = {
                "request_id": transfer_request_id,
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "status": "pending",
                "sender": {
                    "user_id": sender_id,
                    "name": sender_name,
                    "surname": sender_surname
                },
                "recipient": {
                    "user_id": recipient_id,
                    "email": recipient_email
                },
                "event": {
                    "event_id": event["event_id"],
                    "title": event["title"]
                },
                "tickets": tickets_to_transfer
            }
            
            # Save transfer request
            try:
                with open("ticket_transfer_requests.json", "r", encoding="utf-8") as f:
                    transfer_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                transfer_data = {"transfer_requests": []}
            
            transfer_data["transfer_requests"].append(transfer_request)
            
            with open("ticket_transfer_requests.json", "w", encoding="utf-8") as f:
                json.dump(transfer_data, f, ensure_ascii=False, indent=4)
            
            # Create notification data
            notification_data = {
                "type": "ticket_transfer",
                "transfer_request_id": transfer_request_id,
                "sender_id": sender_id,
                "sender_name": f"{sender_name} {sender_surname}",
                "event_title": event["title"],
                "tickets": tickets_to_transfer
            }
            
            success = self.parent_app.add_notification(
                recipient_id,
                "Ticket Transfer Request",
                f"You have received a ticket transfer request for '{event['title']}' from {sender_name} {sender_surname}. Tickets: {summary_text}",
                "Ticket Transfers",
                notification_data
            )
            
            if not success:
                raise Exception("Failed to create notification")
            
            print("Debug - Notification added successfully")
            
            # Show success message
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Transfer Request Sent")
            msg.setText(f"Transfer request has been sent to {recipient_email}. They will receive a notification to accept or decline the transfer.\n\nTickets: {summary_text}")
            msg.exec_()
            
            self.accept()
            
        except Exception as e:
            print(f"Debug - Error creating notification data: {str(e)}")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Error creating notification data: {str(e)}")
            msg.exec_()
    
    def generate_transfer_request_id(self):
        """Generate a unique transfer request ID."""
        try:
            with open("ticket_transfer_requests.json", "r", encoding="utf-8") as f:
                transfer_data = json.load(f)
            
            if transfer_data["transfer_requests"]:
                max_id = max(int(req["request_id"]) for req in transfer_data["transfer_requests"])
                return str(max_id + 1)
            else:
                return "1"
        except (FileNotFoundError, json.JSONDecodeError):
            return "1"

class TicketPDFPreviewDialog(QDialog):
    """Dialog for previewing and downloading ticket PDF."""
    
    def __init__(self, ticket, event, parent=None):
        super().__init__(parent)
        self.ticket = ticket
        self.event = event
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Ticket Preview")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Προεπισκόπηση Εισιτηρίου")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        title.setStyleSheet("color: #D91656;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Ticket Preview Section
        preview_group = QGroupBox("Στοιχεία Εισιτηρίου")
        preview_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px;
            }
        """)
        preview_layout = QVBoxLayout(preview_group)
        # Event Details
        event_details = [
            ("Event:", self.event["title"]),
            ("Date:", f"{self.event['start_date']} - {self.event['end_date']}"),
            ("Time:", self.event["start_time"]),
            ("Location:", self.event["location"]),
            ("Ticket Type:", self.ticket["ticket_type"]),
            ("Quantity:", str(self.ticket["quantity_bought"])),
            ("Price per Ticket:", f"€{self.ticket['price']}"),
            ("Total Price:", f"€{self.ticket['price'] * self.ticket['quantity_bought']}")
        ]
        
        for label, value in event_details:
            detail_widget = QWidget()
            detail_layout = QHBoxLayout(detail_widget)
            detail_layout.setContentsMargins(5, 5, 5, 5)
            
            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-weight: bold; color: #333; min-width: 120px;")
            detail_layout.addWidget(label_widget)
            
            value_widget = QLabel(value)
            value_widget.setStyleSheet("color: #555;")
            detail_layout.addWidget(value_widget)
            
            preview_layout.addWidget(detail_widget)
        
        layout.addWidget(preview_group)
        
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
        """)
        back_button.clicked.connect(self.reject)
        
        # Download button
        download_button = QPushButton("Download PDF")
        download_button.setStyleSheet("""
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
            """)
        download_button.clicked.connect(self.download_pdf)
        
        button_layout.addWidget(back_button)
        button_layout.addStretch()
        button_layout.addWidget(download_button)
        
        layout.addLayout(button_layout)
    
    def download_pdf(self):
        """Generate and save the ticket PDF."""
        try:
            if not REPORTLAB_AVAILABLE:
                QMessageBox.warning(
                    self,
                    "PDF Generation Not Available",
                    "The PDF generation library (reportlab) is not installed. The ticket will be saved as a text file instead."
                )
                self.parent.download_ticket_text(self.ticket, self.event)
                return
            
            # Create default filename
            default_filename = f"ticket_{self.ticket['ticket_id']}_{self.event['title'].replace(' ', '_')}.pdf"
            
            # Open file dialog for user to choose save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Ticket PDF",
                default_filename,
                "PDF Files (*.pdf);;All Files (*.*)"
            )
            
            # If user cancels the dialog, return without doing anything
            if not file_path:
                return
                
            # Add .pdf extension if not present
            if not file_path.lower().endswith('.pdf'):
                file_path += '.pdf'
            
            # Generate PDF
            self.generate_professional_pdf(file_path)
            
            # Open the generated PDF
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', file_path))
            elif platform.system() == 'Windows':  # Windows
                os.startfile(file_path)
            else:  # Linux
                subprocess.call(('xdg-open', file_path))
            
            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"Ticket has been saved as PDF:\n{file_path}"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error generating PDF: {str(e)}\nFalling back to text format."
            )
            self.parent.download_ticket_text(self.ticket, self.event)
    
    def generate_professional_pdf(self, file_path):
        """Generate a professional PDF with proper Greek character support."""
        from reportlab.lib.colors import HexColor, white, black
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # Register a font that supports Greek characters
        try:
            # Try to use a system font that supports Greek
            if platform.system() == 'Windows':
                pdfmetrics.registerFont(TTFont('Greek', 'arial.ttf'))
                pdfmetrics.registerFont(TTFont('GreekBold', 'arialbd.ttf'))
            else:
                # Fallback to default fonts
                pdfmetrics.registerFont(TTFont('Greek', 'Helvetica'))
                pdfmetrics.registerFont(TTFont('GreekBold', 'Helvetica-Bold'))
        except:
            # If font registration fails, use default fonts
            pass
        
        # Create PDF document
        doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        
        # Define colors
        primary_color = HexColor('#D91656')
        secondary_color = HexColor('#640D5F')
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles with Greek font support
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName='GreekBold' if 'GreekBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold',
            fontSize=24,
            textColor=primary_color,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontName='GreekBold' if 'GreekBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold',
            fontSize=18,
            textColor=white,
            alignment=TA_CENTER,
            backColor=primary_color,
            borderPadding=10
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName='Greek' if 'Greek' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=12,
            textColor=black
        )
        
        # Title
        story.append(Paragraph("🎫 ΕΙΣΙΤΗΡΙΟ ΕΚΔΗΛΩΣΗΣ 🎫", title_style))
        story.append(Spacer(1, 20))
        
        # Event title
        story.append(Paragraph(self.event['title'], subtitle_style))
        story.append(Spacer(1, 20))
        
        # Event image
        if os.path.exists(self.event.get("image", "")):
            try:
                img = ReportLabImage(self.event["image"], width=4*inch, height=2*inch)
                story.append(img)
                story.append(Spacer(1, 20))
            except:
                pass  # Skip image if there's an error
        
        # Event details table
        event_data = [
            ['📅 Ημερομηνία:', f"{self.event['start_date']} - {self.event['end_date']}"],
            ['🕐 Ώρα:', self.event['start_time']],
            ['📍 Τοποθεσία:', self.event['location']],
            ['👤 Διοργανωτής:', self.event.get('organizer', 'N/A')]
        ]
        
        event_table = Table(event_data, colWidths=[2*inch, 4*inch])
        event_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), primary_color),
            ('FONTNAME', (0, 0), (0, -1), 'GreekBold' if 'GreekBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Greek' if 'Greek' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#ddd')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [white, HexColor('#f8f9fa')])
        ]))
        
        story.append(Paragraph("Στοιχεία Εκδήλωσης", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(event_table)
        story.append(Spacer(1, 20))
        
        # Ticket details table
        ticket_data = [
            ['🎟️ Τύπος Εισιτηρίου:', self.ticket['ticket_type']],
            ['🔢 Ποσότητα:', str(self.ticket['quantity_bought'])],
            ['💰 Τιμή ανά Εισιτήριο:', f"€{self.ticket['price']}"],
            ['💳 Συνολική Τιμή:', f"€{self.ticket['price'] * self.ticket['quantity_bought']}"],
            ['📅 Ημερομηνία Αγοράς:', self.ticket['purchase_date']],
            ['📊 Κατάσταση:', self.ticket['status'].title()]
        ]
        
        ticket_table = Table(ticket_data, colWidths=[2*inch, 4*inch])
        ticket_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), primary_color),
            ('FONTNAME', (0, 0), (0, -1), 'GreekBold' if 'GreekBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Greek' if 'Greek' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#ddd')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [white, HexColor('#f8f9fa')])
        ]))
        
        story.append(Paragraph("Στοιχεία Εισιτηρίου", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(ticket_table)
        story.append(Spacer(1, 20))
        
        # QR Code section for valid tickets
        if self.ticket['status'] == 'valid':
            story.append(Paragraph("QR Code για Είσοδο", subtitle_style))
            story.append(Spacer(1, 10))
            
            qr_data = [[self.ticket['qr_code']]]
            qr_table = Table(qr_data, colWidths=[4*inch])
            qr_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), white),
                ('TEXTCOLOR', (0, 0), (-1, -1), black),
                ('FONTNAME', (0, 0), (-1, -1), 'Courier-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 16),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 2, primary_color),
                ('BOX', (0, 0), (-1, -1), 3, primary_color)
            ]))
            
            story.append(qr_table)
            story.append(Spacer(1, 10))
            story.append(Paragraph("Παρουσιάστε αυτόν τον κωδικό στην είσοδο της εκδήλωσης", normal_style))
            story.append(Spacer(1, 20))
        
        # Footer
        footer_text = f"Δημιουργήθηκε στις: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontName='Greek' if 'Greek' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=10,
            textColor=HexColor('#666'),
            alignment=TA_CENTER
        )
        story.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(story)