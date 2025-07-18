# OOPS!Vault - Lost and Found Portal

OOPS!Vault is a web-based Lost and Found Portal built using Flask and MySQL, designed to help users report, search, and recover lost or found items. The platform allows users to register, manage their submissions, and resolve items through an intuitive dashboard.

---

## 🌟 Features

- 🔐 **User Authentication** (Login/Signup with secure password hashing)
- 🧾 **Report Lost or Found Items** with detailed descriptions and image uploads
- 📷 **Image Capture** via camera or file upload with preview before submission
- 🔍 **View Lost and Found Items** categorized by status and type
- 🧑‍💼 **User Profile Dashboard** showing personal submissions
- ✏️ **Edit/Delete Items** anytime
- ✅ **Mark Items as Found/Returned**
- 🧭 **Navigation Bar** with dynamic links and current page indication

---

## 🛠️ Tech Stack

| Layer        | Technology             |
|--------------|------------------------|
| Frontend     | HTML, CSS, Bootstrap   |
| Backend      | Python (Flask)         |
| Database     | MySQL (via flask_mysqldb) |
| Auth         | Flask-Login, Werkzeug  |

---

## 📁 Project Structure

OOPSVault/
├── static/
│ └── uploads/ # Uploaded item images
├── templates/
│ ├── base.html # Common layout
│ ├── index.html # Homepage
│ ├── login.html # Login page
│ ├── signup.html # Signup page
│ ├── report_item.html # Item reporting form
│ ├── lost_items.html # Lost items list
│ ├── found_items.html # Found items list
│ ├── profile.html # User profile page
│ ├── edit_item.html # Edit item details
├── app.py # Main Flask app
├── db_config.py # MySQL DB config
├── requirements.txt # Python dependencies
└── README.md # Project description


---

## ⚙️ Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/OOPSVault.git
   cd OOPSVault

2.Create virtual environment & install dependencies:

  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install -r requirements.txt

3.Configure MySQL database:

Create a database: lost_and_found1

Import the provided SQL schema (optional, if available)

Set DB credentials in db_config.py

4.Run the app:

python app.py

5.Visit in browser:

http://127.0.0.1:5000/


