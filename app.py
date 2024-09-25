from flask import Flask, request, render_template, redirect, url_for, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Used for flash messages
app.config["MONGO_URI"] = "mongodb://localhost:27017/EventApp"
mongo = PyMongo(app)

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin321"

# Event Types
EVENT_TYPES = ["meet up", "conference", "party", "festival"]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Admin login
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            
            return redirect(url_for('admin_dashboard'))

        # User login
        user = mongo.db.users.find_one({"username": username})
        if user and user['password'] == password:
            if ObjectId.is_valid(user['_id']):
             return redirect(url_for('user_dashboard', user_id=user['_id']))
        else:
            flash("Invalid credentials. Please try again.", "error")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists
        if mongo.db.users.find_one({"username": username}):
            flash("Username already exists. Please choose a different one.", "error")
            return render_template('register.html')
        elif mongo.db.users.find_one({"email": email}):
            flash("Email already exists. Please choose a different one.", "error")
            return render_template('register.html')

        # Create new user
        mongo.db.users.insert_one({
            'username': username,
            'password': password,
            'name' : name,
            'surname' : surname,
            'email' : email,
            'role': 'user'
        })
        flash("Registration successful! You can now log in.", "success")

        return redirect(url_for('login'))

    return render_template('register.html')

### Admin Dashboard ###
@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    users = list(mongo.db.users.find())
    events = list(mongo.db.events.find())
    
    # Έλεγξε αν υπάρχουν χρήστες
    if not users:
        flash("No users found.", "info")
        if not users:
            flash("No users found in the database.", "error")

    # Έλεγξε αν υπάρχουν events
    if not events:
        flash("No events found.", "info")

    # Filter out the creator's events and events user is interested in
    created_events = [event for event in events if event['creator_id'] == "admin"]
    participating_events = [event for event in events if "admin" in event.get('participants', [])]

    # Fetch usernames for creator and participants
    for event in events:
        participant_usernames = []
        maybe_usernames = []

        # Διαχείριση συμμετεχόντων
        for participant_id in event.get('participants', []):
            if participant_id == "admin":
                participant_usernames.append("Admin")
            elif ObjectId.is_valid(participant_id):
                participant = mongo.db.users.find_one({"_id": ObjectId(participant_id)})
                if participant:
                    participant_usernames.append(participant['username'])
        event['participant_usernames'] = participant_usernames

        # Διαχείριση 'Maybe' χρηστών
        for maybe_id in event.get('maybe', []):
            if maybe_id == "admin":
                maybe_usernames.append("Admin")
            elif ObjectId.is_valid(maybe_id):
                maybe_user = mongo.db.users.find_one({"_id": ObjectId(maybe_id)})
                if maybe_user:
                    maybe_usernames.append(maybe_user['username'])
        event['maybe_usernames'] = maybe_usernames


    # Εκδηλώσεις που έχει δημιουργήσει ο χρήστης
    created_events = list(mongo.db.events.find({"creator_id": "admin"}))

    # Εκδηλώσεις στις οποίες συμμετέχει ο χρήστης (Interested)
    participating_events = list(mongo.db.events.find({"participants": "admin"}))

    # Εκδηλώσεις στις οποίες έχει δηλώσει 'Maybe' ο χρήστης
    maybe_events = list(mongo.db.events.find({"maybe": "admin"}))

    for event in created_events + participating_events + maybe_events:
        if event['creator_id'] == "admin":
            event['creator_username'] = "Admin"
        else:
            # Μόνο αν το creator_id δεν είναι "admin", τότε το μετατρέπουμε σε ObjectId
            if ObjectId.is_valid(event['creator_id']):
                creator = mongo.db.users.find_one({"_id": ObjectId(event['creator_id'])})
                event['creator_username'] = creator['username'] if creator else 'Unknown'
            else:
                event['creator_username'] = 'Unknown'

        participant_usernames = []
        maybe_usernames = []

        # Διαχείριση συμμετεχόντων
        for participant_id in event.get('participants', []):
            if participant_id == "admin":
                participant_usernames.append("Admin")
            elif ObjectId.is_valid(participant_id):
                participant = mongo.db.users.find_one({"_id": ObjectId(participant_id)})
                if participant:
                    participant_usernames.append(participant['username'])
        event['participant_usernames'] = participant_usernames

        # Διαχείριση 'Maybe' χρηστών
        for maybe_id in event.get('maybe', []):
            if maybe_id == "admin":
                maybe_usernames.append("Admin")
            elif ObjectId.is_valid(maybe_id):
                maybe_user = mongo.db.users.find_one({"_id": ObjectId(maybe_id)})
                if maybe_user:
                    maybe_usernames.append(maybe_user['username'])
        event['maybe_usernames'] = maybe_usernames

        # If a search query is posted, update the events list
    if request.method == 'POST':
        search_title = request.form.get('search_title', '').strip()
        search_type = request.form.get('search_type', '').strip()
        search_location = request.form.get('search_location', '').strip()

        query = {}

        if search_title:
            query['name'] = {'$regex': search_title, '$options': 'i'}  # Case-insensitive search
        if search_type:
            query['type'] = search_type
        if search_location:
            query['location'] = {'$regex': search_location, '$options': 'i'}  # Case-insensitive

        # Fetch the filtered events
        events = list(mongo.db.events.find(query))

    return render_template(
        'admin_dashboard.html',
        user="admin",
        users=users,
        events=events,
        created_events=created_events,
        participating_events=participating_events,
        maybe_events=maybe_events
    )

@app.route('/admin/event/<event_id>/update', methods=['POST'])
def admin_update_event(event_id):
    # Λήψη των δεδομένων της φόρμας
    name = request.form.get('name')
    description = request.form.get('description')
    date = request.form.get('date')
    time = request.form.get('time')
    location = request.form.get('location')
    event_type = request.form.get('type')

    # Ενημέρωση του event στη βάση δεδομένων
    mongo.db.events.update_one(
        {"_id": ObjectId(event_id)},
        {"$set": {
            'name': name,
            'description': description,
            'date': date,
            'time': time,
            'location': location,
            'type': event_type
        }}
    )

    flash("Event updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))

### User Dashboard ###
@app.route('/user/<user_id>/dashboard', methods=['GET', 'POST'])
def user_dashboard(user_id):
    if ObjectId.is_valid(user_id):
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    else:
        # Handle error case where user_id is not a valid ObjectId
        flash("Invalid User ID", "error")
        return redirect(url_for('login'))

    # All events initially
    query = {}
    events = list(mongo.db.events.find(query))

    # Filter out the creator's events and events user is interested in
    created_events = [event for event in events if event['creator_id'] == user_id]
    participating_events = [event for event in events if user_id in event.get('participants', [])]
    
    # If a search query is posted, update the events list
    if request.method == 'POST':
        search_title = request.form.get('search_title', '').strip()
        search_type = request.form.get('search_type', '').strip()
        search_location = request.form.get('search_location', '').strip()

        query = {}

        if search_title:
            query['name'] = {'$regex': search_title, '$options': 'i'}  # Case-insensitive search
        if search_type:
            query['type'] = search_type
        if search_location:
            query['location'] = {'$regex': search_location, '$options': 'i'}  # Case-insensitive

        # Fetch the filtered events
        events = list(mongo.db.events.find(query))

    # Εκδηλώσεις που έχει δημιουργήσει ο χρήστης
    created_events = list(mongo.db.events.find({"creator_id": user_id}))

    # Εκδηλώσεις στις οποίες συμμετέχει ο χρήστης (Interested)
    participating_events = list(mongo.db.events.find({"participants": user_id}))

    # Εκδηλώσεις στις οποίες έχει δηλώσει 'Maybe' ο χρήστης
    maybe_events = list(mongo.db.events.find({"maybe": user_id}))

    # Προσθήκη των usernames για δημιουργούς, συμμετέχοντες και χρήστες που είναι 'Maybe'
    for event in created_events + participating_events + maybe_events:
        if event['creator_id']=="admin":
            event['creator_username']="Admin"
        else: 
            creator = mongo.db.users.find_one({"_id": ObjectId(event['creator_id'])})
            event['creator_username'] = creator['username'] if creator else 'Unknown'

        # Fetch usernames for creator and participants
    for event in events:
        # Έλεγχος αν το creator_id είναι "admin"
        if event['creator_id'] == "admin":
            event['creator_username'] = "Admin"
        else:
            creator = mongo.db.users.find_one({"_id": ObjectId(event['creator_id'])})
            event['creator_username'] = creator['username'] if creator else 'Unknown'

        # Λίστα συμμετεχόντων
        participant_usernames = []
        for participant_id in event.get('participants', []):
            # Ελέγχουμε αν ο συμμετέχων είναι ο admin
            if participant_id == "admin":
                participant_usernames.append("Admin")
            # Ελέγχουμε αν είναι έγκυρο ObjectId για άλλους χρήστες
            elif ObjectId.is_valid(participant_id):
                participant = mongo.db.users.find_one({"_id": ObjectId(participant_id)})
                if participant:
                    participant_usernames.append(participant['username'])
        event['participant_usernames'] = participant_usernames

        # Λίστα χρηστών που είναι 'Maybe'
        maybe_usernames = []
        for maybe_id in event.get('maybe', []):
            if maybe_id == "admin":
                maybe_usernames.append("Admin")
            elif ObjectId.is_valid(maybe_id):
                maybe_user = mongo.db.users.find_one({"_id": ObjectId(maybe_id)})
                if maybe_user:
                    maybe_usernames.append(maybe_user['username'])
        event['maybe_usernames'] = maybe_usernames

    return render_template(
        'user_dashboard.html',
        user=user,
        events=events,
        created_events=created_events,
        participating_events=participating_events,
        maybe_events=maybe_events
    )


@app.route('/event/<event_id>')
def view_event(event_id):
    # Βρίσκουμε την εκδήλωση με βάση το ID
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    
    if event:
        # Βρίσκουμε τα usernames των συμμετεχόντων
        participant_usernames = []
        for participant_id in event.get('participants', []):
            participant = mongo.db.users.find_one({"_id": ObjectId(participant_id)})
            if participant:
                participant_usernames.append(participant['username'])

        # Βρίσκουμε τα usernames των χρηστών που έχουν δηλώσει "Maybe"
        maybe_usernames = []
        for maybe_id in event.get('maybe', []):
            maybe_user = mongo.db.users.find_one({"_id": ObjectId(maybe_id)})
            if maybe_user:
                maybe_usernames.append(maybe_user['username'])
        
        return render_template('view_event.html', event=event, participant_usernames=participant_usernames, maybe_usernames=maybe_usernames)
    else:
        flash("Event not found!", "error")
        return redirect(url_for('user_dashboard', user_id=request.args.get('user_id')))


### Create Event (for Admins and Users) ###
@app.route('/events/create', methods=['POST'])
def create_event():
    user_id = request.form.get('user_id')
    
    # If the user is admin, handle it differently
    if user_id == "admin":
        creator_id = "admin"
        creator_username = ADMIN_USERNAME  # Ορίζεις το username του admin
    else:
        creator_id = ObjectId(user_id)  # Μετατρέπεις σε ObjectId για κανονικούς χρήστες
        user = mongo.db.users.find_one({"_id": creator_id})
        creator_username = user['username'] if user else 'Unknown'

    # Μετατροπή της ημερομηνίας και ώρας από string σε datetime
    event_date_str = request.form['date']  # Π.χ. "2024-09-25"
    event_time_str = request.form['time']  # Π.χ. "14:30"
    
    # Συνδυασμός της ημερομηνίας και της ώρας σε datetime
    event_date_str = request.form['date']  # Παίρνουμε την ημερομηνία ως string
    event_date = datetime.strptime(event_date_str, '%Y-%m-%d')  # Μετατροπή σε datetime

    if event_date <= datetime.now():
        flash("Event date invalid please choose a date after the today.", "error")
        if user_id == "admin":
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard', user_id=user_id))
    
    creator_id = ObjectId(user_id) if user_id != "admin" else "admin"
    # Create event
    event = {
        'name': request.form['name'],
        'description': request.form['description'],
        'date': event_date,  # Αποθήκευση ως datetime στη MongoDB
        'location': request.form['location'],
        'type': request.form['type'],
        'creator_id': creator_id,  # Admin or user
        'creator_username': creator_username,
        'participants': [],
        'maybe': []
    }
    mongo.db.events.insert_one(event)
    
    return redirect(url_for('user_dashboard', user_id=user_id))

### Edit Event (User Can Only Edit Their Own Events) ###
@app.route('/events/<event_id>/edit', methods=['POST'])
def edit_event(event_id):
    user_id = request.form.get('user_id')
    event = mongo.db.events.find_one({"_id": ObjectId(event_id), "creator_id": ObjectId(user_id)})
    
    # Για admin δεν κάνουμε ObjectId conversion
    if user_id == "admin":
        event = mongo.db.events.find_one({"_id": ObjectId(event_id), "creator_id": "admin"})
    else:
        event = mongo.db.events.find_one({"_id": ObjectId(event_id), "creator_id": ObjectId(user_id)})

    if not event:
        flash("You are not allowed to edit this event.", "error")
        return redirect(url_for('user_dashboard', user_id=user_id))

    mongo.db.events.update_one(
        {"_id": ObjectId(event_id)},
        {"$set": {
            'name': request.form['name'],
            'description': request.form['description'],
            'date': request.form['date'],
            'time': request.form['time'],
            'location': request.form['location'],
            'type': request.form['type']
        }}
    )
    flash("You successfully edited your event!", "success")
    return redirect(url_for('user_dashboard', user_id=user_id))

### Delete Event (User Can Only Delete Their Own Events) ###
@app.route('/events/<event_id>/delete', methods=['POST'])
def delete_event(event_id):
    user_id = request.form.get('user_id')

    # Convert user_id to ObjectId for proper comparison
    try:
        user_id = ObjectId(user_id)  # Convert to ObjectId
    except Exception:
        flash("Invalid user ID.", "error")
        return redirect(url_for('user_dashboard', user_id=user_id))

    # Find the event by event ID and creator ID
    event = mongo.db.events.find_one({"_id": ObjectId(event_id), "creator_id": user_id})

    # If the event does not exist or the user is not the creator, deny deletion
    if not event:
        flash("You are not allowed to delete this event.", "error")
        return redirect(url_for('user_dashboard', user_id=user_id))

    # Delete the event if the user is the creator
    mongo.db.events.delete_one({"_id": ObjectId(event_id)})
    flash("Event deleted successfully!", "success")
    
    return redirect(url_for('user_dashboard', user_id=user_id))


### Participate in an Event (Any User Can Participate) ###
@app.route('/events/<event_id>/participate', methods=['POST'])
def participate_event(event_id):
    user_id = request.form.get('user_id')
    
    # Αν το user_id είναι 'admin', μην προσπαθήσεις να βρεις ObjectId
    if user_id == 'admin':
        username = 'Admin'
    else:
        # Για τους κανονικούς χρήστες, ελέγξτε αν είναι έγκυρο ObjectId
        if not ObjectId.is_valid(user_id):
            flash("Invalid User ID", "error")
            return redirect(url_for('login'))
        
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            flash("User not found", "error")
            return redirect(url_for('login'))
        username = user['username']

    # Αφαίρεση του χρήστη από τη λίστα "Maybe" αν υπάρχει
    mongo.db.events.update_one(
        {"_id": ObjectId(event_id)},
        {"$pull": {"maybe": user_id}}  # Αφαίρεση από τους "Maybe"
    )

    # Προσθήκη του χρήστη στη λίστα "Interested"
    mongo.db.events.update_one(
        {"_id": ObjectId(event_id)},
        {"$addToSet": {"participants": user_id}}  # Προσθήκη στους "Interested"
    )

    flash(f"{username} has participated in this event", "success")
    # Ανακατεύθυνση στο σωστό dashboard για τον χρήστη ή τον admin
    if user_id == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('user_dashboard', user_id=user_id))


@app.route('/events/<event_id>/maybe_participate', methods=['POST'])
def maybe_participate_event(event_id):
    user_id = request.form.get('user_id')
    # Αν το user_id είναι 'admin', μην προσπαθήσεις να βρεις ObjectId
    if user_id == 'admin':
        username = 'Admin'
    else:
        # Για τους κανονικούς χρήστες, έλεγξε αν είναι έγκυρο ObjectId
        if not ObjectId.is_valid(user_id):
            flash("Invalid User ID", "error")
            return redirect(url_for('login'))
        
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            flash("User not found", "error")
            return redirect(url_for('login'))
        
        username = user['username']
    # Αφαίρεση του χρήστη από τη λίστα "Interested" αν υπάρχει
    mongo.db.events.update_one(
        {"_id": ObjectId(event_id)},
        {"$pull": {"participants": user_id}}  # Αφαίρεση από τους "Interested"
    )

    # Προσθήκη του χρήστη στη λίστα "Maybe"
    mongo.db.events.update_one(
        {"_id": ObjectId(event_id)},
        {"$addToSet": {"maybe": user_id}}  # Προσθήκη στους "Maybe"
    )
    flash(f"{username} has maybe participated in this event", "success")

    # Ανακατεύθυνση στο σωστό dashboard για τον χρήστη ή τον admin
    if user_id == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('user_dashboard', user_id=user_id))


### Search Events ###
@app.route('/search_events', methods=['GET'])
def search_events():
    search_title = request.args.get('search_title')
    search_type = request.args.get('search_type')
    search_location = request.args.get('search_location')

    # Έλεγχος αν όλα τα πεδία είναι κενά
    if not search_title and not search_type and not search_location:
        flash("Please fill in at least one search field!", "error")
        return redirect(url_for('user_dashboard', user_id=request.args.get('user_id')))

    # Δημιουργία του query για αναζήτηση
    query = {}

    # Αν έχει συμπληρωθεί ο τίτλος, προσθέτουμε στο query το όνομα
    if search_title:
        query['name'] = {'$regex': search_title, '$options': 'i'}  # Case-insensitive αναζήτηση

    # Αν έχει συμπληρωθεί ο τύπος εκδήλωσης, προσθέτουμε στο query το type
    if search_type:
        query['type'] = search_type

    # Αν έχει συμπληρωθεί η τοποθεσία, προσθέτουμε στο query την τοποθεσία
    if search_location:
        query['location'] = {'$regex': search_location, '$options': 'i'}  # Case-insensitive αναζήτηση

    # Αναζήτηση στη βάση δεδομένων με το query που φτιάξαμε
    events = list(mongo.db.events.find(query))

    # Ενημέρωση των στοιχείων για δημιουργούς και συμμετέχοντες
    for event in events:
        if 'creator_id' in event:
            creator = mongo.db.users.find_one({"_id": ObjectId(event['creator_id'])})
            event['creator_username'] = creator['username'] if creator else 'Unknown'

        # Fetch usernames for participants
        participant_usernames = []
        for participant_id in event.get('participants', []):
            if participant_id == "admin":
                participant_usernames.append("Admin")
            elif ObjectId.is_valid(participant_id):
                participant = mongo.db.users.find_one({"_id": ObjectId(participant_id)})
                if participant:
                    participant_usernames.append(participant['username'])
        event['participant_usernames'] = participant_usernames

        # Fetch usernames for maybe users
        maybe_usernames = []
        for maybe_id in event.get('maybe', []):
            if maybe_id == "admin":
                maybe_usernames.append("Admin")
            elif ObjectId.is_valid(maybe_id):
                maybe_user = mongo.db.users.find_one({"_id": ObjectId(maybe_id)})
                if maybe_user:
                    maybe_usernames.append(maybe_user['username'])
        event['maybe_usernames'] = maybe_usernames

    flash("Please fill in at least one search field!", "error")
    # Επιστροφή στη σελίδα αναζήτησης με τα αποτελέσματα
    flash("These are your searched results!", "success")
    return render_template('search_results.html', events=events)

###event edit by user 
@app.route('/events/<event_id>/toggle_edit', methods=['POST'])
def toggle_edit_event(event_id):
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    
    # Toggle the 'is_editing' field in the event document
    new_edit_status = not event.get("is_editing", False)
    mongo.db.events.update_one(
        {"_id": ObjectId(event_id)},
        {"$set": {"is_editing": new_edit_status}}
    )
    
    flash("Edit mode toggled!", "success")
    return redirect(url_for('user_dashboard', user_id=event['creator_id']))

### Admin Deletes Any Event ###
@app.route('/admin/event/<event_id>/delete', methods=['POST'])
def admin_delete_event(event_id):
    mongo.db.events.delete_one({"_id": ObjectId(event_id)})
    flash("Event deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

### Admin Deletes Any User ###
@app.route('/admin/user/<user_id>/delete', methods=['POST'])
def admin_delete_user(user_id):
    mongo.db.users.delete_one({"_id": ObjectId(user_id)})
    flash("User deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

if __name__ == "__main__":
    app.run(debug=True)
