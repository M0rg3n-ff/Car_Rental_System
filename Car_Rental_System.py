import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
app.secret_key = 'super_secret_car_rental_key'
DATABASE = 'car_rental.db'

# --- DATABASE SETUP & HELPERS ---

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Enable Foreign Keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT CHECK(role IN ('Admin', 'Staff', 'User')) NOT NULL
        )
    ''')

    # 2. Cars Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Cars (
            car_id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            license_plate TEXT UNIQUE NOT NULL,
            status TEXT CHECK(status IN ('Available', 'Rented', 'Maintenance')) DEFAULT 'Available',
            rental_rate REAL NOT NULL
        )
    ''')

    # 3. Drivers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Drivers (
            driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            license_number TEXT UNIQUE NOT NULL,
            status TEXT CHECK(status IN ('Available', 'Assigned', 'On-Leave')) DEFAULT 'Available'
        )
    ''')

    # 4. Appointments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            driver_id INTEGER,
            appointment_date TEXT NOT NULL,
            fulfillment_type TEXT CHECK(fulfillment_type IN ('Pick-up', 'Service')) NOT NULL,
            status TEXT DEFAULT 'Confirmed',
            FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
            FOREIGN KEY (car_id) REFERENCES Cars (car_id) ON DELETE CASCADE,
            FOREIGN KEY (driver_id) REFERENCES Drivers (driver_id) ON DELETE SET NULL
        )
    ''')

    # 5. Payments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER UNIQUE NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            payment_date TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Successful',
            FOREIGN KEY (appointment_id) REFERENCES Appointments (appointment_id) ON DELETE CASCADE
        )
    ''')

    # 6. Expenses Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            expense_date TEXT NOT NULL,
            FOREIGN KEY (car_id) REFERENCES Cars (car_id) ON DELETE CASCADE
        )
    ''')

    # Seed Initial Data
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Users (username, password, full_name, role) VALUES ('admin', 'admin123', 'System Admin', 'Admin')")
        cursor.execute("INSERT INTO Users (username, password, full_name, role) VALUES ('staff', 'staff123', 'System Staff', 'Staff')")
        cursor.execute("INSERT INTO Users (username, password, full_name, role) VALUES ('johndoe', '123', 'John Doe', 'User')")
        
        # Extended Car Inventory
        cursor.execute("INSERT INTO Cars (model, license_plate, status, rental_rate) VALUES ('Toyota Vios 2023', 'NXX-1029', 'Available', 1800.00)")
        cursor.execute("INSERT INTO Cars (model, license_plate, status, rental_rate) VALUES ('Mitsubishi Montero Sport', 'BAL-8831', 'Available', 3500.00)")
        cursor.execute("INSERT INTO Cars (model, license_plate, status, rental_rate) VALUES ('Nissan NV350 Urvan', 'CBA-4420', 'Rented', 4000.00)")
        cursor.execute("INSERT INTO Cars (model, license_plate, status, rental_rate) VALUES ('Honda City RS', 'EAG-9912', 'Maintenance', 2200.00)")
        cursor.execute("INSERT INTO Cars (model, license_plate, status, rental_rate) VALUES ('Ford Ranger Wildtrak', 'SBT-7721', 'Available', 3800.00)")
        cursor.execute("INSERT INTO Cars (model, license_plate, status, rental_rate) VALUES ('Toyota Innova E', 'XYZ-5541', 'Available', 2500.00)")
        cursor.execute("INSERT INTO Cars (model, license_plate, status, rental_rate) VALUES ('Honda Civic RS Turbo', 'ABC-1234', 'Available', 3000.00)")
        cursor.execute("INSERT INTO Cars (model, license_plate, status, rental_rate) VALUES ('Toyota Hiace Commuter', 'VAN-8899', 'Available', 4500.00)")

        cursor.execute("INSERT INTO Drivers (full_name, phone_number, license_number, status) VALUES ('Pedro Penduko', '09171234567', 'N01-12-345678', 'Available')")
        cursor.execute("INSERT INTO Drivers (full_name, phone_number, license_number, status) VALUES ('Ricardo Dalisay', '09189876543', 'N02-98-765432', 'Available')")

        cursor.execute("INSERT INTO Expenses (car_id, description, amount, expense_date) VALUES (4, 'Engine Oil Change & Brake Replacement', 4500.00, '2026-10-05')")
        cursor.execute("INSERT INTO Expenses (car_id, description, amount, expense_date) VALUES (2, 'Tire Alignment & Balancing', 2800.00, '2026-10-02')")

    conn.commit()
    conn.close()


# --- BACKEND API ROUTES ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Users (username, password, full_name, role) VALUES (?, ?, ?, 'User')",
            (data['username'], data['password'], data['full_name'])
        )
        conn.commit()
        user_id = cursor.lastrowid
        user = {'user_id': user_id, 'username': data['username'], 'full_name': data['full_name'], 'role': 'User'}
        return jsonify({'success': True, 'user': user})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Username already exists!'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data['username'].strip()
    password = data['password'].strip()

    if username == 'admin' and password == 'admin123':
        return jsonify({
            'success': True, 
            'user': {'user_id': 1, 'username': 'admin', 'full_name': 'System Admin', 'role': 'Admin'}
        })
    elif username == 'staff' and password == 'staff123':
        return jsonify({
            'success': True, 
            'user': {'user_id': 2, 'username': 'staff', 'full_name': 'System Staff', 'role': 'Staff'}
        })

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password))
    row = cursor.fetchone()
    conn.close()
    if row:
        user = dict(row)
        return jsonify({'success': True, 'user': user})
        
    return jsonify({'success': False, 'message': 'Invalid username or password!'}), 401

@app.route('/api/data', methods=['GET'])
def get_data():
    conn = get_db()
    cursor = conn.cursor()
    
    cars = [dict(r) for r in cursor.execute("SELECT * FROM Cars").fetchall()]
    drivers = [dict(r) for r in cursor.execute("SELECT * FROM Drivers").fetchall()]
    appointments = [dict(r) for r in cursor.execute("SELECT * FROM Appointments").fetchall()]
    payments = [dict(r) for r in cursor.execute("SELECT * FROM Payments").fetchall()]
    expenses = [dict(r) for r in cursor.execute("SELECT * FROM Expenses").fetchall()]
    users = [dict(r) for r in cursor.execute("SELECT user_id, username, full_name, role FROM Users").fetchall()]
    
    conn.close()
    return jsonify({
        'cars': cars,
        'drivers': drivers,
        'appointments': appointments,
        'payments': payments,
        'expenses': expenses,
        'users': users
    })

@app.route('/api/book', methods=['POST'])
def book_appointment():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    car_id = data['car_id']
    
    cursor.execute("SELECT status FROM Cars WHERE car_id = ?", (car_id,))
    car = cursor.fetchone()
    if not car or car['status'] == 'Rented' or car['status'] == 'Maintenance':
        conn.close()
        return jsonify({'success': False, 'message': 'Selected car is no longer available!'}), 400

    cursor.execute(
        "INSERT INTO Appointments (user_id, car_id, driver_id, appointment_date, fulfillment_type, status) VALUES (?, ?, ?, ?, ?, 'Confirmed')",
        (data['user_id'], car_id, data['driver_id'], data['appointment_date'], data['fulfillment_type'])
    )
    app_id = cursor.lastrowid
    
    cursor.execute(
        "INSERT INTO Payments (appointment_id, amount, payment_method) VALUES (?, ?, ?)",
        (app_id, data['amount'], data['payment_method'])
    )
    
    cursor.execute("UPDATE Cars SET status = 'Rented' WHERE car_id = ?", (car_id,))
    
    if data['driver_id']:
        cursor.execute("UPDATE Drivers SET status = 'Assigned' WHERE driver_id = ?", (data['driver_id'],))

    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/cancel-appointment', methods=['POST'])
def cancel_appointment():
    data = request.json
    appointment_id = data.get('appointment_id')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM Appointments WHERE appointment_id = ?", (appointment_id,))
    app_row = cursor.fetchone()
    
    if not app_row:
        conn.close()
        return jsonify({'success': False, 'message': 'Appointment not found!'}), 404
        
    if app_row['status'] == 'Cancelled':
        conn.close()
        return jsonify({'success': False, 'message': 'Appointment is already cancelled!'}), 400

    car_id = app_row['car_id']
    driver_id = app_row['driver_id']

    cursor.execute("UPDATE Appointments SET status = 'Cancelled' WHERE appointment_id = ?", (appointment_id,))
    cursor.execute("UPDATE Cars SET status = 'Available' WHERE car_id = ?", (car_id,))
    
    if driver_id:
        cursor.execute("UPDATE Drivers SET status = 'Available' WHERE driver_id = ?", (driver_id,))
        
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/update-car-status', methods=['POST'])
def update_car_status():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE Cars SET status = ? WHERE car_id = ?", (data['status'], data['car_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# --- FRONTEND TEMPLATE ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DriveEase - Car Rental System</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: { 50: '#eef2ff', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca' }
          }
        }
      }
    }
  </script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen font-sans flex flex-col">

  <!-- TOP NAVBAR -->
  <nav class="bg-slate-800/85 backdrop-blur border-b border-slate-700 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center gap-3">
          <div class="bg-brand-600 p-2 rounded-lg text-white">
            <i class="fa-solid fa-car-side text-xl"></i>
          </div>
          <span class="font-bold text-xl tracking-tight text-white">DriveEase <span class="text-brand-500 text-xs uppercase px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">Python Edition</span></span>
        </div>

        <div id="nav-user-info" class="hidden flex items-center gap-4">
          <div class="text-right">
            <div id="user-display-name" class="font-semibold text-sm text-slate-200">Username</div>
            <div id="user-display-role" class="text-xs text-brand-400 font-medium uppercase tracking-wider">Role</div>
          </div>
          <button onclick="logout()" class="bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm px-3 py-1.5 rounded-lg transition border border-slate-600">
            <i class="fa-solid fa-right-from-bracket mr-1"></i> Logout
          </button>
        </div>
      </div>
    </div>
  </nav>

  <!-- MAIN CONTAINER -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">

    <!-- LANDING PAGE -->
    <div id="view-landing" class="max-w-md mx-auto my-12 bg-slate-800 rounded-2xl border border-slate-700 p-8 shadow-2xl text-center">
      <div class="w-16 h-16 bg-brand-600/20 border border-brand-500/30 text-brand-400 rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl">
        <i class="fa-solid fa-database"></i>
      </div>
      <h2 class="text-2xl font-bold text-white mb-2">Welcome to DriveEase</h2>
      <p class="text-slate-400 text-sm mb-6">Car Rental System (Persistent SQLite Backend)</p>
      
      <div class="space-y-3">
        <button onclick="showAuthView('login')" class="w-full bg-brand-600 hover:bg-brand-500 text-white font-medium py-3 rounded-xl transition shadow-lg shadow-brand-600/30">
          Login to System
        </button>
        <button onclick="showAuthView('register')" class="w-full bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium py-3 rounded-xl transition border border-slate-600">
          Register New Account
        </button>
      </div>
    </div>

    <!-- AUTHENTICATION FORM -->
    <div id="view-auth" class="hidden max-w-md mx-auto my-8 bg-slate-800 rounded-2xl border border-slate-700 p-8 shadow-2xl">
      <div id="auth-register-header" class="mb-6">
        <h2 class="text-xl font-bold text-white">Create an Account</h2>
        <p class="text-slate-400 text-sm">Register as a customer</p>
      </div>

      <div id="auth-login-header" class="mb-6">
        <h2 class="text-xl font-bold text-white">System Login</h2>
        <p class="text-slate-400 text-sm">Enter your credentials to continue</p>
      </div>

      <form id="auth-form" onsubmit="handleAuthSubmit(event)" class="space-y-4">
        <div id="field-full-name">
          <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Full Name</label>
          <input type="text" id="input-fullname" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-brand-500 text-sm" placeholder="e.g. Juan Dela Cruz">
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Username</label>
          <input type="text" id="input-username" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-brand-500 text-sm" placeholder="Enter username">
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Password</label>
          <input type="password" id="input-password" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-brand-500 text-sm" placeholder="••••••••">
        </div>

        <div id="auth-error" class="hidden text-red-400 text-xs bg-red-500/10 border border-red-500/20 p-3 rounded-lg">
          Invalid credentials or registration error!
        </div>

        <button type="submit" id="auth-submit-btn" class="w-full bg-brand-600 hover:bg-brand-500 text-white font-medium py-3 rounded-xl transition shadow-lg shadow-brand-600/30">
          Submit
        </button>
      </form>

      <div class="mt-6 pt-4 border-t border-slate-700 text-center">
        <button onclick="showLanding()" class="text-xs text-slate-400 hover:text-slate-200">
          <i class="fa-solid fa-arrow-left mr-1"></i> Back to Landing Page
        </button>
      </div>
    </div>

    <!-- USER DASHBOARD -->
    <div id="view-user-dashboard" class="hidden space-y-6 max-w-4xl mx-auto">
      <div class="bg-slate-800 rounded-2xl p-6 border border-slate-700 flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-white">Customer Dashboard</h1>
          <p class="text-slate-400 text-sm">Book appointments directly linked to Python SQLite database.</p>
        </div>
        <button onclick="startBooking()" class="bg-brand-600 hover:bg-brand-500 text-white px-5 py-2.5 rounded-xl font-medium shadow-lg shadow-brand-600/30 transition">
          <i class="fa-solid fa-calendar-plus mr-2"></i> Book Appointment
        </button>
      </div>

      <!-- WIZARD -->
      <div id="booking-wizard" class="hidden bg-slate-800 rounded-2xl border border-slate-700 p-6 space-y-6">
        <div class="flex items-center justify-between border-b border-slate-700 pb-4">
          <h2 class="text-lg font-bold text-white">Appointment Booking</h2>
          <span id="wizard-step-badge" class="text-xs font-semibold px-2.5 py-1 bg-brand-500/20 text-brand-400 border border-brand-500/30 rounded-full">Step 1 of 4</span>
        </div>

        <!-- STEP 1 -->
        <div id="step-date-time" class="space-y-4">
          <label class="block text-sm font-medium text-slate-300">Select Appointment Date and Time</label>
          <input type="datetime-local" id="booking-datetime" class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-slate-200 text-sm focus:border-brand-500 focus:outline-none">
          <div class="flex justify-end gap-3 pt-2">
            <button onclick="cancelBookingWizard()" class="px-4 py-2 bg-slate-700 text-slate-300 rounded-lg text-sm">Exit</button>
            <button onclick="nextStep(2)" class="px-5 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-sm font-medium">Continue</button>
          </div>
        </div>

        <!-- STEP 2 -->
        <div id="step-available-cars" class="hidden space-y-4">
          <label class="block text-sm font-medium text-slate-300">List of Available Cars</label>
          <div id="cars-grid" class="grid sm:grid-cols-2 gap-4 max-h-96 overflow-y-auto pr-2"></div>
          <div class="flex justify-between pt-2">
            <button onclick="nextStep(1)" class="px-4 py-2 bg-slate-700 text-slate-300 rounded-lg text-sm">Go Back</button>
            <button onclick="nextStep(3)" id="btn-to-step3" disabled class="px-5 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium">Continue</button>
          </div>
        </div>

        <!-- STEP 3 -->
        <div id="step-fulfillment" class="hidden space-y-4">
          <label class="block text-sm font-medium text-slate-300">Select Fulfillment Type</label>
          <div class="grid grid-cols-2 gap-4">
            <button type="button" onclick="selectFulfillment('Pick-up')" id="opt-pickup" class="p-4 border border-slate-700 rounded-xl text-left hover:border-brand-500 bg-slate-900/50">
              <div class="font-bold text-white text-base mb-1"><i class="fa-solid fa-car-side mr-2 text-brand-400"></i>Pick-up</div>
              <p class="text-xs text-slate-400">Self-drive option.</p>
            </button>
            <button type="button" onclick="selectFulfillment('Service')" id="opt-service" class="p-4 border border-slate-700 rounded-xl text-left hover:border-brand-500 bg-slate-900/50">
              <div class="font-bold text-white text-base mb-1"><i class="fa-solid fa-user-tie mr-2 text-brand-400"></i>Service</div>
              <p class="text-xs text-slate-400">Includes professional driver.</p>
            </button>
          </div>

          <div id="drivers-section" class="hidden pt-4 border-t border-slate-700/60 space-y-3">
            <label class="block text-xs font-semibold text-brand-400 uppercase tracking-wider">List of Available Drivers & Info</label>
            <div id="drivers-list" class="space-y-2"></div>
          </div>

          <div class="flex justify-between pt-2">
            <button onclick="nextStep(2)" class="px-4 py-2 bg-slate-700 text-slate-300 rounded-lg text-sm">Go Back</button>
            <button onclick="nextStep(4)" id="btn-to-step4" disabled class="px-5 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium">Continue</button>
          </div>
        </div>

        <!-- STEP 4 -->
        <div id="step-payment" class="hidden space-y-4">
          <div class="bg-slate-900 border border-slate-700 rounded-xl p-4 space-y-2 text-sm">
            <h3 class="font-bold text-white border-b border-slate-800 pb-2">Booking Summary</h3>
            <div class="flex justify-between text-slate-400"><span>Car:</span> <span id="summary-car" class="text-slate-200">--</span></div>
            <div class="flex justify-between text-slate-400"><span>Fulfillment:</span> <span id="summary-fulfillment" class="text-slate-200">--</span></div>
            <div class="flex justify-between text-slate-400"><span>Driver:</span> <span id="summary-driver" class="text-slate-200">--</span></div>
            <div class="flex justify-between text-slate-400"><span>Date:</span> <span id="summary-date" class="text-slate-200">--</span></div>
            <div class="flex justify-between text-slate-200 font-bold border-t border-slate-800 pt-2 text-base">
              <span>Total Rental Rate:</span>
              <span id="summary-amount" class="text-brand-400">₱0.00</span>
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Payment Method</label>
            <select id="payment-method" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-slate-200 text-sm">
              <option value="Credit Card">Credit Card</option>
              <option value="GCash">GCash</option>
              <option value="Cash">Cash</option>
            </select>
          </div>

          <div class="flex justify-between pt-2">
            <button onclick="nextStep(3)" class="px-4 py-2 bg-slate-700 text-slate-300 rounded-lg text-sm">Go Back</button>
            <button onclick="processPayment()" id="btn-confirm-pay" class="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium">Confirm & Pay</button>
          </div>
        </div>
      </div>

      <!-- APPOINTMENTS -->
      <div class="bg-slate-800 rounded-2xl border border-slate-700 p-6 space-y-4">
        <h3 class="font-bold text-white text-lg">My Appointments</h3>
        <div id="user-appointments-list" class="space-y-3"></div>
      </div>
    </div>

    <!-- STAFF DASHBOARD -->
    <div id="view-staff-dashboard" class="hidden space-y-6">
      <div class="bg-slate-800 rounded-2xl p-6 border border-slate-700">
        <h1 class="text-2xl font-bold text-white">Staff Dashboard</h1>
        <p class="text-slate-400 text-sm">Fleet Management & Customer Service Log</p>
      </div>

      <div class="grid lg:grid-cols-2 gap-6">
        <div class="bg-slate-800 rounded-2xl border border-slate-700 p-6 space-y-4">
          <h2 class="font-bold text-white text-lg"><i class="fa-solid fa-car text-brand-400 mr-2"></i>Fleet Management</h2>
          <div id="staff-fleet-list" class="space-y-3 max-h-96 overflow-y-auto pr-2"></div>
        </div>

        <div class="bg-slate-800 rounded-2xl border border-slate-700 p-6 space-y-4">
          <h2 class="font-bold text-white text-lg"><i class="fa-solid fa-headset text-brand-400 mr-2"></i>Customer Appointments</h2>
          <div id="staff-appointments-list" class="space-y-3"></div>
        </div>
      </div>
    </div>

    <!-- ADMIN DASHBOARD -->
    <div id="view-admin-dashboard" class="hidden space-y-6">
      <div class="bg-slate-800 rounded-2xl p-6 border border-slate-700">
        <h1 class="text-2xl font-bold text-white">Admin Dashboard</h1>
        <p class="text-slate-400 text-sm">Financial Analytics & Sales Reports</p>
      </div>

      <div class="grid md:grid-cols-2 gap-6">
        <div class="bg-slate-800 rounded-2xl border border-slate-700 p-6 space-y-4">
          <h2 class="font-bold text-white text-lg"><i class="fa-solid fa-file-invoice-dollar text-emerald-400 mr-2"></i>Financial Reports (Expenses)</h2>
          <div id="admin-expenses-list" class="space-y-3"></div>
        </div>

        <div class="bg-slate-800 rounded-2xl border border-slate-700 p-6 space-y-4">
          <div class="flex justify-between items-center">
            <h2 class="font-bold text-white text-lg"><i class="fa-solid fa-chart-line text-brand-400 mr-2"></i>Sales Reports</h2>
            <span id="total-sales-badge" class="text-xs font-bold px-2.5 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full">Total: ₱0.00</span>
          </div>
          <div id="admin-sales-list" class="space-y-3"></div>
        </div>
      </div>
    </div>

  </main>

  <script>
    let currentUser = null;
    let authMode = 'login';
    let dbData = { cars: [], drivers: [], appointments: [], payments: [], expenses: [], users: [] };
    let bookingState = { datetime: '', selectedCarId: null, fulfillment: '', selectedDriverId: null };
    let isSubmittingBooking = false;

    function formatPeso(amount) {
      return '₱' + parseFloat(amount).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    async function fetchDBData() {
      try {
        const res = await fetch('/api/data');
        dbData = await res.json();
      } catch (err) {
        console.error("Error fetching DB data:", err);
      }
    }

    function showLanding() {
      hideAllViews();
      document.getElementById('view-landing').classList.remove('hidden');
    }

    function showAuthView(mode) {
      authMode = mode;
      hideAllViews();
      document.getElementById('view-auth').classList.remove('hidden');
      document.getElementById('auth-error').classList.add('hidden');
      document.getElementById('auth-form').reset();

      if (mode === 'register') {
        document.getElementById('auth-register-header').classList.remove('hidden');
        document.getElementById('auth-login-header').classList.add('hidden');
        document.getElementById('field-full-name').classList.remove('hidden');
      } else {
        document.getElementById('auth-register-header').classList.add('hidden');
        document.getElementById('auth-login-header').classList.remove('hidden');
        document.getElementById('field-full-name').classList.add('hidden');
      }
    }

    function hideAllViews() {
      ['view-landing', 'view-auth', 'view-user-dashboard', 'view-staff-dashboard', 'view-admin-dashboard'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add('hidden');
      });
    }

    async function handleAuthSubmit(e) {
      e.preventDefault();
      const usernameInput = document.getElementById('input-username');
      const passwordInput = document.getElementById('input-password');
      const fullnameInput = document.getElementById('input-fullname');
      const errorDiv = document.getElementById('auth-error');

      if (!usernameInput || !passwordInput) return;

      const username = usernameInput.value.trim();
      const password = passwordInput.value.trim();

      const endpoint = authMode === 'register' ? '/api/register' : '/api/login';
      const bodyData = authMode === 'register' ? {
        username, password,
        full_name: (fullnameInput ? fullnameInput.value.trim() : '') || username
      } : { username, password };

      try {
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(bodyData)
        });
        const result = await res.json();

        if (res.ok && result.success) {
          currentUser = result.user;
          await fetchDBData();
          routeDashboard();
        } else {
          errorDiv.innerText = result.message || 'Invalid credentials or registration error!';
          errorDiv.classList.remove('hidden');
        }
      } catch (err) {
        console.error("Auth error:", err);
        errorDiv.innerText = 'Server connection error!';
        errorDiv.classList.remove('hidden');
      }
    }

    function routeDashboard() {
      hideAllViews();
      document.getElementById('nav-user-info').classList.remove('hidden');
      document.getElementById('user-display-name').innerText = currentUser.full_name;
      document.getElementById('user-display-role').innerText = currentUser.role;

      if (currentUser.role === 'Admin') {
        document.getElementById('view-admin-dashboard').classList.remove('hidden');
        renderAdminDashboard();
      } else if (currentUser.role === 'Staff') {
        document.getElementById('view-staff-dashboard').classList.remove('hidden');
        renderStaffDashboard();
      } else {
        document.getElementById('view-user-dashboard').classList.remove('hidden');
        renderUserDashboard();
      }
    }

    function logout() {
      currentUser = null;
      document.getElementById('nav-user-info').classList.add('hidden');
      showLanding();
    }

    function renderUserDashboard() {
      const listEl = document.getElementById('user-appointments-list');
      const userApps = dbData.appointments.filter(a => a.user_id === currentUser.user_id);

      if (userApps.length === 0) {
        listEl.innerHTML = `<p class="text-sm text-slate-400">No appointments found in SQLite DB.</p>`;
        return;
      }

      listEl.innerHTML = userApps.map(app => {
        const car = dbData.cars.find(c => c.car_id === app.car_id);
        const driver = app.driver_id ? dbData.drivers.find(d => d.driver_id === app.driver_id) : null;
        const payment = dbData.payments.find(p => p.appointment_id === app.appointment_id);
        
        let statusBadgeClass = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
        if (app.status === 'Cancelled') {
          statusBadgeClass = 'bg-red-500/20 text-red-400 border-red-500/30';
        }

        return `
          <div class="bg-slate-900 border border-slate-700/80 rounded-xl p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <div>
              <div class="font-bold text-white text-base">${car ? car.model : 'Car'} (${car ? car.license_plate : ''})</div>
              <div class="text-xs text-slate-400 mt-1">Date: ${app.appointment_date} | Type: <span class="text-brand-400 font-medium">${app.fulfillment_type}</span></div>
              ${driver ? `<div class="text-xs text-slate-400">Driver: ${driver.full_name} (${driver.phone_number})</div>` : ''}
            </div>
            <div class="flex items-center gap-4">
              <div class="text-right">
                <span class="inline-block px-2.5 py-1 text-xs font-semibold rounded-full border ${statusBadgeClass}">${app.status}</span>
                <div class="text-xs font-bold text-brand-400 mt-1">${payment ? formatPeso(payment.amount) : ''}</div>
              </div>
              ${app.status === 'Confirmed' ? `
                <button onclick="cancelAppointment(${app.appointment_id})" class="px-3 py-1.5 bg-red-600/20 hover:bg-red-600 text-red-400 hover:text-white border border-red-500/30 rounded-lg text-xs transition">
                  Cancel
                </button>
              ` : ''}
            </div>
          </div>
        `;
      }).join('');
    }

    async function cancelAppointment(appointmentId) {
      if (!confirm('Are you sure you want to cancel this appointment?')) return;

      try {
        const res = await fetch('/api/cancel-appointment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ appointment_id: appointmentId })
        });
        const result = await res.json();

        if (res.ok && result.success) {
          alert('Appointment successfully cancelled.');
          await fetchDBData();
          renderUserDashboard();
        } else {
          alert(result.message || 'Failed to cancel appointment.');
        }
      } catch (err) {
        console.error("Cancel error:", err);
        alert('Server error while cancelling appointment.');
      }
    }

    function startBooking() {
      document.getElementById('booking-wizard').classList.remove('hidden');
      bookingState = { datetime: '', selectedCarId: null, fulfillment: '', selectedDriverId: null };
      nextStep(1);
    }

    function cancelBookingWizard() {
      document.getElementById('booking-wizard').classList.add('hidden');
    }

    function nextStep(step) {
      document.getElementById('step-date-time').classList.add('hidden');
      document.getElementById('step-available-cars').classList.add('hidden');
      document.getElementById('step-fulfillment').classList.add('hidden');
      document.getElementById('step-payment').classList.add('hidden');

      if (step === 1) {
        document.getElementById('step-date-time').classList.remove('hidden');
      } else if (step === 2) {
        bookingState.datetime = document.getElementById('booking-datetime').value || '2026-10-15 09:00';
        renderAvailableCars();
        document.getElementById('step-available-cars').classList.remove('hidden');
      } else if (step === 3) {
        renderDriversList();
        document.getElementById('step-fulfillment').classList.remove('hidden');
      } else if (step === 4) {
        const car = dbData.cars.find(c => c.car_id === bookingState.selectedCarId);
        const driver = bookingState.selectedDriverId ? dbData.drivers.find(d => d.driver_id === bookingState.selectedDriverId) : null;
        
        document.getElementById('summary-car').innerText = car ? `${car.model} (${car.license_plate})` : '--';
        document.getElementById('summary-fulfillment').innerText = bookingState.fulfillment;
        document.getElementById('summary-driver').innerText = driver ? driver.full_name : 'None (Self-drive)';
        document.getElementById('summary-date').innerText = bookingState.datetime;
        document.getElementById('summary-amount').innerText = car ? formatPeso(car.rental_rate) : '₱0.00';

        document.getElementById('step-payment').classList.remove('hidden');
      }
    }

    function renderAvailableCars() {
      const grid = document.getElementById('cars-grid');
      const availableCars = dbData.cars.filter(c => c.status === 'Available');

      if (availableCars.length === 0) {
        grid.innerHTML = `<p class="text-sm text-slate-400 col-span-2">No available cars at the moment.</p>`;
        return;
      }

      grid.innerHTML = availableCars.map(car => `
        <div onclick="selectCar(${car.car_id})" id="car-card-${car.car_id}" class="car-card cursor-pointer p-4 rounded-xl border border-slate-700 bg-slate-900/60 hover:border-brand-500 transition">
          <div class="flex justify-between items-start mb-2">
            <h4 class="font-bold text-white text-sm">${car.model}</h4>
            <span class="text-xs font-bold text-brand-400">${formatPeso(car.rental_rate)}/day</span>
          </div>
          <p class="text-xs text-slate-400">Plate: ${car.license_plate}</p>
        </div>
      `).join('');
    }

    function selectCar(carId) {
      bookingState.selectedCarId = carId;
      document.querySelectorAll('.car-card').forEach(el => el.classList.remove('border-brand-500', 'bg-brand-500/10'));
      document.getElementById(`car-card-${carId}`).classList.add('border-brand-500', 'bg-brand-500/10');
      document.getElementById('btn-to-step3').disabled = false;
    }

    function selectFulfillment(type) {
      bookingState.fulfillment = type;
      document.getElementById('opt-pickup').classList.remove('border-brand-500', 'bg-brand-500/10');
      document.getElementById('opt-service').classList.remove('border-brand-500', 'bg-brand-500/10');

      if (type === 'Pick-up') {
        document.getElementById('opt-pickup').classList.add('border-brand-500', 'bg-brand-500/10');
        document.getElementById('drivers-section').classList.add('hidden');
        bookingState.selectedDriverId = null;
        document.getElementById('btn-to-step4').disabled = false;
      } else {
        document.getElementById('opt-service').classList.add('border-brand-500', 'bg-brand-500/10');
        document.getElementById('drivers-section').classList.remove('hidden');
        document.getElementById('btn-to-step4').disabled = !bookingState.selectedDriverId;
      }
    }

    function renderDriversList() {
      const list = document.getElementById('drivers-list');
      const availDrivers = dbData.drivers.filter(d => d.status === 'Available');

      if (availDrivers.length === 0) {
        list.innerHTML = `<p class="text-xs text-slate-400">No drivers available. Please choose Pick-up instead.</p>`;
        return;
      }

      list.innerHTML = availDrivers.map(d => `
        <div onclick="selectDriver(${d.driver_id})" id="driver-card-${d.driver_id}" class="driver-card cursor-pointer p-3 rounded-lg border border-slate-700 bg-slate-900 hover:border-brand-500 transition flex justify-between items-center text-xs">
          <div>
            <div class="font-semibold text-slate-200">${d.full_name}</div>
            <div class="text-slate-400">Phone: ${d.phone_number}</div>
          </div>
          <span class="text-emerald-400 font-medium">${d.status}</span>
        </div>
      `).join('');
    }

    function selectDriver(driverId) {
      bookingState.selectedDriverId = driverId;
      document.querySelectorAll('.driver-card').forEach(el => el.classList.remove('border-brand-500', 'bg-brand-500/10'));
      document.getElementById(`driver-card-${driverId}`).classList.add('border-brand-500', 'bg-brand-500/10');
      document.getElementById('btn-to-step4').disabled = false;
    }

    async function processPayment() {
      if (isSubmittingBooking) return;
      isSubmittingBooking = true;
      const confirmBtn = document.getElementById('btn-confirm-pay');
      confirmBtn.disabled = true;
      confirmBtn.innerText = 'Processing...';

      const car = dbData.cars.find(c => c.car_id === bookingState.selectedCarId);

      try {
        const res = await fetch('/api/book', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: currentUser.user_id,
            car_id: bookingState.selectedCarId,
            driver_id: bookingState.selectedDriverId,
            appointment_date: bookingState.datetime,
            fulfillment_type: bookingState.fulfillment,
            amount: car ? car.rental_rate : 0,
            payment_method: document.getElementById('payment-method').value
          })
        });

        const result = await res.json();

        if (res.ok && result.success) {
          alert('Saved to Python Database! Appointment Confirmed.');
          cancelBookingWizard();
          await fetchDBData();
          renderUserDashboard();
        } else {
          alert(result.message || 'Booking failed. Please try again.');
        }
      } catch (err) {
        console.error("Booking error:", err);
        alert('Server connection error during booking.');
      } finally {
        isSubmittingBooking = false;
        confirmBtn.disabled = false;
        confirmBtn.innerText = 'Confirm & Pay';
      }
    }

    function renderStaffDashboard() {
      const fleetEl = document.getElementById('staff-fleet-list');
      fleetEl.innerHTML = dbData.cars.map(c => `
        <div class="bg-slate-900 border border-slate-700 rounded-xl p-3 flex justify-between items-center text-sm">
          <div>
            <span class="font-bold text-white">${c.model}</span>
            <span class="text-xs text-slate-400 ml-2">(${c.license_plate})</span>
          </div>
          <select onchange="updateCarStatus(${c.car_id}, this.value)" class="bg-slate-800 border border-slate-700 text-xs rounded-lg px-2.5 py-1 text-slate-200">
            <option value="Available" ${c.status === 'Available' ? 'selected' : ''}>Available</option>
            <option value="Rented" ${c.status === 'Rented' ? 'selected' : ''}>Rented</option>
            <option value="Maintenance" ${c.status === 'Maintenance' ? 'selected' : ''}>Maintenance</option>
          </select>
        </div>
      `).join('');

      const appsEl = document.getElementById('staff-appointments-list');
      const activeApps = dbData.appointments.filter(a => a.status !== 'Cancelled');
      if (activeApps.length === 0) {
        appsEl.innerHTML = `<p class="text-xs text-slate-400">No active customer appointments.</p>`;
        return;
      }

      appsEl.innerHTML = activeApps.map(a => {
        const u = dbData.users.find(usr => usr.user_id === a.user_id);
        const c = dbData.cars.find(car => car.car_id === a.car_id);
        return `
          <div class="bg-slate-900 p-3 rounded-lg border border-slate-700/60 text-xs space-y-1">
            <div class="flex justify-between font-semibold text-slate-200">
              <span>Customer: ${u ? u.full_name : 'User'}</span>
              <span class="text-emerald-400">${a.status}</span>
            </div>
            <div class="text-slate-400">Car: ${c ? c.model : ''} | Date: ${a.appointment_date}</div>
          </div>
        `;
      }).join('');
    }

    async function updateCarStatus(carId, status) {
      await fetch('/api/update-car-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ car_id: carId, status: status })
      });
      await fetchDBData();
      renderStaffDashboard();
    }

    function renderAdminDashboard() {
      const expEl = document.getElementById('admin-expenses-list');
      expEl.innerHTML = dbData.expenses.map(e => {
        const car = dbData.cars.find(c => c.car_id === e.car_id);
        return `
          <div class="bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs flex justify-between items-center">
            <div>
              <div class="font-bold text-slate-200">${e.description}</div>
              <div class="text-slate-400">Vehicle: ${car ? car.model : ''}</div>
            </div>
            <div class="text-red-400 font-bold">${formatPeso(e.amount)}</div>
          </div>
        `;
      }).join('');

      const salesEl = document.getElementById('admin-sales-list');
      let totalSales = 0;
      const validPayments = dbData.payments.filter(p => {
        const app = dbData.appointments.find(a => a.appointment_id === p.appointment_id);
        return app && app.status !== 'Cancelled';
      });

      salesEl.innerHTML = validPayments.map(p => {
        totalSales += p.amount;
        const app = dbData.appointments.find(a => a.appointment_id === p.appointment_id);
        const user = app ? dbData.users.find(u => u.user_id === app.user_id) : null;
        return `
          <div class="bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs flex justify-between items-center">
            <div>
              <div class="font-bold text-slate-200">Appointment #${p.appointment_id} - ${user ? user.full_name : ''}</div>
              <div class="text-slate-400">Method: ${p.payment_method}</div>
            </div>
            <div class="text-emerald-400 font-bold">${formatPeso(p.amount)}</div>
          </div>
        `;
      }).join('');

      document.getElementById('total-sales-badge').innerText = `Total: ${formatPeso(totalSales)}`;
    }
  </script>
</body>
</html>
"""

# --- MAIN EXECUTION (Cloud Ready) ---

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"Database initialized. Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
