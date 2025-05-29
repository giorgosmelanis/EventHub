import sys
import os
import shutil
import qtawesome as qta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTextEdit, QComboBox, QFormLayout, QFileDialog, QMessageBox,
    QDateEdit, QSpinBox, QDoubleSpinBox, QScrollArea, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QDate, QDateTime
from models import load_services, save_services


class AddServicesModal(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_user = parent.current_user
        services_data = load_services()  # Load existing services
        self.services = services_data["services"]  # Get the services list
        self.setWindowTitle("Προσθήκη Νέας Υπηρεσίας")
        self.setGeometry(200, 200, 600, 800)
        self.setStyleSheet("""
            background-color: #f0f0f0;
            color: #333333;
            font-family: 'Helvetica';
        """)

        # Initialize UI components
        self.setup_ui()

    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        # Container widget for the scroll area
        container = QWidget()
        self.form = QFormLayout(container)
        self.form.setSpacing(15)
        self.form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Align labels to the left
        self.form.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)   # Align fields to the left

        # Title with center alignment
        title_label = QLabel("Προσθήκη Νέας Υπηρεσίας")
        title_label.setFont(QFont("Helvetica", 20, QFont.Bold))
        title_label.setStyleSheet("color: #D91656;")
        title_label.setAlignment(Qt.AlignCenter)  # Center align the title
        layout.addWidget(title_label)

        # Service Name
        self.service_name = QLineEdit()
        self.service_name.setPlaceholderText("π.χ. Catering, DJ, Φωτογραφία")
        self.service_name.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.form.addRow("Όνομα Υπηρεσίας:", self.service_name)

        # Service Type
        self.service_type = QComboBox()
        self.service_type.addItems([
            "Ενοικίαση Χώρου", "Catering", "DJ", "Φωτογραφία",
            "Ηχητικός Εξοπλισμός", "Φωτισμός", "Διακόσμηση",
            "Ασφάλεια", "Parking", "Άλλο"
        ])
        self.service_type.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.form.addRow("Τύπος Υπηρεσίας:", self.service_type)

        # Service Description
        self.description = QTextEdit()
        self.description.setPlaceholderText("Περιγράψτε αναλυτικά την υπηρεσία σας...")
        self.description.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.form.addRow("Περιγραφή:", self.description)

        # Available Dates - Improved alignment
        dates_label = QLabel("Διαθέσιμες Ημερομηνίες:")
        dates_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        date_widget = QWidget()
        date_layout = QFormLayout()
        date_layout.setSpacing(10)
        date_layout.setLabelAlignment(Qt.AlignLeft)
        date_layout.setFormAlignment(Qt.AlignLeft)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addYears(1))
        self.end_date.setCalendarPopup(True)
        self.end_date.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        
        date_layout.addRow("Από:", self.start_date)
        date_layout.addRow("Έως:", self.end_date)
        date_widget.setLayout(date_layout)
        self.form.addRow(dates_label, date_widget)

        # Pricing Policy - Improved alignment
        pricing_label = QLabel("Τιμολογιακή Πολιτική:")
        pricing_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        pricing_widget = QWidget()
        pricing_layout = QVBoxLayout()
        pricing_layout.setSpacing(10)
        pricing_layout.setAlignment(Qt.AlignLeft)

        self.pricing_type = QComboBox()
        self.pricing_type.addItems(["Ανά Άτομο", "Ανά Ώρα", "Ανά Ημέρα", "Πακέτο"])  # Added "Ανά Άτομο"
        self.pricing_type.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        
        self.price = QLineEdit()
        self.price.setPlaceholderText("€")
        self.price.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        
        pricing_layout.addWidget(self.pricing_type)
        pricing_layout.addWidget(self.price)
        pricing_widget.setLayout(pricing_layout)
        self.form.addRow(pricing_label, pricing_widget)

        # Capacity Limits - Improved alignment
        capacity_label = QLabel("Αριθμός Ατόμων:")
        capacity_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        capacity_widget = QWidget()
        capacity_layout = QFormLayout()
        capacity_layout.setSpacing(10)
        capacity_layout.setLabelAlignment(Qt.AlignLeft)
        capacity_layout.setFormAlignment(Qt.AlignLeft)
        
        self.min_capacity = QLineEdit()
        self.min_capacity.setPlaceholderText("Ελάχιστος αριθμός")
        self.min_capacity.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        
        self.max_capacity = QLineEdit()
        self.max_capacity.setPlaceholderText("Μέγιστος αριθμός")
        self.max_capacity.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        
        capacity_layout.addRow("Ελάχιστος:", self.min_capacity)
        capacity_layout.addRow("Μέγιστος:", self.max_capacity)
        capacity_widget.setLayout(capacity_layout)
        self.form.addRow(capacity_label, capacity_widget)

        # Media Upload
        self.media_path = None
        self.media_label = QLabel("Δεν έχει επιλεγεί αρχείο")
        self.media_label.setStyleSheet("font-size: 14px; color: #777;")

        upload_btn = QPushButton("Επιλογή Αρχείου")
        upload_btn.setFixedWidth(130)
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #88b04b;
                color: white;
                padding: 8px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #6d8b3a;
            }
        """)
        upload_btn.clicked.connect(self.upload_media)

        media_layout = QHBoxLayout()
        media_layout.addWidget(self.media_label)
        media_layout.addWidget(upload_btn)
        self.form.addRow("Πολυμέσα:", media_layout)

        # Add the container to the scroll area
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()
        
        # Cancel Button
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
        cancel_btn.clicked.connect(self.handle_cancel)
        button_layout.addWidget(cancel_btn)

        # Preview Button
        preview_btn = QPushButton("Προεπισκόπηση")
        preview_btn.setStyleSheet("""
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
        preview_btn.clicked.connect(self.preview_service)
        button_layout.addWidget(preview_btn)

        # Create Button
        create_btn = QPushButton("Δημοσίευση")
        create_btn.setStyleSheet("""
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
        create_btn.clicked.connect(self.create_service)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

    def upload_media(self):
        """Open a file dialog to select media files and save them to the media directory."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Επιλογή Αρχείου",
            "service_media",
            "Media Files (*.png *.jpg *.jpeg *.mp4 *.pdf);;All Files (*)",
            options=options
        )

        if file_path:
            # Create the media directory if it doesn't exist
            if not os.path.exists("service_media"):
                os.makedirs("service_media")

            # Copy the file to the media directory
            file_name = os.path.basename(file_path)
            save_path = os.path.normpath(os.path.join("service_media", file_name))

            # Copy only if source and destination are different
            if os.path.abspath(file_path) != os.path.abspath(save_path):
                shutil.copy(file_path, save_path)

            self.media_path = save_path.replace("\\", "/")
            
            # Update label with file name
            self.media_label.setText(file_name)
            
            # If it's an image, show preview
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                pixmap = QPixmap(save_path)
                self.media_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))

    def preview_service(self):
        """Show a preview of the service before creation."""
        # Get all form values
        name = self.service_name.text().strip()
        service_type = self.service_type.currentText()
        description = self.description.toPlainText().strip()
        start_date = self.start_date.date().toString("dd/MM/yyyy")
        end_date = self.end_date.date().toString("dd/MM/yyyy")
        pricing_type = self.pricing_type.currentText()
        
        try:
            price = float(self.price.text().strip() or "0")
            min_capacity = int(self.min_capacity.text().strip() or "0")
            max_capacity = int(self.max_capacity.text().strip() or "0")
        except ValueError:
            QMessageBox.warning(self, "Σφάλμα", "Παρακαλώ εισάγετε έγκυρους αριθμούς για την τιμή και τη χωρητικότητα.")
            return

        # Validate required fields
        if not self.validate_fields():
            return

        # Create and store preview window as instance variable
        self.preview_window = QWidget()
        self.preview_window.setWindowTitle("Προεπισκόπηση Υπηρεσίας")
        self.preview_window.setGeometry(250, 250, 600, 600)
        self.preview_window.setStyleSheet("background-color: white;")
        self.preview_window.setWindowFlags(Qt.Window)  # Make it a proper window

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        self.preview_window.setLayout(layout)

        # Show media preview if available
        if self.media_path and self.media_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_label = QLabel()
            pixmap = QPixmap(self.media_path)
            image_label.setPixmap(pixmap.scaled(300, 200, Qt.KeepAspectRatio))
            layout.addWidget(image_label, alignment=Qt.AlignCenter)
            layout.addSpacing(20)

        # Service details
        details = QLabel(
            f"<b>Όνομα Υπηρεσίας:</b> {name}<br><br>"
            f"<b>Τύπος:</b> {service_type}<br><br>"
            f"<b>Περιγραφή:</b><br>{description}<br><br>"
            f"<b>Διαθεσιμότητα:</b> {start_date} - {end_date}<br><br>"
            f"<b>Τιμολόγηση:</b> {price}€ {pricing_type}<br><br>"
            f"<b>Χωρητικότητα:</b> {min_capacity} - {max_capacity} άτομα<br><br>"
            f"<b>Πάροχος:</b> {self.current_user['name']} {self.current_user['surname']}"
        )
        details.setStyleSheet("font-size: 14px; color: #333;")
        details.setWordWrap(True)
        layout.addWidget(details)

        # Close button
        close_btn = QPushButton("Κλείσιμο")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b5b95;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #524778;
            }
        """)
        close_btn.clicked.connect(self.preview_window.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        self.preview_window.show()

    def validate_fields(self):
        """Validate all required fields."""
        missing_fields = []
        
        if not self.service_name.text().strip():
            missing_fields.append("Όνομα Υπηρεσίας")
        
        if not self.description.toPlainText().strip():
            missing_fields.append("Περιγραφή")
        
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "Σφάλμα", 
                              "Η ημερομηνία έναρξης δεν μπορεί να είναι μεταγενέστερη της λήξης.")
            return False

        try:
            min_cap = int(self.min_capacity.text().strip() or "0")
            max_cap = int(self.max_capacity.text().strip() or "0")
            if min_cap > max_cap:
                QMessageBox.warning(self, "Σφάλμα", 
                                  "Ο ελάχιστος αριθμός ατόμων δεν μπορεί να είναι μεγαλύτερος από τον μέγιστο.")
                return False
        except ValueError:
            QMessageBox.warning(self, "Σφάλμα", 
                              "Παρακαλώ εισάγετε έγκυρους αριθμούς για τη χωρητικότητα.")
            return False
        
        if not self.media_path:
            missing_fields.append("Πολυμέσα")

        if missing_fields:
            QMessageBox.warning(self, "Σφάλμα", 
                              "Παρακαλώ συμπληρώστε τα παρακάτω πεδία:\n- " + "\n- ".join(missing_fields))
            return False

        return True

    def check_date_overlap(self, start_date, end_date):
        """Check if the selected dates overlap with existing bookings."""
        # This is a placeholder - implement actual booking check logic
        return False

    def create_service(self):
        """Create and save the new service."""
        if not self.validate_fields():
            return

        # Check for date overlaps
        if self.check_date_overlap(self.start_date.date(), self.end_date.date()):
            QMessageBox.warning(self, "Σφάλμα", 
                              "Οι επιλεγμένες ημερομηνίες επικαλύπτονται με υπάρχουσες κρατήσεις.")
            return

        # Create new service object
        new_service = {
            "service_id": len(self.services) + 1,
            "name": self.service_name.text().strip(),
            "type": self.service_type.currentText(),
            "description": self.description.toPlainText().strip(),
            "start_date": self.start_date.date().toString("dd/MM/yyyy"),
            "end_date": self.end_date.date().toString("dd/MM/yyyy"),
            "pricing_type": self.pricing_type.currentText(),
            "price": self.price.text().strip(),
            "min_capacity": self.min_capacity.text().strip(),
            "max_capacity": self.max_capacity.text().strip(),
            "media_path": self.media_path,
            "vendor_id": self.current_user["user_id"],
            "vendor_name": f"{self.current_user['name']} {self.current_user['surname']}",
            "event_id": None,  # Will be set when assigned to an event
            "event_title": None,  # Will be set when assigned to an event
            "status": "available"  # available, assigned, completed
        }

        # Add the new service to the list
        self.services.append(new_service)
        # Save the services list
        save_services(self.services)

        QMessageBox.information(self, "Επιτυχία", "Η υπηρεσία δημιουργήθηκε με επιτυχία!")
        self.close()

    def handle_cancel(self):
        """Handle the cancellation of service creation."""
        reply = QMessageBox.question(
            self,
            "Επιβεβαίωση Ακύρωσης",
            "Είστε σίγουροι ότι θέλετε να ακυρώσετε τη δημιουργία της υπηρεσίας;",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.close() 