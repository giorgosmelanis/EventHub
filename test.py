from PyQt5.QtWidgets import QListWidget, QVBoxLayout, QWidget, QApplication

class EventViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Create a QListWidget to display the events
        event_list_widget = QListWidget()
        event_list_widget.setStyleSheet("""
            /* Style for the QListWidget itself */
            QListWidget {
                font-size: 14px;                     /* Set font size */
                font-family: Arial, sans-serif;       /* Set font family */
                background-color: #f0f0f0;           /* Background color */
                border: 1px solid #ccc;              /* Border color and width */
                border-radius: 5px;                  /* Rounded corners */
                padding: 5px;                        /* Padding inside the widget */
                outline: none;                       /* Remove focus outline */
            }

            /* Style for individual items in the QListWidget */
            QListWidget::item {
                padding: 10px;                       /* Padding inside each item */
                border-bottom: 1px solid #ddd;       /* Bottom border for each item */
                color: #333;                         /* Text color */
                background-color: #fff;               /* Background color of items */
            }

            /* Style for items when hovered */
            QListWidget::item:hover {
                background-color: #e0e0e0;           /* Background color on hover */
                color: #000;                         /* Text color on hover */
                border-bottom: 1px solid #bbb;       /* Darker border on hover */
            }

            /* Style for selected items */
            QListWidget::item:selected {
                background-color: #0078d7;           /* Background color when selected */
                color: #fff;                         /* Text color when selected */
                border-bottom: 1px solid #005bb5;    /* Border color when selected */
            }

            /* Style for the scrollbar */
            QScrollBar:vertical {
                background-color: #f0f0f0;           /* Background color of the scrollbar */
                width: 12px;                        /* Width of the scrollbar */
                margin: 0px 0px 0px 0px;            /* Margin around the scrollbar */
            }

            /* Style for the scrollbar handle */
            QScrollBar::handle:vertical {
                background-color: #ccc;              /* Color of the scrollbar handle */
                border-radius: 6px;                  /* Rounded corners for the handle */
                min-height: 20px;                   /* Minimum height of the handle */
            }

            /* Style for the scrollbar handle when hovered */
            QScrollBar::handle:vertical:hover {
                background-color: #aaa;              /* Color of the handle on hover */
            }

            /* Style for the scrollbar add-line (bottom arrow) */
            QScrollBar::add-line:vertical {
                background: none;                   /* Remove default background */
            }

            /* Style for the scrollbar sub-line (top arrow) */
            QScrollBar::sub-line:vertical {
                background: none;                   /* Remove default background */
            }

            /* Style for the scrollbar add-page (area below the handle) */
            QScrollBar::add-page:vertical {
                background: none;                   /* Remove default background */
            }

            /* Style for the scrollbar sub-page (area above the handle) */
            QScrollBar::sub-page:vertical {
                background: none;                   /* Remove default background */
            }
        """)

        # Add sample items to the QListWidget
        event_list_widget.addItem("Event 1: Tech Conference 2023")
        event_list_widget.addItem("Event 2: Music Festival")
        event_list_widget.addItem("Event 3: Art Exhibition")

        layout.addWidget(event_list_widget)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EventViewer()
    window.show()
    sys.exit(app.exec_())