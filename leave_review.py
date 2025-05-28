import json
from datetime import datetime
import math
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTextEdit, QPushButton, QMessageBox, QWidget)
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QPolygonF, QPainterPath
import os

class StarRating(QWidget):
    # Signal emitted when rating changes
    ratingChanged = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)  # Enable mouse tracking for hover effects
        
        # Configuration
        self.star_count = 5
        self.star_size = 30
        self.spacing = 5
        self.current_rating = 0
        self.hover_rating = 0
        self.is_hovered = False
        
        # Colors
        self.filled_color = QColor("#FFD700")  # Gold
        self.empty_color = QColor("#D3D3D3")   # Light gray
        self.hover_color = QColor("#FFA500")   # Orange
        
        # Set fixed height based on star size
        self.setFixedHeight(self.star_size + 10)
        # Set fixed width based on stars and spacing
        self.setFixedWidth((self.star_size * self.star_count) + (self.spacing * (self.star_count - 1)) + 10)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for i in range(self.star_count):
            # Calculate star position
            x = i * (self.star_size + self.spacing)
            y = 5
            
            # Determine fill level (0 to 1)
            if self.is_hovered:
                fill = 1.0 if i < int(self.hover_rating) else (
                    self.hover_rating - int(self.hover_rating) if i == int(self.hover_rating) else 0.0
                )
                color = self.hover_color
            else:
                fill = 1.0 if i < int(self.current_rating) else (
                    self.current_rating - int(self.current_rating) if i == int(self.current_rating) else 0.0
                )
                color = self.filled_color
            
            self.draw_star(painter, x, y, fill, color)
    
    def draw_star(self, painter, x, y, fill_level, fill_color):
        # Star points for a 5-pointed star
        points = []
        center_x = x + self.star_size / 2
        center_y = y + self.star_size / 2
        outer_radius = self.star_size / 2
        inner_radius = outer_radius * 0.382  # Golden ratio for nice star shape
        
        for i in range(10):  # 5 points * 2 (outer and inner points)
            angle_rad = math.radians(i * 36 - 90)  # Convert -90 to 270 degrees to radians
            radius = outer_radius if i % 2 == 0 else inner_radius
            
            # Calculate point coordinates using math.cos and math.sin
            px = center_x + radius * math.cos(angle_rad)
            py = center_y + radius * math.sin(angle_rad)
            points.append(QPointF(px, py))
        
        # Create star path
        star_path = QPainterPath()
        polygon = QPolygonF(points)
        star_path.addPolygon(polygon)
        star_path.closeSubpath()
        
        # Draw empty star
        painter.setPen(QPen(self.empty_color, 1))
        painter.setBrush(self.empty_color)
        painter.drawPath(star_path)
        
        if fill_level > 0:
            # Create clipping path for partial fill
            clip_path = QPainterPath()
            clip_rect = QRectF(x, y, self.star_size * fill_level, self.star_size)
            clip_path.addRect(clip_rect)
            
            # Draw filled portion
            painter.setClipPath(clip_path)
            painter.setPen(QPen(fill_color, 1))
            painter.setBrush(fill_color)
            painter.drawPath(star_path)
            painter.setClipping(False)
    
    def mouseMoveEvent(self, event):
        self.is_hovered = True
        # Calculate rating based on mouse position
        x = event.pos().x()
        star_and_gap = self.star_size + self.spacing
        star_index = x // star_and_gap
        remainder = x % star_and_gap
        
        if remainder <= self.star_size:
            # Calculate partial star (in 0.5 increments)
            partial = round((remainder / self.star_size) * 2) / 2
            self.hover_rating = min(self.star_count, star_index + partial)
            self.update()
    
    def leaveEvent(self, event):
        self.is_hovered = False
        self.hover_rating = 0
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.current_rating = self.hover_rating
            self.ratingChanged.emit(self.current_rating)
            self.update()
    
    def get_rating(self):
        return self.current_rating
    
    def set_rating(self, rating):
        self.current_rating = min(max(0, rating), self.star_count)
        self.update()

class LeaveReviewModal(QDialog):
    def __init__(self, parent=None, review_type="event", event_id=None, vendor_id=None, user_id=None):
        super().__init__(parent)
        self.review_type = review_type
        self.event_id = event_id
        self.vendor_id = vendor_id
        self.user_id = user_id
        
        self.setWindowTitle("Αφήστε μια αξιολόγηση!")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Rating selection with stars
        rating_layout = QHBoxLayout()
        rating_label = QLabel("Βαθμολογία:")
        self.star_rating = StarRating()
        rating_layout.addWidget(rating_label)
        rating_layout.addWidget(self.star_rating)
        rating_layout.addStretch()
        layout.addLayout(rating_layout)
        
        # Comments section
        layout.addWidget(QLabel("Σχόλια:"))
        self.comments = QTextEdit()
        self.comments.setPlaceholderText("Γράψτε τα σχόλιά σας εδώ...")
        layout.addWidget(self.comments)
        
        # Suggestions/Improvements section
        layout.addWidget(QLabel("Προτάσεις για βελτίωση:"))
        self.suggestions = QTextEdit()
        self.suggestions.setPlaceholderText("Προτείνετε τρόπους βελτίωσης...")
        layout.addWidget(self.suggestions)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.submit_btn = QPushButton("Υποβολή")
        self.cancel_btn = QPushButton("Ακύρωση")
        
        # Style the buttons
        for btn in [self.submit_btn, self.cancel_btn]:
            btn.setStyleSheet("""
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
        
        self.submit_btn.clicked.connect(self.submit_review)
        self.cancel_btn.clicked.connect(self.handle_cancel)
        
        button_layout.addWidget(self.submit_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def can_leave_review(self):
        if self.review_type == "event":
            # Load tickets to check if user has attended
            with open("tickets.json", "r", encoding='utf-8') as f:
                tickets = json.load(f)
            
            # Load events to check if event has passed
            with open("events.json", "r", encoding='utf-8') as f:
                events = json.load(f)
            
            event = next((e for e in events if e["event_id"] == self.event_id), None)
            if not event:
                return False
                
            # Check if event date has passed
            try:
                event_date = datetime.strptime(event["start_date"], "%d/%m/%Y").date()
                if event_date > datetime.now().date():
                    return False
            except ValueError as e:
                print(f"Date parsing error: {e}")
                return False
                
            # Check if user has ticket
            user_ticket = any(t["user_id"] == self.user_id and t["event_id"] == self.event_id for t in tickets)
            return user_ticket
            
        elif self.review_type == "vendor":
            # Load events to check if event is completed
            with open("events.json", "r", encoding='utf-8') as f:
                events = json.load(f)
            
            event = next((e for e in events if e["event_id"] == self.event_id), None)
            if not event:
                return False
                
            # Check if event has ended (only check event end date, not service dates)
            try:
                # Debug current time
                current_date = datetime.now().date()
                print(f"\nDebug - Current system date: {current_date}")
                
                # Debug event dates
                print(f"Debug - Raw event end date from JSON: {event['end_date']}")
                event_end_date = datetime.strptime(event["end_date"], "%d/%m/%Y").date()
                print(f"Debug - Parsed event end date: {event_end_date}")
                
                # Debug comparison
                print(f"Debug - Current date <= Event end date? {current_date <= event_end_date}")
                print(f"Debug - Current date > Event end date? {current_date > event_end_date}")
                
                # The event must be completely over (end date must be in the past)
                if current_date <= event_end_date:
                    print("Debug - Cannot review: Event hasn't completed yet")
                    QMessageBox.warning(None, "Προσοχή", 
                                      f"Η εκδήλωση δεν έχει ολοκληρωθεί ακόμα!\n\n"
                                      f"Σημερινή ημερομηνία: {current_date.strftime('%d/%m/%Y')}\n"
                                      f"Ημερομηνία λήξης: {event_end_date.strftime('%d/%m/%Y')}")
                    return False
                else:
                    print("Debug - Can review: Event has completed")

            except ValueError as e:
                print(f"Date parsing error: {e}")
                return False
                
            # Check if user is the organizer of the event
            print(f"\nDebug - Checking organizer")
            print(f"Debug - Event organizer_id: {event.get('organizer_id')}")
            print(f"Debug - Current user_id: {self.user_id}")
            if event.get("organizer_id") != self.user_id:
                print("Debug - User is not the organizer")
                return False
            else:
                print("Debug - User is the organizer")
                
            # Check if vendor is assigned to this event (ignore service dates)
            try:
                with open("services.json", "r", encoding='utf-8') as f:
                    services = json.load(f)
                    vendor_service = next(
                        (s for s in services["services"] 
                         if s.get("vendor_id") == self.vendor_id and s.get("event_id") == self.event_id),
                        None
                    )
                    print(f"Debug - Found vendor service: {vendor_service is not None}")
                    if vendor_service is None:
                        print("Debug - No vendor service found for this event")
                        return False
                    return True
            except Exception as e:
                print(f"Debug - Error checking vendor service: {str(e)}")
                return False
            
        return False
    
    def submit_review(self):
        print("\nDebug - Starting submit_review")
        
        if not self.star_rating.get_rating():
            print("Debug - No star rating provided")
            QMessageBox.warning(self, "Σφάλμα", "Παρακαλώ δώστε μια βαθμολογία (1-5 αστέρια)")
            return

        if not self.comments.toPlainText().strip():
            print("Debug - No comments provided")
            QMessageBox.warning(self, "Σφάλμα", "Παρακαλώ γράψτε ένα σχόλιο για την εμπειρία σας")
            return

        print("Debug - About to check can_leave_review")
        can_review = self.can_leave_review()
        print(f"Debug - can_leave_review returned: {can_review}")
        
        if not can_review:
            error_msg = "Δεν μπορείτε να αφήσετε κριτική: "
            if self.review_type == "event":
                error_msg += "Η εκδήλωση δεν έχει πραγματοποιηθεί ακόμα ή δεν έχετε εισιτήριο."
            else:
                error_msg += "Η εκδήλωση δεν έχει ολοκληρωθεί ακόμα."
            
            print(f"Debug - Cannot leave review: {error_msg}")
            QMessageBox.warning(self, "Σφάλμα", error_msg)
            self.reject()
            return
            
        try:
            # Initialize or load reviews.json
            reviews_file = "reviews.json"
            reviews_template = {
                "event_reviews": [],
                "vendor_reviews": [],
                "metadata": {
                    "last_updated": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "version": "1.0"
                }
            }
            
            try:
                # Try to read existing reviews
                if os.path.exists(reviews_file):
                    with open(reviews_file, "r", encoding='utf-8') as f:
                        reviews = json.load(f)
                    # Ensure all required keys exist
                    if "event_reviews" not in reviews:
                        reviews["event_reviews"] = []
                    if "vendor_reviews" not in reviews:
                        reviews["vendor_reviews"] = []
                    if "metadata" not in reviews:
                        reviews["metadata"] = reviews_template["metadata"]
                else:
                    # Create new reviews file with template
                    reviews = reviews_template
                    with open(reviews_file, "w", encoding='utf-8') as f:
                        json.dump(reviews, f, indent=4, ensure_ascii=False)
            except (json.JSONDecodeError, FileNotFoundError):
                # If file is corrupted or any other error occurs, create new
                reviews = reviews_template
                with open(reviews_file, "w", encoding='utf-8') as f:
                    json.dump(reviews, f, indent=4, ensure_ascii=False)

            # Get current timestamp
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
                
            new_review = {
                "id": len(reviews[f"{self.review_type}_reviews"]) + 1,
                "review_type": self.review_type,
                "rating": self.star_rating.get_rating(),
                "comments": self.comments.toPlainText().strip(),
                "suggestions": self.suggestions.toPlainText().strip(),
                "created_at": current_time,
                "updated_at": current_time,
                "status": "active",
                "user": {
                    "id": self.user_id,
                    "name": self.parent().current_user.get("name", ""),
                    "surname": self.parent().current_user.get("surname", "")
                },
                "notification_status": {
                    "organizer_notified": False,
                    "vendor_notified": False,
                    "notification_sent_at": None
                },
                "metadata": {
                    "client_version": "1.0",
                    "platform": "desktop",
                    "language": "el"
                }
            }

            # Add event-specific or vendor-specific data
            if self.review_type == "event":
                with open("events.json", "r", encoding='utf-8') as f:
                    events = json.load(f)
                event = next((e for e in events if e["event_id"] == self.event_id), None)
                
                if event:
                    new_review.update({
                        "event_id": self.event_id,
                        "event_data": {
                            "title": event.get("title", ""),
                            "organizer_id": event.get("organizer_id", ""),
                            "date": event.get("start_date", "")
                        }
                    })
            else:  # vendor review
                new_review.update({
                    "vendor_id": self.vendor_id,
                    "event_id": self.event_id,
                    "service_details": {
                        "service_type": "",
                        "service_date": datetime.now().strftime("%d/%m/%Y")
                    }
                })
                
            # Add the review and update metadata
            reviews[f"{self.review_type}_reviews"].append(new_review)
            reviews["metadata"]["last_updated"] = current_time
            
            # Save the updated reviews
            with open(reviews_file, "w", encoding='utf-8') as f:
                json.dump(reviews, f, indent=4, ensure_ascii=False)

            # Send notification to the reviewed entity
            if self.review_type == "vendor":
                # Get vendor name for notification
                with open("users.json", "r", encoding='utf-8') as f:
                    users = json.load(f)
                    vendor = next((u for u in users if u["user_id"] == self.vendor_id), None)
                    vendor_name = f"{vendor['name']} {vendor['surname']}" if vendor else "Vendor"
                
                self.parent().add_notification(
                    self.vendor_id,
                    "Νέα Αξιολόγηση",
                    f"Λάβατε νέα αξιολόγηση από τον διοργανωτή {self.parent().current_user['name']} {self.parent().current_user['surname']}.",
                    category="Service Reviews",
                    additional_data={
                        "review_data": {
                            "rating": self.star_rating.get_rating(),
                            "comments": self.comments.toPlainText().strip(),
                            "suggestions": self.suggestions.toPlainText().strip(),
                            "reviewer_name": f"{self.parent().current_user['name']} {self.parent().current_user['surname']}",
                            "review_type": self.review_type
                        }
                    }
                )
                print(f"Debug - Sent notification to vendor {self.vendor_id}")
                
            else:  # event review
                # Get event organizer ID
                with open("events.json", "r", encoding='utf-8') as f:
                    events = json.load(f)
                    event = next((e for e in events if e["event_id"] == self.event_id), None)
                    if event:
                        self.parent().add_notification(
                            event["organizer_id"],
                            "Νέα Αξιολόγηση Εκδήλωσης",
                            f"Η εκδήλωση '{event['title']}' έλαβε νέα αξιολόγηση από έναν συμμετέχοντα.",
                            category="Event Reviews",
                            additional_data={
                                "review_data": {
                                    "rating": self.star_rating.get_rating(),
                                    "comments": self.comments.toPlainText().strip(),
                                    "suggestions": self.suggestions.toPlainText().strip(),
                                    "reviewer_name": f"{self.parent().current_user['name']} {self.parent().current_user['surname']}",
                                    "review_type": self.review_type,
                                    "event_title": event['title']
                                }
                            }
                        )
                        print(f"Debug - Sent notification to organizer {event['organizer_id']}")
                
            print("Debug - Notification sent successfully")
                
            QMessageBox.information(self, "Επιτυχία", "Η κριτική υποβλήθηκε με επιτυχία!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Σφάλμα", f"Αποτυχία υποβολής κριτικής: {str(e)}")
            print(f"Error details: {str(e)}")  # For debugging
            
    def handle_cancel(self):
        reply = QMessageBox.question(self, "Επιβεβαίωση Ακύρωσης", 
                                   "Είστε σίγουροι ότι θέλετε να ακυρώσετε την κριτική;",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.reject() 