# 🚗 Vehicle Parking Management System

Welcome! This is your all-in-one web app for managing parking lots, bookings, and users-built with love using Flask and SQLAlchemy.

## ✨ Features

### 👥 For Users
- **Easy Sign Up & Login**: Get started in seconds
- **Book a Spot**: Find and reserve parking with just a click
- **See What’s Available**: Real-time lot status
- **Your Parking History**: Track where and when you parked
- **Release Spots**: Free up your spot and see your cost
- **Search**: Quickly find lots by location or PIN code

### 🛠️ For Admins
- **Admin Dashboard**: See everything at a glance
- **Manage Lots**: Add, edit, or remove parking lots
- **User Management**: View and help your users
- **Analytics & Reports**: Visual charts for occupancy and revenue
- **Live Monitoring**: See what’s happening right now

### 📊 Analytics & Reporting
- **Occupancy Charts**: See which lots are busy
- **Revenue Tracking**: Know how much you’ve earned
- **User Stats**: See who’s using your app
- **Monthly Reports**: Track your parking costs over time

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (for dev) / PostgreSQL (for production)
- **Frontend**: HTML, CSS, Bootstrap 5, Chart.js
- **Authentication**: Session-based

## 🚀 Quick Start

### What You’ll Need
- Python 3.8+
- pip (Python package installer)

### Get Going

1. **Clone this repo**
   ```bash
   git clone <your-repository-url>
   cd vehicle-parking-app
   ```

2. **Install what you need**
   ```bash
   pip install flask flask-sqlalchemy 
   ```

3. **Run the app**
   ```bash
   python app.py
   ```

4. **Open it up**
   - Go to `http://localhost:5000`
   - Admin login: `admin@parking.com` / `admin`
   - Or register as a new user

## 📁 Project Structure

```
vehicle-parking-app/
├── app.py                 # Main Flask app
├── README.md             # This file
├── instance/
│   └── parking.sqlite3   # SQLite DB
├── static/
│   └── css/
│       └── style.css    # Custom styles
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Home page
    ├── user_*.html       # User pages
    └── admin_*.html      # Admin pages
```

## 🔒 Security

- **Sessions**: Keeps users logged in safely
- **Input Checks**: Validates forms
- **SQL Injection? Nope!**: SQLAlchemy keeps you safe
- **XSS? Not here!**: Templates escape by default
- **CSRF**: Add a token for extra safety in production

## 🗄️ Database

### Users
- Register, login, and roles (admin/user)

### Parking Lots
- Info, location, price, and capacity

### Parking Spots
- Each spot, tracked by status

### Reserved Spots
- Bookings, costs, and timestamps

## ⚙️ Config

### Environment Variables
- `SECRET_KEY`: For sessions
- `DATABASE_URL`: For production DB
- `PORT`: App port (default: 5000)

## 📈 Monitoring

### Health Check
- `/health` endpoint
- Shows if the app is running

### Logs
- For debugging and tracking

### DB Backups
- Back up regularly
- Use migrations for changes

## 🤝 Contributing

1. Fork this repo
2. Make a branch
3. Add your feature
4. Test it out
5. Open a pull request

## 📝 License

MIT License — use it, share it, improve it!

## 🆘 Need Help?

- Check your logs
- Double-check your environment variables
- Make sure you installed everything
- Try running locally first

## 🎯 Roadmap

- [ ] Password hashing
- [ ] Email verification
- [ ] Payments
- [ ] Mobile app
- [ ] Real-time notifications
- [ ] More analytics
- [ ] Multi-language support

---

**Made with ❤️ using Flask and modern web tech!**
