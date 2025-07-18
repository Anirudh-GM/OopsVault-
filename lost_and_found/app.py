from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor
import os
import uuid
from werkzeug.utils import secure_filename
import base64
from datetime import datetime
from werkzeug.security import generate_password_hash
import re

app = Flask(__name__)
app.secret_key = 'Anirudh'

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

login_manager = LoginManager()
login_manager.init_app(app)

# Set the login page for unauthenticated users
login_manager.login_view = 'login'

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Anirudh@rnsit'  # Replace with your MySQL password
app.config['MYSQL_DB'] = 'lost_and_found'

mysql = MySQL(app)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Anirudh@rnsit",
        database="lost_and_found"
    )


# Landing page

@app.route('/')
def landing_page():
    return render_template('landing_page.html')  # Create a new template for this page

@app.errorhandler(413)
def request_entity_too_large(error):
    return "File too large. Please upload a file smaller than 16MB.", 413


@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = current_user.id
    cursor = mysql.connection.cursor(DictCursor)

    # Fetch user details
    cursor.execute('SELECT user_id, name, phone FROM users WHERE user_id = %s', (user_id,))
    user = cursor.fetchone()

    # Fetch unresolved lost items (status = 'open', resolved = FALSE)
    cursor.execute('''
        SELECT * 
        FROM lost_items 
        WHERE user_id = %s AND status = 'open' AND resolved = FALSE
    ''', (user_id,))
    lost_items = cursor.fetchall()

    # Fetch resolved lost items (status = 'closed', resolved = TRUE)
    cursor.execute('''
        SELECT * 
        FROM lost_items 
        WHERE user_id = %s AND status = 'closed' AND resolved = TRUE
    ''', (user_id,))
    resolved_lost_items = cursor.fetchall()

    # Fetch unresolved found items (status = 'unclaimed', resolved = FALSE)
    cursor.execute('''
        SELECT * 
        FROM found_items 
        WHERE user_id = %s AND status = 'unclaimed' AND resolved = FALSE
    ''', (user_id,))
    found_items = cursor.fetchall()

    # Fetch resolved found items (status = 'claimed', resolved = TRUE)
    cursor.execute('''
        SELECT * 
        FROM found_items 
        WHERE user_id = %s AND status = 'claimed' AND resolved = TRUE
    ''', (user_id,))
    resolved_found_items = cursor.fetchall()

    cursor.close()

    return render_template('profile.html', 
                           user=user, 
                           lost_items=lost_items, 
                           resolved_lost_items=resolved_lost_items,
                           found_items=found_items, 
                           resolved_found_items=resolved_found_items)


@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if new_password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('edit_profile'))

    hashed_password = generate_password_hash(new_password)

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s",
                   (hashed_password, current_user.id))
    mysql.connection.commit()
    cursor.close()

    flash('Password changed successfully.')
    return redirect(url_for('edit_profile'))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']

        # Update the user's profile information in the database
        cursor.execute("UPDATE users SET name = %s, phone = %s WHERE user_id = %s",
                       (name, phone, current_user.id))
        mysql.connection.commit()
        cursor.close()

        flash('Profile updated successfully.')
        return redirect(url_for('edit_profile'))

    # For GET request, fetch the user data to prefill the form
    cursor.execute("SELECT name, phone FROM users WHERE user_id = %s", (current_user.id,))
    user_data = cursor.fetchone()
    cursor.close()

    return render_template('edit_profile.html', user=user_data)


@app.route('/edit_item/<string:item_type>/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_type, item_id):
    cursor = mysql.connection.cursor(cursorclass=DictCursor)

    # Determine table & columns based on item_type
    if item_type == 'lost':
        table = 'lost_items'
        id_column = 'lost_id'
        date_column = 'lost_date'
    else:
        table = 'found_items'
        id_column = 'found_id'
        date_column = 'found_date'

    # Get today's date in YYYY-MM-DD format
    current_date = datetime.today().strftime('%Y-%m-%d')

    if request.method == 'POST':
        item_name = request.form['item_name']
        description = request.form['description']
        location = request.form['location']
        date = request.form['date']
        photo_option = request.form.get('photo_option')
        old_photo = request.form.get('old_photo')
        new_filename = old_photo  # Default to old one unless a new one is submitted

        # Handle webcam photo
        if photo_option == 'webcam':
            photo_base64 = request.form.get('photo_base64')
            if photo_base64:
                try:
                    import base64
                    photo_data = base64.b64decode(photo_base64.split(',')[1])
                    new_filename = f"{uuid.uuid4().hex}.png"
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                    with open(photo_path, "wb") as f:
                        f.write(photo_data)
                except Exception as e:
                    flash(f"Error saving webcam image: {e}", "danger")
                    return redirect(url_for('edit_item', item_type=item_type, item_id=item_id))

        # Handle file upload
        elif photo_option == 'upload':
            photo = request.files.get('photo')
            if photo and photo.filename != '':
                new_filename = f"{uuid.uuid4().hex}_{secure_filename(photo.filename)}"
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                photo.save(photo_path)

        # Update item in the database
        try:
            cursor.execute(f'''
                UPDATE {table}
                SET item_name = %s, description = %s, location = %s, {date_column} = %s, image_filename = %s
                WHERE {id_column} = %s AND user_id = %s
            ''', (item_name, description, location, date, new_filename, item_id, current_user.id))
            mysql.connection.commit()

            # Delete old photo only if it was replaced
            if old_photo and old_photo != new_filename:
                old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], old_photo)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)

            flash('Item updated successfully.', 'success')
            return redirect(url_for('profile'))

        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error updating item: {e}", 'danger')
            return redirect(url_for('edit_item', item_type=item_type, item_id=item_id))

    # Pre-fill form with existing item details
    cursor.execute(f'SELECT * FROM {table} WHERE {id_column} = %s AND user_id = %s', (item_id, current_user.id))
    item = cursor.fetchone()
    cursor.close()

    if not item:
        flash('Item not found or unauthorized.', 'danger')
        return redirect(url_for('profile'))

    return render_template('edit_item.html', item=item, item_type=item_type, current_date=current_date)

@app.route('/delete_item/<string:item_type>/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_type, item_id):
    cursor = mysql.connection.cursor(cursorclass=DictCursor)

    # Determine table and columns
    if item_type == 'lost':
        table = 'lost_items'
        id_column = 'lost_id'
    else:
        table = 'found_items'
        id_column = 'found_id'

    try:
        # Get photo filename before deletion
        cursor.execute(f'''
            SELECT image_filename FROM {table}
            WHERE {id_column} = %s AND user_id = %s
        ''', (item_id, current_user.id))
        item = cursor.fetchone()

        if not item:
            flash('Item not found or unauthorized.', 'danger')
            return redirect(url_for('profile'))

        photo_filename = item['image_filename']

        # Delete item from DB
        cursor.execute(f'''
            DELETE FROM {table}
            WHERE {id_column} = %s AND user_id = %s
        ''', (item_id, current_user.id))
        mysql.connection.commit()

        # Delete photo from uploads folder
        if photo_filename:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            if os.path.exists(photo_path):
                os.remove(photo_path)

        flash('Item deleted successfully.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error deleting item: {e}", 'danger')
    finally:
        cursor.close()

    return redirect(url_for('profile'))


@app.route('/mark_resolved/<item_type>/<int:item_id>', methods=['GET','POST'])
@login_required
def mark_resolved(item_type, item_id):
    cur = mysql.connection.cursor()

    if item_type == 'lost':
        # Update lost item if user owns it
        cur.execute("UPDATE lost_items SET status = %s, resolved = %s WHERE lost_id = %s AND user_id = %s",
                    ('Closed', 1, item_id, current_user.id))
        if cur.rowcount > 0:
            mysql.connection.commit()
            flash('Lost item marked as closed successfully!', 'success')
        else:
            flash('Lost item not found or unauthorized.', 'danger')

    elif item_type == 'found':
        # Update found item if user owns it
        cur.execute("UPDATE found_items SET status = %s, resolved = %s WHERE found_id = %s AND user_id = %s",
                    ('Claimed', 1, item_id, current_user.id))
        if cur.rowcount > 0:
            mysql.connection.commit()
            flash('Found item marked as claimed successfully!', 'success')
        else:
            flash('Found item not found or unauthorized.', 'danger')

    else:
        flash('Invalid item type.', 'danger')

    cur.close()
    return redirect(url_for('profile'))


# Report item page
@app.route('/report_item', methods=['GET', 'POST'])
@login_required
def report_item():
    if request.method == 'POST':
        item_type = request.form['item_type']
        item_name = request.form['item_name']
        description = request.form['description']
        date = request.form['date']
        location = request.form['location']
        file = request.files.get('image')
        base64_photo = request.form.get('photo_base64')

        image_filename = None

        # If image file is uploaded
        if file and file.filename != '':
            ext = os.path.splitext(file.filename)[1]  # e.g., '.jpg'
            unique_name = secure_filename(str(uuid.uuid4()) + ext)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(save_path)
            image_filename = unique_name

        # If camera photo is captured
        elif base64_photo and base64_photo.startswith('data:image'):
            try:
                header, encoded = base64_photo.split(',', 1)
                file_data = base64.b64decode(encoded)
                ext = header.split('/')[1].split(';')[0]  # 'jpeg', 'png', etc.
                unique_name = secure_filename(str(uuid.uuid4()) + '.' + ext)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                with open(save_path, 'wb') as f:
                    f.write(file_data)
                image_filename = unique_name
            except Exception as e:
                print("Error decoding base64 image:", e)

        if not image_filename:
            # This should not happen due to front-end validation, but is a fallback
            return "Image is required", 400

        user_id = current_user.id

        cursor = mysql.connection.cursor()
        if item_type == 'lost':
            cursor.execute('''
                INSERT INTO lost_items (user_id, item_name, description, lost_date, location, image_filename)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, item_name, description, date, location, image_filename))
        else:
            cursor.execute('''
                INSERT INTO found_items (user_id, item_name, description, found_date, location, image_filename)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, item_name, description, date, location, image_filename))

        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('lost_items' if item_type == 'lost' else 'found_items'))

    return render_template('report_item.html', current_page='Report Item')

@app.route('/lost')
@login_required
def lost_items():
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute("""
        SELECT li.*, u.name AS reporter_name, u.phone AS reporter_phone
        FROM lost_items li
        JOIN users u ON li.user_id = u.user_id
        WHERE li.status = 'open'
        """)
    items = cursor.fetchall()
    cursor.close()

    return render_template('lost_items.html', items=items, current_page='Lost Items')

@app.route('/found')
@login_required
def found_items():
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute("""
        SELECT fi.*, u.name AS reporter_name, u.phone AS reporter_phone
        FROM found_items fi
        JOIN users u ON fi.user_id = u.user_id
        WHERE fi.status = 'unclaimed' AND fi.resolved = FALSE
        ORDER BY fi.posted_at DESC
    """)
    items = cursor.fetchall()
    cursor.close()

    return render_template("found_items.html", items=items)



class User(UserMixin):
    def __init__(self, user_id, name):
        self.id = user_id
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT user_id, name FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return User(result[0], result[1])
    return None

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        phone = request.form['phone']
        hashed_pw = generate_password_hash(password)

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (name, password_hash, phone) VALUES (%s, %s, %s)",
                       (name, hashed_pw, phone))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT user_id, password_hash FROM users WHERE name = %s", (name,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user[1], password):
            user_obj = User(user[0], name)
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            return "Invalid credentials"
    return render_template('login.html', current_page='Home')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing_page'))  # Redirect to landing page after logout

if __name__ == '__main__':
    app.run(debug=True)
