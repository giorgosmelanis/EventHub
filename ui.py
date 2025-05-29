import sys
import os
import json
import shutil
import qtawesome as qta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QMessageBox, QHBoxLayout, QListWidget, QListWidgetItem, QFormLayout, QSpacerItem,
    QDateEdit, QTimeEdit, QDateTimeEdit, QFileDialog, QGroupBox, QStackedWidget, QGridLayout, QScrollArea, QSizePolicy, QDialog,
    QCheckBox, QGraphicsDropShadowEffect, QSpinBox, QMenu, QSystemTrayIcon, QDialogButtonBox
)
from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon, QBrush, QPalette, QImage
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QDate, QTime, QDateTime, QTimer, QSize, QPoint
from models import load_events, save_events, load_users, save_users, load_services
from datetime import date, datetime, timedelta
from ticket_purchase import TicketPurchaseModal
from vendor_add_services import AddServicesModal 
from collaborations import CollaborationRequest, save_collaboration_request, get_pending_requests_for_vendor, CollaborationRequestDetailsDialog
from ticket_management import TicketManagementMixin

class EventManagementApp(QMainWindow, TicketManagementMixin):
    def __init__(self):
        super().__init__()
        self.initialize_attributes()  # Initialize all necessary attributes
        self.setup_ui()  # Set up the UI components
        
        # Initialize system tray icon
        self.setup_system_tray()
        
        # Connect tab change signal
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
    def setup_system_tray(self):
        """Initialize the system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("eventHub_logo.jpg"))
        
        # Create tray menu
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Εμφάνιση")
        show_action.triggered.connect(self.show)
        
        notifications_action = tray_menu.addAction("Notifications")
        notifications_action.triggered.connect(lambda: self.tabs.setCurrentIndex(self.get_tab_index("Notifications")))
        
        quit_action = tray_menu.addAction("Έξοδος")
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

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

        # Store window references
        self.detail_window = None  # Add this line to store the detail window reference

        # Pagination attributes
        self.events_per_page = 5  # Default number of events per page
        self.current_page = 1  # Track the current page
        self.total_pages = 1  # Default value

        # Set up notification timer
        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(self.check_notifications)
        self.notification_timer.start(5000)  # Check every 5 seconds

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
                background-color: #6b5b95;  /* Grey color */
                color: white;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #524778;  /* Darker grey for hover */
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
        """Create a widget for displaying an event in the list."""
        event_widget = QWidget()
        event_widget.setStyleSheet("""
            QWidget#eventContainer {
                background-color: white;
                border: none;
                border-radius: 8px;
            }
            QWidget#eventContainer:hover {
                border: 1px solid #D91656;
            }
        """)
        event_widget.setObjectName("eventContainer")
        event_layout = QHBoxLayout(event_widget)
        event_layout.setContentsMargins(15, 15, 15, 15)
        
        # Left side: Event image container
        image_container = QWidget()
        image_container.setFixedSize(180, 180)
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setAlignment(Qt.AlignCenter)
        
        image_label = QLabel()
        image_label.setFixedSize(180, 180)
        image_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: none;
                border-radius: 4px;
            }
        """)
        
        if event.get('image'):
            pixmap = QPixmap(event['image'])
            if not pixmap.isNull():
                pixmap = pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(pixmap)
        else:
                image_label.setText("No Image")
                image_label.setAlignment(Qt.AlignCenter)

        image_layout.addWidget(image_label)
        event_layout.addWidget(image_container)
        
        # Add some spacing between image and info
        event_layout.addSpacing(20)
        
        # Middle: Event info
        info_widget = QWidget()
        info_widget.setStyleSheet("border: none;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(5)
        
        # Event Title
        title = QLabel(event["title"])
        title.setFont(QFont("Helvetica", 16, QFont.Bold))
        title.setStyleSheet("color: #333; border: none;")
        info_layout.addWidget(title)
        
        # Event Date and Time
        date_str = f"{event['start_date']} {event['start_time']}"
        date_label = QLabel(f"Ημερομηνία: {date_str}")
        date_label.setStyleSheet("color: #666; font-size: 14px; border: none;")
        info_layout.addWidget(date_label)
        
        # Location
        location_label = QLabel(f"Τοποθεσία: {event['location']}")
        location_label.setStyleSheet("color: #666; font-size: 14px; border: none;")
        info_layout.addWidget(location_label)
        
        # Type
        type_label = QLabel(f"Τύπος: {event['type']}")
        type_label.setStyleSheet("color: #666; font-size: 14px; border: none;")
        info_layout.addWidget(type_label)
        
        info_layout.addStretch()
        event_layout.addWidget(info_widget, stretch=1)
        
        # Right side: View Details Button
        button_widget = QWidget()
        button_widget.setStyleSheet("border: none;")
        button_layout = QVBoxLayout(button_widget)
        button_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        details_btn = QPushButton("Περισσότερα")
        details_btn.setStyleSheet("""
            QPushButton {
                background-color: #D91656;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #640D5F;
            }
        """)
        details_btn.clicked.connect(lambda: self.show_event_details(event))
        button_layout.addWidget(details_btn)
        
        event_layout.addWidget(button_widget)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        event_widget.setGraphicsEffect(shadow)
        
        return event_widget

    def show_event_details(self, event):
        """Show detailed information about an event in a new window."""
        print(f"Current user: {self.current_user}")  # Debug print
        
        self.detail_window = QWidget()
        self.detail_window.setWindowTitle(f"Προεπισκόπηση Εκδήλωσης")
        self.detail_window.setGeometry(150, 150, 600, 650)
        self.detail_window.setStyleSheet("background-color: white;")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 10)
        layout.setSpacing(8)
        self.detail_window.setLayout(layout)

        # Event image
        if event.get("image"):
            image_label = QLabel()
            pixmap = QPixmap(event["image"])
            image_label.setPixmap(pixmap.scaled(300, 200, Qt.KeepAspectRatio))
            layout.addWidget(image_label, alignment=Qt.AlignCenter | Qt.AlignBottom)
        
        # Add spacing below image
        layout.addSpacing(30)

        # Event details
        details = QLabel(
            f"<b>Τίτλος:</b> {event.get('title', '')}<br>"
            f"<b>Τοποθεσία:</b> {event.get('location', '')}<br>"
            f"<b>Τύπος:</b> {event.get('type', '')}<br>"
            f"<b>Περιγραφή:</b><br>{event.get('description', '')}<br><br>"
            f"<b>Ημερομηνία Έναρξης:</b> {event.get('start_date', '')}<br>"
            f"<b>Ώρα Έναρξης:</b> {event.get('start_time', '')}<br>"
            f"<b>Ημερομηνία Λήξης:</b> {event.get('end_date', '')}<br><br>"
        )
        details.setStyleSheet("font-size: 14px; color: #333;")
        details.setWordWrap(True)
        layout.addWidget(details)

        # Add ratings if they exist
        try:
            with open("reviews.json", "r") as f:
                reviews = json.load(f)
                event_reviews = [r for r in reviews["event_reviews"] if r["event_id"] == event["event_id"]]
                if event_reviews:
                    avg_rating = sum(r["rating"] for r in event_reviews) / len(event_reviews)
                    rating_label = QLabel(f"<b>Μέση Βαθμολογία:</b> {avg_rating:.1f}/5 ({len(event_reviews)} κριτικές)")
                    rating_label.setStyleSheet("font-size: 14px; color: #333;")
                    layout.addWidget(rating_label)
                    
                    # Show last 3 reviews
                    if len(event_reviews) > 0:
                        reviews_group = QGroupBox("Πρόσφατες Κριτικές")
                        reviews_layout = QVBoxLayout()
                        for review in sorted(event_reviews, key=lambda x: x["date"], reverse=True)[:3]:
                            review_text = f"Βαθμολογία: {review['rating']}/5\nΗμερομηνία: {review['date']}\n{review['comments']}"
                            review_label = QLabel(review_text)
                            review_label.setWordWrap(True)
                            reviews_layout.addWidget(review_label)
                        reviews_group.setLayout(reviews_layout)
                        layout.addWidget(reviews_group)
        except:
            pass

        # Add spacer to push buttons to bottom
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Button container
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Add spacing between buttons

        # OK Button
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #D91656;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #640D5F;
            }
        """)
        ok_button.clicked.connect(self.detail_window.close)
        button_layout.addWidget(ok_button)

        # Review Button (only for attendees and if they have a ticket)
        if self.current_user and self.current_user.get("type") == "attendee":
            print(f"User is an attendee")  # Debug print
            try:
                with open("tickets.json", "r") as f:
                    tickets = json.load(f)
                    print(f"Event ID being checked: {event['event_id']}")  # Debug print
                    print(f"User ID being checked: {self.current_user['user_id']}")  # Debug print
                    print(f"Available tickets: {tickets}")  # Debug print
                    
                    user_has_ticket = any(t["user_id"] == self.current_user["user_id"] and 
                                        t["event_id"] == event["event_id"] for t in tickets)
                    print(f"User has ticket: {user_has_ticket}")  # Debug print
                    
                    if user_has_ticket:
                        print("Adding review button")  # Debug print
                        review_button = QPushButton("Αξιολόγηση")
                        review_button.setStyleSheet("""
                            QPushButton {
                                background-color: #D91656;
                                color: white;
                                padding: 10px 20px;
                                font-size: 14px;
                                border-radius: 5px;
                            }
                            QPushButton:hover {
                                background-color: #640D5F;
                            }
                        """)
                        review_button.clicked.connect(lambda: self.show_review_modal("event", event["event_id"]))
                        button_layout.addWidget(review_button)
            except FileNotFoundError:
                print("tickets.json not found")  # Debug print
            except json.JSONDecodeError:
                print("Error decoding tickets.json")  # Debug print

        layout.addLayout(button_layout)
        self.detail_window.show()

    def show_vendor_details(self, vendor_id, event_id=None):
        """Show detailed information about a vendor in a new window."""
        # Load users to get vendor information
        users = load_users()
        vendor = next((u for u in users if u["user_id"] == vendor_id), None)
        
        if not vendor:
            QMessageBox.warning(self, "Error", "Vendor not found.")
            return
            
        detail_window = QWidget()
        detail_window.setWindowTitle(f"Vendor Details: {vendor['name']} {vendor['surname']}")
        detail_window.setGeometry(200, 200, 600, 800)
        
        layout = QVBoxLayout()
        
        # Vendor details
        details_group = QGroupBox("Vendor Details")
        details_layout = QVBoxLayout()
        
        # Add vendor information
        details_layout.addWidget(QLabel(f"Name: {vendor['name']} {vendor['surname']}"))
        details_layout.addWidget(QLabel(f"Email: {vendor['email']}"))
        details_layout.addWidget(QLabel(f"Phone: {vendor['phone']}"))
        
        # Load vendor's services
        services = load_services()
        vendor_services = [s for s in services["services"] if s["vendor_id"] == vendor_id]
        
        if vendor_services:
            services_group = QGroupBox("Services Offered")
            services_layout = QVBoxLayout()
            for service in vendor_services:
                service_label = QLabel(f"{service['name']} - {service['type']}")
                service_label.setWordWrap(True)
                services_layout.addWidget(service_label)
            services_group.setLayout(services_layout)
            details_layout.addWidget(services_group)
        
        # Load and display vendor ratings
        try:
            with open("reviews.json", "r") as f:
                reviews = json.load(f)
                vendor_reviews = [r for r in reviews["vendor_reviews"] if r["vendor_id"] == vendor_id]
                if vendor_reviews:
                    avg_rating = sum(r["rating"] for r in vendor_reviews) / len(vendor_reviews)
                    details_layout.addWidget(QLabel(f"Average Rating: {avg_rating:.1f}/5 ({len(vendor_reviews)} reviews)"))
                    
                    # Show last 3 reviews
                    if len(vendor_reviews) > 0:
                        reviews_group = QGroupBox("Recent Reviews")
                        reviews_layout = QVBoxLayout()
                        for review in sorted(vendor_reviews, key=lambda x: x["date"], reverse=True)[:3]:
                            review_text = f"Rating: {review['rating']}/5\nDate: {review['date']}\n{review['comments']}"
                            review_label = QLabel(review_text)
                            review_label.setWordWrap(True)
                            reviews_layout.addWidget(review_label)
                        reviews_group.setLayout(reviews_layout)
                        details_layout.addWidget(reviews_group)
        except:
            pass  # If reviews.json doesn't exist yet
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Add review button for organizers
        if self.current_user and self.current_user.get("type") == "organizer" and event_id:
            review_btn = QPushButton("Leave Review")
            review_btn.clicked.connect(lambda: self.show_review_modal("vendor", event_id, vendor_id))
            button_layout.addWidget(review_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(detail_window.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        detail_window.setLayout(layout)
        detail_window.show()

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
                # Convert user type to lowercase for consistency
                user["type"] = user["type"].lower()
                self.current_user = user
                
                # Debug print for user login
                print(f"Debug - User logged in: ID={user['user_id']}, Type={user['type']}, Name={user['name']} {user['surname']}")
                
                # Start notification timer
                if hasattr(self, 'notification_timer'):
                    self.notification_timer.start(5000)  # Check every 5 seconds
                
                QMessageBox.information(self, "Σύνδεση", "Συνδεθήκατε με επιτυχία!")
                self.redirect_to_dashboard(user.get("type", "guest"))

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

        # Stop notification timer
        if hasattr(self, 'notification_timer'):
            self.notification_timer.stop()

        # Clean up organizer-specific attributes
        if hasattr(self, 'organizer_events_layout'):
            delattr(self, 'organizer_events_layout')
        if hasattr(self, 'organizer_events_stack'):
            delattr(self, 'organizer_events_stack')
        if hasattr(self, 'organizer_event_details_widget'):
            delattr(self, 'organizer_event_details_widget')
        if hasattr(self, 'organizer_event_details_layout'):
            delattr(self, 'organizer_event_details_layout')

        # Remove private tabs
        for tab_name, tab_widget in self.private_tabs.items():
            self.tabs.removeTab(self.tabs.indexOf(tab_widget))
        self.private_tabs.clear()

        # Remove notifications tab if it exists
        notifications_index = self.get_tab_index("Notifications")
        if notifications_index is not None:
            self.tabs.removeTab(notifications_index)

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
        if user_type == "organizer":
            self.add_organizer_tab()
            i = self.get_tab_index("Organizer")
            self.tabs.setCurrentIndex(i)  # Redirect to Organizer dashboard
        elif user_type == "vendor":
            self.add_vendor_tab()
            i = self.get_tab_index("Vendor")
            self.tabs.setCurrentIndex(i) # Redirect to Vendor dashboard
        elif user_type == "attendee":
            self.add_attendee_tab()
            i = self.get_tab_index("Attendee")
            self.tabs.setCurrentIndex(i)  # Redirect to Attendee dashboard
    #endregion

    #endregion

    # region Organizer Section #

    def add_organizer_tab(self):
        i = self.get_tab_index("Home")
        self.tabs.removeTab(i)
        i = self.get_tab_index("Events")
        self.tabs.removeTab(i)
        
        self.logoff_btn.show()

        # --- Organizer Dashboard Tab --- #
        organizer_tab = QWidget()
        layout_organizer_dashboard = QVBoxLayout(organizer_tab)

        # Header
        label = QLabel("Home Page")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #ff6f61;")
        layout_organizer_dashboard.addWidget(label)

        # Create Event Button
        create_event_btn = AnimatedButton("Create Event")
        create_event_btn.setIcon(qta.icon("fa5s.plus"))
        create_event_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #EB5B00;
            }
        """)
        create_event_btn.clicked.connect(self.open_create_event_modal)
        layout_organizer_dashboard.addWidget(create_event_btn)

        # My Events Button
        my_events_btn = AnimatedButton("My Events")
        my_events_btn.setIcon(qta.icon("fa5s.calendar-alt"))
        my_events_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #EB5B00;
            }
        """)
        my_events_btn.clicked.connect(self.show_organizer_my_events_tab)
        layout_organizer_dashboard.addWidget(my_events_btn)

        # Similar Events Button
        similar_events_btn = AnimatedButton("Similar Events")
        similar_events_btn.setIcon(qta.icon("fa5s.calendar-plus"))
        similar_events_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #EB5B00;
            }
        """)
        similar_events_btn.clicked.connect(self.show_organizer_similar_events_tab)
        layout_organizer_dashboard.addWidget(similar_events_btn)

        # History Button
        history_btn = AnimatedButton("History")
        history_btn.setIcon(qta.icon("fa5s.history"))
        history_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #EB5B00;
            }
        """)
        history_btn.clicked.connect(self.show_organizer_history_tab)
        layout_organizer_dashboard.addWidget(history_btn)

        organizer_tab.setLayout(layout_organizer_dashboard)

        # --- My Events Tab --- #
        my_events_tab = QWidget()
        my_events_layout = QVBoxLayout()
        label = QLabel("My Events")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #D91656;")
        my_events_layout.addWidget(label)
        
        # Add scroll area for events
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        
        events_container = QWidget()
        self.organizer_events_layout = QVBoxLayout(events_container)
        scroll_area.setWidget(events_container)
        my_events_layout.addWidget(scroll_area)
        
        my_events_tab.setLayout(my_events_layout)

        # --- Similar Events Tab --- #
        similar_events_tab = QWidget()
        similar_events_layout = QVBoxLayout()
        label = QLabel("Similar Events")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #D91656;")
        similar_events_layout.addWidget(label)
        similar_events_tab.setLayout(similar_events_layout)

        # --- History Tab --- #
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        label = QLabel("History")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #D91656;")
        history_layout.addWidget(label)
        history_tab.setLayout(history_layout)

        # Add notifications button
        notifications_btn = AnimatedButton("Notifications")
        notifications_btn.setIcon(qta.icon("fa5s.bell"))
        notifications_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #EB5B00;
            }
        """)
        notifications_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(self.get_tab_index("Notifications")))
        layout_organizer_dashboard.addWidget(notifications_btn)

        # Add all tabs
        self.tabs.addTab(organizer_tab, qta.icon("fa5s.user-edit"), "Organizer")
        self.tabs.addTab(my_events_tab, qta.icon("fa5s.calendar-alt"), "My Events")
        self.tabs.addTab(similar_events_tab, qta.icon("fa5s.calendar-plus"), "Similar Events")
        self.tabs.addTab(history_tab, qta.icon("fa5s.history"), "History")
        
        # Add notifications tab with red background
        notifications_tab = NotificationsTab(self)
        self.tabs.addTab(notifications_tab, qta.icon("fa5s.bell"), "Notifications")
        self.tabs.tabBar().setTabTextColor(self.tabs.count() - 1, QColor("#ff6f61"))

        # Save references
        self.private_tabs["Organizer"] = organizer_tab
        self.private_tabs["My Events"] = my_events_tab
        self.private_tabs["Similar Events"] = similar_events_tab
        self.private_tabs["History"] = history_tab

    def add_vendor_tab(self):
        i = self.get_tab_index("Home")
        self.tabs.removeTab(i)
        i = self.get_tab_index("Events")
        self.tabs.removeTab(i)
        
        self.logoff_btn.show()

        vendor_tab = QWidget()
        layout = QVBoxLayout(vendor_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title container
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(20, 20, 20, 0)

        # Title
        label = QLabel("Vendor Dashboard")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #ff6f61;")
        title_layout.addWidget(label)
        layout.addWidget(title_container)

        # Add spacer to push buttons to bottom
        layout.addStretch()

        # Button container
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(20, 0, 20, 20)

        # Add Service Button
        add_service_btn = AnimatedButton("Add Service")
        add_service_btn.setIcon(qta.icon("fa5s.plus-circle"))
        add_service_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #EB5B00;
            }
        """)
        add_service_btn.clicked.connect(self.show_add_service_modal)
        button_layout.addWidget(add_service_btn)

        # Manage Services Button
        manage_services_btn = AnimatedButton("Manage Services")
        manage_services_btn.setIcon(qta.icon("fa5s.cogs"))
        manage_services_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
                margin-top: 5px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #EB5B00;
            }
        """)
        manage_services_btn.clicked.connect(self.show_manage_services)
        button_layout.addWidget(manage_services_btn)

        # My Services Button
        my_services_btn = AnimatedButton("My Services")
        my_services_btn.setIcon(qta.icon("fa5s.list"))
        my_services_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
                margin-top: 5px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #EB5B00;
            }
        """)
        my_services_btn.clicked.connect(self.show_my_services)
        button_layout.addWidget(my_services_btn)

        # Add notifications button
        notifications_btn = AnimatedButton("Notifications")
        notifications_btn.setIcon(qta.icon("fa5s.bell"))
        notifications_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB200;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 10px;
                border: none;
                margin-top: 5px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #EB5B00;
            }
        """)
        notifications_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(self.get_tab_index("Notifications")))
        button_layout.addWidget(notifications_btn)

        layout.addWidget(button_container)
        
        self.tabs.addTab(vendor_tab, qta.icon("fa5s.user-tie"), "Vendor")
        
        # Add notifications tab with red background
        notifications_tab = NotificationsTab(self)
        self.tabs.addTab(notifications_tab, qta.icon("fa5s.bell"), "Notifications")
        self.tabs.tabBar().setTabTextColor(self.tabs.count() - 1, QColor("#ff6f61"))
        
        self.private_tabs["Vendor"] = vendor_tab

    def show_add_service_modal(self):
        """Open the Add Service Modal."""
        self.add_service_modal = AddServicesModal(self)  # Store reference to prevent garbage collection
        self.add_service_modal.setWindowFlags(Qt.Window)  # Make it a proper window
        self.add_service_modal.show()

    def show_manage_services(self):
        """Show the manage services tab."""
        # To be implemented
        QMessageBox.information(self, "Info", "Manage Services functionality coming soon!")

    def show_my_services(self):
        """Show the my services tab."""
        # To be implemented
        QMessageBox.information(self, "Info", "My Services functionality coming soon!")

    #endregion

    # region Attendee  Section #
    def add_attendee_tab(self):
        i = self.get_tab_index("Home")
        self.tabs.removeTab(i)
        i = self.get_tab_index("Events")
        self.tabs.removeTab(i)
        
        self.logoff_btn.show()  # Show the button   

        # --- Attendee Dashboard Tab --- #
        attendee_tab = QWidget()
        layout_attendee_dashboard = QVBoxLayout(attendee_tab)

        #Header
        label = QLabel("Home Page")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #ff6f61;")
        layout_attendee_dashboard.addWidget(label)

        #Find Events Button
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
        find_events_btn.clicked.connect(self.show_events_tab)
        layout_attendee_dashboard.addWidget(find_events_btn)

        # My Events Button
        my_events_btn = AnimatedButton("My Events")
        my_events_btn.setIcon(qta.icon("fa5s.calendar-check"))
        my_events_btn.setStyleSheet("""
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
        my_events_btn.clicked.connect(lambda: self.show_attendee_my_events_tab())
        layout_attendee_dashboard.addWidget(my_events_btn)

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
        my_tickets_btn.clicked.connect(self.show_my_tickets_tab)
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
        
        attendee_tab.setLayout(layout_attendee_dashboard)
        
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
        
        self.show_events_tab
        find_events_tab.setLayout(layout_find_events)
        #endregion

        # --- My Tickets Tab --- #
        my_tickets_tab = QWidget()
        layout_my_tickets = QVBoxLayout()
        label = QLabel("My Tickets")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #ff6f61;")
        layout_my_tickets.addWidget(label)
        # self.create_attendee_my_tickets_tab(layout_my_tickets)
        my_tickets_tab.setLayout(layout_my_tickets)

        # --- My History Tab --- #
        my_history_tab = QWidget()
        layout_my_history = QVBoxLayout()
        label = QLabel("My History")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #ff6f61;")
        layout_my_history.addWidget(label)
        # self.create_attendee_my_history_tab(layout_my_history)
        my_history_tab.setLayout(layout_my_history)
        
        # --- My Events Tab --- #
        my_events_tab = QWidget()
        layout_my_events = QVBoxLayout()
        label = QLabel("My Events")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #D91656;")
        layout_my_events.addWidget(label)
        
        # Add scroll area for events
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        
        events_container = QWidget()
        self.my_events_layout = QVBoxLayout(events_container)
        scroll_area.setWidget(events_container)
        layout_my_events.addWidget(scroll_area)
        
        my_events_tab.setLayout(layout_my_events)

        # Add notifications button
        notifications_btn = AnimatedButton("Notifications")
        notifications_btn.setIcon(qta.icon("fa5s.bell"))
        notifications_btn.setStyleSheet("""
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
        notifications_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(self.get_tab_index("Notifications")))
        layout_attendee_dashboard.addWidget(notifications_btn)

        # Add tabs to the tab widget
        self.tabs.addTab(attendee_tab, qta.icon("fa5s.user-edit"), "Attendee")
        self.tabs.addTab(find_events_tab, qta.icon("fa5s.search"), "Find Events")
        self.tabs.addTab(my_events_tab, qta.icon("fa5s.calendar-check"), "My Events")
        self.tabs.addTab(my_tickets_tab, qta.icon("fa5s.ticket-alt"), "My Tickets")
        self.tabs.addTab(my_history_tab, qta.icon("fa5s.history"), "My History")
        
        # Add notifications tab with red background
        notifications_tab = NotificationsTab(self)
        self.tabs.addTab(notifications_tab, qta.icon("fa5s.bell"), "Notifications")
        self.tabs.tabBar().setTabTextColor(self.tabs.count() - 1, QColor("#ff6f61"))

        # Save references
        self.private_tabs["Attendee"] = attendee_tab
        self.private_tabs["Find Events"] = find_events_tab
        self.private_tabs["My Events"] = my_events_tab
        self.private_tabs["My Tickets"] = my_tickets_tab
        self.private_tabs["My History"] = my_history_tab

    def show_attendee_my_events_tab(self):
        """Show the My Events tab and display events the attendee has tickets for."""
        i = self.get_tab_index("My Events")
        if i is not None:
            self.tabs.setCurrentIndex(i)
            self.display_attendee_my_events()

    def display_attendee_my_events(self):
        """Display events that the attendee has tickets for."""
        # Clear existing events
        while self.my_events_layout.count():
            item = self.my_events_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            # Load tickets
            with open("tickets.json", "r") as f:
                tickets = json.load(f)
            
            # Filter tickets for current user
            user_tickets = [t for t in tickets if t["user_id"] == self.current_user["user_id"]]
            
            # Get events for these tickets
            my_events = [e for e in self.events if any(t["event_id"] == e["event_id"] for t in user_tickets)]
            
            if not my_events:
                no_events_label = QLabel("You don't have any event tickets yet.")
                no_events_label.setStyleSheet("font-size: 14px; color: #666;")
                self.my_events_layout.addWidget(no_events_label)
                return
            
            # Create a stacked widget to hold both the events list and event details
            self.events_stack = QStackedWidget()
            self.my_events_layout.addWidget(self.events_stack)

            # Create the events list widget
            events_list_widget = QWidget()
            events_list_layout = QVBoxLayout(events_list_widget)
            events_list_layout.setSpacing(10)
            events_list_layout.setContentsMargins(0, 0, 0, 0)

            # Create the event details widget
            self.event_details_widget = QWidget()
            self.event_details_layout = QVBoxLayout(self.event_details_widget)

            # Add both widgets to the stack
            self.events_stack.addWidget(events_list_widget)
            self.events_stack.addWidget(self.event_details_widget)
            
            # Sort events by date
            my_events.sort(key=lambda x: datetime.strptime(x["start_date"], "%d/%m/%Y"))
            
            # Display each event in the list
            for event in my_events:
                # Event Container
                event_widget = QWidget()
                event_widget.setStyleSheet("""
                    QWidget#eventContainer {
                        background-color: white;
                        border: none;
                        border-radius: 8px;
                    }
                    QWidget#eventContainer:hover {
                        border: 1px solid #D91656;
                    }
                """)
                event_widget.setObjectName("eventContainer")
                event_layout = QHBoxLayout(event_widget)
                event_layout.setContentsMargins(15, 15, 15, 15)
                
                # Left: Event Image container
                image_container = QWidget()
                image_container.setFixedSize(180, 180)
                image_layout = QVBoxLayout(image_container)
                image_layout.setContentsMargins(0, 0, 0, 0)
                
                image_label = QLabel()
                pixmap = QPixmap(event.get("image", "event_images/default_event.jpg"))
                scaled_pixmap = pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(scaled_pixmap)
                image_label.setAlignment(Qt.AlignVCenter)
                image_layout.addWidget(image_label)
                event_layout.addWidget(image_container)
                
                # Right: Event Details
                details_widget = QWidget()
                details_layout = QVBoxLayout(details_widget)
                details_layout.setSpacing(8)
                details_layout.setContentsMargins(0, 0, 0, 0)
                
                # Event Title
                title_label = QLabel(event["title"])
                title_label.setFont(QFont("Helvetica", 16, QFont.Bold))
                title_label.setStyleSheet("color: #D91656;")
                details_layout.addWidget(title_label)
                
                details_label = QLabel(
                    f"<b>Ημερομηνία:</b> {event['start_date']} - {event['end_date']}<br>"
                    f"<b>Ώρα Έναρξης:</b> {event['start_time']}<br>"
                    f"<b>Τοποθεσία:</b> {event['location']}<br>"
                    f"<b>Τύπος:</b> {event['type']}"
                )
                details_label.setStyleSheet("font-size: 14px; color: #333;")
                details_label.setWordWrap(True)
                details_layout.addWidget(details_label)
                
                # Add stretch to push button to bottom
                details_layout.addStretch()
                
                # View More Button
                view_more_btn = QPushButton("Περισσότερα")
                view_more_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #D91656;
                        color: white;
                        padding: 8px 15px;
                        border-radius: 5px;
                        max-width: 120px;
                    }
                    QPushButton:hover {
                        background-color: #640D5F;
                    }
                """)
                view_more_btn.clicked.connect(lambda checked, e=event: self.show_event_details_in_stack(e))
                details_layout.addWidget(view_more_btn, alignment=Qt.AlignRight)
                
                event_layout.addWidget(details_widget, stretch=1)
                
                # Add shadow effect
                shadow = QGraphicsDropShadowEffect()
                shadow.setBlurRadius(10)
                shadow.setColor(QColor(0, 0, 0, 30))
                shadow.setOffset(0, 2)
                event_widget.setGraphicsEffect(shadow)
                
                events_list_layout.addWidget(event_widget)
                
        except FileNotFoundError:
            error_label = QLabel("No ticket information found.")
            error_label.setStyleSheet("font-size: 14px; color: #666;")
            self.my_events_layout.addWidget(error_label)

    def show_event_details_in_stack(self, event):
        """Show event details in the stacked widget."""
        # Clear previous content
        while self.event_details_layout.count():
            item = self.event_details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create a scroll area for the content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Event Title
        title = QLabel(event["title"])
        title.setFont(QFont("Helvetica", 24, QFont.Bold))
        title.setStyleSheet("color: #D91656;")
        content_layout.addWidget(title, alignment=Qt.AlignCenter)
        
        # Event Image
        image_label = QLabel()
        pixmap = QPixmap(event.get("image", "event_images/default_event.jpg"))
        scaled_pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        content_layout.addWidget(image_label, alignment=Qt.AlignCenter)
        
        # Event Details Section
        details_group = QGroupBox("Στοιχεία Εκδήλωσης")
        details_group.setStyleSheet("""
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
        details_layout = QVBoxLayout()
        
        details_text = f"""
        <p style='font-size: 16px;'>
        <b>Ημερομηνία:</b> {event['start_date']} - {event['end_date']}<br>
        <b>Ώρα Έναρξης:</b> {event['start_time']}<br>
        <b>Τοποθεσία:</b> {event['location']}<br>
        <b>Τύπος:</b> {event['type']}<br>
        <b>Περιγραφή:</b> {event.get('description', 'Δεν υπάρχει διαθέσιμη περιγραφή')}<br>
        <b>Διοργανωτής:</b> {event.get('organizer', 'Άγνωστος')}
        </p>
        """
        
        details_label = QLabel(details_text)
        details_label.setWordWrap(True)
        details_label.setStyleSheet("color: #333;")
        details_layout.addWidget(details_label)
        
        # Add ticket types information
        if event.get("ticket_types"):
            ticket_info = "<b>Διαθέσιμα Εισιτήρια:</b><br>"
            for ticket in event["ticket_types"]:
                ticket_info += f"• {ticket['type']}: {ticket['price']}€ ({ticket['total_quantity']} διαθέσιμα)<br>"
            ticket_label = QLabel(ticket_info)
            ticket_label.setWordWrap(True)
            ticket_label.setStyleSheet("color: #333; font-size: 14px;")
            details_layout.addWidget(ticket_label)
        
        details_group.setLayout(details_layout)
        content_layout.addWidget(details_group)

        # Add ratings if they exist
        try:
            with open("reviews.json", "r") as f:
                reviews = json.load(f)
                event_reviews = [r for r in reviews["event_reviews"] if r["event_id"] == event["event_id"]]
                if event_reviews:
                    # Reviews Section
                    reviews_group = QGroupBox("Κριτικές")
                    reviews_group.setStyleSheet("""
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
                    reviews_layout = QVBoxLayout()
                    
                    # Average Rating
                    avg_rating = sum(r["rating"] for r in event_reviews) / len(event_reviews)
                    rating_text = f"""
                    <p style='font-size: 16px;'>
                    <b>Μέση Βαθμολογία:</b> {avg_rating:.1f}/5 ({len(event_reviews)} κριτικές)
                    </p>
                    """
                    rating_label = QLabel(rating_text)
                    rating_label.setStyleSheet("color: #333;")
                    reviews_layout.addWidget(rating_label)
                    
                    # Show last 3 reviews
                    if len(event_reviews) > 0:
                        reviews_layout.addWidget(QLabel("<b>Πρόσφατες Κριτικές:</b>"))
                        for review in sorted(event_reviews, key=lambda x: x["date"], reverse=True)[:3]:
                            review_text = f"""
                            <div style='background-color: #f8f8f8; padding: 10px; border-radius: 5px; margin: 5px 0;'>
                            <p style='font-size: 14px; margin: 5px 0;'>
                            <b>Βαθμολογία:</b> {review['rating']}/5<br>
                            <b>Ημερομηνία:</b> {review['date']}<br>
                            <b>Σχόλια:</b><br>{review['comments']}
                            </p>
                            </div>
                            """
                            review_label = QLabel(review_text)
                            review_label.setWordWrap(True)
                            review_label.setStyleSheet("color: #333;")
                            reviews_layout.addWidget(review_label)
                    
                        reviews_group.setLayout(reviews_layout)
                    content_layout.addWidget(reviews_group)
        except:
            pass

        # Buttons Container
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        
        # Center container for buttons
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setSpacing(20)

        # Back Button
        back_btn = QPushButton("Πίσω")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b5b95;
                color: white;
                padding: 12px 30px;
                font-size: 16px;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #524778;
            }
        """)
        back_btn.clicked.connect(lambda: self.events_stack.setCurrentIndex(0))
        center_layout.addWidget(back_btn)

        # Review Button (only if they have a ticket)
        try:
            with open("tickets.json", "r") as f:
                tickets = json.load(f)
                user_has_ticket = any(t["user_id"] == self.current_user["user_id"] and 
                                    t["event_id"] == event["event_id"] for t in tickets)
                if user_has_ticket:
                    review_button = QPushButton("Αξιολόγηση")
                    review_button.setStyleSheet("""
                        QPushButton {
                            background-color: #D91656;
                            color: white;
                            padding: 12px 30px;
                            font-size: 16px;
                            border-radius: 5px;
                            min-width: 150px;
                        }
                        QPushButton:hover {
                            background-color: #640D5F;
                        }
                    """)
                    review_button.clicked.connect(lambda: self.show_review_modal("event", event["event_id"]))
                    center_layout.addWidget(review_button)
        except FileNotFoundError:
            print("tickets.json not found")
        except json.JSONDecodeError:
            print("Error decoding tickets.json")

        # Add center widget to main layout with stretches on both sides
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(center_widget)
        buttons_layout.addStretch(1)
        
        content_layout.addWidget(buttons_container)
        
        # Set the content widget to the scroll area
        scroll.setWidget(content_widget)
        self.event_details_layout.addWidget(scroll)

        # Switch to the details view
        self.events_stack.setCurrentIndex(1)

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
        """Show and load the Find Events tab content."""
        print("Debug - Loading Find Events tab")
        
        # Get the Find Events tab
        find_events_tab = self.private_tabs.get("Find Events")
        if not find_events_tab:
            print("Debug - Find Events tab not found")
            return
            
        self.tabs.setCurrentWidget(find_events_tab)
        
        # Get the current date for filtering
        current_date = datetime.now().date()
        print(f"Debug - Current date: {current_date}")
        
        # Filter upcoming events
        upcoming_events = [
            event for event in self.events 
            if datetime.strptime(event["start_date"], "%d/%m/%Y").date() >= current_date
        ]
        
        print(f"Debug - Found {len(upcoming_events)} upcoming events")
        
        # Clear existing layout
        layout = find_events_tab.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clean up old stacked widget and event details widget if they exist
        if hasattr(self, 'attendee_events_stack'):
            self.attendee_events_stack.deleteLater()
            delattr(self, 'attendee_events_stack')
        if hasattr(self, 'attendee_event_details_widget'):
            self.attendee_event_details_widget.deleteLater()
            delattr(self, 'attendee_event_details_widget')
                
        # Add title
        label = QLabel("Find Events")
        label.setFont(QFont("Helvetica", 20, QFont.Bold))
        label.setStyleSheet("color: #ff6f61;")
        layout.addWidget(label)
        
        # Create a stacked widget to hold both the events list and event details
        self.attendee_events_stack = QStackedWidget()
        layout.addWidget(self.attendee_events_stack)

        # Create the events list widget
        events_list_widget = QWidget()
        events_list_layout = QVBoxLayout(events_list_widget)
        events_list_layout.setSpacing(10)
        events_list_layout.setContentsMargins(0, 0, 0, 0)

        # Create the event details widget with proper initialization
        self.attendee_event_details_widget = QWidget()
        self.attendee_event_details_widget.setStyleSheet("background-color: white;")
        self.attendee_event_details_layout = QVBoxLayout(self.attendee_event_details_widget)
        self.attendee_event_details_layout.setSpacing(20)
        self.attendee_event_details_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add scroll area for events
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        
        events_container = QWidget()
        events_layout = QVBoxLayout(events_container)
        events_layout.setSpacing(10)
        
        if not upcoming_events:
            no_events_label = QLabel("No upcoming events found.")
            no_events_label.setStyleSheet("font-size: 14px; color: #666;")
            events_layout.addWidget(no_events_label)
        else:
            # Sort events by date
            upcoming_events.sort(key=lambda x: datetime.strptime(x["start_date"], "%d/%m/%Y"))
            
            # Add each event
            for event in upcoming_events:
                self.create_event_widget_for_attendee(event, events_layout)
        
        scroll_area.setWidget(events_container)
        events_list_layout.addWidget(scroll_area)

        # Add both widgets to the stack
        self.attendee_events_stack.addWidget(events_list_widget)
        self.attendee_events_stack.addWidget(self.attendee_event_details_widget)
        
        # Show the events list
        self.attendee_events_stack.setCurrentIndex(0)

    def create_event_widget_for_attendee(self, event, parent_layout):
        """Create a widget for an individual event in the attendee's list."""
        # Create event widget
        event_widget = QWidget()
        event_widget.setStyleSheet("""
            QWidget#eventContainer {
                background-color: white;
                border: 1px solid transparent;
                border-radius: 8px;
            }
            QWidget#eventContainer:hover {
                border: 1px solid #D91656;
            }
        """)
        event_widget.setObjectName("eventContainer")
        event_layout = QHBoxLayout(event_widget)
        event_layout.setContentsMargins(15, 10, 15, 15)
        event_layout.setSpacing(20)
        
        # Image container
        image_container = QWidget()
        image_container.setFixedSize(180, 180)
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(0)
        
        # Event image
        image_label = QLabel()
        image = QPixmap(event.get("image", "event_images/default_event.jpg"))
        scaled_pixmap = image.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        image_layout.addWidget(image_label, 0, Qt.AlignTop)
        event_layout.addWidget(image_container)
        
        # Details container
        details_container = QWidget()
        details_container_layout = QHBoxLayout(details_container)
        details_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Details widget
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setSpacing(5)
        
        # Event title
        title_label = QLabel(event["title"])
        title_label.setFont(QFont("Helvetica", 16, QFont.Bold))
        title_label.setStyleSheet("color: #D91656;")
        details_layout.addWidget(title_label)
        
        # Event details
        details_label = QLabel(
            f"<b>Ημερομηνία:</b> {event['start_date']} - {event['end_date']}<br>"
            f"<b>Ώρα Έναρξης:</b> {event['start_time']}<br>"
            f"<b>Τοποθεσία:</b> {event['location']}<br>"
            f"<b>Τύπος:</b> {event['type']}"
        )
        details_label.setStyleSheet("font-size: 14px; color: #333;")
        details_label.setWordWrap(True)
        details_layout.addWidget(details_label)
        
        # Add stretch to push button to bottom
        details_layout.addStretch()
        
        # View More Button
        view_more_btn = QPushButton("Περισσότερα")
        view_more_btn.setStyleSheet("""
            QPushButton {
                background-color: #D91656;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                max-width: 120px;
            }
            QPushButton:hover {
                background-color: #640D5F;
            }
        """)
        view_more_btn.clicked.connect(lambda checked, e=event: self.show_attendee_event_details_in_stack(e))
        details_layout.addWidget(view_more_btn, alignment=Qt.AlignRight)
        
        details_container_layout.addWidget(details_widget, stretch=1)
        event_layout.addWidget(details_container)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        event_widget.setGraphicsEffect(shadow)
        
        parent_layout.addWidget(event_widget)

    def show_attendee_event_details_in_stack(self, event):
        """Show event details in the stacked widget for attendees with ticket purchase option."""
        # Reload the event data to get the latest ticket quantities
        try:
            with open("events.json", "r", encoding="utf-8") as f:
                events = json.load(f)
                for e in events:
                    if e["event_id"] == event["event_id"]:
                        event = e
                        break
        except Exception as e:
            print(f"Error reloading event data: {str(e)}")

        # Clear previous content
        while self.attendee_event_details_layout.count():
            item = self.attendee_event_details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create a scroll area for the content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Event Title
        title = QLabel(event["title"])
        title.setFont(QFont("Helvetica", 24, QFont.Bold))
        title.setStyleSheet("color: #D91656;")
        content_layout.addWidget(title, alignment=Qt.AlignCenter)
        
        # Event Image
        image_label = QLabel()
        pixmap = QPixmap(event.get("image", "event_images/default_event.jpg"))
        scaled_pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        content_layout.addWidget(image_label, alignment=Qt.AlignCenter)
        
        # Event Details Section
        details_group = QGroupBox("Στοιχεία Εκδήλωσης")
        details_group.setStyleSheet("""
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
        details_layout = QVBoxLayout()
        
        details_text = f"""
        <p style='font-size: 16px;'>
        <b>Ημερομηνία:</b> {event['start_date']} - {event['end_date']}<br>
        <b>Ώρα Έναρξης:</b> {event['start_time']}<br>
        <b>Τοποθεσία:</b> {event['location']}<br>
        <b>Τύπος:</b> {event['type']}<br>
        <b>Περιγραφή:</b> {event.get('description', 'Δεν υπάρχει διαθέσιμη περιγραφή')}<br>
        <b>Διοργανωτής:</b> {event.get('organizer', 'Άγνωστος')}
        </p>
        """
        
        details_label = QLabel(details_text)
        details_label.setWordWrap(True)
        details_label.setStyleSheet("color: #333;")
        details_layout.addWidget(details_label)
        
        # Add ticket types information
        if event.get("ticket_types"):
            ticket_info = "<b>Διαθέσιμα Εισιτήρια:</b><br>"
            for ticket in event["ticket_types"]:
                ticket_info += f"• {ticket['type']}: {ticket['price']}€ ({ticket['total_quantity']} διαθέσιμα)<br>"
            ticket_label = QLabel(ticket_info)
            ticket_label.setWordWrap(True)
            ticket_label.setStyleSheet("color: #333; font-size: 14px;")
            details_layout.addWidget(ticket_label)
        
        details_group.setLayout(details_layout)
        content_layout.addWidget(details_group)

        # Add ratings if they exist
        try:
            with open("reviews.json", "r") as f:
                reviews = json.load(f)
                event_reviews = [r for r in reviews["event_reviews"] if r["event_id"] == event["event_id"]]
                if event_reviews:
                    # Reviews Section
                    reviews_group = QGroupBox("Κριτικές")
                    reviews_group.setStyleSheet("""
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
                    reviews_layout = QVBoxLayout()
                    
                    # Average Rating
                    avg_rating = sum(r["rating"] for r in event_reviews) / len(event_reviews)
                    rating_text = f"""
                    <p style='font-size: 16px;'>
                    <b>Μέση Βαθμολογία:</b> {avg_rating:.1f}/5 ({len(event_reviews)} κριτικές)
                    </p>
                    """
                    rating_label = QLabel(rating_text)
                    rating_label.setStyleSheet("color: #333;")
                    reviews_layout.addWidget(rating_label)
                    
                    # Show last 3 reviews
                    if len(event_reviews) > 0:
                        reviews_layout.addWidget(QLabel("<b>Πρόσφατες Κριτικές:</b>"))
                        for review in sorted(event_reviews, key=lambda x: x["date"], reverse=True)[:3]:
                            review_text = f"""
                            <div style='background-color: #f8f8f8; padding: 10px; border-radius: 5px; margin: 5px 0;'>
                            <p style='font-size: 14px; margin: 5px 0;'>
                            <b>Βαθμολογία:</b> {review['rating']}/5<br>
                            <b>Ημερομηνία:</b> {review['date']}<br>
                            <b>Σχόλια:</b><br>{review['comments']}
                            </p>
                            </div>
                            """
                            review_label = QLabel(review_text)
                            review_label.setWordWrap(True)
                            review_label.setStyleSheet("color: #333;")
                            reviews_layout.addWidget(review_label)
                    
                    reviews_group.setLayout(reviews_layout)
                    content_layout.addWidget(reviews_group)
        except:
            pass

        # Buttons Container
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        
        # Center container for buttons
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setSpacing(20)

        # Back Button
        back_btn = QPushButton("Πίσω")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b5b95;
                color: white;
                padding: 12px 30px;
                font-size: 16px;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #524778;
            }
        """)
        back_btn.clicked.connect(lambda: self.attendee_events_stack.setCurrentIndex(0))
        center_layout.addWidget(back_btn)

        # Buy Tickets Button
        buy_tickets_btn = QPushButton("Αγορά Εισιτηρίων")
        buy_tickets_btn.setStyleSheet("""
            QPushButton {
                background-color: #D91656;
                color: white;
                padding: 12px 30px;
                font-size: 16px;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #640D5F;
            }
        """)
        buy_tickets_btn.clicked.connect(lambda: self.show_ticket_purchase_modal(event))
        center_layout.addWidget(buy_tickets_btn)

        # Add center widget to main layout with stretches on both sides
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(center_widget)
        buttons_layout.addStretch(1)
        
        content_layout.addWidget(buttons_container)
        
        # Set the content widget to the scroll area
        scroll.setWidget(content_widget)
        self.attendee_event_details_layout.addWidget(scroll)

        # Switch to the details view
        self.attendee_events_stack.setCurrentIndex(1)

    def show_ticket_purchase_modal(self, event):
        """Show the ticket purchase modal."""
        from ticket_purchase import TicketPurchaseModal
        self.ticket_purchase_modal = TicketPurchaseModal(event, self.current_user, self)
        self.ticket_purchase_modal.show()

    def reload_events_data(self):
        """Reload events data from file and refresh the current view."""
        self.events = load_events()
        
        # Refresh the current Find Events view if it's active
        current_tab = self.tabs.currentWidget()
        find_events_tab = self.private_tabs.get("Find Events")
        
        if current_tab == find_events_tab and hasattr(self, 'attendee_events_stack'):
            # If we're currently viewing the events list, refresh it
            if self.attendee_events_stack.currentIndex() == 0:
                self.show_events_tab()
            # If we're viewing event details, we might want to update the ticket info
            # but for now, we'll just keep the current view

    def show_login_tab(self):
        i= self.get_tab_index("Login")
        self.tabs.setCurrentIndex(i)

    def show_organizer_my_events_tab(self):
        """Show the My Events tab and display events the organizer has created."""
        print("Debug - Loading organizer my events tab")
        
        # Security check: Only allow organizers to access this function
        if not self.current_user or self.current_user.get("type") != "organizer":
            print(f"Debug - Access denied. User type: {self.current_user.get('type') if self.current_user else 'None'}")
            QMessageBox.warning(self, "Access Denied", "Only organizers can access this functionality.")
            return
        
        # Switch to the My Events tab
        my_events_tab = self.private_tabs.get("My Events")
        if not my_events_tab:
            print("Debug - My Events tab not found")
            return
            
        self.tabs.setCurrentWidget(my_events_tab)
        
        # Ensure we have the organizer_events_layout
        if not hasattr(self, 'organizer_events_layout'):
            print("Debug - Creating new organizer_events_layout")
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setStyleSheet("border: none;")
            
            events_container = QWidget()
            self.organizer_events_layout = QVBoxLayout(events_container)
            scroll_area.setWidget(events_container)
            my_events_tab.layout().addWidget(scroll_area)
        
        # Clear existing events and widgets
        while self.organizer_events_layout.count():
            item = self.organizer_events_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clean up old stacked widget and event details widget if they exist
        if hasattr(self, 'organizer_events_stack'):
            self.organizer_events_stack.deleteLater()
            delattr(self, 'organizer_events_stack')
        if hasattr(self, 'organizer_event_details_widget'):
            self.organizer_event_details_widget.deleteLater()
            delattr(self, 'organizer_event_details_widget')
        
        print("Debug - Loading events for organizer:", self.current_user["user_id"])
        # Filter events created by the current user
        my_events = [event for event in self.events if event.get("organizer_id") == self.current_user["user_id"]]
        
        if not my_events:
            print("Debug - No events found for organizer")
            no_events_label = QLabel("You haven't created any events yet.")
            no_events_label.setStyleSheet("font-size: 14px; color: #666;")
            self.organizer_events_layout.addWidget(no_events_label)
            return
        
        print(f"Debug - Found {len(my_events)} events")
        
        # Create a stacked widget to hold both the events list and event details
        self.organizer_events_stack = QStackedWidget()
        self.organizer_events_layout.addWidget(self.organizer_events_stack)

        # Create the events list widget
        events_list_widget = QWidget()
        events_list_layout = QVBoxLayout(events_list_widget)
        events_list_layout.setSpacing(10)
        events_list_layout.setContentsMargins(0, 0, 0, 0)

        # Create the event details widget with proper initialization
        self.organizer_event_details_widget = QWidget()
        self.organizer_event_details_widget.setStyleSheet("background-color: white;")
        self.organizer_event_details_layout = QVBoxLayout(self.organizer_event_details_widget)
        self.organizer_event_details_layout.setSpacing(20)
        self.organizer_event_details_layout.setContentsMargins(20, 20, 20, 20)

        # Sort events by date
        my_events.sort(key=lambda x: datetime.strptime(x["start_date"], "%d/%m/%Y"))
        
        # Add events to the list
        for event in my_events:
            self.create_event_widget_for_organizer(event, events_list_layout)

        # Add both widgets to the stack
        self.organizer_events_stack.addWidget(events_list_widget)
        self.organizer_events_stack.addWidget(self.organizer_event_details_widget)
        
        # Show the events list
        self.organizer_events_stack.setCurrentIndex(0)

    def create_event_widget_for_organizer(self, event, parent_layout):
        """Create a widget for an individual event in the organizer's list."""
        # Create event widget
        event_widget = QWidget()
        event_widget.setStyleSheet("""
            QWidget#eventContainer {
                background-color: white;
                border: 1px solid transparent;
                border-radius: 8px;
            }
            QWidget#eventContainer:hover {
                border: 1px solid #D91656;
            }
        """)
        event_widget.setObjectName("eventContainer")
        event_layout = QHBoxLayout(event_widget)
        event_layout.setContentsMargins(15, 10, 15, 15)
        
        # Image container
        image_container = QWidget()
        image_container.setFixedSize(180, 180)
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        # Event image
        image_label = QLabel()
        image = QPixmap(event.get("image", "event_images/default_event.jpg"))
        scaled_pixmap = image.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        image_layout.setAlignment(Qt.AlignTop)
        image_layout.addWidget(image_label)
        event_layout.addWidget(image_container)
        
        # Add some spacing between image and info
        event_layout.addSpacing(20)
        
        # Details container
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(0, 5, 0, 0)
        details_layout.setSpacing(5)
        
        # Event title
        title_label = QLabel(event["title"])
        title_label.setFont(QFont("Helvetica", 16, QFont.Bold))
        title_label.setStyleSheet("color: #D91656;")
        details_layout.addWidget(title_label)
        # Event details
        details_label = QLabel(
            f"<b>Ημερομηνία:</b> {event['start_date']} - {event['end_date']}<br>"
            f"<b>Ώρα Έναρξης:</b> {event['start_time']}<br>"
            f"<b>Τοποθεσία:</b> {event['location']}<br>"
                f"<b>Τύπος:</b> {event['type']}"
            )
        details_label.setStyleSheet("font-size: 14px; color: #333;")
        details_label.setWordWrap(True)
        details_layout.addWidget(details_label)
        # Add stretch to push button to bottom
        details_layout.addStretch()
        # View More Button
        view_more_btn = QPushButton("Περισσότερα")
        view_more_btn.setStyleSheet("""
            QPushButton {
                background-color: #D91656;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                max-width: 120px;
            }
            QPushButton:hover {
                background-color: #640D5F;
            }
        """)
        view_more_btn.clicked.connect(lambda checked, e=event: self.show_organizer_event_details_in_stack(e))
        details_layout.addWidget(view_more_btn, alignment=Qt.AlignRight)
        
        event_layout.addWidget(details_container, stretch=1)
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        event_widget.setGraphicsEffect(shadow)
        
        parent_layout.addWidget(event_widget)

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

    def show_add_service_modal(self):
        """Open the Add Service Modal."""
        self.add_service_modal = AddServicesModal(self)  # Store reference to prevent garbage collection
        self.add_service_modal.setWindowFlags(Qt.Window)  # Make it a proper window
        self.add_service_modal.show()

    def show_review_modal(self, review_type, event_id, vendor_id=None):
        """Show the review modal for events or vendors."""
        if review_type == "event":
            # Get event details
            event = next((e for e in self.events if e["event_id"] == event_id), None)
            if not event:
                return
            
            # Check if event has already happened
            event_date = datetime.strptime(event["start_date"], "%d/%m/%Y").date()
            if event_date > datetime.now().date():
                QMessageBox.warning(
                    self,
                    "Warning",
                    "You cannot review an event that hasn't taken place yet."
                )
                return
            
            # Show review modal
            from leave_review import LeaveReviewModal
            self.review_modal = LeaveReviewModal(
                parent=self,
                review_type="event",
                event_id=event_id,
                user_id=self.current_user["user_id"]
            )
            self.review_modal.show()
    
        elif review_type == "vendor":
            # Get event details
            event = next((e for e in self.events if e["event_id"] == event_id), None)
            if not event:
                return
            
            # Check if event has already happened
            event_date = datetime.strptime(event["start_date"], "%d/%m/%Y").date()
            if event_date > datetime.now().date():
                QMessageBox.warning(
                    self,
                    "Warning",
                    "You cannot review a vendor before the event has taken place."
                )
                return
            
            # Check if the current user is the organizer of this event
            if event.get("organizer_id") != self.current_user["user_id"]:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Only the event organizer can review the vendor."
                )
                return
            
            # Show review modal
            from leave_review import LeaveReviewModal
            self.review_modal = LeaveReviewModal(
                parent=self,
                review_type="vendor",
                event_id=event_id,
                vendor_id=vendor_id,
                user_id=self.current_user["user_id"]
            )
            self.review_modal.show()

    def show_event_details_modal(self, event, show_vendor_review=False):
        """Show event details in a modal window with vendor information and review functionality."""
        modal = QDialog(self)
        modal.setWindowTitle(event["title"])
        modal.setMinimumWidth(600)
        modal.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Event Image
        image_label = QLabel()
        image = QPixmap(event.get("image", "event_images/default_event.jpg"))
        image_label.setPixmap(image.scaled(400, 300, Qt.KeepAspectRatio))
        layout.addWidget(image_label, alignment=Qt.AlignCenter)
        
        # Event Details
        details_label = QLabel(
            f"<h2>{event['title']}</h2>"
            f"<p><b>Ημερομηνία:</b> {event['start_date']} - {event['end_date']}</p>"
            f"<p><b>Ώρα Έναρξης:</b> {event['start_time']}</p>"
            f"<p><b>Τοποθεσία:</b> {event['location']}</p>"
            f"<p><b>Τύπος:</b> {event['type']}</p>"
            f"<p><b>Περιγραφή:</b> {event['description']}</p>"
        )
        details_label.setStyleSheet("font-size: 14px; color: #333;")
        details_label.setWordWrap(True)
        layout.addWidget(details_label)
        
        # Vendor Information
        vendor_info = QWidget()
        vendor_layout = QVBoxLayout(vendor_info)
        vendor_layout.setSpacing(10)
        
        vendor_title = QLabel("<h3>Πληροφορίες Vendor</h3>")
        vendor_title.setStyleSheet("color: #333;")
        vendor_layout.addWidget(vendor_title)
        
        # Load vendor information
        try:
            with open("services.json", "r") as f:
                services = json.load(f)
                event_services = [s for s in services["services"] if s.get("event_id") == event["event_id"]]
                
                if event_services:
                    for service in event_services:
                        vendor_details = QLabel(
                            f"<p><b>Όνομα:</b> {service['vendor_name']}</p>"
                            f"<p><b>Υπηρεσία:</b> {service['name']}</p>"
                            f"<p><b>Τύπος:</b> {service['type']}</p>"
                            f"<p><b>Περιγραφή:</b> {service['description']}</p>"
                            f"<p><b>Τιμολόγηση:</b> {service['price']}€ ({service['pricing_type']})</p>"
                        )
                        vendor_details.setStyleSheet("font-size: 14px; color: #333;")
                        vendor_details.setWordWrap(True)
                        vendor_layout.addWidget(vendor_details)
                        
                        if show_vendor_review:
                            # Check if event has passed
                            event_date = datetime.strptime(event["start_date"], "%d/%m/%Y").date()
                            if event_date <= datetime.now().date():
                                review_btn = QPushButton("Αξιολόγηση Vendor")
                                review_btn.setStyleSheet("""
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
                                review_btn.clicked.connect(
                                    lambda checked, e=event["event_id"], v=service["vendor_id"]: 
                                    self.show_review_modal("vendor", e, v)
                                )
                                vendor_layout.addWidget(review_btn)
                                
                                # Add vendor ratings if they exist
                                try:
                                    with open("reviews.json", "r") as f:
                                        reviews = json.load(f)
                                        vendor_reviews = [r for r in reviews["vendor_reviews"] 
                                                        if r["vendor_id"] == service["vendor_id"]]
                                        if vendor_reviews:
                                            avg_rating = sum(r["rating"] for r in vendor_reviews) / len(vendor_reviews)
                                            rating_label = QLabel(
                                                f"<p><b>Μέση Βαθμολογία Vendor:</b> {avg_rating:.1f}/5 "
                                                f"({len(vendor_reviews)} κριτικές)</p>"
                                            )
                                            rating_label.setStyleSheet("font-size: 14px; color: #333;")
                                            vendor_layout.addWidget(rating_label)
                                except:
                                    pass
                            else:
                                notice = QLabel(
                                    "Η αξιολόγηση του vendor θα είναι διαθέσιμη μετά την ολοκλήρωση της εκδήλωσης."
                                )
                                notice.setStyleSheet("font-size: 14px; color: #666; font-style: italic;")
                                notice.setWordWrap(True)
                                vendor_layout.addWidget(notice)
                else:
                    no_vendor = QLabel("Δεν έχουν ορισθεί vendors για την εκδήλωση ακόμα.")
                    no_vendor.setStyleSheet("font-size: 14px; color: #666; font-style: italic;")
                    vendor_layout.addWidget(no_vendor)
        except Exception as e:
            error_label = QLabel("Σφάλμα κατά τη φόρτωση των πληροφοριών του vendor.")
            error_label.setStyleSheet("font-size: 14px; color: #D91656;")
            vendor_layout.addWidget(error_label)
        
        layout.addWidget(vendor_info)
        
        # Close Button
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
        close_btn.clicked.connect(modal.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        modal.setLayout(layout)
        modal.exec_()

    def show_organizer_event_details_in_stack(self, event):
        """Show event details in the stack for organizers."""
        print(f"Debug - Showing details for event {event['event_id']}")
        
        # Security check: Only allow organizers to access this function
        if not self.current_user or self.current_user.get("type") != "organizer":
            print(f"Debug - Access denied. User type: {self.current_user.get('type') if self.current_user else 'None'}")
            QMessageBox.warning(self, "Access Denied", "Only organizers can access this functionality.")
            return
        
        # Clear previous content
        while self.organizer_event_details_layout.count():
            item = self.organizer_event_details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            
        # Create a scroll area for the content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Event Title
        title = QLabel(event["title"])
        title.setFont(QFont("Helvetica", 24, QFont.Bold))
        title.setStyleSheet("color: #D91656;")
        content_layout.addWidget(title, alignment=Qt.AlignCenter)
        
        # Event Image
        image_label = QLabel()
        pixmap = QPixmap(event.get("image", "event_images/default_event.jpg"))
        scaled_pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(image_label, alignment=Qt.AlignCenter)
        
        # Event Details Section
        details_group = QGroupBox("Στοιχεία Εκδήλωσης")
        details_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 5px;
            }
            QGroupBox::title {
                color: #D91656;
                padding: 0 10px;
            }
        """)
        details_layout = QVBoxLayout()
        
        details_text = f"""
        <p style='font-size: 16px;'>
        <b>Ημερομηνία:</b> {event['start_date']} - {event['end_date']}<br>
        <b>Ώρα Έναρξης:</b> {event['start_time']}<br>
        <b>Τοποθεσία:</b> {event['location']}<br>
        <b>Τύπος:</b> {event['type']}<br>
        <b>Περιγραφή:</b> {event.get('description', 'Δεν υπάρχει διαθέσιμη περιγραφή')}<br>
        <b>Αριθμός Ατόμων:</b> {event.get('max_attendees', 'Απεριόριστος')}
        </p>
        """
        
        details_label = QLabel(details_text)
        details_label.setWordWrap(True)
        details_label.setStyleSheet("color: #333;")
        details_layout.addWidget(details_label)
        details_group.setLayout(details_layout)
        content_layout.addWidget(details_group)
        
        # Load vendor information
        try:
            with open("services.json", "r", encoding='utf-8') as f:
                services = json.load(f)["services"]
                event_services = [s for s in services if s.get("event_id") == event["event_id"]]
                
            if event_services:
                # Vendor Information Section
                vendor_group = QGroupBox("Πληροφορίες Vendor")
                vendor_group.setStyleSheet("""
                    QGroupBox {
                        font-size: 16px;
                        padding: 10px;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        margin-top: 5px;
                    }
                    QGroupBox::title {
                        color: #D91656;
                        padding: 0 10px;
                    }
                """)
                vendor_layout = QVBoxLayout()
                
                # Display vendor information and add review button
                for service in event_services:
                    vendor_info = QLabel(
                        f"""
                        <p style='font-size: 16px; margin: 5px 0;'>
                        <b>Όνομα Vendor:</b> {service.get('vendor_name', 'Μη διαθέσιμο')}<br>
                        <b>Υπηρεσία:</b> {service.get('name', 'Μη διαθέσιμο')}<br>
                        <b>Τύπος:</b> {service.get('type', 'Μη διαθέσιμο')}<br>
                        <b>Περιγραφή:</b> {service.get('description', 'Μη διαθέσιμο')}
                        </p>
                        """
                    )
                    vendor_info.setWordWrap(True)
                    vendor_layout.addWidget(vendor_info)
                
                vendor_group.setLayout(vendor_layout)
                content_layout.addWidget(vendor_group)
                
                # Buttons Container (outside the vendor group)
                buttons_container = QWidget()
                buttons_layout = QHBoxLayout(buttons_container)
                
                # Center container for buttons
                center_widget = QWidget()
                center_layout = QHBoxLayout(center_widget)
                center_layout.setSpacing(20)
                
                # Back Button (Left)
                back_btn = QPushButton("Πίσω")
                back_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #6b5b95;
                        color: white;
                        padding: 12px 30px;
                        font-size: 16px;
                        border-radius: 5px;
                        min-width: 150px;
                    }
                    QPushButton:hover {
                        background-color: #524778;
                    }
                """)
                back_btn.clicked.connect(lambda: self.organizer_events_stack.setCurrentIndex(0))
                
                # Review Vendor Button (Right)
                review_btn = QPushButton("Αξιολόγηση Vendor")
                review_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #D91656;
                        color: white;
                        padding: 12px 30px;
                        font-size: 16px;
                        border-radius: 5px;
                        min-width: 200px;
                    }
                    QPushButton:hover {
                        background-color: #640D5F;
                    }
                """)
                review_btn.clicked.connect(lambda checked, e=event, v=event_services[0]["vendor_id"]: 
                    self.show_review_modal("vendor", e["event_id"], v))
                
                # Add buttons to center layout
                center_layout.addWidget(back_btn)
                center_layout.addWidget(review_btn)
                
                # Add center widget to main layout with stretches on both sides
                buttons_layout.addStretch(1)
                buttons_layout.addWidget(center_widget)
                buttons_layout.addStretch(1)
                
                content_layout.addWidget(buttons_container)
            else:
                # No vendor assigned - show message and buttons
                no_vendor_label = QLabel("Δεν έχουν ανατεθεί vendors σε αυτή την εκδήλωση ακόμα.")
                no_vendor_label.setStyleSheet("color: #666; font-size: 14px; margin-top: 10px;")
                content_layout.addWidget(no_vendor_label)
                
                # Buttons container
                buttons_container = QWidget()
                buttons_layout = QHBoxLayout(buttons_container)
                
                # Center container for buttons
                center_widget = QWidget()
                center_layout = QHBoxLayout(center_widget)
                center_layout.setSpacing(20)
                
                # Back Button (Left)
                back_btn = QPushButton("Πίσω")
                back_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #6b5b95;
                        color: white;
                        padding: 12px 30px;
                        font-size: 16px;
                        border-radius: 5px;
                        min-width: 150px;
                    }
                    QPushButton:hover {
                        background-color: #524778;
                    }
                """)
                back_btn.clicked.connect(lambda: self.organizer_events_stack.setCurrentIndex(0))
                
                # Find Vendors Button (Right)
                find_vendors_btn = QPushButton("Βρείτε Vendors για το Event")
                find_vendors_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #D91656;
                        color: white;
                        padding: 12px 30px;
                        font-size: 16px;
                        border-radius: 5px;
                        min-width: 250px;
                    }
                    QPushButton:hover {
                        background-color: #640D5F;
                    }
                """)
                find_vendors_btn.clicked.connect(lambda: self.show_available_vendors(event))
                
                # Add buttons to center layout
                center_layout.addWidget(back_btn)
                center_layout.addWidget(find_vendors_btn)
                
                # Add center widget to main layout with stretches on both sides
                buttons_layout.addStretch(1)
                buttons_layout.addWidget(center_widget)
                buttons_layout.addStretch(1)
                
                content_layout.addWidget(buttons_container)
                
        except Exception as e:
            print(f"Error loading vendor information: {e}")
            
        scroll.setWidget(content_widget)
        self.organizer_event_details_layout.addWidget(scroll)
        self.organizer_events_stack.setCurrentIndex(1)

    def on_tab_changed(self, index):
        """Handle tab changes and ensure content is loaded."""
        current_tab_text = self.tabs.tabText(index)
        print(f"Debug - Switching to tab: {current_tab_text}")
        
        # Handle different tab switches
        if current_tab_text == "My Events" and self.current_user:
            if self.current_user.get("type") == "organizer":
                self.show_organizer_my_events_tab()
            elif self.current_user.get("type") == "attendee":
                self.display_attendee_my_events()
        elif current_tab_text == "My Tickets" and self.current_user:
            if self.current_user.get("type") == "attendee":
                self.display_my_tickets()
        elif current_tab_text == "History" and self.current_user:
            if self.current_user.get("type") == "organizer":
                self.show_organizer_history_tab()
        elif current_tab_text == "Similar Events" and self.current_user:
            if self.current_user.get("type") == "organizer":
                self.show_organizer_similar_events_tab()
        elif current_tab_text == "Find Events" and self.current_user:
            if self.current_user.get("type") == "attendee":
                self.show_events_tab()

    def show_available_vendors(self, event):
        """Show available vendors for an event with filtering options."""
        print(f"Debug - Showing available vendors for event {event['event_id']}")
        
        # Security check: Only allow organizers to access this function
        if not self.current_user or self.current_user.get("type") != "organizer":
            print(f"Debug - Access denied. User type: {self.current_user.get('type') if self.current_user else 'None'}")
            QMessageBox.warning(self, "Access Denied", "Only organizers can access this functionality.")
            return
        
        # Clear previous content
        while self.organizer_event_details_layout.count():
            item = self.organizer_event_details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Main container
        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)
        
        # Left sidebar for filters
        filters_widget = QWidget()
        filters_widget.setFixedWidth(300)  # Fixed width for the sidebar
        filters_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 5px;
            }
        """)
        filters_layout = QVBoxLayout(filters_widget)
        filters_layout.setContentsMargins(15, 15, 15, 15)
        filters_layout.setSpacing(15)
        
        # Filters Title
        filters_title = QLabel("Φίλτρα")
        filters_title.setFont(QFont("Helvetica", 18, QFont.Bold))
        filters_title.setStyleSheet("color: #333; margin-bottom: 10px;")
        filters_layout.addWidget(filters_title)
        
        # Service Type Filter
        type_group = QGroupBox("Τύπος Υπηρεσίας")
        type_group.setStyleSheet("""
            QGroupBox {
                border: none;
                font-weight: bold;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #333;
            }
        """)
        type_layout = QVBoxLayout()
        type_layout.setSpacing(5)
        
        service_types = [
            "Ενοικίαση Χώρου", "Catering", "DJ", "Φωτογραφία",
            "Ηχητικός Εξοπλισμός", "Φωτισμός", "Διακόσμηση",
            "Ασφάλεια", "Parking", "Άλλο"
        ]
        self.type_checkboxes = []
        for stype in service_types:
            cb = QCheckBox(stype)
            cb.setStyleSheet("""
                QCheckBox {
                    padding: 5px;
                    font-size: 14px;
                }
                QCheckBox:hover {
                    background-color: #f5f5f5;
                }
            """)
            type_layout.addWidget(cb)
            self.type_checkboxes.append(cb)
        type_group.setLayout(type_layout)
        filters_layout.addWidget(type_group)
        
        # Pricing Policy Filter
        pricing_group = QGroupBox("Τιμολογιακή Πολιτική")
        pricing_group.setStyleSheet("""
            QGroupBox {
                border: none;
                font-weight: bold;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #333;
            }
        """)
        pricing_layout = QVBoxLayout()
        pricing_layout.setSpacing(5)
        
        pricing_policies = ["Ανά Άτομο", "Ανά Ώρα", "Ανά Ημέρα", "Πακέτο"]
        self.pricing_checkboxes = []
        for policy in pricing_policies:
            cb = QCheckBox(policy)
            cb.setStyleSheet("""
                QCheckBox {
                    padding: 5px;
                    font-size: 14px;
                }
                QCheckBox:hover {
                    background-color: #f5f5f5;
                }
            """)
            pricing_layout.addWidget(cb)
            self.pricing_checkboxes.append(cb)
        pricing_group.setLayout(pricing_layout)
        filters_layout.addWidget(pricing_group)
        
        # Cost Range Filter
        cost_group = QGroupBox("Εύρος Κόστους")
        cost_group.setStyleSheet("""
            QGroupBox {
                border: none;
                font-weight: bold;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #333;
            }
        """)
        cost_layout = QVBoxLayout()
        
        cost_range_widget = QWidget()
        cost_range_layout = QHBoxLayout(cost_range_widget)
        cost_range_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cost_min = QLineEdit()
        self.cost_min.setPlaceholderText("Από €")
        self.cost_min.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        
        self.cost_max = QLineEdit()
        self.cost_max.setPlaceholderText("Έως €")
        self.cost_max.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        
        cost_range_layout.addWidget(self.cost_min)
        cost_range_layout.addWidget(QLabel("-"))
        cost_range_layout.addWidget(self.cost_max)
        
        cost_layout.addWidget(cost_range_widget)
        cost_group.setLayout(cost_layout)
        filters_layout.addWidget(cost_group)
        
        # Rating Filter
        rating_group = QGroupBox("Βαθμολογία")
        rating_group.setStyleSheet("""
            QGroupBox {
                border: none;
                font-weight: bold;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #333;
            }
        """)
        rating_layout = QVBoxLayout()
        
        ratings = ["4+ αστέρια", "3+ αστέρια", "2+ αστέρια", "1+ αστέρι"]
        self.rating_checkboxes = []
        for rating in ratings:
            cb = QCheckBox(rating)
            cb.setStyleSheet("""
                QCheckBox {
                    padding: 5px;
                    font-size: 14px;
                }
                QCheckBox:hover {
                    background-color: #f5f5f5;
                }
            """)
            rating_layout.addWidget(cb)
            self.rating_checkboxes.append(cb)
        
        rating_group.setLayout(rating_layout)
        filters_layout.addWidget(rating_group)

        # Buttons at the bottom of filters
        buttons_widget = QWidget()
        buttons_layout = QVBoxLayout(buttons_widget)
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(0, 15, 0, 0)

        # Search Button
        search_btn = QPushButton("Αναζήτηση")
        search_btn.setStyleSheet("""
                QPushButton {
                    background-color: #D91656;
                    color: white;
                    padding: 10px;
                    border-radius: 4px;
                    font-size: 14px;
                    min-width: 200px;
                }
                QPushButton:hover {
                    background-color: #640D5F;
                }
            """)
        search_btn.clicked.connect(lambda: self.apply_vendor_filters(event))
        buttons_layout.addWidget(search_btn)

        # Back Button
        back_btn = QPushButton("Πίσω")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b5b95;
                color: white;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #524778;
            }
        """)
        back_btn.clicked.connect(lambda: self.show_organizer_event_details_in_stack(event))
        buttons_layout.addWidget(back_btn)

        filters_layout.addWidget(buttons_widget)
        
        # Right content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        
        # Title
        title = QLabel("Διαθέσιμοι Vendors")
        title.setFont(QFont("Helvetica", 24, QFont.Bold))
        title.setStyleSheet("color: #333;")
        content_layout.addWidget(title)
        
        # Create container for vendor list with scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.vendors_container = QWidget()
        self.vendors_layout = QVBoxLayout(self.vendors_container)
        self.vendors_layout.setSpacing(10)
        
        # Load and display initial vendors
        self.display_filtered_vendors(event)
        
        scroll.setWidget(self.vendors_container)
        content_layout.addWidget(scroll)
        
        # Add both sides to main layout
        main_layout.addWidget(filters_widget)
        main_layout.addWidget(content_widget, stretch=1)
        
        self.organizer_event_details_layout.addWidget(main_container)

    def apply_vendor_filters(self, event):
        """Apply filters to the vendor list."""
        print("Debug - Applying vendor filters")
        self.display_filtered_vendors(event)
        
    def display_filtered_vendors(self, event):
        """Display filtered vendors based on selected criteria."""
        # Clear previous vendors
        while self.vendors_layout.count():
            item = self.vendors_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            # Load services data
            with open("services.json", "r", encoding='utf-8') as f:
                services = json.load(f)["services"]

            # Filter out services that are already assigned to events
            available_services = [s for s in services if not s.get("event_id")]

            if not available_services:
                no_results = QLabel("Δεν βρέθηκαν διαθέσιμες υπηρεσίες")
                no_results.setStyleSheet("""
                    QLabel {
                        color: #666;
                        font-size: 16px;
                        padding: 20px;
                        background-color: #f5f5f5;
                        border-radius: 4px;
                    }
                """)
                self.vendors_layout.addWidget(no_results, alignment=Qt.AlignCenter)
                return

            # Filter services based on criteria
            filtered_services = []
            for service in available_services:
                # Type filter
                selected_types = [cb.text() for cb in self.type_checkboxes if cb.isChecked()]
                if selected_types and "Όλα" not in selected_types and service['type'] not in selected_types:
                    continue

                # Pricing policy filter
                selected_policies = [cb.text() for cb in self.pricing_checkboxes if cb.isChecked()]
                if selected_policies and service.get('pricing_type') not in selected_policies:
                    continue

                # Cost filter
                try:
                    min_cost = float(self.cost_min.text()) if self.cost_min.text() else 0
                    max_cost = float(self.cost_max.text()) if self.cost_max.text() else float('inf')
                    service_cost = float(service['price'])
                    if not (min_cost <= service_cost <= max_cost):
                        continue
                except ValueError:
                    pass

                # Rating filter
                selected_ratings = [cb.text() for cb in self.rating_checkboxes if cb.isChecked()]
                if selected_ratings:
                    try:
                        with open("reviews.json", "r") as f:
                            reviews = json.load(f)
                            vendor_reviews = [r for r in reviews["vendor_reviews"] if r["vendor_id"] == service["vendor_id"]]
                            if vendor_reviews:
                                avg_rating = sum(r["rating"] for r in vendor_reviews) / len(vendor_reviews)
                                min_rating = min(int(r.split("+")[0]) for r in selected_ratings)
                                if avg_rating < min_rating:
                                    continue
                            else:
                                continue  # Skip if no reviews and rating filter is active
                    except (FileNotFoundError, KeyError, json.JSONDecodeError):
                        if selected_ratings:
                            continue  # Skip if can't verify rating and rating filter is active

                filtered_services.append(service)

            if not filtered_services:
                no_results = QLabel("Δεν βρέθηκαν υπηρεσίες για τα επιλεγμένα φίλτρα")
                no_results.setStyleSheet("""
                    QLabel {
                        color: #666;
                        font-size: 16px;
                        padding: 20px;
                        background-color: #f5f5f5;
                        border-radius: 4px;
                    }
                """)
                self.vendors_layout.addWidget(no_results, alignment=Qt.AlignCenter)
                return

            # Display filtered services
            for service in filtered_services:
                service_widget = self.create_service_card(service, event)
                self.vendors_layout.addWidget(service_widget)

            # Add stretch at the end
            self.vendors_layout.addStretch()

        except FileNotFoundError:
            error_label = QLabel("Δεν βρέθηκε το αρχείο των υπηρεσιών")
            error_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 16px;
                    padding: 20px;
                    background-color: #f5f5f5;
                    border-radius: 4px;
                }
            """)
            self.vendors_layout.addWidget(error_label, alignment=Qt.AlignCenter)
        except Exception as e:
            print(f"Error loading services: {str(e)}")
            error_label = QLabel(f"Σφάλμα κατά τη φόρτωση των υπηρεσιών: {str(e)}")
            error_label.setStyleSheet("color: red;")
            self.vendors_layout.addWidget(error_label)

    def create_service_card(self, service, event):
        """Create a card widget for displaying a service."""
        card_widget = QWidget()
        card_widget.setStyleSheet("""
            QWidget#eventContainer {
                background-color: white;
                border: none;
                border-radius: 8px;
            }
            QWidget#eventContainer:hover {
                border: 1px solid #D91656;
            }
        """)
        card_widget.setObjectName("eventContainer")
        card_layout = QHBoxLayout(card_widget)
        card_layout.setContentsMargins(15, 15, 15, 15)
        
        # Left side: Service image container
        image_container = QWidget()
        image_container.setFixedSize(180, 180)
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setAlignment(Qt.AlignCenter)  # Align to top
        
        image_label = QLabel()
        image_label.setFixedSize(180, 180)
        image_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: none;
                border-radius: 4px;
            }
        """)
        
        if service.get('media_path'):
            pixmap = QPixmap(service['media_path'])
            if not pixmap.isNull():
                pixmap = pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(pixmap)
            else:
                image_label.setText("No Image")
                image_label.setAlignment(Qt.AlignCenter)
        else:
            image_label.setText("No Image")
            image_label.setAlignment(Qt.AlignCenter)

        image_layout.addWidget(image_label)
        card_layout.addWidget(image_container)
        
        # Add some spacing between image and info
        card_layout.addSpacing(20)
        
        # Middle: Basic service info
        info_widget = QWidget()
        info_widget.setStyleSheet("border: none;")  # Remove border from info widget
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(5)
        
        # Service Title
        title = QLabel(service["name"])
        title.setFont(QFont("Helvetica", 16, QFont.Bold))
        title.setStyleSheet("color: #333; border: none;")  # Remove border from label
        info_layout.addWidget(title)
        
        # Vendor Name
        if service.get('vendor_name'):
            vendor_label = QLabel(f"από {service['vendor_name']}")
            vendor_label.setStyleSheet("color: #666; font-size: 14px; border: none;")  # Remove border from label
            info_layout.addWidget(vendor_label)
        
        # Basic Price Info
        price_label = QLabel(f"€{service['price']} {service.get('pricing_type', '')}")
        price_label.setFont(QFont("Helvetica", 14))
        price_label.setStyleSheet("color: #D91656; border: none;")  # Remove border from label
        info_layout.addWidget(price_label)
        
        info_layout.addStretch()
        card_layout.addWidget(info_widget, stretch=1)
        
        # Add some spacing between info and button
        card_layout.addSpacing(15)
        
        # Right side: More Details Button
        button_widget = QWidget()
        button_widget.setStyleSheet("border: none;")  # Remove border from button widget
        button_layout = QVBoxLayout(button_widget)
        button_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        details_btn = QPushButton("Περισσότερα")
        details_btn.setStyleSheet("""
            QPushButton {
                background-color: #D91656;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #640D5F;
            }
        """)
        details_btn.clicked.connect(lambda: self.show_service_details(service, event))
        button_layout.addWidget(details_btn)
        
        card_layout.addWidget(button_widget)

        # Add a subtle shadow effect to the card
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        card_widget.setGraphicsEffect(shadow)
        
        return card_widget

    def show_service_details(self, service, event):
        """Show detailed information about a service."""
        # Create a dialog for service details
        dialog = QDialog(self)
        dialog.setWindowTitle("Λεπτομέρειες Υπηρεσίας")
        dialog.setMinimumWidth(600)
        dialog.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        
        # Service image at the top
        if service.get('media_path'):
            image_label = QLabel()
            pixmap = QPixmap(service['media_path'])
            if not pixmap.isNull():
                pixmap = pixmap.scaled(400, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(pixmap)
                image_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(image_label)
        
        # Service Title
        title = QLabel(service["name"])
        title.setFont(QFont("Helvetica", 20, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)
        
        # Vendor Name
        if service.get('vendor_name'):
            vendor_label = QLabel(f"Πάροχος: {service['vendor_name']}")
            vendor_label.setStyleSheet("color: #666; font-size: 16px;")
            layout.addWidget(vendor_label)
        
        # Service Details
        details_group = QGroupBox("Πληροφορίες Υπηρεσίας")
        details_layout = QVBoxLayout()
        
        # Type and Price
        type_price = QLabel(f"<b>Τύπος:</b> {service['type']}<br>"
                          f"<b>Κόστος:</b> €{service['price']} {service.get('pricing_type', '')}")
        type_price.setStyleSheet("font-size: 14px;")
        details_layout.addWidget(type_price)
        
        # Capacity
        if service.get('min_capacity') and service.get('max_capacity'):
            capacity = QLabel(f"<b>Χωρητικότητα:</b> {service['min_capacity']} - {service['max_capacity']} άτομα")
            capacity.setStyleSheet("font-size: 14px;")
            details_layout.addWidget(capacity)
        
        # Dates
        if service.get('start_date') and service.get('end_date'):
            dates = QLabel(f"<b>Διαθεσιμότητα:</b> {service['start_date']} - {service['end_date']}")
            dates.setStyleSheet("font-size: 14px;")
            details_layout.addWidget(dates)
        
        # Description
        if service.get('description'):
            desc = QLabel(f"<b>Περιγραφή:</b><br>{service['description']}")
            desc.setWordWrap(True)
            desc.setStyleSheet("font-size: 14px;")
            details_layout.addWidget(desc)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Buttons at the bottom
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        close_btn = QPushButton("Πίσω")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        close_btn.clicked.connect(dialog.close)
        
        select_btn = QPushButton("Αιτηθείτε Συνεργασία")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #D91656;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #640D5F;
            }
        """)
        select_btn.clicked.connect(lambda: [self.request_collaboration(service, event), dialog.close()])
        
        buttons_layout.addWidget(close_btn)
        buttons_layout.addWidget(select_btn)
        
        layout.addWidget(buttons_widget)
        
        dialog.exec_()

    def request_collaboration(self, service, event):
        """Send a collaboration request to a vendor for their service."""
        try:
            # Create collaboration request
            request = CollaborationRequest(
                event_id=event["event_id"],
                organizer_id=self.current_user["user_id"],
                vendor_id=service["vendor_id"],
                service_id=service["service_id"]
            )
            
            # Save the request
            if save_collaboration_request(request):
                QMessageBox.information(
                    self,
                    "Επιτυχία",
                    "Το αίτημα συνεργασίας στάλθηκε επιτυχώς στον vendor."
                )
                
                # Add notification for vendor with detailed information
                self.add_notification(
                    service["vendor_id"],
                    "Νέο Αίτημα Συνεργασίας",
                    f"Έχετε ένα νέο αίτημα συνεργασίας για την υπηρεσία '{service['name']}' από τον διοργανωτή {self.current_user['name']} {self.current_user['surname']}.",
                    category="Collaboration Requests",
                    additional_data={
                        "collaboration_request": {
                            "request_id": request.request_id,
                            "organizer_info": {
                                "id": self.current_user["user_id"],
                                "name": self.current_user["name"],
                                "surname": self.current_user["surname"],
                                "email": self.current_user["email"]
                            },
                            "event_info": {
                                "id": event["event_id"],
                                "title": event["title"],
                                "description": event["description"],
                                "start_date": event["start_date"],
                                "end_date": event["end_date"],
                                "location": event["location"],
                                "type": event.get("type", "")
                            },
                            "service_info": {
                                "id": service["service_id"],
                                "name": service["name"],
                                "description": service["description"],
                                "price": service["price"],
                                "type": service.get("type", "")
                            }
                        }
                    }
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "An error occurred while sending the request."
                )
        except Exception as e:
            print(f"Error in request_collaboration: {e}")
            QMessageBox.warning(
                self,
                "Error",
                "An error occurred while sending the request."
            )

    def get_back_button_style(self):
        """Return the consistent style for back buttons."""
        return """
            QPushButton {
                background-color: #6b5b95;
                color: white;
                padding: 12px 30px;
                font-size: 16px;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #524778;
            }
        """
        
    def create_back_button(self):
        """Create a consistently styled back button."""
        back_btn = QPushButton("Back")
        back_btn.setStyleSheet(self.get_back_button_style())
        return back_btn

    def add_notification(self, user_id, title, message, category=None, additional_data=None):
        """Add a notification for a user."""
        try:
            # Load existing notifications
            try:
                with open("notifications.json", "r", encoding='utf-8') as f:
                    notifications_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                notifications_data = {"notifications": []}
            
            # Create new notification
            notification = {
                "notification_id": f"notif_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "user_id": user_id,
                "title": title,
                "message": message,
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "read": False,
                "category": category
            }

            # Add additional data if provided
            if additional_data:
                notification.update(additional_data)
            
            # Add new notification
            notifications_data["notifications"].append(notification)
            
            # Save updated data
            with open("notifications.json", "w", encoding='utf-8') as f:
                json.dump(notifications_data, f, ensure_ascii=False, indent=4)
            
            # Update notifications tab if it exists and belongs to the target user
            if (hasattr(self, 'current_user') and 
                self.current_user and 
                self.current_user["user_id"] == user_id and 
                "Notifications" in self.private_tabs):
                self.private_tabs["Notifications"].load_notifications()
            
            return True
        except Exception as e:
            print(f"Error adding notification: {e}")
            return False

    def check_notifications(self):
        """Check for unread notifications for the current user."""
        if not hasattr(self, 'current_user'):
            return
        
        try:
            with open("notifications.json", "r", encoding='utf-8') as f:
                data = json.load(f)
                unread = [n for n in data["notifications"] 
                         if n["user_id"] == self.current_user["user_id"] and not n.get("read", False)]
                
                if unread and "Notifications" in self.private_tabs:
                    # Update the notifications tab
                    self.private_tabs["Notifications"].load_notifications()
                    
                    # Update tab text to show unread count
                    notifications_index = self.get_tab_index("Notifications")
                    if notifications_index >= 0:
                        self.tabs.setTabText(notifications_index, f"Notifications ({len(unread)})")
                        
                    # Show collaboration requests immediately
                    for notification in unread:
                        if notification.get("category") == "Collaboration Requests":
                            self.show_collaboration_request(notification)
                            self.mark_notification_as_read(notification["notification_id"])
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error checking notifications: {e}")

    def mark_notification_as_read(self, notification_id):
        """Mark a notification as read."""
        try:
            with open("notifications.json", "r", encoding='utf-8') as f:
                data = json.load(f)
            
            notification = next((n for n in data["notifications"] 
                               if n["notification_id"] == notification_id), None)
            if notification:
                notification["read"] = True
                
                with open("notifications.json", "w", encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                    
                # Update notifications tab if it exists
                if "Notifications" in self.private_tabs:
                    self.private_tabs["Notifications"].load_notifications()
                    
                    # Update tab text to show unread count
                    notifications_index = self.get_tab_index("Notifications")
                    if notifications_index >= 0:
                        unread_count = len([n for n in data["notifications"] 
                                          if n["user_id"] == self.current_user["user_id"] and 
                                          not n.get("read", False)])
                        if unread_count > 0:
                            self.tabs.setTabText(notifications_index, f"Notifications ({unread_count})")
                        else:
                            self.tabs.setTabText(notifications_index, "Notifications")
                    
        except Exception as e:
            print(f"Error marking notification as read: {e}")

    def show_collaboration_request(self, notification):
        """Show the collaboration request details dialog."""
        try:
            # Get request data from the notification
            collab_data = notification.get("collaboration_request", {})
            request_id = collab_data.get("request_id")
            
            if not request_id:
                return
            
            # Get request details from collaboration_requests.json
            with open("collaboration_requests.json", "r") as f:
                data = json.load(f)
                request = next((r for r in data["requests"] if r["request_id"] == request_id), None)
            
            if not request or request["status"] != "pending":
                return
            
            # Get event info from notification
            event = collab_data.get("event_info")
            if not event:
                return
            
            # Get service info from notification
            service = collab_data.get("service_info")
            if not service:
                return
            
            # Show the collaboration request details dialog - pass the notification
            dialog = CollaborationRequestDetailsDialog(request, event, service, self, notification)
            dialog.exec_()
            
        except Exception as e:
            print(f"Error showing collaboration request: {e}")

    def add_notification_tab(self):
        """Add the notifications tab to the current user's dashboard."""
        notifications_tab = NotificationsTab(self)
        self.tabs.addTab(notifications_tab, qta.icon("fa5s.bell"), "Notifications")
        self.private_tabs["Notifications"] = notifications_tab
        notifications_tab.load_notifications()

    def handle_collaboration_response(self, notification, response):
        """Handle vendor's response to a collaboration request."""
        try:
            collab_data = notification.get("collaboration_request", {})
            request_id = collab_data.get("request_id")
            
            if not request_id:
                QMessageBox.warning(self, "Σφάλμα", "Δεν βρέθηκαν στοιχεία αιτήματος.")
                return

            # Load collaboration requests
            with open("collaboration_requests.json", "r", encoding='utf-8') as f:
                data = json.load(f)
                requests = data.get("requests", [])

            # Find and update the specific request
            request = next((r for r in requests if r["request_id"] == request_id), None)
            if request:
                request["status"] = response
                request["response_date"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                # Save updated requests
                with open("collaboration_requests.json", "w", encoding='utf-8') as f:
                    json.dump({"requests": requests}, f, ensure_ascii=False, indent=4)

                # Get detailed information for notifications
                organizer_info = collab_data.get("organizer_info", {})
                event_info = collab_data.get("event_info", {})
                service_info = collab_data.get("service_info", {})
                vendor_name = f"{self.current_user['name']} {self.current_user['surname']}"

                if response == "accepted":
                    # Update service status if accepted
                    with open("services.json", "r", encoding='utf-8') as f:
                        services_data = json.load(f)
                        service = next((s for s in services_data["services"] 
                                      if s["service_id"] == service_info.get("id")), None)
                        if service:
                            service["event_id"] = event_info.get("id")
                            service["status"] = "assigned"
                            service["assigned_date"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            
                    with open("services.json", "w", encoding='utf-8') as f:
                        json.dump(services_data, f, ensure_ascii=False, indent=4)

                    # Send acceptance notification to organizer
                    self.add_notification(
                        organizer_info.get("id"),
                        "Αίτημα Συνεργασίας Εγκρίθηκε! ✅",
                        f"Ο vendor {vendor_name} αποδέχτηκε το αίτημα συνεργασίας για την υπηρεσία '{service_info.get('name', '')}' στην εκδήλωση '{event_info.get('title', '')}'.",
                        category="Collaboration Requests",
                        additional_data={
                            "collaboration_response": {
                                "status": "accepted",
                                "vendor_name": vendor_name,
                                "service_name": service_info.get("name", ""),
                                "event_title": event_info.get("title", ""),
                                "response_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            }
                        }
                    )

                    QMessageBox.information(
                        self,
                        "Επιτυχία",
                        f"Αποδεχτήκατε επιτυχώς το αίτημα συνεργασίας!\n\nΗ υπηρεσία '{service_info.get('name', '')}' έχει ανατεθεί στην εκδήλωση '{event_info.get('title', '')}'.\n\nΟ διοργανωτής θα ειδοποιηθεί για την αποδοχή σας."
                    )

                else:  # rejected
                    # Send rejection notification to organizer
                    self.add_notification(
                        organizer_info.get("id"),
                        "Αίτημα Συνεργασίας Απορρίφθηκε ❌",
                        f"Ο vendor {vendor_name} απέρριψε το αίτημα συνεργασίας για την υπηρεσία '{service_info.get('name', '')}' στην εκδήλωση '{event_info.get('title', '')}'.",
                        category="Collaboration Requests",
                        additional_data={
                            "collaboration_response": {
                                "status": "rejected",
                                "vendor_name": vendor_name,
                                "service_name": service_info.get("name", ""),
                                "event_title": event_info.get("title", ""),
                                "response_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            }
                        }
                    )

                    QMessageBox.information(
                        self,
                        "Απόρριψη Καταγράφηκε",
                        f"Απορρίψατε το αίτημα συνεργασίας για την υπηρεσία '{service_info.get('name', '')}'.\n\nΟ διοργανωτής θα ειδοποιηθεί για την απόρριψη."
                    )

                # Mark the original notification as deleted and refresh the notifications tab
                try:
                    with open("notifications.json", "r", encoding='utf-8') as f:
                        notif_data = json.load(f)
                    
                    for notif in notif_data["notifications"]:
                        if notif.get("notification_id") == notification.get("notification_id"):
                            notif["deleted"] = True
                            break
                    
                    with open("notifications.json", "w", encoding='utf-8') as f:
                        json.dump(notif_data, f, ensure_ascii=False, indent=4)
                    
                    # Refresh the notifications tab to remove the processed notification
                    if "Notifications" in self.private_tabs:
                        self.private_tabs["Notifications"].load_notifications()
                        
                        # Update tab text to show unread count
                        notifications_index = self.get_tab_index("Notifications")
                        if notifications_index >= 0:
                            unread_count = len([n for n in notif_data["notifications"] 
                                              if n["user_id"] == self.current_user["user_id"] and 
                                              not n.get("read", False) and not n.get("deleted", False)])
                            if unread_count > 0:
                                self.tabs.setTabText(notifications_index, f"Notifications ({unread_count})")
                            else:
                                self.tabs.setTabText(notifications_index, "Notifications")
                        
                except Exception as e:
                    print(f"Error marking notification as deleted: {e}")

            else:
                QMessageBox.warning(self, "Σφάλμα", "Δεν βρέθηκε το αίτημα συνεργασίας.")

        except Exception as e:
            print(f"Error handling collaboration response: {e}")
            QMessageBox.warning(
                self,
                "Σφάλμα",
                f"Παρουσιάστηκε σφάλμα κατά την επεξεργασία της απάντησης: {str(e)}"
            )



    def mark_notification_as_read(self, notification_id):
        """Mark a notification as read."""
        try:
            with open("notifications.json", "r", encoding='utf-8') as f:
                data = json.load(f)
                
            notification = next((n for n in data["notifications"] 
                               if n["notification_id"] == notification_id), None)
            if notification:
                notification["read"] = True
                
                with open("notifications.json", "w", encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                    
                # Update notifications tab if it exists
                if "Notifications" in self.private_tabs:
                    self.private_tabs["Notifications"].load_notifications()
                    
        except Exception as e:
            print(f"Error marking notification as read: {e}")

    def update_ui_after_login(self, user_type):
        """Update UI after successful login."""
        # Hide the Login Tab
        login_index = self.get_tab_index("Login")
        if login_index >= 0:
            self.tabs.removeTab(login_index)
        
        # Show Log Off button
        self.logoff_btn.show()
        
        # Add appropriate tabs based on user type
        if user_type == "organizer":
            self.add_organizer_tab()
        elif user_type == "vendor":
            self.add_vendor_tab()
        elif user_type == "attendee":
            self.add_attendee_tab()
            
        # Add notifications tab for all user types
        self.add_notification_tab()

    def check_notifications(self):
        """Check for new notifications periodically."""
        if not self.current_user:
            return

        try:
            with open("notifications.json", "r", encoding='utf-8') as f:
                data = json.load(f)
                
            # Check for unread notifications for current user
            current_user_id = self.current_user["user_id"]
            current_notifications = [n for n in data["notifications"] 
                                  if n["user_id"] == current_user_id]
            unread = [n for n in current_notifications if not n.get("read", False)]
            
            if "Notifications" in self.private_tabs:
                # Update the notifications tab
                notifications_tab = self.private_tabs["Notifications"]
                
                # Update tab text to show unread count
                notifications_index = self.get_tab_index("Notifications")
                if notifications_index >= 0:
                    self.tabs.setTabText(notifications_index, 
                                       f"Notifications ({len(unread)})" if unread else "Notifications")
                    
                    # If we're on the notifications tab, refresh the display
                    if self.tabs.currentIndex() == notifications_index:
                        notifications_tab.load_notifications(notifications_tab.category_combo.currentText())
                
                # Show system tray notification for new unread notifications
                if unread:
                    # Get the most recent unread notification
                    newest_unread = max(
                        unread,
                        key=lambda x: datetime.strptime(x['timestamp'], "%d/%m/%Y %H:%M:%S")
                    )
                    
                    # Show system tray notification
                    if hasattr(self, 'tray_icon'):
                        self.tray_icon.showMessage(
                            newest_unread['title'],
                            newest_unread['message'],
                            QSystemTrayIcon.Information,
                            3000  # Display for 3 seconds
                        )
                    
        except Exception as e:
            print(f"Error checking notifications: {e}")

    def show_review_response_modal(self, notification):
        """Show modal for responding to a review."""
        # To be implemented based on review response requirements
        pass

    def show_ticket_modification_modal(self, notification):
        """Show modal for modifying a ticket."""
        # To be implemented based on ticket modification requirements
        pass

    def save_notifications(self):
        try:
            with open('notifications.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Filter out expired notifications (older than 30 days)
            current_time = datetime.now()
            notifications = []
            for notif in data['notifications']:
                notif_time = datetime.strptime(notif['timestamp'], "%d/%m/%Y %H:%M:%S")
                if (current_time - notif_time).days <= 30:
                    notifications.append(notif)
            
            data['notifications'] = notifications
            
            with open('notifications.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"Error saving notifications: {str(e)}")
            
    def cleanup_old_notifications(self):
        """This method now only removes notifications that have been explicitly marked for deletion"""
        try:
            with open('notifications.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Only remove notifications that have been explicitly marked for deletion
            notifications = [notif for notif in data['notifications'] if not notif.get('deleted', False)]
            data['notifications'] = notifications
            
            with open('notifications.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"Error cleaning up notifications: {str(e)}")

    def load_notifications(self, category="All Notifications"):
        """Load notifications with improved error handling and sorting"""
        try:
            with open('notifications.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get notifications for current user that haven't been deleted
            current_user_id = self.parent.current_user.get('id')
            notifications = [
                n for n in data.get('notifications', [])
                if n.get('user_id') == current_user_id and not n.get('deleted', False)
            ]
            
            # Sort notifications by date (newest first) and unread status
            notifications.sort(key=lambda x: (
                x.get('read', False),  # Unread first
                datetime.strptime(x['timestamp'], "%d/%m/%Y %H:%M:%S")  # Then by date
            ), reverse=True)
            
            # Filter by category if specified
            if category != "All Notifications":
                notifications = [n for n in notifications if n.get('category') == category]
            
            return notifications
            
        except Exception as e:
            print(f"Error loading notifications: {str(e)}")
            return []

    def handle_transfer_response(self, notification, accepted):
        """Handle the response to a ticket transfer request."""
        try:
            print("Debug - Starting transfer response handling")
            print(f"Debug - Notification data: {notification}")
            print(f"Debug - Response: {'Accept' if accepted else 'Reject'}")
            
            # Get transfer request data
            with open("ticket_transfer_requests.json", "r", encoding="utf-8") as f:
                transfer_data = json.load(f)
            
            request = next((req for req in transfer_data["transfer_requests"] 
                          if req["request_id"] == notification["transfer_request_id"]), None)
            
            if not request:
                raise ValueError("Transfer request not found")
            
            print(f"Debug - Found transfer request: {request}")
            
            # Update request status
            request["status"] = "accepted" if accepted else "rejected"
            
            if accepted:
                print("Debug - Processing acceptance")
                # Get tickets data
                with open("tickets.json", "r", encoding="utf-8") as f:
                    tickets_data = json.load(f)
                
                print("Debug - Current tickets data:", tickets_data)
                
                # Keep track of new tickets to add
                new_tickets = []
                
                # Transfer tickets from sender to recipient
                for ticket_item in request["tickets"]:
                    ticket_id = ticket_item["ticket"]["ticket_id"]
                    ticket_type = ticket_item["ticket"]["ticket_type"]
                    transfer_quantity = ticket_item["quantity"]
                    print(f"Debug - Processing ticket {ticket_id}, type {ticket_type}, quantity {transfer_quantity}")
                    
                    # Find the sender's ticket in the tickets data
                    sender_ticket = next((t for t in tickets_data if t["ticket_id"] == ticket_id and 
                                        t["ticket_type"] == ticket_type and 
                                        t["user_id"] == request["sender"]["user_id"]), None)
                    
                    if sender_ticket:
                        print(f"Debug - Found sender's ticket: {sender_ticket}")
                        
                        # Calculate remaining quantity for sender
                        remaining_quantity = sender_ticket["quantity_bought"] - transfer_quantity
                        
                        if remaining_quantity > 0:
                            # Update sender's quantity
                            sender_ticket["quantity_bought"] = remaining_quantity
                            print(f"Debug - Updated sender's quantity to: {remaining_quantity}")
                        else:
                            # Remove sender's ticket entry if no tickets remain
                            tickets_data.remove(sender_ticket)
                            print("Debug - Removed sender's ticket entry (no tickets remain)")
                        
                        # Create new ticket entry for recipient
                        new_ticket = sender_ticket.copy()
                        new_ticket["user_id"] = request["recipient"]["user_id"]
                        new_ticket["quantity_bought"] = transfer_quantity
                        new_tickets.append(new_ticket)
                        print(f"Debug - Created new ticket for recipient: {new_ticket}")
                
                # Add new tickets to tickets_data
                tickets_data.extend(new_tickets)
                print(f"Debug - Added {len(new_tickets)} new tickets for recipient")
                
                # Save updated tickets data
                with open("tickets.json", "w", encoding="utf-8") as f:
                    json.dump(tickets_data, f, indent=4, ensure_ascii=False)
                print("Debug - Saved updated tickets data")
            
            # Save updated transfer request data
            with open("ticket_transfer_requests.json", "w", encoding="utf-8") as f:
                json.dump(transfer_data, f, indent=4, ensure_ascii=False)
            print("Debug - Saved updated transfer request data")
            
            # Delete the notification for the recipient
            with open("notifications.json", "r", encoding="utf-8") as f:
                notifications_data = json.load(f)
            
            # Remove the notification
            notifications_data["notifications"] = [
                n for n in notifications_data["notifications"] 
                if n["notification_id"] != notification["notification_id"]
            ]
            
            # Save updated notifications
            with open("notifications.json", "w", encoding="utf-8") as f:
                json.dump(notifications_data, f, indent=4, ensure_ascii=False)
            print("Debug - Deleted recipient's notification")
            
            # Create notification for sender
            response_message = "αποδέχτηκε" if accepted else "απέρριψε"
            self.add_notification(
                request["sender"]["user_id"],
                "Απάντηση σε Αίτημα Μεταφοράς Εισιτηρίων",
                f"Ο χρήστης {request['recipient']['email']} {response_message} το αίτημα μεταφοράς εισιτηρίων.",
                "Ticket Transfers"
            )
            print("Debug - Created notification for sender")
            
            # Show success message
            QMessageBox.information(
                self,
                "Επιτυχία",
                "Η απάντηση στο αίτημα μεταφοράς εισιτηρίων ολοκληρώθηκε με επιτυχία."
            )
            
            # Refresh notifications display
            self.load_notifications()
            print("Debug - Refreshed notifications display")
            
        except Exception as e:
            print(f"Error handling transfer response: {str(e)}")
            print(f"Debug - Full error details:", e)
            QMessageBox.critical(
                self,
                "Σφάλμα",
                f"Παρουσιάστηκε σφάλμα κατά την επεξεργασία της απάντησης: {str(e)}"
            )

    def handle_login_success(self, user):
        """Handle successful login."""
        self.current_user = user
        # Ensure credit is stored as a string
        if "credit" in self.current_user:
            self.current_user["credit"] = str(self.current_user["credit"])
        self.update_ui_for_user()
        
        # Show welcome message
        welcome_msg = QMessageBox()
        welcome_msg.setIcon(QMessageBox.Information)
        welcome_msg.setWindowTitle("Welcome")
        welcome_msg.setText(f"Welcome {user.get('name', '')}!")
        welcome_msg.exec_()

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
        user_type = self.user_type_combobox.currentText().lower()  # Convert to lowercase

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
            "user_id": user_id,
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

class NotificationsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title and actions row
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Notifications")
        title.setFont(QFont("Helvetica", 24, QFont.Bold))
        title.setStyleSheet("color: #333;")
        header_layout.addWidget(title)

        # Remove bulk action buttons - no longer needed
        layout.addWidget(header_widget)

        # Filter section
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        # Category filter
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                min-width: 200px;
            }
        """)
        self.category_combo.currentIndexChanged.connect(self.filter_notifications)
        filter_layout.addWidget(self.category_combo)
        filter_layout.addStretch()

        layout.addWidget(filter_widget)

        # Notifications list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self.notifications_container = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_container)
        self.notifications_layout.setSpacing(10)
        self.notifications_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.notifications_container)
        layout.addWidget(scroll)

        # Update categories based on user type
        self.update_categories()



    def update_categories(self):
        """Update filter categories based on user type."""
        self.category_combo.clear()
        self.category_combo.addItem("All Notifications")

        user_type = self.parent.current_user.get("type") if self.parent.current_user else None
        
        if user_type == "attendee":
            categories = [
                "Ticket Purchases",
                "Event Changes",
                "Event Suggestions"
            ]
        elif user_type == "organizer":
            categories = [
                "Ticket Sales",
                "Collaboration Requests",
                "Event Reviews"
            ]
        elif user_type == "vendor":
            categories = [
                "Collaboration Requests",
                "Payment Confirmations",
                "Service Reviews"
            ]
        else:
            categories = []

        self.category_combo.addItems(categories)

    def create_notification_card(self, notification):
        """Create a card widget for a notification."""
        card = QWidget()
        card.setStyleSheet("""
            QWidget#card {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                margin: 5px;
            }
            QWidget#card:hover {
                border: 2px solid #D91656;
                background-color: #fafafa;
            }
        """)
        card.setObjectName("card")
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 3)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # Header with unread indicator, title and timestamp
        header = QWidget()
        header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Unread indicator (if not read)
        if not notification.get("read", False):
            unread_indicator = QLabel("●")
            unread_indicator.setStyleSheet("color: #D91656; font-size: 16px; background-color: transparent; font-weight: bold;")
            header_layout.addWidget(unread_indicator)

        # Category badge
        category = notification.get("category", "General")
        category_badge = QLabel(category)
        category_badge.setStyleSheet("""
            background-color: #D91656;
            color: white;
            padding: 4px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
        """)
        header_layout.addWidget(category_badge)

        header_layout.addStretch()

        timestamp = QLabel(notification["timestamp"])
        timestamp.setStyleSheet("color: #888; font-size: 11px; background-color: transparent;")
        header_layout.addWidget(timestamp)

        layout.addWidget(header)

        # Title
        title = QLabel(notification["title"])
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; background-color: transparent; margin: 5px 0px;")
        layout.addWidget(title)

        # Message preview
        message_text = notification["message"]
        if len(message_text) > 100:
            message_text = message_text[:100] + "..."
        
        message = QLabel(message_text)
        message.setWordWrap(True)
        message.setStyleSheet("color: #555; font-size: 13px; background-color: transparent; line-height: 1.4;")
        layout.addWidget(message)

        # Review preview (if it's a review notification)
        if "review_data" in notification:
            review_data = notification["review_data"]
            
            # Rating stars preview
            rating_widget = QWidget()
            rating_layout = QHBoxLayout(rating_widget)
            rating_layout.setContentsMargins(0, 5, 0, 0)
            
            rating_label = QLabel("Βαθμολογία:")
            rating_label.setStyleSheet("color: #666; font-size: 12px; font-weight: bold;")
            rating_layout.addWidget(rating_label)
            
            # Create star display
            stars_text = "★" * int(review_data.get("rating", 0)) + "☆" * (5 - int(review_data.get("rating", 0)))
            stars_label = QLabel(stars_text)
            stars_label.setStyleSheet("color: #FFD700; font-size: 14px;")
            rating_layout.addWidget(stars_label)
            
            rating_value = QLabel(f"({review_data.get('rating', 0)}/5)")
            rating_value.setStyleSheet("color: #666; font-size: 12px;")
            rating_layout.addWidget(rating_value)
            
            rating_layout.addStretch()
            layout.addWidget(rating_widget)

        # Click to view more indicator
        view_more = QLabel("Κάντε κλικ για περισσότερες λεπτομέρειες →")
        view_more.setStyleSheet("color: #D91656; font-size: 11px; font-style: italic; background-color: transparent; margin-top: 5px;")
        layout.addWidget(view_more)

        # Make the card clickable
        card.mousePressEvent = lambda e: self.show_notification_details(notification)
        
        return card

    def show_notification_details(self, notification):
        """Show detailed view of a notification with possible actions."""
        # Mark notification as read
        if not notification.get("read", True):
            self.parent.mark_notification_as_read(notification["notification_id"])

        # Create detail dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Λεπτομέρειες Ειδοποίησης")
        dialog.setMinimumWidth(800)
        dialog.setMinimumHeight(600)
        dialog.resize(900, 700)  # Set a good default size
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
        """)

        # Create main layout with scroll area
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel(notification["title"])
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: #D91656; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Message
        message = QLabel(notification["message"])
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 16px; color: #333; line-height: 1.4;")
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)

        # Add action buttons based on notification type
        action_buttons_added = False

        if notification.get("category") == "Collaboration Requests" and self.parent.current_user.get("type") == "vendor":
            # Check if this is a pending collaboration request
            try:
                collab_data = notification.get("collaboration_request", {})
                request_id = collab_data.get("request_id")
                
                if request_id:
                    with open("collaboration_requests.json", "r") as f:
                        data = json.load(f)
                        request = next((r for r in data["requests"] if r["request_id"] == request_id and r["status"] == "pending"), None)
                        
                        if request:
                            # Add collaboration action buttons
                            self.add_collaboration_actions(layout, notification, dialog)
                            action_buttons_added = True
            except Exception as e:
                print(f"Error adding collaboration action buttons: {e}")

        elif notification.get("type") == "ticket_transfer":
            # Add action buttons for ticket transfer
            action_buttons_added = self.add_ticket_actions(layout, notification, dialog)

        # Add back button only if no action buttons were added
        if not action_buttons_added:
            button_container = QWidget()
            button_container.setStyleSheet("background-color: #f8f9fa; padding: 15px; border-radius: 10px;")
            button_layout = QHBoxLayout(button_container)
            button_layout.setSpacing(15)

            # Back button (grey)
            back_btn = QPushButton("Πίσω")
            back_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    padding: 12px 25px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)
            back_btn.clicked.connect(dialog.close)

            button_layout.addWidget(back_btn, alignment=Qt.AlignCenter)
            layout.addWidget(button_container)

        # Set the content widget
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        dialog.exec_()

    def get_review_data_from_file(self, notification):
        """Fetch review data from reviews.json for old notifications."""
        try:
            import json
            from datetime import datetime
            
            with open("reviews.json", "r", encoding='utf-8') as f:
                reviews = json.load(f)
            
            # Determine which review list to search based on category
            if notification.get("category") == "Service Reviews":
                review_list = reviews.get("vendor_reviews", [])
            else:
                review_list = reviews.get("event_reviews", [])
            
            # Try to find a review that matches the notification timestamp
            notification_time = notification.get("timestamp", "")
            
            # Look for a review with a similar timestamp (within the same day/hour)
            for review in reversed(review_list):  # Start from most recent
                review_time = review.get("created_at", "")
                
                # Simple matching: if the notification and review are from the same day and hour
                if notification_time[:13] == review_time[:13]:  # Match "DD/MM/YYYY HH"
                    return {
                        "rating": review.get("rating", 0),
                        "comments": review.get("comments", ""),
                        "suggestions": review.get("suggestions", ""),
                        "reviewer_name": f"{review.get('user', {}).get('name', '')} {review.get('user', {}).get('surname', '')}".strip(),
                        "review_type": review.get("review_type", "")
                    }
            
            # If no exact match, return the most recent review
            if review_list:
                latest_review = review_list[-1]
                return {
                    "rating": latest_review.get("rating", 0),
                    "comments": latest_review.get("comments", ""),
                    "suggestions": latest_review.get("suggestions", ""),
                    "reviewer_name": f"{latest_review.get('user', {}).get('name', '')} {latest_review.get('user', {}).get('surname', '')}".strip(),
                    "review_type": latest_review.get("review_type", "")
                }
                
        except Exception as e:
            print(f"Error fetching review data: {e}")
        
        return None

    def add_collaboration_actions(self, layout, notification, dialog):
        """Add action buttons for collaboration requests."""
        if self.parent.current_user.get("type") == "vendor":
            buttons_widget = QWidget()
            buttons_widget.setStyleSheet("background-color: #f8f9fa; padding: 15px; border-radius: 10px;")
            buttons_layout = QHBoxLayout(buttons_widget)
            buttons_layout.setSpacing(15)

            # Back button (grey)
            back_btn = QPushButton("Πίσω")
            back_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    padding: 12px 25px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)
            back_btn.clicked.connect(dialog.close)

            # Reject button (red)
            reject_btn = QPushButton("Απόρριψη")
            reject_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    padding: 12px 25px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            reject_btn.clicked.connect(lambda: [
                self.parent.handle_collaboration_response(notification, "rejected"),
                dialog.close(),
                self.parent.private_tabs["Notifications"].load_notifications() if "Notifications" in self.parent.private_tabs else None
            ])

            # Accept button (green)
            accept_btn = QPushButton("Αποδοχή")
            accept_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    padding: 12px 25px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            accept_btn.clicked.connect(lambda: [
                self.parent.handle_collaboration_response(notification, "accepted"),
                dialog.close(),
                self.parent.private_tabs["Notifications"].load_notifications() if "Notifications" in self.parent.private_tabs else None
            ])

            buttons_layout.addWidget(back_btn)
            buttons_layout.addStretch()
            buttons_layout.addWidget(reject_btn)
            buttons_layout.addWidget(accept_btn)
            layout.addWidget(buttons_widget)

    def add_review_actions(self, layout, notification, dialog):
        """Add action buttons for review notifications."""
        if notification.get("can_respond", False):
            response_btn = QPushButton("Respond")
            response_btn.setStyleSheet("""
                QPushButton {
                    background-color: #D91656;
                    color: white;
                    padding: 10px;
                    border-radius: 4px;
                    font-size: 14px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #640D5F;
                }
            """)
            response_btn.clicked.connect(lambda: [
                self.parent.show_review_response_modal(notification),
                dialog.close()
            ])
            layout.addWidget(response_btn, alignment=Qt.AlignCenter)

    def add_ticket_actions(self, layout, notification, dialog):
        """Add action buttons for ticket-related notifications."""
        # Check if this is a ticket transfer notification
        if notification.get("type") == "ticket_transfer":
            # Check if this is a pending transfer request
            try:
                with open("ticket_transfer_requests.json", "r", encoding="utf-8") as f:
                    transfer_data = json.load(f)
                    request = next((req for req in transfer_data["transfer_requests"] 
                                  if req["request_id"] == notification.get("transfer_request_id") 
                                  and req["status"] == "pending"), None)
                    if request:
                        # Add action buttons
                        buttons_widget = QWidget()
                        buttons_widget.setStyleSheet("background-color: #f8f9fa; padding: 15px; border-radius: 10px;")
                        buttons_layout = QHBoxLayout(buttons_widget)
                        buttons_layout.setSpacing(15)

                        # Back button (grey)
                        back_btn = QPushButton("Πίσω")
                        back_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #6c757d;
                                color: white;
                                padding: 12px 25px;
                                border-radius: 8px;
                                font-size: 14px;
                                font-weight: bold;
                                min-width: 100px;
                            }
                            QPushButton:hover {
                                background-color: #5a6268;
                            }
                        """)
                        back_btn.clicked.connect(dialog.close)

                        # Reject button (red)
                        reject_btn = QPushButton("Απόρριψη")
                        reject_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #dc3545;
                                color: white;
                                padding: 12px 25px;
                                border-radius: 8px;
                                font-size: 14px;
                                font-weight: bold;
                                min-width: 100px;
                            }
                            QPushButton:hover {
                                background-color: #c82333;
                            }
                        """)
                        reject_btn.clicked.connect(lambda: [
                            self.parent.handle_transfer_response(notification, False),
                            dialog.close(),
                            self.load_notifications()
                        ])

                        # Accept button (green)
                        accept_btn = QPushButton("Αποδοχή")
                        accept_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #28a745;
                                color: white;
                                padding: 12px 25px;
                                border-radius: 8px;
                                font-size: 14px;
                                font-weight: bold;
                                min-width: 100px;
                            }
                            QPushButton:hover {
                                background-color: #218838;
                            }
                        """)
                        accept_btn.clicked.connect(lambda: [
                            self.parent.handle_transfer_response(notification, True),
                            dialog.close(),
                            self.load_notifications()
                        ])

                        buttons_layout.addWidget(back_btn)
                        buttons_layout.addStretch()
                        buttons_layout.addWidget(reject_btn)
                        buttons_layout.addWidget(accept_btn)
                        layout.addWidget(buttons_widget)
                        return True  # Indicate that buttons were added
                        
            except Exception as e:
                print(f"Error adding transfer action buttons: {e}")
        
        # Handle other ticket actions
        elif notification.get("can_modify", False):
            modify_btn = QPushButton("Modify Booking")
            modify_btn.setStyleSheet("""
                QPushButton {
                    background-color: #D91656;
                    color: white;
                    padding: 10px;
                    border-radius: 4px;
                    font-size: 14px;
                    min-width: 150px;
                }
                QPushButton:hover {
                    background-color: #640D5F;
                }
            """)
            modify_btn.clicked.connect(lambda: [
                self.parent.show_ticket_modification_modal(notification),
                dialog.close()
            ])
            layout.addWidget(modify_btn, alignment=Qt.AlignCenter)
            return True  # Indicate that buttons were added
        
        return False  # No buttons were added

    def filter_notifications(self):
        """Filter notifications based on selected category."""
        selected_category = self.category_combo.currentText()
        self.load_notifications(category=selected_category)

    def load_notifications(self, category="All Notifications"):
        """Load notifications for the current user."""
        # Clear existing notifications
        while self.notifications_layout.count():
            item = self.notifications_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            with open("notifications.json", "r", encoding='utf-8') as f:
                data = json.load(f)
                notifications = data.get("notifications", [])

                # Filter notifications for current user (exclude deleted ones)
                user_notifications = [
                    n for n in notifications
                    if n["user_id"] == self.parent.current_user["user_id"] and not n.get("deleted", False)
                ]

                # Apply category filter if not "All"
                if category != "All Notifications":
                    user_notifications = [
                        n for n in user_notifications
                        if n.get("category", "") == category
                    ]

                if not user_notifications:
                    no_notifications = QLabel("You have no new notifications")
                    no_notifications.setStyleSheet("""
                        color: #666;
                        font-size: 16px;
                        padding: 20px;
                        background-color: #f5f5f5;
                        border-radius: 4px;
                    """)
                    self.notifications_layout.addWidget(no_notifications, alignment=Qt.AlignCenter)
                    return

                # Sort notifications by timestamp (newest first)
                user_notifications.sort(
                    key=lambda x: datetime.strptime(x["timestamp"], "%d/%m/%Y %H:%M:%S"),
                    reverse=True
                )

                # Create notification cards
                for notification in user_notifications:
                    card = self.create_notification_card(notification)
                    self.notifications_layout.addWidget(card)

                # Add stretch at the end
                self.notifications_layout.addStretch()

        except FileNotFoundError:
            error_label = QLabel("No notifications found")
            error_label.setStyleSheet("color: #666; font-size: 16px;")
            self.notifications_layout.addWidget(error_label, alignment=Qt.AlignCenter)
        except Exception as e:
            error_label = QLabel(f"Σφάλμα κατά τη φόρτωση των ειδοποιήσεων: {str(e)}")
            error_label.setStyleSheet("color: red; font-size: 14px;")
            self.notifications_layout.addWidget(error_label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EventManagementApp()
    window.show()
    sys.exit(app.exec_())
