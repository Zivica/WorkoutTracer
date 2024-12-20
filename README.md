# **Workout Tracker Application**

## Overview
This Python script implements a workout tracking application using **PyQt5** for GUI, **SQLite** for database management, and **matplotlib** for data visualization. It supports multiple user profiles, workout plans, tracking of exercise data, and visualization of workout progress.

---

## **Key Functionalities**

### **1. Database Initialization (`init_db`)**
- Initializes a SQLite database (`workouts.db`) with three tables:
  - **profiles**: Stores user profile information.
  - **workouts**: Defines workout templates (exercise types and sets).
  - **records**: Tracks workout session data (e.g., reps, weight, RPE, etc.).

---

### **2. Profile Management**
#### Functions
- **`get_profiles()`**:
  - Fetches all profiles from the database.
- **`create_profile(name)`**:
  - Creates a new user profile if it doesn’t already exist.

#### Class: `ProfileDialog`
- Allows users to select an existing profile or create a new one.
- Input: User can choose a profile or enter a name for a new profile.
- Output: Returns the selected or newly created profile ID.

---

### **3. Workout Management**
#### Class: `ManageDaysTab`
- Enables users to manage workout days and exercises.
- Key Components:
  - **Form Inputs**: Add day type (push/pull/legs), exercises, and set count.
  - **Table Display**: Shows existing workouts for the profile.
- **Features**:
  - Add new exercises to a workout day.
  - Delete specific exercises or days.

---

### **4. Tracking Workout Progress**
#### Class: `TrackProgressTab`
- Allows users to log their workout data.
- Key Components:
  - **Day Selection**: Choose a day type to load associated exercises.
  - **Data Entry Table**: Log reps, weight, rest, RPE, heart rate, etc.
- **Features**:
  - Save entered data to the database.
  - Export data to Excel or PDF for external use.

---

### **5. Visualizing Workout Trends**
#### Class: `ViewTrendsTab`
- Provides data visualization for workout progress.
- Key Components:
  - **Filters**: Select date range and day type.
  - **Plot**: Displays volume trends over time.
- **Features**:
  - Weekly or monthly summaries.
  - Suggestions based on changes in workout volume.

---

### **6. Main Application Window**
#### Class: `MainWindow`
- Combines all tabs (`ManageDaysTab`, `TrackProgressTab`, `ViewTrendsTab`) in a single interface.
- Includes a timer to periodically remind users to log their progress.

---

## **Code Components**

### **Imports**
- Libraries used:
  - **PyQt5**: GUI framework.
  - **SQLite3**: Database management.
  - **Pandas**: Data handling.
  - **Matplotlib**: Plotting and visualization.
  - **ReportLab**: Generating PDFs for data export.

### **Database Schema**
- **Profiles Table**:
  ```sql
  CREATE TABLE profiles (
      id INTEGER PRIMARY KEY,
      name TEXT UNIQUE NOT NULL
  );
  ```
- **Workouts Table**:
  ```sql
  CREATE TABLE workouts (
      id INTEGER PRIMARY KEY,
      profile_id INTEGER,
      day_type TEXT,
      exercise TEXT,
      sets INTEGER,
      FOREIGN KEY(profile_id) REFERENCES profiles(id)
  );
  ```
- **Records Table**:
  ```sql
  CREATE TABLE records (
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
  );
  ```

---

## **Workflow**
1. **Profile Selection**:
   - Open the application and select or create a profile.
2. **Manage Days**:
   - Define workout days, exercises, and sets.
3. **Log Workouts**:
   - Log exercise details (reps, weight, etc.) for specific days.
4. **Visualize Progress**:
   - View trends and summaries of workout data over time.
5. **Export Data**:
   - Save workout logs to Excel or PDF files.

---

## **Error Handling**
- **Database Errors**:
  - Prevents duplicate profile creation.
- **Input Validation**:
  - Ensures required fields (e.g., exercise name) are not empty.
- **User Warnings**:
  - Alerts for invalid operations, such as attempting to delete without a selection.

---

## **Future Improvements**
- Add support for advanced filtering and analytics.
- Introduce user authentication for enhanced security.
- Expand visualization options (e.g., bar charts, pie charts).
- Allow synchronization with cloud services for backup and multi-device access.

---

## **Execution**
- To run the application:
  ```bash
  python <script_name>.py
  
