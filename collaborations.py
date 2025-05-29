import json
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QWidget, QScrollArea, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class CollaborationRequest:
    def __init__(self, event_id, organizer_id, vendor_id, service_id, status="pending"):
        self.request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.event_id = event_id
        self.organizer_id = organizer_id
        self.vendor_id = vendor_id
        self.service_id = service_id
        self.status = status  # pending, accepted, rejected
        self.timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "event_id": self.event_id,
            "organizer_id": self.organizer_id,
            "vendor_id": self.vendor_id,
            "service_id": self.service_id,
            "status": self.status,
            "timestamp": self.timestamp
        }

def save_collaboration_request(request):
    try:
        # Load existing requests
        try:
            with open("collaboration_requests.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {"requests": []}
        
        # Add new request
        data["requests"].append(request.to_dict())
        
        # Save updated data
        with open("collaboration_requests.json", "w") as f:
            json.dump(data, f, indent=4)
        
        return True
    except Exception as e:
        print(f"Error saving collaboration request: {e}")
        return False

def get_pending_requests_for_vendor(vendor_id):
    try:
        with open("collaboration_requests.json", "r") as f:
            data = json.load(f)
            return [req for req in data["requests"] if req["vendor_id"] == vendor_id and req["status"] == "pending"]
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error getting pending requests: {e}")
        return []

def update_request_status(request_id, new_status):
    try:
        with open("collaboration_requests.json", "r") as f:
            data = json.load(f)
        
        for request in data["requests"]:
            if request["request_id"] == request_id:
                request["status"] = new_status
                break
        
        with open("collaboration_requests.json", "w") as f:
            json.dump(data, f, indent=4)
        
        if new_status == "accepted":
            # Update services.json to connect vendor to event
            with open("services.json", "r") as f:
                services_data = json.load(f)
            
            for service in services_data["services"]:
                if service["service_id"] == request["service_id"]:
                    service["event_id"] = request["event_id"]
                    break
            
            with open("services.json", "w") as f:
                json.dump(services_data, f, indent=4)
        
        return True
    except Exception as e:
        print(f"Error updating request status: {e}")
        return False

class CollaborationRequestDetailsDialog(QDialog):
    def __init__(self, request_data, event_data, service_data, parent=None, notification=None):
        super().__init__(parent)
        self.request_data = request_data
        self.event_data = event_data
        self.service_data = service_data
        self.parent_app = parent
        self.original_notification = notification
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Λεπτομέρειες Εκδήλωσης")
        self.setMinimumWidth(600)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Title
        title = QLabel("Νέο Αίτημα Συνεργασίας")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        title.setStyleSheet("color: #D91656; text-align: center;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Message - get organizer name from notification if available
        organizer_name = "διοργανωτή"
        if self.original_notification:
            organizer_info = self.original_notification.get("collaboration_request", {}).get("organizer_info", {})
            if organizer_info:
                organizer_name = f"τον διοργανωτή {organizer_info.get('name', '')} {organizer_info.get('surname', '')}"
        
        message = QLabel(f"Έχετε ένα νέο αίτημα συνεργασίας για την υπηρεσία '{self.service_data.get('name', '')}' από {organizer_name}.")
        message.setFont(QFont("Arial", 12))
        message.setStyleSheet("color: #333; padding: 10px; text-align: center;")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        layout.addWidget(message)

        # Event Details
        event_group = QWidget()
        event_layout = QVBoxLayout(event_group)
        
        event_title = QLabel("Στοιχεία Εκδήλωσης")
        event_title.setFont(QFont("Helvetica", 14, QFont.Bold))
        event_layout.addWidget(event_title)

        event_details = QLabel(
            f"<p><b>Τίτλος:</b> {self.event_data['title']}</p>"
            f"<p><b>Ημερομηνία:</b> {self.event_data['start_date']} - {self.event_data['end_date']}</p>"
            f"<p><b>Τοποθεσία:</b> {self.event_data['location']}</p>"
            f"<p><b>Τύπος:</b> {self.event_data['type']}</p>"
            f"<p><b>Περιγραφή:</b> {self.event_data.get('description', 'Δεν υπάρχει περιγραφή')}</p>"
        )
        event_details.setStyleSheet("font-size: 14px; color: #333;")
        event_details.setWordWrap(True)
        event_layout.addWidget(event_details)
        layout.addWidget(event_group)

        # Service Details
        service_group = QWidget()
        service_layout = QVBoxLayout(service_group)
        
        service_title = QLabel("Στοιχεία Υπηρεσίας")
        service_title.setFont(QFont("Helvetica", 14, QFont.Bold))
        service_layout.addWidget(service_title)

        service_details = QLabel(
            f"<p><b>Όνομα Υπηρεσίας:</b> {self.service_data['name']}</p>"
            f"<p><b>Τύπος:</b> {self.service_data['type']}</p>"
            f"<p><b>Περιγραφή:</b> {self.service_data['description']}</p>"
            f"<p><b>Τιμή:</b> {self.service_data['price']}€ ({self.service_data['pricing_type']})</p>"
        )
        service_details.setStyleSheet("font-size: 14px; color: #333;")
        service_details.setWordWrap(True)
        service_layout.addWidget(service_details)
        layout.addWidget(service_group)

        # Buttons
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(20)

        reject_btn = QPushButton("Απόρριψη")
        reject_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        reject_btn.clicked.connect(lambda: self.handle_response("rejected"))

        accept_btn = QPushButton("Αποδοχή")
        accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #D91656;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #640D5F;
            }
        """)
        accept_btn.clicked.connect(lambda: self.handle_response("accepted"))

        button_layout.addWidget(reject_btn)
        button_layout.addStretch()
        button_layout.addWidget(accept_btn)
        layout.addWidget(button_container)

    def handle_response(self, response):
        """Handle the vendor's response to the collaboration request."""
        if self.parent_app and self.original_notification:
            # Use the original notification to maintain all the proper data structure
            self.parent_app.handle_collaboration_response(self.original_notification, response)
            self.accept()
        else:
            # Fallback to old method if no parent or notification
            if update_request_status(self.request_data["request_id"], response):
                status_text = "αποδοχή" if response == "accepted" else "απόρριψη"
                QMessageBox.information(
                    self,
                    "Επιτυχία",
                    f"Η {status_text} του αιτήματος ολοκληρώθηκε με επιτυχία."
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Σφάλμα",
                    "Παρουσιάστηκε σφάλμα κατά την επεξεργασία του αιτήματος."
                ) 