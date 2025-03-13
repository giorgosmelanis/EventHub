import sys
import os
import shutil
import qtawesome as qta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QMessageBox, QHBoxLayout, QListWidget, QListWidgetItem, QFormLayout,
    QDateEdit, QFileDialog, QGroupBox, QStackedWidget, QGridLayout, QScrollArea
)
from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon, QBrush, QPalette
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QDate, QTimer 
from models import load_events, save_events, load_users, save_users

class EventManagementApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initialize_attributes()  # Initialize all necessary attributes
        self.setup_ui()  # Set up the UI components

    def initialize_attributes(self):
        """Initialize all necessary attributes for the application."""
        # Window and UI attributes
        self.setWindowTitle("Event Hub")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)  # Set a minimum size to prevent the window from becoming too small

        # Background image
        self.background_image = QPixmap("eventHub_logo.jpg")  # Replace with your image path
        self.set_background()

        # Display mode
        self.display_mode = "grid"  # Default to grid mode

        # Data attributes
        self.events = load_events()
        self.users = load_users()
        self.current_user = None  # Track the logged-in user

        # Pagination attributes
        self.events_per_page = 5  # Default number of events per page
        self.current_page = 1  # Track the current page
        self.total_pages = 1  # Default value

        # Debug: Print initial events
        print("Initial Events:")
        for event in self.events:
            print(event)

        # Tabs and UI components
        self.tabs = QTabWidget()
        self.private_tabs = {}  # Store private tabs for logged-in users
        self.login_tab = None  # Reference to the login tab
        self.logoff_btn = None  # Log Off button
        self.top_right_widget = None  # Widget for the top-right corner
        self.top_right_layout = None  # Layout for the top-right corner

        # Filter attributes
        self.from_date_filter_edit = None
        self.to_date_filter_edit = None
        self.location_filter_combobox = None
        self.type_filter_combobox = None
        self.items_per_page_combobox = None
        self.tiles_per_row_combobox = None

        # Stacked widget for grid and list modes
        self.stacked_widget = None
        self.grid_widget = None
        self.grid_layout = None
        self.list_widget = None
        self.list_layout = None

        # Pagination controls
        self.pagination_layout = None
        self.prev_page_btn = None
        self.next_page_btn = None
        self.page_label = None

    def setup_ui(self):
        """Set up the UI components."""
        # Set up the tabs
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background-color: rgba(255, 111, 97, 0.8);  /* Semi-transparent coral */
                color: white;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                margin: 5px;
            }
            QTabBar::tab:selected {
                background-color: rgba(255, 59, 47, 0.8);  /* Semi-transparent darker coral */
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: rgba(255, 255, 255, 0.8);  /* Semi-transparent white */
            }
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #D91656;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
                                
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal {
                background: #D91656;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                background: none;
            }
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        self.setCentralWidget(self.tabs)

        # Public menus (visible to everyone)
        self.create_home_tab()
        self.create_events_tab()
        self.login_tab = self.create_login_tab()

        # Log Off Button (initially hidden)
        self.logoff_btn = AnimatedButton("Log Off")
        self.logoff_btn.setStyleSheet("""
            QPushButton {
                background-color: #D91656;  /* Accent Color 1 */
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #640D5F;  /* Accent Color 2 */
            }
        """)
        self.logoff_btn.clicked.connect(self.logoff)
        self.logoff_btn.hide()  # Hide the button initially

        # Add the Log Off button to the top-right corner
        self.top_right_widget = QWidget()
        self.top_right_layout = QHBoxLayout()
        self.top_right_layout.addStretch()
        self.top_right_layout.addWidget(self.logoff_btn)
        self.top_right_widget.setLayout(self.top_right_layout)
        self.setMenuWidget(self.top_right_widget)

    def set_background(self):
        """Set the background image and make it responsive."""
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(self.background_image.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )))
        self.setPalette(palette)

    def resizeEvent(self, event):
        """Resize the background image dynamically when the window is resized."""
        self.set_background()
        self.adjust_grid_layout()
        super().resizeEvent(event)

    def create_home_tab(self):
        home_tab = QWidget()
        layout = QVBoxLayout()

        # Header with logo and title
        header = QWidget()
        header_layout = QHBoxLayout()

        logo = QLabel()
        logo.setPixmap(QPixmap("logo.png").scaled(100, 100, Qt.KeepAspectRatio))
        header_layout.addWidget(logo)

        title = QLabel("Καλώς ήρθατε στο Event Hub!")
        title.setFont(QFont("Helvetica", 24, QFont.Bold))
        title.setStyleSheet("color: #ff6f61;")
        header_layout.addWidget(title)

        header.setLayout(header_layout)
        layout.addWidget(header)

        # Buttons with animations
        button_frame = QWidget()
        button_layout = QHBoxLayout()

        # View Events Button
        view_events_btn = AnimatedButton("Προβολή Εκδηλώσεων")
        view_events_btn.setIcon(qta.icon("fa5s.calendar"))  # Calendar icon
        view_events_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b5b95;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #524778;
            }
        """)
        view_events_btn.clicked.connect(self.show_events_tab)
        button_layout.addWidget(view_events_btn)

        # Login Button
        login_btn = AnimatedButton("Σύνδεση/Εγγραφή")
        login_btn.setIcon(qta.icon("fa5s.sign-in-alt"))  # Sign-in icon
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #88b04b;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #6d8b3a;
            }
        """)
        login_btn.clicked.connect(self.show_login_tab)
        button_layout.addWidget(login_btn)

        button_frame.setLayout(button_layout)
        layout.addWidget(button_frame)

        home_tab.setLayout(layout)
        self.tabs.addTab(home_tab, QIcon("icons/home.png"), "Αρχική")  # Add icon to the Home tab

    # Event Section #
    def create_events_tab(self):
        events_tab = QWidget()
        main_layout = QVBoxLayout(events_tab)

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the widget to resize
        scroll_area.setStyleSheet("border: none;")  # Remove border

        # Create a container widget for the scroll area
        container = QWidget()
        layout = QVBoxLayout(container)

        # Title
        label = QLabel("Διαθέσιμες Εκδηλώσεις")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #640D5F;")
        layout.addWidget(label)

        # Filters
        filter_frame = QWidget()
        filter_layout = QHBoxLayout()
        filter_frame.setLayout(filter_layout)

        # From Date Filter
        filter_layout.addWidget(QLabel("Από Ημερομηνία:"))
        self.from_date_filter_edit = QDateEdit()
        self.from_date_filter_edit.setDate(QDate.currentDate().addDays(-7))  # Default: one week before
        self.from_date_filter_edit.setCalendarPopup(True)
        self.from_date_filter_edit.setStyleSheet("""
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        filter_layout.addWidget(self.from_date_filter_edit)

        # To Date Filter
        filter_layout.addWidget(QLabel("Έως Ημερομηνία:"))
        self.to_date_filter_edit = QDateEdit()
        self.to_date_filter_edit.setDate(QDate.currentDate().addDays(21))  # Default: three weeks after
        self.to_date_filter_edit.setCalendarPopup(True)
        self.to_date_filter_edit.setStyleSheet("""
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        filter_layout.addWidget(self.to_date_filter_edit)

        # Location Filter
        filter_layout.addWidget(QLabel("Τοποθεσία:"))
        self.location_filter_combobox = QComboBox()
        self.location_filter_combobox.addItems(["Όλες", "Αθήνα", "Θεσσαλονίκη", "Πάτρα", "Ηράκλειο"])
        self.location_filter_combobox.setStyleSheet("padding: 5px; border-radius: 5px; border: 1px solid #ddd;")
        filter_layout.addWidget(self.location_filter_combobox)

        # Type Filter
        filter_layout.addWidget(QLabel("Είδος:"))
        self.type_filter_combobox = QComboBox()
        self.type_filter_combobox.addItems(["Όλα", "Δημόσιο", "Ιδιωτικό"])
        self.type_filter_combobox.setStyleSheet("padding: 5px; border-radius: 5px; border: 1px solid #ddd;")
        filter_layout.addWidget(self.type_filter_combobox)

        # Items Per Page ComboBox (for List Mode)
        filter_layout.addWidget(QLabel("Εγγραφές ανά σελίδα:"))
        self.items_per_page_combobox = QComboBox()
        self.items_per_page_combobox.addItems(["5", "10", "20", "50"])
        self.items_per_page_combobox.setCurrentText("5")  # Default to 5 items per page
        self.items_per_page_combobox.setStyleSheet("padding: 5px; border-radius: 5px; border: 1px solid #ddd;")
        self.items_per_page_combobox.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.items_per_page_combobox)

        # Tiles Per Row ComboBox (for Grid Mode)
        filter_layout.addWidget(QLabel("Πλακίδια ανά σειρά:"))
        self.tiles_per_row_combobox = QComboBox()
        self.tiles_per_row_combobox.addItems(["3", "5"])
        self.tiles_per_row_combobox.setCurrentText("3")  # Default to 3 tiles per row
        self.tiles_per_row_combobox.setStyleSheet("padding: 5px; border-radius: 5px; border: 1px solid #ddd;")
        self.tiles_per_row_combobox.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.tiles_per_row_combobox)

        # Apply Filters Button
        apply_filters_btn = QPushButton("Εφαρμογή Φίλτρων")
        apply_filters_btn.setIcon(qta.icon("fa5s.filter"))  # Filter icon
        apply_filters_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;  /* Primary color */
                color: white;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #EB5B00;  /* Secondary color */
            }
        """)
        apply_filters_btn.clicked.connect(self.apply_filters)
        filter_layout.addWidget(apply_filters_btn)

        # Reset Filters Button
        reset_filters_btn = QPushButton("Επαναφορά Φίλτρων")
        reset_filters_btn.setIcon(qta.icon("fa5s.undo"))  # Undo icon
        reset_filters_btn.setStyleSheet("""
            QPushButton {
                background-color: #D91656;  /* Accent Color 1 */
                color: white;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #640D5F;  /* Accent Color 2 */
            }
        """)
        reset_filters_btn.clicked.connect(self.reset_filters)
        filter_layout.addWidget(reset_filters_btn)

        # Grid/List Toggle Button
        self.toggle_display_mode_btn = QPushButton("Εμφάνιση Λίστας")
        self.toggle_display_mode_btn.setIcon(qta.icon("fa5s.th-list"))  # List icon
        self.toggle_display_mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b5b95;
                color: white;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #524778;
            }
        """)
        self.toggle_display_mode_btn.clicked.connect(self.toggle_display_mode)
        filter_layout.addWidget(self.toggle_display_mode_btn)

        filter_frame.setLayout(filter_layout)
        layout.addWidget(filter_frame)

        # Stacked Widget for Grid and List Modes
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Grid Mode
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.stacked_widget.addWidget(self.grid_widget)

        # List Mode
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.stacked_widget.addWidget(self.list_widget)

        # Pagination
        self.current_page = 1
        self.pagination_layout = QHBoxLayout()
        self.prev_page_btn = AnimatedButton("Προηγούμενη")
        self.prev_page_btn.setIcon(qta.icon("fa5s.arrow-left"))  # Arrow-left icon
        self.prev_page_btn.setStyleSheet("background-color: #FFB200; color: white; padding: 10px; border-radius: 5px;")
        self.prev_page_btn.clicked.connect(self.prev_page)

        self.next_page_btn = AnimatedButton("Επόμενη")
        self.next_page_btn.setIcon(qta.icon("fa5s.arrow-right"))  # Arrow-right icon
        self.next_page_btn.setStyleSheet("background-color: #FFB200; color: white; padding: 10px; border-radius: 5px;")
        self.next_page_btn.clicked.connect(self.next_page)

        # Add current page and total pages label
        self.page_label = QLabel("1/1")
        self.page_label.setStyleSheet("font-size: 14px; color: #333;")

        # Add widgets to pagination layout
        self.pagination_layout.addWidget(self.prev_page_btn)
        self.pagination_layout.addWidget(self.next_page_btn)
        self.pagination_layout.addWidget(self.page_label)

        # Add the pagination layout to the main layout
        layout.addLayout(self.pagination_layout)

        # Set the container as the scroll area's widget
        scroll_area.setWidget(container)

        # Add the scroll area to the main layout
        main_layout.addWidget(scroll_area)

        self.tabs.addTab(events_tab, QIcon("icons/events.png"), "Εκδηλώσεις")  # Add icon to the Events tab

    def toggle_display_mode(self):
        if self.display_mode == "grid":
            self.display_mode = "list"
            self.toggle_display_mode_btn.setText("Εμφάνιση Πλέγματος")
            self.stacked_widget.setCurrentIndex(1)
        else:
            self.display_mode = "grid"
            self.toggle_display_mode_btn.setText("Εμφάνιση Λίστας")
            self.stacked_widget.setCurrentIndex(0)

        # Debug: Print display mode and events
        print(f"\nDisplay Mode Changed to: {self.display_mode}")
        print("Current Events:")
        if self.display_mode == "grid":
            for i in range(self.grid_layout.count()):
                widget = self.grid_layout.itemAt(i).widget()
                if widget:
                    print(widget.title())
        else:
            for i in range(self.list_layout.count()):
                widget = self.list_layout.itemAt(i).widget()
                if widget:
                    print(widget.title())

        # Reapply filters to update the displayed events
        self.apply_filters()

    def display_events(self, events):
        if self.display_mode == "grid":
            self.display_grid(events)
        else:
            self.display_list(events)

    def adjust_grid_layout(self):
        window_width = self.width()
        column_width = 320  # Approximate width of each grid item
        num_columns = max(1, window_width // column_width)  # At least 1 column
        self.grid_layout.setColumnMinimumWidth(0, column_width)
        self.grid_layout.setColumnStretch(num_columns, 1)  # Add stretch to fill space

    def display_grid(self, events):
        """Display events in a grid layout."""
        self.events = events  # Store the events for resizing

        # Debug: Print events being displayed in grid mode
        print("\nDisplaying Events in Grid Mode:")
        for event in events:
            print(event)

        # Clear the grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Get the number of tiles per row
        tiles_per_row = int(self.tiles_per_row_combobox.currentText())

        # Add events to the grid
        row, col = 0, 0
        for event in events:
            event_widget = self.create_event_widget(event)
            self.grid_layout.addWidget(event_widget, row, col)
            col += 1
            if col == tiles_per_row:
                col = 0
                row += 1

    def display_list(self, events):
        """Display events in a list layout."""
        # Debug: Print events being displayed in list mode
        print("\nDisplaying Events in List Mode:")
        for event in events:
            print(event)

        # Clear the list layout by removing all widgets
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Add new event widgets
        for event in events:
            event_widget = self.create_event_widget(event, is_list=True)
            self.list_layout.addWidget(event_widget)

    def create_event_widget(self, event, is_list=False):
        event_widget = QGroupBox(event["title"])
        event_widget.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 15px;
                margin: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
                font-size: 16px;
                font-weight: bold;
                color: #640D5F;
            }
        """)

        # Use QHBoxLayout for the main layout
        event_layout = QHBoxLayout()
        event_layout.setSpacing(15)  # Add spacing between widgets

        # Event Image (Left Side)
        if event["image"]:
            image_label = QLabel()
            pixmap = QPixmap(event["image"])
            image_label.setPixmap(pixmap.scaled(200, 150, Qt.KeepAspectRatio))  # Scale the image
            image_label.setFixedWidth(int(self.width() / 5))  # Set image width to 1/5 of the widget width
            event_layout.addWidget(image_label, alignment=Qt.AlignLeft)
        else:
            # Add a placeholder if no image is available
            placeholder_label = QLabel("No Image Available")
            placeholder_label.setAlignment(Qt.AlignCenter)
            placeholder_label.setStyleSheet("font-size: 14px; color: #777;")
            placeholder_label.setFixedWidth(int(self.width() / 5))  # Set placeholder width to 1/5 of the widget width
            event_layout.addWidget(placeholder_label, alignment=Qt.AlignLeft)

        # Event Details (Right Side)
        details_layout = QVBoxLayout()
        details_layout.setSpacing(10)

        # Event Details Text
        details_label = QLabel(
            f"<b>Ημερομηνία:</b> {event['date']}<br>"
            f"<b>Τοποθεσία:</b> {event['location']}<br>"
            f"<b>Τύπος:</b> {event['type']}"
        )
        details_label.setStyleSheet("font-size: 14px; color: #333;")
        details_label.setWordWrap(True)  # Ensure text wraps within the widget
        details_layout.addWidget(details_label)

        # View More Button
        view_more_btn = AnimatedButton("Περισσότερα")
        view_more_btn.clicked.connect(lambda _, e=event: self.show_event_details(e))
        details_layout.addWidget(view_more_btn, alignment=Qt.AlignLeft)

        # Add the details layout to the main layout
        event_layout.addLayout(details_layout)

        event_widget.setLayout(event_layout)
        return event_widget

    def show_event_details(self, event):
        details_window = QWidget()
        details_window.setWindowTitle(event["title"])
        details_window.setGeometry(100, 100, 600, 500)  # Set window size
        details_window.setStyleSheet("""
            background-color: #f0f0f0;
            color: #333333;
            font-family: 'Helvetica';
        """)

        # Main layout
        details_layout = QVBoxLayout()
        details_window.setLayout(details_layout)

        # Event Image
        if event["image"]:
            image_label = QLabel()
            pixmap = QPixmap(event["image"])
            image_label.setPixmap(pixmap.scaled(400, 300, Qt.KeepAspectRatio))  # Scale the image
            details_layout.addWidget(image_label, alignment=Qt.AlignCenter)

        # Event Details
        details_label = QLabel(
            f"<b>Τίτλος:</b> {event['title']}<br>"
            f"<b>Ημερομηνία:</b> {event['date']}<br>"
            f"<b>Τοποθεσία:</b> {event['location']}<br>"
            f"<b>Τύπος:</b> {event['type']}<br>"
            f"<b>Περιγραφή:</b> {event['description']}"
        )
        details_label.setStyleSheet("font-size: 16px; color: #333;")
        details_label.setWordWrap(True)  # Ensure text wraps within the window
        details_layout.addWidget(details_label)

        # Close Button
        close_btn = AnimatedButton("Κλείσιμο")
        close_btn.setIcon(qta.icon("fa5s.times"))  # Times (close) icon
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #D91656;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #640D5F;
            }
        """)
        close_btn.clicked.connect(details_window.close)
        details_layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        details_window.show()

    def calculate_total_pages(self, filtered_events, items_per_page):
        total_pages_test = len(filtered_events) + items_per_page - 1
        print("Total_Pages : ", total_pages_test)
        return (len(filtered_events) + items_per_page - 1) // items_per_page
    
    def apply_filters(self):
        # Get filter values
        from_date_filter = self.from_date_filter_edit.date().toString("yyyy-MM-dd") if self.from_date_filter_edit.date().isValid() else None
        to_date_filter = self.to_date_filter_edit.date().toString("yyyy-MM-dd") if self.to_date_filter_edit.date().isValid() else None
        location_filter = self.location_filter_combobox.currentText()
        type_filter = self.type_filter_combobox.currentText()

        # Debug: Print filter values
        print("\nFilter Values:")
        print(f"From Date: {from_date_filter}")
        print(f"To Date: {to_date_filter}")
        print(f"Location: {location_filter}")
        print(f"Type: {type_filter}")

        # Determine items per page based on the display mode
        if self.display_mode == "grid":
            tiles_per_row = int(self.tiles_per_row_combobox.currentText())
            items_per_page = tiles_per_row * 4  # Fixed 4 rows
        else:
            items_per_page = int(self.items_per_page_combobox.currentText())

        # Filter events
        self.filtered_events = []  # Store filtered events as an instance variable
        for event in self.events:
            event_date = event["date"]

            # Debug: Print event details
            print(f"\nChecking Event: {event['title']}")
            print(f"Event Date: {event_date}")
            print(f"Event Location: {event['location']}")
            print(f"Event Type: {event['type']}")

            # Check location filter
            location_match = location_filter == "Όλες" or event["location"] == location_filter

            # Check type filter
            type_match = type_filter == "Όλα" or event["type"] == type_filter

            # Check date range filters
            date_match = True
            if from_date_filter and to_date_filter:
                date_match = from_date_filter <= event_date <= to_date_filter
            elif from_date_filter:
                date_match = event_date >= from_date_filter
            elif to_date_filter:
                date_match = event_date <= to_date_filter

            # Debug: Print filter results
            print(f"Location Match: {location_match}")
            print(f"Type Match: {type_match}")
            print(f"Date Match: {date_match}")

            # Add event if it matches ANY of the filters (OR logic)
            if location_match or type_match or date_match:
                print("Event Matches Filters!")
                self.filtered_events.append(event)

        # Debug: Print filtered events
        print("\nFiltered Events:")
        for event in self.filtered_events:
            print(event)

        # Recalculate total pages
        self.total_pages = self.calculate_total_pages(self.filtered_events, items_per_page)

        # Debug: Print total pages and current page
        print(f"Total Pages: {self.total_pages}")
        print(f"Current Page: {self.current_page}")

        # Paginate events
        start_index = (self.current_page - 1) * items_per_page
        end_index = start_index + items_per_page
        paginated_events = self.filtered_events[start_index:end_index]

        # Debug: Print paginated events
        print("\nPaginated Events:")
        for event in paginated_events:
            print(event)

        # Display filtered and paginated events
        self.display_events(paginated_events)

        # Update pagination buttons and page label
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < self.total_pages)
        self.page_label.setText(f"{self.current_page}/{self.total_pages}")

    def reset_filters(self):
        # Reset date filters
        self.from_date_filter_edit.setDate(QDate.currentDate().addDays(-7))  # Default: one week before
        self.to_date_filter_edit.setDate(QDate.currentDate().addDays(21))  # Default: three weeks after

        # Reset location filter
        self.location_filter_combobox.setCurrentText("Όλες")

        # Reset type filter
        self.type_filter_combobox.setCurrentText("Όλα")

        # Reset items per page (for list mode)
        self.items_per_page_combobox.setCurrentText("5")

        # Reset tiles per row (for grid mode)
        self.tiles_per_row_combobox.setCurrentText("3")

        # Reapply filters
        self.apply_filters()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.apply_filters()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.apply_filters()

    # Login Section #
    def create_login_tab(self):
        login_tab = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)  # Center the entire layout

        # Title label with gradient effect
        title_label = QLabel("Σύνδεση/Εγγραφή")
        title_label.setFont(QFont("Helvetica", 28, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #FFB200, stop:1 #EB5B00);  /* Gradient from Primary to Secondary */
                padding: 10px;
            }
        """)
        layout.addWidget(title_label, alignment=Qt.AlignCenter)  # Center the title

        # Add some spacing
        layout.addSpacing(30)

        # Form container
        form_container = QWidget()
        form_layout = QVBoxLayout()
        form_container.setLayout(form_layout)
        form_container.setMaximumWidth(400)  # Set a maximum width for the form

        # Email input
        email_container = QWidget()
        email_layout = QVBoxLayout()
        email_label = QLabel("Email:")
        email_label.setFont(QFont("Helvetica", 14, QFont.Bold))
        email_label.setStyleSheet("color: #640D5F;")  # Deep Purple for labels
        email_layout.addWidget(email_label)

        self.email_entry = QLineEdit()
        self.email_entry.setPlaceholderText("Εισάγετε το email σας")
        self.email_entry.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        email_layout.addWidget(self.email_entry)
        email_container.setLayout(email_layout)
        form_layout.addWidget(email_container)

        # Add some spacing
        form_layout.addSpacing(20)

        # Password input
        password_container = QWidget()
        password_layout = QVBoxLayout()
        password_label = QLabel("Κωδικός:")
        password_label.setFont(QFont("Helvetica", 14, QFont.Bold))
        password_label.setStyleSheet("color: #640D5F;")  # Deep Purple for labels
        password_layout.addWidget(password_label)

        self.password_entry = QLineEdit()
        self.password_entry.setPlaceholderText("Εισάγετε τον κωδικό σας")
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.password_entry.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        password_layout.addWidget(self.password_entry)
        password_container.setLayout(password_layout)
        form_layout.addWidget(password_container)

        # Add some spacing
        form_layout.addSpacing(30)

        # Login Button
        login_btn = AnimatedButton("Σύνδεση")
        login_btn.setIcon(qta.icon("fa5s.sign-in-alt"))  # Sign-in icon
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;  /* Primary Color */
                color: white;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #EB5B00;  /* Secondary Color */
            }
        """)
        login_btn.clicked.connect(self.login)
        form_layout.addWidget(login_btn, alignment=Qt.AlignCenter)

        # Add some spacing
        form_layout.addSpacing(10)

        # Signup Button
        signup_btn = AnimatedButton("Εγγραφή")
        signup_btn.setIcon(qta.icon("fa5s.user-plus"))  # User-plus icon
        signup_btn.setStyleSheet("""
            QPushButton {
                background-color: #D91656;  /* Accent Color 1 */
                color: white;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #640D5F;  /* Accent Color 2 */
            }
        """)
        signup_btn.clicked.connect(self.open_signup_modal)
        form_layout.addWidget(signup_btn, alignment=Qt.AlignCenter)

        # Add the form container to the main layout
        layout.addWidget(form_container)

        # Set the layout for the login tab
        login_tab.setLayout(layout)
        self.tabs.addTab(login_tab, QIcon("icons/login.png"), "Σύνδεση/Εγγραφή")  # Add icon to the Login tab
        
        return login_tab  # Return the login tab

    def login(self):
        email = self.email_entry.text()
        password = self.password_entry.text()

        if email and password:
            user = self.authenticate_user(email, password)
            if user:
                self.current_user = user
                QMessageBox.information(self, "Σύνδεση", "Συνδεθήκατε με επιτυχία!")
                self.redirect_to_dashboard(user.get("type", "Guest"))

                # Hide the Login Tab
                self.tabs.removeTab(self.tabs.indexOf(self.login_tab))  
            else:
                QMessageBox.warning(self, "Σφάλμα", "Λάθος email ή κωδικός.")
        else:
            QMessageBox.warning(self, "Σφάλμα", "Παρακαλώ συμπληρώστε email και κωδικό.")

    def update_ui_after_login(self, user_type):
        # Hide the Login Tab
        self.tabs.removeTab(2)  # Remove the Login Tab (index 2)

        # Show the Log Off button
        self.logoff_btn.show()

        # Add private tabs based on user type
        if user_type == "Creator":
            self.add_creator_tab()
        elif user_type == "Supplier":
            self.add_supplier_tab()
        elif user_type == "Attendee":
            self.add_attendee_tab()

    def logoff(self):
        # Reset the app state
        self.current_user = None

        # Remove private tabs
        for tab_name, tab_widget in self.private_tabs.items():
            self.tabs.removeTab(self.tabs.indexOf(tab_widget))
        self.private_tabs.clear()

        # Show the Login Tab again
        if self.tabs.indexOf(self.login_tab) == -1:  # Only add if not exists
            self.login_tab = self.create_login_tab()

        # Hide the Log Off button
        self.logoff_btn.hide()

        # Switch to the Home Tab
        self.tabs.setCurrentIndex(0)

    def authenticate_user(self, email, password):
        for user in self.users:
            if user["email"] == email and user["password"] == password:
                return user
        return None
    
    # Tab Redirection #
    def redirect_to_dashboard(self, user_type):
        # Remove existing private tabs
        for tab_name, tab_widget in self.private_tabs.items():
            self.tabs.removeTab(self.tabs.indexOf(tab_widget))

        # Add private tabs based on user type
        if user_type == "Creator":
            self.add_creator_tab()
            self.tabs.setCurrentIndex(self.tabs.count()-1)  # Redirect to Creator dashboard
        elif user_type == "Supplier":
            self.add_supplier_tab()
            self.tabs.setCurrentIndex(self.tabs.count()-1) # Redirect to Supplier dashboard
        elif user_type == "Attendee":
            self.add_attendee_tab()
            self.tabs.setCurrentIndex(self.tabs.count()-1)  # Redirect to Attendee dashboard

    # Creator Section #
    def add_creator_tab(self):
        self.logoff_btn.show()  # Show the button
        creator_tab = QWidget()
        layout_dashboard = QVBoxLayout()

        label = QLabel("Δημιουργός Εκδηλώσεων")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #ff6f61;")
        layout_dashboard.addWidget(label)



        # Create Event Button
        create_event_btn = AnimatedButton("Δημιουργία Εκδήλωσης")
        create_event_btn.setIcon(qta.icon("fa5s.plus"))  # Plus icon
        create_event_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;  /* Primary color */
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #EB5B00;  /* Secondary color */
            }
        """)
        create_event_btn.clicked.connect(self.open_create_event_modal)
        layout_dashboard.addWidget(create_event_btn)

            # My Event Button

        show_event_btn = AnimatedButton("My Events")
        show_event_btn.setIcon(qta.icon("fa5s.history"))  # History icon

        # show_event_btn = QPushButton("My Events")
        # show_event_btn.setIcon(qta.icon("fa5s.history"))  # Plus icon
        show_event_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;  /* Primary color */
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #EB5B00;  /* Secondary color */
            }
        """)
        show_event_btn.clicked.connect(self.show_my_events_tab)
        layout_dashboard.addWidget(show_event_btn)

        

        my_events_tab = QWidget()
        layout_my_events = QVBoxLayout()

        label = QLabel("My Events")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #ff6f61;")
        layout_my_events.addWidget(label)

            # Add a scroll area for the event list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the widget to resize
        scroll_area.setStyleSheet("border: none;")  # Remove border

        # Create a container widget for the event list
        event_list_container = QWidget()
        event_list_layout = QVBoxLayout(event_list_container)
        event_list_layout.setAlignment(Qt.AlignTop)  # Align items to the top

        # Add creator-specific content here
        event_list_layout.addWidget(QLabel("Διαχείριση Εκδηλώσεων"))

        # Add the event list to the container
        self.display_creator_events(event_list_layout)

        # Set the container as the scroll area's widget
        scroll_area.setWidget(event_list_container)

        # Add the scroll area to the main layout
        layout_my_events.addWidget(scroll_area)

        creator_tab.setLayout(layout_dashboard)
        my_events_tab.setLayout(layout_my_events)
        self.tabs.addTab(creator_tab, qta.icon("fa5s.user-edit"), "Δημιουργός")  # Add icon to the Creator tab
        self.tabs.addTab(my_events_tab, qta.icon("fa5s.calendar-alt"), "My Events")  # Add icon to the Creator tab
        self.private_tabs["Creator"] = creator_tab
        self.private_tabs["My Events"] = my_events_tab

    def display_creator_events(self, layout):
        """Display events created by the logged-in user with pagination."""
        if not self.current_user:
            return

        # Filter events created by the current user
        creator_events = [event for event in self.events if event.get("creator_id") == self.current_user["user_id"]]

        # Clear the layout before adding new widgets
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Paginate events
        total_events = len(creator_events)
        total_pages = (total_events + self.events_per_page - 1) // self.events_per_page  # Calculate total pages

        # Ensure current_page is within valid range
        self.current_page = max(1, min(self.current_page, total_pages))

        # Get events for the current page
        start_index = (self.current_page - 1) * self.events_per_page
        end_index = start_index + self.events_per_page
        paginated_events = creator_events[start_index:end_index]

        # Add event widgets to the layout
        for event in paginated_events:
            event_widget = self.create_event_widget(event, is_list=True)
            layout.addWidget(event_widget)

        # Add pagination controls
        pagination_layout = QHBoxLayout()

        # Previous button
        prev_button = QPushButton("Previous")
        prev_button.clicked.connect(lambda: self.change_page(layout, -1))
        prev_button.setEnabled(self.current_page > 1)  # Disable on first page
        pagination_layout.addWidget(prev_button)

        # Page number label
        page_label = QLabel(f"Page {self.current_page} of {total_pages}")
        pagination_layout.addWidget(page_label)

        # Next button
        next_button = QPushButton("Next")
        next_button.clicked.connect(lambda: self.change_page(layout, 1))
        next_button.setEnabled(self.current_page < total_pages)  # Disable on last page
        pagination_layout.addWidget(next_button)

        layout.addLayout(pagination_layout)

    def change_page(self, layout, delta):
        """Change the current page and update the displayed events."""
        self.current_page += delta
        self.display_creator_events(layout)

    # Supplier Section #
    def add_supplier_tab(self):
        supplier_tab = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Προμηθευτής")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #6b5b95;")
        layout.addWidget(label)

        # Add supplier-specific content here
        layout.addWidget(QLabel("Διαχείριση Προμηθειών"))

        supplier_tab.setLayout(layout)
        self.tabs.addTab(supplier_tab, QIcon("icons/supplier.png"), "Προμηθευτής")  # Add icon to the Supplier tab
        self.private_tabs["Supplier"] = supplier_tab

    # Attendee Section #
    def add_attendee_tab(self):
        attendee_tab = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Συμμετέχων")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #88b04b;")
        layout.addWidget(label)

        # Add attendee-specific content here
        layout.addWidget(QLabel("Εγγραφή σε Εκδηλώσεις"))

        attendee_tab.setLayout(layout)
        self.tabs.addTab(attendee_tab, QIcon("icons/attendee.png"), "Συμμετέχων")  # Add icon to the Attendee tab
        self.private_tabs["Attendee"] = attendee_tab

    def open_create_event_modal(self):
        self.create_event_modal = CreateEventModal(self)
        self.create_event_modal.show()
    
    def open_signup_modal(self):
        self.create_event_modal = SignupModal(self)
        self.create_event_modal.show()

    def show_events_tab(self):
        self.tabs.setCurrentIndex(1)

    def show_login_tab(self):
        self.tabs.setCurrentIndex(2)

    def show_my_events_tab(self):
        self.tabs.setCurrentIndex()


class SignupModal(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("Εγγραφή")
        self.setGeometry(200, 200, 400, 500)  # Increased height for additional fields
        self.setStyleSheet("""
            background-color: #f0f0f0;
            color: #333333;
            font-family: 'Helvetica';
        """)

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)  # Add padding
        layout.setSpacing(15)  # Add spacing between widgets
        self.setLayout(layout)

        # Title label with gradient effect
        title_label = QLabel("Εγγραφή")
        title_label.setFont(QFont("Helvetica", 20, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 #FFB200, stop:1 #EB5B00);  /* Gradient from Primary to Secondary */
                padding: 10px;
            }
        """)
        layout.addWidget(title_label, alignment=Qt.AlignCenter)  # Center the title

        # Form layout
        form = QFormLayout()
        form.setSpacing(15)  # Add spacing between form rows
        layout.addLayout(form)

        # Name input
        self.signup_name_entry = QLineEdit()
        self.signup_name_entry.setPlaceholderText("Εισάγετε το όνομά σας")
        self.signup_name_entry.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        form.addRow("Όνομα:", self.signup_name_entry)

        # Surname input
        self.signup_surname_entry = QLineEdit()
        self.signup_surname_entry.setPlaceholderText("Εισάγετε το επώνυμό σας")
        self.signup_surname_entry.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        form.addRow("Επώνυμο:", self.signup_surname_entry)

        # Email input
        self.signup_email_entry = QLineEdit()
        self.signup_email_entry.setPlaceholderText("Εισάγετε το email σας")
        self.signup_email_entry.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        form.addRow("Email:", self.signup_email_entry)

        # Password input
        self.signup_password_entry = QLineEdit()
        self.signup_password_entry.setPlaceholderText("Εισάγετε τον κωδικό σας")
        self.signup_password_entry.setEchoMode(QLineEdit.Password)
        self.signup_password_entry.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        form.addRow("Κωδικός:", self.signup_password_entry)

        # Phone input
        self.signup_phone_entry = QLineEdit()
        self.signup_phone_entry.setPlaceholderText("Εισάγετε το τηλέφωνό σας")
        self.signup_phone_entry.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        form.addRow("Τηλέφωνο:", self.signup_phone_entry)

        # User type selection
        self.user_type_combobox = QComboBox()
        self.user_type_combobox.addItems(["Attendee", "Creator", "Supplier"])
        self.user_type_combobox.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        form.addRow("Τύπος Χρήστη:", self.user_type_combobox)

        # Signup button
        signup_btn = AnimatedButton("Εγγραφή")
        signup_btn.setStyleSheet("""
            QPushButton {
                background-color: #D91656;  /* Accent Color 1 */
                color: white;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #640D5F;  /* Accent Color 2 */
            }
        """)
        signup_btn.clicked.connect(self.signup)
        layout.addWidget(signup_btn, alignment=Qt.AlignCenter)  # Center the button

    def signup(self):
        name = self.signup_name_entry.text().strip()
        surname = self.signup_surname_entry.text().strip()
        email = self.signup_email_entry.text().strip()
        password = self.signup_password_entry.text().strip()
        phone = self.signup_phone_entry.text().strip()
        user_type = self.user_type_combobox.currentText()

        # Input validation
        if not name or not surname or not email or not password or not phone:
            QMessageBox.warning(self, "Σφάλμα", "Παρακαλώ συμπληρώστε όλα τα πεδία.")
            return

        if not self.is_valid_email(email):
            QMessageBox.warning(self, "Σφάλμα", "Παρακαλώ εισάγετε ένα έγκυρο email.")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Σφάλμα", "Ο κωδικός πρέπει να έχει τουλάχιστον 6 χαρακτήρες.")
            return

        if not phone.isdigit() or len(phone) != 10:
            QMessageBox.warning(self, "Σφάλμα", "Παρακαλώ εισάγετε ένα έγκυρο τηλέφωνο (10 ψηφία).")
            return

        # Check if email already exists
        if any(user["email"] == email for user in self.parent.users):
            QMessageBox.warning(self, "Σφάλμα", "Το email χρησιμοποιείται ήδη.")
            return

        # Generate a new user_id
        user_id = self.generate_user_id()

        # Create new user
        new_user = {
            "user_id": user_id,  # Add the generated user_id
            "email": email,
            "password": password,
            "name": name,
            "surname": surname,
            "type": user_type,
            "phone": phone
        }
        self.parent.users.append(new_user)
        save_users(self.parent.users)

        QMessageBox.information(self, "Επιτυχία", "Εγγραφήκατε με επιτυχία!")
        self.close()

    def generate_user_id(self):
        """Generate a new user_id based on the last user_id in users.json."""
        if not self.parent.users:
            return 1  # If no users exist, start with user_id 1
        last_user = self.parent.users[-1]
        last_user_id = last_user.get("user_id", 0)
        # Convert last_user_id to an integer if it's a string
        if isinstance(last_user_id, str):
            last_user_id = int(last_user_id)
        return last_user_id + 1  # Increment the last user_id

    def is_valid_email(self, email):
        """Simple email validation."""
        return "@" in email and "." in email


class CreateEventModal(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("Δημιουργία Νέας Εκδήλωσης")
        self.setGeometry(200, 200, 500, 450)
        self.setStyleSheet("""
            background-color: #f0f0f0;
            color: #333333;
            font-family: 'Helvetica';
        """)

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Event creation form
        form = QFormLayout()
        layout.addLayout(form)

        # Event name input
        self.event_name_entry = QLineEdit()
        self.event_name_entry.setPlaceholderText("Εισάγετε το όνομα της εκδήλωσης")
        self.event_name_entry.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        form.addRow("Όνομα Εκδήλωσης:", self.event_name_entry)

        # Event date input (date picker)
        self.event_date_edit = QDateEdit()
        self.event_date_edit.setDate(QDate.currentDate())  # Set default to today's date
        self.event_date_edit.setCalendarPopup(True)  # Enable calendar popup
        self.event_date_edit.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        form.addRow("Ημερομηνία:", self.event_date_edit)

        # Event location input (drop-down box)
        self.event_location_combobox = QComboBox()
        self.event_location_combobox.addItems(["Αθήνα", "Θεσσαλονίκη", "Πάτρα", "Ηράκλειο"])
        self.event_location_combobox.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        form.addRow("Τοποθεσία:", self.event_location_combobox)

        # Event type selection
        self.event_type_combobox = QComboBox()
        self.event_type_combobox.addItems(["Δημόσιο", "Ιδιωτικό"])
        self.event_type_combobox.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        form.addRow("Τύπος Εκδήλωσης:", self.event_type_combobox)

        # Event description input
        self.event_description_entry = QTextEdit()
        self.event_description_entry.setPlaceholderText("Εισάγετε μια περιγραφή για την εκδήλωση")
        self.event_description_entry.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        form.addRow("Περιγραφή:", self.event_description_entry)

        # Event image upload
        self.image_path = None
        self.image_label = QLabel("Δεν έχει επιλεγεί εικόνα")
        self.image_label.setStyleSheet("font-size: 14px; color: #777;")
        form.addRow("Εικόνα Εκδήλωσης:", self.image_label)

        upload_btn = QPushButton("Επιλογή Εικόνας")
        upload_btn.setStyleSheet("""
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
        upload_btn.clicked.connect(self.upload_image)
        form.addRow(upload_btn)

        # Buttons
        button_frame = QWidget()
        button_layout = QHBoxLayout()

        close_btn = QPushButton("Κλείσιμο")
        close_btn.setStyleSheet("""
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
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        create_btn = QPushButton("Δημιουργία")
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
        create_btn.clicked.connect(self.create_event)
        button_layout.addWidget(create_btn)

        button_frame.setLayout(button_layout)
        layout.addWidget(button_frame)

    def upload_image(self):
        """Open a file dialog to select an image and save it to the images directory."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Επιλογή Εικόνας",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)",
            options=options
        )

        if file_path:
            # Create the images directory if it doesn't exist
            if not os.path.exists("event_images"):
                os.makedirs("event_images")

            # Copy the image to the images directory
            file_name = os.path.basename(file_path)
            save_path = os.path.normpath(os.path.join("event_images", file_name))  # Normalize path
            self.image_path = os.path.relpath(save_path)  # Store relative path
            shutil.copy(file_path, save_path)
            self.image_path = save_path.replace("\\", "/")  # Ensure forward slashes

            # Store the relative path
            self.image_path = save_path

            # Display the image preview
            pixmap = QPixmap(save_path)
            self.image_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            self.image_label.setText("")

    def create_event(self):
        event_name = self.event_name_entry.text().strip()
        event_date = self.event_date_edit.date().toString("yyyy-MM-dd")  # Format date as YYYY-MM-DD
        event_location = self.event_location_combobox.currentText()
        event_type = self.event_type_combobox.currentText()
        event_description = self.event_description_entry.toPlainText().strip()

        if not event_name or not event_date or not event_location or not event_type or not event_description:
            QMessageBox.warning(self, "Σφάλμα", "Παρακαλώ συμπληρώστε όλα τα πεδία.")
            return

        if not self.image_path:
            QMessageBox.warning(self, "Σφάλμα", "Παρακαλώ επιλέξτε μια εικόνα.")
            return

        # Create new event
        new_event = {
            "id": len(self.parent.events) + 1,
            "title": event_name,
            "date": event_date,
            "location": event_location,
            "type": event_type,
            "description": event_description,
            "image": self.image_path,
            "creator_id": self.parent.current_user["user_id"],  # Store the creator's user_id
            "creator": f"{self.parent.current_user['name']} {self.parent.current_user['surname']}"  # Store the creator's name and surname
        }
        self.parent.events.append(new_event)
        save_events(self.parent.events)
        self.parent.apply_filters()
        QMessageBox.information(self, "Επιτυχία", "Η εκδήλωση δημιουργήθηκε με επιτυχία!")
        self.close()


# Styling Tests


class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #D91656;  /* Accent Color 1 */
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #640D5F;  /* Accent Color 2 */
            }
            QPushButton:pressed {
                background-color: #4A0A4A;  /* Darker shade for pressed state */
            }
        """)

        # Animation for hover effect
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)  # Duration in milliseconds
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

    def enterEvent(self, event):
        """Triggered when the mouse enters the button area."""
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QRect(self.x() - 5, self.y() - 5, self.width() + 10, self.height() + 10))
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Triggered when the mouse leaves the button area."""
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QRect(self.x() + 5, self.y() + 5, self.width() - 10, self.height() - 10))
        self.animation.start()
        super().leaveEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EventManagementApp()
    window.show()
    sys.exit(app.exec_())