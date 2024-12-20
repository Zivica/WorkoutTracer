import sys
# import os
import sqlite3
from datetime import datetime
import pandas as pd
import matplotlib

matplotlib.use('Agg')  # For off-screen before embedding in Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDateEdit, QSpinBox, QDialog,
                             QFileDialog)
from PyQt5.QtCore import QDate, QTimer

DATABASE = "workouts.db"


def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Profiles
    c.execute('''CREATE TABLE IF NOT EXISTS profiles (
                 id INTEGER PRIMARY KEY,
                 name TEXT UNIQUE NOT NULL
                 )''')
    # Workouts (template: sets, no reps/weight yet)
    c.execute('''CREATE TABLE IF NOT EXISTS workouts (
                 id INTEGER PRIMARY KEY,
                 profile_id INTEGER,
                 day_type TEXT, -- push/pull/legs
                 exercise TEXT,
                 sets INTEGER,
                 FOREIGN KEY(profile_id) REFERENCES profiles(id)
                 )''')
    # Records: user tracks reps/weight/RPE, etc.
    c.execute('''CREATE TABLE IF NOT EXISTS records (
                 id INTEGER PRIMARY KEY,
                 workout_id INTEGER,
                 date TEXT,
                 reps INTEGER,
                 weight REAL,
                 rest INTEGER,
                 rpe INTEGER,
                 heart_rate INTEGER,
                 volume REAL,
                 FOREIGN KEY(workout_id) REFERENCES workouts(id)
                 )''')
    conn.commit()
    conn.close()


init_db()


def get_profiles():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT * FROM profiles", conn)
    conn.close()
    return df


def create_profile(name):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO profiles (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)


class ProfileDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select or Create Profile")
        layout = QVBoxLayout()

        self.profiles = get_profiles()
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Create New...")
        for _, row in self.profiles.iterrows():
            self.profile_combo.addItem(row['name'])

        layout.addWidget(QLabel("Select a profile or create a new one:"))
        layout.addWidget(self.profile_combo)

        self.new_profile_line = QLineEdit()
        self.new_profile_line.setPlaceholderText("Enter new profile name if creating new")
        layout.addWidget(self.new_profile_line)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_profile_id(self):
        sel = self.profile_combo.currentText()
        if sel == "Create New...":
            new_name = self.new_profile_line.text().strip()
            if new_name:
                create_profile(new_name)
                # get the new profile id
                df = get_profiles()
                pid = df[df['name'] == new_name].iloc[0]['id']
                return pid
            else:
                return None
        else:
            df = get_profiles()
            pid = df[df['name'] == sel].iloc[0]['id']
            return pid


class ManageDaysTab(QWidget):
    def __init__(self, profile_id):
        super().__init__()
        self.profile_id = profile_id
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Fields to create/update day
        form = QFormLayout()
        self.day_type_combo = QComboBox()
        self.day_type_combo.addItems(["push", "pull", "legs"])
        self.exercise_line = QLineEdit()
        self.sets_spin = QSpinBox()
        self.sets_spin.setRange(1, 100)

        form.addRow("Day Type:", self.day_type_combo)
        form.addRow("Exercise:", self.exercise_line)
        form.addRow("Sets:", self.sets_spin)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Exercise to Day")
        self.add_btn.clicked.connect(self.add_exercise)
        self.delete_btn = QPushButton("Delete Selected Day/Exercise")
        self.delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)

        layout.addLayout(btn_layout)

        # Table to display days
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Day", "Exercise", "Sets"])
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_table()

    def load_table(self):
        conn = sqlite3.connect(DATABASE)
        df = pd.read_sql_query("SELECT id, day_type, exercise, sets FROM workouts WHERE profile_id = ?",
                               conn, params=(self.profile_id,))
        conn.close()

        self.table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(row['day_type']))
            self.table.setItem(i, 1, QTableWidgetItem(row['exercise']))
            self.table.setItem(i, 2, QTableWidgetItem(str(row['sets'])))

        self.table.resizeColumnsToContents()

    def add_exercise(self):
        day_type = self.day_type_combo.currentText()
        exercise = self.exercise_line.text().strip()
        sets = self.sets_spin.value()
        if not exercise:
            QMessageBox.warning(self, "Error", "Exercise name cannot be empty.")
            return

        # Insert into DB
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO workouts (profile_id, day_type, exercise, sets) VALUES (?,?,?,?)",
                  (self.profile_id, day_type, exercise, sets))
        conn.commit()
        conn.close()
        self.load_table()
        self.exercise_line.clear()

    def delete_selected(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Error", "No selection made.")
            return
        day_type = self.table.item(selected, 0).text()
        exercise = self.table.item(selected, 1).text()

        # Confirm deletion
        ret = QMessageBox.question(self, "Confirm Delete",
                                   f"Delete '{day_type}' with exercise '{exercise}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            # Delete all workouts for that day_type & exercise for this profile
            c.execute("DELETE FROM workouts WHERE profile_id = ? AND day_type=? AND exercise=?",
                      (self.profile_id, day_type, exercise))
            conn.commit()
            conn.close()
            self.load_table()


class TrackProgressTab(QWidget):
    def __init__(self, profile_id):
        super().__init__()
        self.profile_id = profile_id
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # User selects day
        hl_day = QHBoxLayout()
        hl_day.addWidget(QLabel("Select Day:"))
        self.day_combo = QComboBox()
        hl_day.addWidget(self.day_combo)
        self.load_days()
        layout.addLayout(hl_day)

        # Button to load exercises
        self.load_ex_btn = QPushButton("Load Exercises")
        self.load_ex_btn.clicked.connect(self.load_exercises)
        layout.addWidget(self.load_ex_btn)

        # Table of exercises - user enters reps, weight, rest, RPE, HR
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Exercise", "Sets", "Reps", "Weight(kg)",
                                              "Rest(sec)", "RPE", "Heart Rate"])
        layout.addWidget(self.table)

        # Buttons to save
        hl_btn = QHBoxLayout()
        self.save_btn = QPushButton("Save Records")
        self.save_btn.clicked.connect(self.save_records)
        hl_btn.addWidget(self.save_btn)

        # Export options
        self.export_excel_btn = QPushButton("Export to Excel")
        self.export_excel_btn.clicked.connect(self.export_excel)
        hl_btn.addWidget(self.export_excel_btn)

        self.export_pdf_btn = QPushButton("Export to PDF")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        hl_btn.addWidget(self.export_pdf_btn)

        layout.addLayout(hl_btn)

        self.setLayout(layout)

    def load_days(self):
        conn = sqlite3.connect(DATABASE)
        df = pd.read_sql_query("SELECT DISTINCT day_type FROM workouts WHERE profile_id=?",
                               conn, params=(self.profile_id,))
        conn.close()
        self.day_combo.clear()
        for d in df['day_type'].tolist():
            self.day_combo.addItem(d)

    def load_exercises(self):
        day_type = self.day_combo.currentText()
        conn = sqlite3.connect(DATABASE)
        df = pd.read_sql_query("SELECT id, exercise, sets FROM workouts WHERE profile_id=? AND day_type=?",
                               conn, params=(self.profile_id, day_type))
        conn.close()

        self.table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(row['exercise']))
            self.table.setItem(i, 1, QTableWidgetItem(str(row['sets'])))

            # Reps
            reps_item = QTableWidgetItem("0")
            self.table.setItem(i, 2, reps_item)

            # Weight
            weight_item = QTableWidgetItem("0")
            self.table.setItem(i, 3, weight_item)

            # Rest
            rest_item = QTableWidgetItem("0")
            self.table.setItem(i, 4, rest_item)

            # RPE
            rpe_item = QTableWidgetItem("0")
            self.table.setItem(i, 5, rpe_item)

            # Heart Rate
            hr_item = QTableWidgetItem("0")
            self.table.setItem(i, 6, hr_item)

        self.table.resizeColumnsToContents()

    def save_records(self):
        # Save user-entered data to DB
        day_type = self.day_combo.currentText()
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        # Get workout IDs for this day
        df = pd.read_sql_query("SELECT id, exercise, sets FROM workouts WHERE profile_id=? AND day_type=?",
                               conn, params=(self.profile_id, day_type))
        workout_map = {row['exercise']: row['id'] for i, row in df.iterrows()}

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for i in range(self.table.rowCount()):
            exercise = self.table.item(i, 0).text()
            sets = int(self.table.item(i, 1).text())
            reps = int(self.table.item(i, 2).text())
            weight = float(self.table.item(i, 3).text())
            rest = int(self.table.item(i, 4).text())
            rpe = int(self.table.item(i, 5).text())
            hr = int(self.table.item(i, 6).text())

            volume = sets * reps * weight
            wid = workout_map[exercise]
            c.execute(
                "INSERT INTO records (workout_id, date, reps, weight, rest, rpe, heart_rate, volume) VALUES (?,?,?,?,?,?,?,?)",
                (wid, date_str, reps, weight, rest, rpe, hr, volume))

        conn.commit()
        conn.close()
        QMessageBox.information(self, "Saved", "Records saved successfully!")

    def export_excel(self):
        # Export current profile's workout data to Excel
        conn = sqlite3.connect(DATABASE)
        df = pd.read_sql_query("""
        SELECT p.name as profile, w.day_type, w.exercise, w.sets, r.date, r.reps, r.weight, r.rest, r.rpe, r.heart_rate, r.volume
        FROM records r
        JOIN workouts w ON r.workout_id = w.id
        JOIN profiles p ON w.profile_id = p.id
        WHERE p.id=? 
        ORDER BY r.date DESC
        """, conn, params=(self.profile_id,))
        conn.close()

        fname, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx)")
        if fname:
            df.to_excel(fname, index=False)
            QMessageBox.information(self, "Exported", f"Data exported to {fname}")

    def export_pdf(self):
        # For simplicity, use reportlab to create a PDF table
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet

        conn = sqlite3.connect(DATABASE)
        df = pd.read_sql_query("""
        SELECT p.name as profile, w.day_type, w.exercise, w.sets, r.date, r.reps, r.weight, r.rest, r.rpe, r.heart_rate, r.volume
        FROM records r
        JOIN workouts w ON r.workout_id = w.id
        JOIN profiles p ON w.profile_id = p.id
        WHERE p.id=?
        ORDER BY r.date DESC
        """, conn, params=(self.profile_id,))
        conn.close()

        fname, _ = QFileDialog.getSaveFileName(self, "Save PDF File", "", "PDF Files (*.pdf)")
        if not fname:
            return

        doc = SimpleDocTemplate(fname, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph("Workout Log", styles["Title"]))

        data = [df.columns.tolist()] + df.values.tolist()

        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
        ]))
        elements.append(t)
        doc.build(elements)

        QMessageBox.information(self, "Exported", f"Data exported to {fname}")


class ViewTrendsTab(QWidget):
    def __init__(self, profile_id):
        super().__init__()
        self.profile_id = profile_id
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Filters: date range, day type
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        filter_layout.addWidget(self.from_date)

        filter_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        filter_layout.addWidget(self.to_date)

        self.day_filter = QComboBox()
        self.day_filter.addItem("All")
        self.day_filter.addItems(["push", "pull", "legs"])
        filter_layout.addWidget(QLabel("Day Filter:"))
        filter_layout.addWidget(self.day_filter)

        self.filter_btn = QPushButton("Apply Filter")
        self.filter_btn.clicked.connect(self.plot_data)
        filter_layout.addWidget(self.filter_btn)

        layout.addLayout(filter_layout)

        # Weekly/Monthly summaries
        summary_layout = QHBoxLayout()
        self.summary_btn = QPushButton("Weekly Summary")
        self.summary_btn.clicked.connect(lambda: self.show_summary('weekly'))
        summary_layout.addWidget(self.summary_btn)

        self.monthly_btn = QPushButton("Monthly Summary")
        self.monthly_btn.clicked.connect(lambda: self.show_summary('monthly'))
        summary_layout.addWidget(self.monthly_btn)
        layout.addLayout(summary_layout)

        # Canvas for plot
        self.canvas = MplCanvas(self, width=5, height=4)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def plot_data(self):
        fdate = self.from_date.date().toString("yyyy-MM-dd")
        tdate = self.to_date.date().toString("yyyy-MM-dd")
        day_filter = self.day_filter.currentText()

        conn = sqlite3.connect(DATABASE)
        query = """
        SELECT w.day_type, r.date, SUM(r.volume) as total_volume
        FROM records r
        JOIN workouts w ON r.workout_id = w.id
        WHERE w.profile_id=?
          AND r.date BETWEEN ? AND ?
        """
        params = [self.profile_id, fdate + " 00:00:00", tdate + " 23:59:59"]
        if day_filter != "All":
            query += " AND w.day_type=?"
            params.append(day_filter)
        query += " GROUP BY w.day_type, r.date ORDER BY r.date"
        df = pd.read_sql_query(query, conn, params=tuple(params))
        conn.close()

        self.canvas.ax.clear()
        if df.empty:
            self.canvas.ax.set_title("No data for selected range/type")
        else:
            # Convert date to datetime
            df['date'] = pd.to_datetime(df['date'])
            df = df.groupby('date')['total_volume'].sum().reset_index()
            self.canvas.ax.plot(df['date'], df['total_volume'], marker='o')
            self.canvas.ax.set_title("Volume Over Time")
            self.canvas.ax.set_xlabel("Date")
            self.canvas.ax.set_ylabel("Volume (kg)")
            self.canvas.ax.grid(True)

        self.canvas.draw()

    def show_summary(self, period):
        # period can be 'weekly' or 'monthly'
        conn = sqlite3.connect(DATABASE)
        df = pd.read_sql_query("""
        SELECT r.date, r.volume
        FROM records r
        JOIN workouts w ON r.workout_id = w.id
        WHERE w.profile_id=?
        """, conn, params=(self.profile_id,))
        conn.close()

        if df.empty:
            QMessageBox.information(self, "No Data", "No data to summarize.")
            return

        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        if period == 'weekly':
            summary = df.resample('W').sum()
        else:
            summary = df.resample('M').sum()

        msg = f"{period.capitalize()} Summary:\n\n"
        msg += str(summary)
        # Suggestion
        if summary['volume'].count() > 1:
            # Compare last two periods:
            last_two = summary['volume'].tail(2)
            if len(last_two) == 2:
                if last_two.iloc[1] < last_two.iloc[0]:
                    msg += "\n\nSuggestion: Volume decreased. Consider adding more sets or weight next session."
                else:
                    msg += "\n\nGreat job! Volume increased or stayed consistent."

        QMessageBox.information(self, f"{period.capitalize()} Summary", msg)


class MainWindow(QMainWindow):
    def __init__(self, profile_id):
        super().__init__()
        self.profile_id = profile_id
        self.setWindowTitle("Workout Tracker")
        self.tabs = QTabWidget()
        self.manage_days_tab = ManageDaysTab(profile_id)
        self.track_progress_tab = TrackProgressTab(profile_id)
        self.view_trends_tab = ViewTrendsTab(profile_id)

        self.tabs.addTab(self.manage_days_tab, "Manage Days")
        self.tabs.addTab(self.track_progress_tab, "Track Progress")
        self.tabs.addTab(self.view_trends_tab, "View Trends")

        self.setCentralWidget(self.tabs)

        # Notifications/Reminders: every 60 seconds a reminder could pop up
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_reminder)
        self.timer.start(60000)  # every 60 seconds for demo; adjust as needed

    def show_reminder(self):
        # Simple reminder
        QMessageBox.information(self, "Reminder", "Time to exercise or log your progress?")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = ProfileDialog()
    if dialog.exec_() == QDialog.Accepted:
        pid = dialog.get_profile_id()
        if pid is None:
            QMessageBox.warning(None, "Error", "No profile selected or created.")
            sys.exit(0)
        window = MainWindow(pid)
        window.resize(800, 600)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
