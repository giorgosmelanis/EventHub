from graphviz import Digraph

# Δημιουργία του διαγράμματος
dot = Digraph('Domain Model v0.1', format='pdf')

# Προσθήκη κλάσεων
dot.node("User", "User")
dot.node("Organizer", "Organizer")
dot.node("Attendee", "Attendee")
dot.node("Vendor", "Vendor")
dot.node("Event", "Event")
dot.node("Ticket", "Ticket")
dot.node("VendorService", "VendorService")
dot.node("Proposal", "Proposal")
dot.node("Review", "Review")
dot.node("Transaction", "Transaction")
dot.node("Refund", "Refund")
dot.node("History", "History")
dot.node("Notification", "Notification")
dot.node("Media", "Media")

# Κληρονομικότητα
dot.edge("User", "Organizer", arrowhead="empty")
dot.edge("User", "Attendee", arrowhead="empty")
dot.edge("User", "Vendor", arrowhead="empty")

# Σχέσεις
dot.edge("Organizer", "Event", label="creates", arrowhead="crow")
dot.edge("Attendee", "Ticket", label="buys", arrowhead="crow")
dot.edge("Ticket", "Event", label="is for", arrowhead="crow")
dot.edge("Vendor", "VendorService", label="offers", arrowhead="crow")
dot.edge("VendorService", "Proposal", label="relates to", arrowhead="crow")
dot.edge("Proposal", "Event", label="applies to", arrowhead="crow")
dot.edge("Attendee", "Review", label="submits", arrowhead="crow")
dot.edge("Organizer", "Review", label="reviews", arrowhead="crow")
dot.edge("Transaction", "Ticket", label="processes", arrowhead="crow")
dot.edge("Transaction", "VendorService", label="pays for", arrowhead="crow")
dot.edge("Refund", "Transaction", label="relates to", arrowhead="crow")
dot.edge("History", "User", label="logs actions", arrowhead="crow")
dot.edge("Notification", "User", label="notifies", arrowhead="crow")
dot.edge("Media", "Event", label="attaches to", arrowhead="crow")

# Αποθήκευση και εμφάνιση του διαγράμματος
diagram_path = "C:/Users/gmela/Desktop/domain_model_v0.1"
dot.render(diagram_path, format='pdf', cleanup=True)

# Επιστροφή του αρχείου στον χρήστη
diagram_path
