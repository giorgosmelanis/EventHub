import sys
import os
import shutil
import qtawesome as qta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QMessageBox, QHBoxLayout, QListWidget, QListWidgetItem, QFormLayout, QSpacerItem,
    QDateEdit, QTimeEdit, QDateTimeEdit, QFileDialog, QGroupBox, QStackedWidget, QGridLayout, QScrollArea, QSizePolicy
)
from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon, QBrush, QPalette
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QDate, QTime, QDateTime, QTimer 
from models import load_events, save_events, load_users, save_users
from datetime import date, datetime

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
        self.home_tab = None  # Reference to the login tab
        self.events_tab = None
        self.login_tab = None
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
        self.hom_tab = self.create_home_tab()
        self.events_tab = self.create_events_tab()
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
            self.size(), Qt.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation
        )))
        self.setPalette(palette)

    def resizeEvent(self, a0):
        """Resize the background image dynamically when the window is resized."""
        self.set_background()
        self.adjust_grid_layout()
        super().resizeEvent(a0)

    # region Home Section #
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
        self.tabs.addTab(home_tab, QIcon("icons/home.png"), "Home")  # Add icon to the Home tab

        i = self.get_tab_index("Home") or 0 
        self.tabs.setCurrentIndex(i)
        return home_tab # Return the home tab
    
    #endregion

    # region Event Section #
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

        self.tabs.addTab(events_tab, QIcon("icons/events.png"), "Events")  # Add icon to the Events tab

    def toggle_display_mode(self):
        if self.display_mode == "grid":
            self.display_mode = "list"
            self.toggle_display_mode_btn.setText("Εμφάνιση Πλέγματος")
            if self.stacked_widget is not None:
                self.stacked_widget.setCurrentIndex(1)
        else:
            self.display_mode = "grid"
            self.toggle_display_mode_btn.setText("Εμφάνιση Λίστας")
            if self.stacked_widget is not None:
                self.stacked_widget.setCurrentIndex(0)

        # Debug: Print display mode and events
        print(f"\nDisplay Mode Changed to: {self.display_mode}")
        print("Current Events:")
        if self.display_mode == "grid":
            if self.grid_layout is not None:
                for i in range(self.grid_layout.count()):
                    item = self.grid_layout.itemAt(i)
                    if item is not None:  # Check if item exists
                        widget = item.widget()
                        if widget is not None:  # Check if widget exists
                            print(widget.title())
        else:
            if self.list_layout is not None:
                for i in range(self.list_layout.count()):
                    item = self.list_layout.itemAt(i)
                    if item is not None:  # Check if item exists
                        widget = item.widget()
                        if widget is not None:  # Check if widget exists
                            print(widget.title())

        # Reapply filters to update the displayed events
        self.apply_filters()

        # Reapply filters to update the displayed events
        self.apply_filters()

    def display_events(self, events):
        if self.display_mode == "grid":
            self.display_grid(events)
        else:
            self.display_list(events)

    def adjust_grid_layout(self):
        if self.grid_layout is None:
            print("Error: grid_layout is not initialized!")
            return  # Exit the method if grid_layout is None

        window_width = self.width()
        column_width = 320  # Approximate width of each grid item
        num_columns = max(1, window_width // column_width)  # At least 1 column

        # Set column minimum width and stretch
        self.grid_layout.setColumnMinimumWidth(0, column_width)
        self.grid_layout.setColumnStretch(num_columns, 1)  # Add stretch to fill space

    def display_grid(self, events):
        """Display events in a grid layout."""
        self.events = events  # Store the events for resizing

        # Debug: Print events being displayed in grid mode
        print("\nDisplaying Events in Grid Mode:")
        for event in events:
            print(event)

        # Check if grid_layout is initialized
        if self.grid_layout is None:
            print("Error: grid_layout is not initialized!")
            return  # Exit the method if grid_layout is None

        # Check if tiles_per_row_combobox is initialized
        if self.tiles_per_row_combobox is None:
            print("Error: tiles_per_row_combobox is not initialized!")
            return  # Exit the method if tiles_per_row_combobox is None

        # Clear the grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item is not None:  # Check if item exists
                widget = item.widget()
                if widget is not None:  # Check if widget exists
                    widget.deleteLater()

        # Get the number of tiles per row
        tiles_per_row = int(self.tiles_per_row_combobox.currentText())

        # Add events to the grid
        row, col = 0, 0
        for event in events:
            event_widget = self.create_event_widget(event)
            if event_widget is not None:  # Check if event_widget is created
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
            if widget is not None:
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
        f"<b>Ημερομηνία:</b> {event['start_date']} - {event['end_date']}<br>"
        f"<b>Ώρα Έναρξης:</b> {event['start_time']}<br>"            
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
            f"<b>Ημερομηνία:</b> {event['start_date']} - {event['end_date']}<br>"
            f"<b>Ώρα Έναρξης:</b> {event['start_time']}<br>"
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
        from_date_filter = self.from_date_filter_edit.date().toString("dd/MM/yyyy") if self.from_date_filter_edit.date().isValid() else None
        to_date_filter = self.to_date_filter_edit.date().toString("dd/MM/yyyy") if self.to_date_filter_edit.date().isValid() else None
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
            event_date = event["start_date"]

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

    #endregion

    # region Login Section #
    def create_login_tab(self):
        login_tab = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)  # Center the entire layout

        # Title label with gradient effect
        title_label = QLabel("Login")
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
        self.tabs.addTab(login_tab, QIcon("icons/login.png"), "Login")  # Add icon to the Login tab
        
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
        i = self.get_tab_index("Login")
        self.tabs.removeTab(i)  

        # Show the Log Off button
        self.logoff_btn.show()

        # Add private tabs based on user type
        if user_type == "Organizer":
            self.add_organizer_tab()
        elif user_type == "Vendor":
            self.add_vendor_tab()
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
        if self.tabs.indexOf(self.home_tab) == -1:  # Only add if not exists
            self.home_tab = self.create_home_tab()

        # Show the Login Tab again
        if self.tabs.indexOf(self.events_tab) == -1:  # Only add if not exists
            self.events_tab = self.create_events_tab()

        # Show the Login Tab again
        if self.tabs.indexOf(self.login_tab) == -1:  # Only add if not exists
            self.login_tab = self.create_login_tab()

        # Hide the Log Off button
        self.logoff_btn.hide()

    def authenticate_user(self, email, password):
        for user in self.users:
            if user["email"] == email and user["password"] == password:
                return user
        return None
    
    #region Tab Redirection #
    def redirect_to_dashboard(self, user_type):
        # Remove existing private tabs
        for tab_name, tab_widget in self.private_tabs.items():
            self.tabs.removeTab(self.tabs.indexOf(tab_widget))

        # Add private tabs based on user type
        if user_type == "Organizer":
            self.add_organizer_tab()
            i = self.get_tab_index( "Organizer")
            self.tabs.setCurrentIndex(i)  # Redirect to Organizer dashboard
        elif user_type == "Vendor":
            self.add_vendor_tab()
            i = self.get_tab_index( "Vendor")
            self.tabs.setCurrentIndex(i) # Redirect to Vendor dashboard
        elif user_type == "Attendee":
            self.add_attendee_tab()
            i = self.get_tab_index( "Attendee")
            self.tabs.setCurrentIndex(i)  # Redirect to Attendee dashboard
    #endregion

    #endregion

    # region Organizer Section #

    def add_organizer_tab(self):
        i = self.get_tab_index("Home")
        self.tabs.removeTab(i)
        i = self.get_tab_index("Events")
        self.tabs.removeTab(i)
        
        self.logoff_btn.show()  # Show the button

        #region Organizer Tab
        organizer_tab = QWidget()
        layout_organizer_dashboard = QVBoxLayout()

        label = QLabel("Διοργανωτής Εκδηλώσεων")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #ff6f61;")
        layout_organizer_dashboard.addWidget(label)
        #endregion 


        #region Create Event Button
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
        layout_organizer_dashboard.addWidget(create_event_btn)
        #endregion


        

        #region My Event Button
        # my_event_btn = AnimatedButton("My Events")
        # my_event_btn.setIcon(qta.icon("fa5s.calendar"))  # History icon

        my_event_btn = QPushButton("My Events")
        my_event_btn.setIcon(qta.icon("fa5s.calendar-alt"))  # Plus icon
        my_event_btn.setStyleSheet("""
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
        my_event_btn.clicked.connect(self.show_organizer_my_events_tab)
        layout_organizer_dashboard.addWidget(my_event_btn)
        #endregion


        #region Similar Event Button
        # similar_event_btn = AnimatedButton("Similar Events")
        # similar_event_btn.setIcon(qta.icon("fa5s.calendar"))  # History icon

        similar_event_btn = QPushButton("Similar Events")
        similar_event_btn.setIcon(qta.icon("fa5s.calendar-plus"))  # Plus icon
        similar_event_btn.setStyleSheet("""
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
        similar_event_btn.clicked.connect(self.show_organizer_similar_events_tab)
        layout_organizer_dashboard.addWidget(similar_event_btn)
        #endregion

        #region History Button
        history_btn = AnimatedButton("History")
        history_btn.setIcon(qta.icon("fa5s.history"))  # History icon

        # show_history_btn = QPushButton("My Events")
        # show_history_btn.setIcon(qta.icon("fa5s.history"))  # Plus icon
        history_btn.setStyleSheet("""
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
        history_btn.clicked.connect(self.show_organizer_history_tab)
        layout_organizer_dashboard.addWidget(history_btn)
        #endregion

        
        # region My Events Tab #
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

        # Add Organizer-specific content here
        event_list_layout.addWidget(QLabel("Διαχείριση Εκδηλώσεων"))

        # Add the event list to the container
        self.create_organizers_my_events_tab(event_list_layout)

        # Set the container as the scroll area's widget
        scroll_area.setWidget(event_list_container)

        # Add the scroll area to the main layout
        layout_my_events.addWidget(scroll_area)
        #endregion

        #region History Tab
        history_tab = QWidget()
        layout_history = QVBoxLayout()

        label = QLabel("History")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #ff6f61;")
        layout_history.addWidget(label)

        # Add a scroll area for the event list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the widget to resize
        scroll_area.setStyleSheet("border: none;")  # Remove border

        # Create a container widget for the event list
        history_list_container = QWidget()
        history_list_layout = QVBoxLayout(history_list_container)
        history_list_layout.setAlignment(Qt.AlignTop)  # Align items to the top

        # Add Organizer-specific content here
        history_list_layout.addWidget(QLabel("Ιστορικό Εκδηλώσεων"))

        # Add the event list to the container
        self.create_organizers_history_tab(history_list_layout)

        # Set the container as the scroll area's widget
        scroll_area.setWidget(history_list_container)

        # Add the scroll area to the main layout
        layout_history.addWidget(scroll_area)
        #endregion

        #region Similar Events Tab
        similar_events_tab = QWidget()
        layout_similar_events = QVBoxLayout()

        label = QLabel("Similar Events")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #ff6f61;")
        layout_similar_events.addWidget(label)

        # Add a scroll area for the event list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the widget to resize
        scroll_area.setStyleSheet("border: none;")  # Remove border

        # Create a container widget for the event list
        similar_events_list_container = QWidget()
        similar_events_list_layout = QVBoxLayout(similar_events_list_container)
        similar_events_list_layout.setAlignment(Qt.AlignTop)  # Align items to the top

        # Add Organizer-specific content here
        similar_events_list_layout.addWidget(QLabel("Παρόμοιες Εκδηλώσεις"))

        # Add the event list to the container
        self.create_organizers_similar_events_tab(similar_events_list_layout)

        # Set the container as the scroll area's widget
        scroll_area.setWidget(similar_events_list_container)

        # Add the scroll area to the main layout
        layout_similar_events.addWidget(scroll_area)
        #endregion


        organizer_tab.setLayout(layout_organizer_dashboard)
        my_events_tab.setLayout(layout_my_events)
        similar_events_tab.setLayout(layout_similar_events)
        history_tab.setLayout(layout_history)
        self.tabs.addTab(organizer_tab, qta.icon("fa5s.user-edit"), "Organizer")  # Add icon to the Organizer tab
        self.tabs.addTab(my_events_tab, qta.icon("fa5s.calendar-alt"), "My Events")  # Add icon to the Organizer tab
        self.tabs.addTab(similar_events_tab, qta.icon("fa5s.calendar-plus"), "Similar Events")  # Add icon to the Organizer tab
        self.tabs.addTab(history_tab, qta.icon("fa5s.history"), "History")  # Add icon to the Organizer tab
        self.private_tabs["Organizer"] = organizer_tab
        self.private_tabs["My Events"] = my_events_tab
        self.private_tabs["Similar Events"] = similar_events_tab
        self.private_tabs["History"] = history_tab

    def create_organizers_my_events_tab(self, layout):
        """Display events created by the logged-in user with pagination."""
        if not self.current_user:
            return

        # Filter events created by the current user
        organizer_events = [event for event in self.events if event.get("organizer_id") == self.current_user["user_id"]]

        # Clear the layout before adding new widgets
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Paginate events
        total_events = len(organizer_events)
        total_pages = (total_events + self.events_per_page - 1) // self.events_per_page  # Calculate total pages

        # Ensure current_page is within valid range
        self.current_page = max(1, min(self.current_page, total_pages))

        # Get events for the current page
        start_index = (self.current_page - 1) * self.events_per_page
        end_index = start_index + self.events_per_page
        paginated_events = organizer_events[start_index:end_index]

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

    def create_organizers_history_tab(self, layout):
        if not self.current_user:
            return
        
        getDate = datetime.now().date()
        print(getDate)
        
        # Filter past events created by the current user
        organizer_history = [
            history for history in self.events
            if history.get("organizer_id") == self.current_user["user_id"] and 
            datetime.strptime(history.get("start_date"), "%d/%m/%Y").date() < getDate
        ]

        # Clear the layout before adding new widgets
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Create a container widget for the scroll area
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_widget.setLayout(scroll_layout)
        
        # Add event widgets to the scroll layout
        for history in organizer_history:
            event_widget = self.create_event_widget(history, is_list=True)
            scroll_layout.addWidget(event_widget)
        
        # Add scrollable widget to the scroll area
        scroll_area.setWidget(scroll_widget)
        
        # Add scroll area to the main layout
        layout.addWidget(scroll_area)

    def create_organizers_similar_events_tab(self, layout):
        if not self.current_user:
            return
        getDate = datetime.now().date()
        print(getDate)
        # Filter events created by the current user

        organizer_similar_events = [similar_events for similar_events in self.events if similar_events.get("organizer_id") != self.current_user["user_id"] and datetime.strptime(similar_events.get("start_date"), "%d/%m/%Y").date() >= getDate]

        # Clear the layout before adding new widgets
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Create a QListWidget to display the events
        event_list_widget = QListWidget()
        event_list_widget.setStyleSheet("""
            QListWidget {
                font-size: 14px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            QListWidget::item:hover {
                background-color: #e0e0e0;
            }
        """)

        # Add each event to the QListWidget
        for event in organizer_similar_events:
            event_name = event.get("title", "Unnamed Event")
            event_date = event.get("start_date", "Unknown Date")
            event_location = event.get("location", "Unknown Location")
            image_path = event.get("image", "default_placeholder.png")  # Default image if none provided

            # Create a custom widget for each event
            event_widget = QWidget()
            event_layout = QVBoxLayout(event_widget)

            # Load event image
            event_image_label = QLabel()
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Resize image
            event_image_label.setPixmap(pixmap)

            # Event details layout
            details_layout = QVBoxLayout()
            details_layout.addWidget(QLabel(f"<b>{event_name}</b>"))
            details_layout.addWidget(QLabel(f"Date: {event_date}"))
            details_layout.addWidget(QLabel(f"Location: {event_location}"))

            # Add image and details to main layout
            event_layout.addWidget(event_image_label)
            event_layout.addLayout(details_layout)

            # Create a QListWidgetItem and set the custom widget
            list_item = QListWidgetItem(event_list_widget)
            list_item.setSizeHint(event_widget.sizeHint())
            event_list_widget.addItem(list_item)
            event_list_widget.setItemWidget(list_item, event_widget)

            # Add the QListWidget to the layout
            layout.addWidget(event_list_widget)

    def change_page(self, layout, delta):
        """Change the current page and update the displayed events."""
        self.current_page += delta
        self.create_organizers_my_events_tab(layout)

    #endregion

    # region Vendor Section #
    def add_vendor_tab(self):
        vendor_tab = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Vendor")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #6b5b95;")
        layout.addWidget(label)

        # Add vendor-specific content here
        layout.addWidget(QLabel("Διαχείριση Προμηθειών"))

        vendor_tab.setLayout(layout)
        self.tabs.addTab(vendor_tab, QIcon("icons/vendor.png"), "Vendor")  # Add icon to the Vendor tab
        self.private_tabs["Vendor"] = vendor_tab

    #endregion

    # region Attendee Section #

    def add_attendee_tab(self):
        i = self.get_tab_index("Home")
        self.tabs.removeTab(i)
        i = self.get_tab_index("Events")
        self.tabs.removeTab(i)
        
        self.logoff_btn.show()  # Show the button

        # region Home Page Tab
        attendee_tab = QWidget()
        layout_attendee_dashboard = QVBoxLayout()

        label = QLabel("Home Page")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #88b04b;")
        layout_attendee_dashboard.addWidget(label)

        # Add attendee-specific content here
        layout_attendee_dashboard.addWidget(QLabel("Επιλογές "))
        #endregion

        # region Find Events Button
        find_events_btn = AnimatedButton("Find Events")
        find_events_btn.setIcon(qta.icon("fa5s.search"))
        find_events_btn.setStyleSheet("""
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
        #find_events_btn.clicked.connect(self.find_events)
        layout_attendee_dashboard.addWidget(find_events_btn)
        #endregion

        # region My Tickets Button
        my_tickets_btn = AnimatedButton("My Tickets")
        my_tickets_btn.setIcon(qta.icon("fa5s.ticket-alt"))
        my_tickets_btn.setStyleSheet(""" 
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
        #my_tickets_btn.clicked.connect(self.my_tickets)
        layout_attendee_dashboard.addWidget(my_tickets_btn)
        #endregion

        # region My History Button
        my_history_btn = QPushButton("My History")
        my_history_btn.setIcon(qta.icon("fa5s.history"))
        my_history_btn.setStyleSheet(""" 
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
        #my_history_btn.clicked.connect(self.my_history_btn)
        layout_attendee_dashboard.addWidget(my_history_btn)
        #endregion

        # region Chat Button ToDo
        #endregion

        # region Find Events Tab
        find_events_tab = QWidget()
        layout_find_events = QVBoxLayout()

        label = QLabel("Find Events")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #ff6f61;")
        layout_find_events.addWidget(label)

        # Add a scroll area for the event list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the widget to resize
        scroll_area.setStyleSheet("border: none;")  # Remove border
        
        self.create_attendee_find_events_tab(layout_find_events)
        #endregion


        # region Find Events Tab

        #endregion

        attendee_tab.setLayout(layout_attendee_dashboard)
        find_events_tab.setLayout(layout_find_events)
        self.tabs.addTab(attendee_tab, qta.icon("fa5s.user-edit"), "Attendee")  # Add icon to the Attendee tab
        self.tabs.addTab(find_events_tab, qta.icon("fa5s.search"), "Find Events")  # Add icon to the Organizer tab
        self.private_tabs["Attendee"] = attendee_tab
        self.private_tabs["Find Events"] = find_events_tab

    def create_attendee_find_events_tab(self, layout):
        if not self.current_user:
            return
        getDate = datetime.now().date()
        print(getDate)
        # Filter events created by the current user

        attendee_find_events = [find_events for find_events in self.events if datetime.strptime(find_events.get("start_date"), "%d/%m/%Y").date() >= getDate]

        # Clear the layout before adding new widgets
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Create a QListWidget to display the events
        event_list_widget = QListWidget()
        event_list_widget.setStyleSheet("""
            QListWidget {
                font-size: 14px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            QListWidget::item:hover {
                background-color: #e0e0e0;
            }
        """)

        # Add each event to the QListWidget
        for event in attendee_find_events:
            event_name = event.get("title", "Unnamed Event")
            event_date = event.get("start_date", "Unknown Date")
            event_location = event.get("location", "Unknown Location")
            image_path = event.get("image", "default_placeholder.png")  # Default image if none provided

            # Create a custom widget for each event
            event_widget = QWidget()
            event_layout = QVBoxLayout(event_widget)

            # Load event image
            event_image_label = QLabel()
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Resize image
            event_image_label.setPixmap(pixmap)

            # Event details layout
            details_layout = QVBoxLayout()
            details_layout.addWidget(QLabel(f"<b>{event_name}</b>"))
            details_layout.addWidget(QLabel(f"Date: {event_date}"))
            details_layout.addWidget(QLabel(f"Location: {event_location}"))

            # Add image and details to main layout
            event_layout.addWidget(event_image_label)
            event_layout.addLayout(details_layout)

            # Create a QListWidgetItem and set the custom widget
            list_item = QListWidgetItem(event_list_widget)
            list_item.setSizeHint(event_widget.sizeHint())
            event_list_widget.addItem(list_item)
            event_list_widget.setItemWidget(list_item, event_widget)

            # Add the QListWidget to the layout
            layout.addWidget(event_list_widget)
    #endregion


    # region Actions #
    def open_create_event_modal(self):
        self.create_event_modal = CreateEventModal(self)
        self.create_event_modal.show()
    
    def open_signup_modal(self):
        self.create_event_modal = SignupModal(self)
        self.create_event_modal.show()

    def show_events_tab(self):
        i = self.get_tab_index("Events")
        self.tabs.setCurrentIndex(i)

    def show_login_tab(self):
        i= self.get_tab_index("Login")
        self.tabs.setCurrentIndex(i)

    def show_organizer_my_events_tab(self):
        i= self.get_tab_index( "My Events")
        self.tabs.setCurrentIndex(i)

    def show_organizer_history_tab(self):
        i = self.get_tab_index( "History")
        self.tabs.setCurrentIndex(i)

    def show_organizer_similar_events_tab(self):
        i = self.get_tab_index( "Similar Events")
        self.tabs.setCurrentIndex(i)

    def get_tab_index(self, tab_name):
        # Find the index of the tab with the given name
        index = -1
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == tab_name:
                index = i
                return index
    #endregion

class SignupModal(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.users = load_users()
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
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)  # Center the title

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
        self.user_type_combobox.addItems(["Attendee", "Organizer", "Vendor"])
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
        layout.addWidget(signup_btn, alignment=Qt.AlignmentFlag.AlignCenter)  # Center the button

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
        if any(user["email"] == email for user in self.users):
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
        self.users.append(new_user)
        save_users(self.users)

        QMessageBox.information(self, "Επιτυχία", "Εγγραφήκατε με επιτυχία!")
        self.close()

    def generate_user_id(self):
        """Generate a new user_id based on the last user_id in users.json."""
        if not self.users:
            return 1  # If no users exist, start with user_id 1
        last_user = self.users[-1]
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
        self.current_user = parent.current_user
        self.setWindowTitle("Δημιουργία Νέας Εκδήλωσης")
        self.setGeometry(200, 200, 500, 450)
        self.setStyleSheet("""
            background-color: #f0f0f0;
            color: #333333;
            font-family: 'Helvetica';
        """)

        self.ticket_entries = []  # αποθηκεύει κάθε ticket γραμμή

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Event creation form
        self.form = QFormLayout()
        layout.addLayout(self.form)

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
        self.form.addRow("Όνομα Εκδήλωσης:", self.event_name_entry)

        # Event Starting Date input
        self.event_start_date_edit = QDateEdit()
        self.event_start_date_edit.setDate(QDate.currentDate())  # Set default to today's date
        self.event_start_date_edit.setCalendarPopup(True)  # Enable calendar popup
        self.event_start_date_edit.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.form.addRow("Ημερομηνία Έναρξης:", self.event_start_date_edit)

        # Event End Date input
        self.event_end_date_edit = QDateEdit()
        self.event_end_date_edit.setDate(QDate.currentDate())
        self.event_end_date_edit.setCalendarPopup(True)
        self.event_end_date_edit.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.form.addRow("Ημερομηνία Λήξης:", self.event_end_date_edit)

        # Starting Time input
        self.event_start_time_edit = QTimeEdit()
        self.event_start_time_edit.setTime(QTime.currentTime())
        self.event_start_time_edit.setDisplayFormat("HH:mm")
        self.event_start_time_edit.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.form.addRow("Ώρα Έναρξης:", self.event_start_time_edit)

        # Event location input (drop-down box)
        self.event_location_combobox = QComboBox()
        self.event_location_combobox.addItems(["Αθήνα", "Θεσσαλονίκη", "Πάτρα", "Ηράκλειο","Λάρισα","Βόλος","Ιωάννινα","Χανιά","Καλαμάτα","Καβάλα","Αλεξανδρούπολη","Κέρκυρα","Τρίκαλα","Ξάνθη"])
        self.event_location_combobox.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.form.addRow("Τοποθεσία:", self.event_location_combobox)

        # Event type selection
        self.event_type_combobox = QComboBox()
        self.event_type_combobox.addItems(["Ιδιωτικό","All-day Festival","Multi-day Festival", "Συναυλία","Κινηματογραφικό", "Επαγγελματικό","Συνέδριο","Διασκέδαση","Αθλητικό","Καλλιτεχνικό","Εκπαιδευτικό","Φιλανθρωπικό","Θρησκευτικό","Οικογενειακό","Διαδικτυακό","Κοινωνικό","Πολιτικό","Εθελοντικό","Εμπορικό","Gaming"])
        self.event_type_combobox.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.form.addRow("Τύπος Εκδήλωσης:", self.event_type_combobox)

# --- Ticket Section ---
        self.ticket_title_label = QLabel("Προσθήκη Εισιτηρίων:")
        self.form.addRow(self.ticket_title_label)

        # Container layout για γραμμές + κουμπί
        ticket_main_layout = QHBoxLayout()

        # Layout με τις σειρές εισιτηρίων
        self.ticket_layout = QVBoxLayout()
        self.ticket_layout.setSpacing(10)  # Λίγο κενό ανάμεσα στις σειρές

        # Κουμπί "Προσθήκη" – θα το βάλουμε σε layout ώστε να κολλάει πάνω δεξιά
        self.add_ticket_button = QPushButton("Προσθήκη")
        self.add_ticket_button.setStyleSheet("""
            QPushButton {
                background-color: #88b04b;
                color: white;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #6d8b3a;
            }
        """)
        self.add_ticket_button.clicked.connect(self.add_ticket_entry)

        # Κουμπί "Διαγραφή"
        self.remove_ticket_button = QPushButton("Διαγραφή")
        self.remove_ticket_button.setStyleSheet("""
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
        self.remove_ticket_button.clicked.connect(self.remove_ticket_entry)

        # Layout 
        button_container = QWidget()
        button_layout = QHBoxLayout() #οριζοντια στοιχιση
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        button_layout.addWidget(self.add_ticket_button, alignment=Qt.AlignTop)
        button_layout.addWidget(self.remove_ticket_button, alignment=Qt.AlignTop)
        
        button_container.setLayout(button_layout)

       # Σταθερό ύψος για να ευθυγραμμίζεται με την 1η γραμμή
        button_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        ticket_main_layout.addLayout(self.ticket_layout)   # Αριστερά: εισιτήρια
        ticket_main_layout.addWidget(button_container, alignment=Qt.AlignTop)     # Δεξιά: κουμπιά

        # Τελική προσθήκη στο form
        ticket_container = QWidget()
        ticket_container.setLayout(ticket_main_layout)
        self.form.addRow(ticket_container)

        # Προσθήκη πρώτων πεδίων
        self.ticket_entries = []
        for _ in range(4):
            self.add_ticket_entry()

### Μέχρι πότε είναι διαθέσιμα για αγορά και πότε για ακύρωση##################################
        self.ticket_availability = QDateTimeEdit(QDateTime.currentDateTime())
        self.ticket_availability.setCalendarPopup(True)
        self.ticket_availability.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.ticket_availability.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.form.addRow("Διαθεσιμότητα εισιτηρίων έως:", self.ticket_availability)

        self.ticket_cancel_availability = QDateTimeEdit(QDateTime.currentDateTime())
        self.ticket_cancel_availability.setCalendarPopup(True)
        self.ticket_cancel_availability.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.ticket_cancel_availability.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.form.addRow("Ακύρωση εισιτηρίων έως:", self.ticket_cancel_availability)
##################################################################################################

### Event description input#######################################################################
        self.event_description_entry = QTextEdit()
        self.event_description_entry.setPlaceholderText("Εισάγετε μια περιγραφή για την εκδήλωση")
        self.event_description_entry.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)
        self.form.addRow("Περιγραφή:", self.event_description_entry)
###################################################################################################
        # Event image upload
        self.image_path = None
        self.image_label = QLabel("Δεν έχει επιλεγεί εικόνα")
        self.image_label.setStyleSheet("font-size: 14px; color: #777;")
        self.image_path = None
        self.image_label = QLabel("Δεν έχει επιλεγεί εικόνα")
        self.image_label.setStyleSheet("font-size: 14px; color: #777;")

        upload_btn = QPushButton("Επιλογή Εικόνας")
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
        upload_btn.clicked.connect(self.upload_image)

        # Δημιουργία layout που περιλαμβάνει ετικέτα και κουμπί δεξιά
        image_layout = QHBoxLayout()
        image_layout.addWidget(self.image_label)
        image_layout.addWidget(upload_btn)

        self.form.addRow("Εικόνα Εκδήλωσης:", image_layout)
####################################################################################################

        #Κλείσιμο
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
        close_btn.clicked.connect(lambda: (
            QMessageBox.question(
                self,
                "Επιβεβαίωση Ακύρωσης",
                "Είστε σίγουροι ότι θέλετε να ακυρώσετε τη δημιουργία της εκδήλωσης;",
                QMessageBox.Ok | QMessageBox.Cancel
             ) == QMessageBox.Ok and self.close()
            ))
        button_layout.addWidget(close_btn)

########Preview Button#########################################
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
        preview_btn.clicked.connect(self.preview_event)
        button_layout.addWidget(preview_btn)

########Δημιουργία########################
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

    def add_ticket_entry(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)

        # Dropdown τύπου εισιτηρίου
        type_combo = QComboBox()
        type_combo.addItems(["Early Bird", "Regular", "VIP", "Zone A", "Zone B", "Backstage Pass", "Arena","All-day Pass" ,"One-day Pass", "Multi-day Pass"])
        type_combo.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)

        # Πεδία τιμής και ποσότητας
        price_input = QLineEdit()
        price_input.setPlaceholderText("Τιμή €")
        price_input.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)

        quantity_input = QLineEdit()
        quantity_input.setPlaceholderText("Ποσότητα")
        quantity_input.setStyleSheet("""
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
            background-color: white;
        """)

        # Προσθήκη στο layout με τη σωστή σειρά
        row_layout.addWidget(type_combo)
        row_layout.addWidget(price_input)
        row_layout.addWidget(quantity_input)
        row_widget.setLayout(row_layout)
        
        self.ticket_layout.addWidget(row_widget)
        self.ticket_entries.append({
            "widget": row_widget,
            "type": type_combo,
            "price_input": price_input,
            "quantity_input": quantity_input
    })
        
    def remove_ticket_entry(self):
         if len(self.ticket_entries) > 1:
            last_entry = self.ticket_entries.pop()
            row_widget = last_entry["widget"]
            self.ticket_layout.removeWidget(row_widget)
            row_widget.deleteLater()
         else:
              QMessageBox.information(self, "Προσοχή", "Πρέπει να υπάρχει τουλάχιστον ένα εισιτήριο.")              
    
    def upload_image(self):
        """Open a file dialog to select an image and save it to the images directory."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Επιλογή Εικόνας",
            "event_images",
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
        
            # Αν η πηγή και ο προορισμός είναι ίδιο αρχείο, μην κάνεις copy
            if os.path.abspath(file_path) != os.path.abspath(save_path):
             shutil.copy(file_path, save_path)
            
             # Αποθήκευση path για μελλοντική χρήση
            self.image_path = save_path.replace("\\", "/")  # Πάντα forward slashes

            # Display the image preview
            pixmap = QPixmap(save_path)
            self.image_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            self.image_label.setText("")
            
    def preview_event(self):
        # Συλλογή τιμών από τη φόρμα
        title = self.event_name_entry.text().strip()
        start_date = self.event_start_date_edit.date().toString("dd/MM/yyyy")
        end_date = self.event_end_date_edit.date().toString("dd/MM/yyyy")
        start_time = self.event_start_time_edit.time().toString("HH:mm")
        location = self.event_location_combobox.currentText()
        event_type = self.event_type_combobox.currentText()
        description = self.event_description_entry.toPlainText().strip()
        ticket_avail = self.ticket_availability.dateTime().toString("dd/MM/yyyy HH:mm")
        ticket_cancel = self.ticket_cancel_availability.dateTime().toString("dd/MM/yyyy HH:mm")

        # Εισιτήρια
        tickets = []
        for entry in self.ticket_entries:
            ticket_type = entry["type"].currentText()
            price = entry["price_input"].text().strip()
            quantity = entry["quantity_input"].text().strip()
            tickets.append({"type": ticket_type, "price": price, "quantity": quantity})

        # Έλεγχος αν όλα τα πεδία είναι συμπληρωμένα
        missing_fields = []
        if not title:
            missing_fields.append("Τίτλος")
        if not description:
            missing_fields.append("Περιγραφή")
        if not self.image_path:
            missing_fields.append("Εικόνα")
        for t in tickets:
            if not t["price"] or not t["quantity"]:
                missing_fields.append("Τιμές/Ποσότητες εισιτηρίων")
                break

        if missing_fields:
            QMessageBox.warning(self, "Σφάλμα", "Τα εξής πεδία είναι κενά:\n- " + "\n- ".join(missing_fields))
            return

        # Δημιουργία παραθύρου προεπισκόπησης
        self.preview_window = QWidget()
        self.preview_window.setWindowTitle("Προεπισκόπηση Εκδήλωσης")
        self.preview_window.setGeometry(150, 150, 600, 650)
        self.preview_window.setStyleSheet("background-color: white;")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 10)  # Μειωμένο bottom margin
        layout.setSpacing(8)  # Λιγότερο κάθετο spacing
        self.preview_window.setLayout(layout)


        # Εικόνα
        if self.image_path:
            image_label = QLabel()
            pixmap = QPixmap(self.image_path)
            image_label.setPixmap(pixmap.scaled(300, 200, Qt.KeepAspectRatio))
            layout.addWidget(image_label, alignment=Qt.AlignCenter | Qt.AlignBottom)
        
        # Προσθήκη κενό κάτω από την εικόνα
        layout.addSpacing(30)
        
        # Λεπτομέρειες εισιτηρίων
        ticket_info = ""
        for t in tickets:
            ticket_info += f"• {t['type']}: {t['price']}€ ({t['quantity']} διαθέσιμα)<br>"

        # Λεπτομέρειες εκδήλωσης
        details = QLabel(
            f"<b>Τίτλος:</b> {title}<br>"
            f"<b>Τοποθεσία:</b> {location}<br>"
            f"<b>Τύπος:</b> {event_type}<br>"
            f"<b>Περιγραφή:</b><br>{description}<br><br>"
            f"<b>Ημερομηνία Έναρξης:</b> {start_date}<br>"
            f"<b>Ώρα Έναρξης:</b> {start_time}<br>"
            f"<b>Ημερομηνία Λήξης:</b> {end_date}<br><br>"
            f"<b>Τύποι Εισιτηρίων:</b><br>{ticket_info}<br>"
            f"<b>Διαθεσιμότητα Εισιτηρίων έως:</b> {ticket_avail}<br>"
            f"<b>Ακύρωση Εισιτηρίων έως:</b> {ticket_cancel}"
        )
        details.setStyleSheet("font-size: 14px; color: #333;")
        details.setWordWrap(True)
        layout.addWidget(details)


        # Spacer για να σπρώξει το κουμπί προς τα κάτω
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Κουμπί OK
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
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
        ok_button.clicked.connect(self.preview_window.close)
        layout.addWidget(ok_button, alignment=Qt.AlignCenter)

        self.preview_window.setLayout(layout)
        self.preview_window.show()

    def create_event(self):
        event_name = self.event_name_entry.text().strip()
        event_start_date = self.event_start_date_edit.date().toString("dd/MM/yyyy")  # Format date as dd/MM/yyyy
        event_end_date = self.event_end_date_edit.date().toString("dd/MM/yyyy")
        event_start_time = self.event_start_time_edit.time().toString("HH:mm")
        event_location = self.event_location_combobox.currentText()
        event_type = self.event_type_combobox.currentText()
        event_description = self.event_description_entry.toPlainText().strip()
        start_dt = QDateTime(
            self.event_start_date_edit.date(),
            self.event_start_time_edit.time()
        )

        ticket_avail_dt = self.ticket_availability.dateTime()
        ticket_cancel_dt = self.ticket_cancel_availability.dateTime()
##STRINGS
        ticket_avail_dt_str = ticket_avail_dt.toString("dd/MM/yyyy HH:mm")
        ticket_cancel_dt_str = ticket_cancel_dt.toString("dd/MM/yyyy HH:mm")
        
        if not event_name or not event_start_date or not event_end_date or not event_location or not event_type or not event_description:
            QMessageBox.warning(self, "Σφάλμα", "Παρακαλώ συμπληρώστε όλα τα πεδία.")
            return
    
        if QDate.fromString(event_start_date, "dd/MM/yyyy") < QDate.currentDate():
            QMessageBox.warning(self, "Σφάλμα", "Η ημερομηνία έναρξης δεν είναι έγκυρη.")
            return

        if QDate.fromString(event_end_date, "dd/MM/yyyy") < QDate.fromString(event_start_date, "dd/MM/yyyy"):
            QMessageBox.warning(self, "Σφάλμα", "Η ημερομηνία λήξης δεν μπορεί να είναι πριν την έναρξης.")
            return

        if not self.image_path:
            QMessageBox.warning(self, "Σφάλμα", "Παρακαλώ επιλέξτε μια εικόνα.")
            return
        
        if ticket_avail_dt > start_dt:
            QMessageBox.warning(self, "Invalid Input", "Η διαθεσιμότητα εισιτηρίων πρέπει να είναι πριν την έναρξη της εκδήλωσης.")
            return

        if ticket_cancel_dt > start_dt:
            QMessageBox.warning(self, "Invalid Input", "Η ημερομηνία ακύρωσης εισιτηρίων πρέπει να είναι πριν την έναρξη της εκδήλωσης.")
            return
        
        # === ΕΙΣΙΤΗΡΙΑ ===
        ticket_types = []
        for entry in self.ticket_entries:
            ticket_type = entry["type"].currentText()
            price_text = entry["price_input"].text().strip()
            quantity_text = entry["quantity_input"].text().strip()

# Έλεγχος: Αν η εκδήλωση είναι μονοήμερη και επιλέχθηκε Multi-day Pass
            if event_start_date == event_end_date and ticket_type == "Multi-day Pass":
                QMessageBox.warning(self, "Σφάλμα", "Δεν μπορείτε να προσθέσετε εισιτήριο τύπου 'Multi-day Pass' σε μονοήμερη εκδήλωση.")
                return
            
            if not price_text or not quantity_text:
                QMessageBox.warning(self, "Σφάλμα", "Συμπλήρωσε τιμή και ποσότητα για κάθε εισιτήριο.")
                return

            try:
                price = float(price_text)
                quantity = int(quantity_text)
            except ValueError:
                QMessageBox.warning(self, "Σφάλμα", "Η τιμή πρέπει να είναι δεκαδικός αριθμός και η ποσότητα ακέραιος.")
                return

            ticket_types.append({
                "type": ticket_type,
                "price": price,
                "total_quantity": quantity
            })

        # Create new event
        new_event = {
            "event_id": len(self.parent.events) + 1,
            "title": event_name,
            "start_date": event_start_date,
            "end_date": event_end_date,
            "start_time": event_start_time,
            "location": event_location,
            "type": event_type,
            "description": event_description,
            "image": self.image_path,
            "organizer_id": self.current_user["user_id"],  # Store the Organizer's user_id
            "organizer": f"{self.current_user['name']} {self.current_user['surname']}",  # Store the Organizer's name and surname
            "ticket_types": ticket_types,
            "ticket_availability": ticket_avail_dt_str,
            "ticket_cancel_availability": ticket_cancel_dt_str
        }
        self.parent.events.append(new_event)
        save_events(self.parent.events)

        self.parent.apply_filters()
        QMessageBox.information(self, "Επιτυχία", "Η εκδήλωση δημιουργήθηκε με επιτυχία!")
        self.close()

#region Styling Tests


class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None, **kwargs):
        super().__init__(text, parent)

        # Default properties
        self._color = kwargs.get("color", "#D91656")  # Default button color
        self._hover_color = kwargs.get("hover_color", "#640D5F")  # Hover color
        self._pressed_color = kwargs.get("pressed_color", "#4A0A4A")  # Pressed color
        self._text_color = kwargs.get("text_color", "white")  # Text color
        self._hover_text_color = kwargs.get("hover_text_color", "white")  # Hover text color
        self._pressed_text_color = kwargs.get("pressed_text_color", "white")  # Pressed text color
        self._border_radius = kwargs.get("border_radius", 5)  # Border radius
        self._border_color = kwargs.get("border_color", "transparent")  # Border color
        self._hover_border_color = kwargs.get("hover_border_color", "transparent")  # Hover border color
        self._pressed_border_color = kwargs.get("pressed_border_color", "transparent")  # Pressed border color
        self._font_size = kwargs.get("font_size", 14)  # Font size
        self._font_family = kwargs.get("font_family", "Arial")  # Font family
        self._icon = kwargs.get("icon", None)  # Optional icon
        #self._icon_size = kwargs.get("icon_size", QSize(24, 24))  # Icon size
        self._animation_duration = kwargs.get("animation_duration", 300)  # Animation duration

        # Apply initial styles
        self._update_styles()

    def _update_styles(self):
        """Update the button's stylesheet based on current properties."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                color: {self._text_color};
                padding: 10px 20px;
                font-size: {self._font_size}px;
                font-family: {self._font_family};
                border-radius: {self._border_radius}px;
                border: 2px solid {self._border_color};
            }}
            QPushButton:hover {{
                background-color: {self._hover_color};
                color: {self._hover_text_color};
                border-color: {self._hover_border_color};
            }}
            QPushButton:pressed {{
                background-color: {self._pressed_color};
                color: {self._pressed_text_color};
                border-color: {self._pressed_border_color};
            }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
                color: #888888;
                border-color: #999999;
            }}
        """)

    #     # Store the original geometry of the button
    #     self.original_geometry = self.geometry()
        
    #     # Animation for hover effect
    #     self.animation = QPropertyAnimation(self, b"geometry")
    #     self.animation.setDuration(100)  # Duration in milliseconds
    #     self.animation.setEasingCurve(QEasingCurve.OutCirc)

    # def enterEvent(self, a0):
    #     """Triggered when the mouse enters the button area."""
    #     self.animation.stop()
    #     self.animation.setStartValue(self.geometry())
    #     self.animation.setEndValue(QRect(self.x() - 5, self.y() - 5, self.width() + 10, self.height() + 10))
    #     self.animation.start()
    #     super().enterEvent(a0)

    # def leaveEvent(self, a0):
    #     """Triggered when the mouse leaves the button area."""
    #     self.animation.stop()
    #     self.animation.setStartValue(self.geometry())
    #     self.animation.setEndValue(QRect(self.x() + 5, self.y() + 5, self.width() - 10, self.height() - 10))  # Return to the original size
    #     self.animation.start()
    #     super().leaveEvent(a0)

    # def resizeEvent(self, a0):
    #     """Update the original geometry when the button is resized."""
    #     self.original_geometry = self.geometry()
    #     super().resizeEvent(a0)
#endregion

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EventManagementApp()
    window.show()
    sys.exit(app.exec_())
