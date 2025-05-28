import sys  # Add this import statement
from PyQt5.QtWidgets import QApplication
from ui import EventManagementApp
from ticket_purchase import TicketPurchaseModal
from vendor_add_services import AddServicesModal  # Add this import

if __name__ == "__main__":
    app = QApplication(sys.argv)  # Now sys.argv is defined
    window = EventManagementApp()
    window.show()
    sys.exit(app.exec_())
    