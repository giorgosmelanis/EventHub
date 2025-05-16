import sys
from PyQt5.QtWidgets import QApplication
from ticket_purchase import TicketPurchaseModal

# Dummy event όπως είναι στο events.json
mock_event = {
    "event_id": 40,
    "title": "Test Αγοράς Εισιτηρίων",
    "start_date": "15/05/2025",
    "end_date": "15/05/2025",
    "start_time": "18:00",
    "location": "Αθήνα",
    "type": "Συναυλία",
    "description": "Πειραματική συναυλία για δοκιμές.",
    "image": "event_images/test_event_2.jpeg",
    "organizer_id": 1,
    "organizer": "Test Organizer",
    "ticket_types": [
        {"type": "Regular", "price": 20.0, "total_quantity": 50},
        {"type": "VIP", "price": 50.0, "total_quantity": 10},
        {"type": "Early Bird", "price": 15.0, "total_quantity": 50}
    ],
    "ticket_availability": "15/05/2025 17:00",
    "ticket_cancel_availability": "14/05/2025 23:59"
}

# Dummy user
mock_user =        {
        "user_id": 2,
        "email": "as",
        "password": "as",
        "name": "Jack",
        "surname": "Taylor",
        "type": "Attendee",
        "phone": "6945674569"
    }

# Run test
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TicketPurchaseModal(mock_event, mock_user)
    window.show()
    sys.exit(app.exec_())
