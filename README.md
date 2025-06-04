Android Health Checker GUI
A desktop utility for quickly checking the health of your Android Studio projects!
This tool runs common diagnostics like lint, syntax checks, stub generation, and project resource scans—all from a user-friendly graphical interface.

Features
Project Scanner:
Scan and analyze Android projects for issues, including XML and resource checks.

Step-by-step Workflow:
Easily reorder, add, or remove steps such as:

Scan XML

Scan Resources

Generate Stubs

Check Syntax

Run Lint (requires Gradle wrapper)

Build APK

Generate HTML Report

Gradle Support:
Automatically detects and uses the Gradle wrapper for lint/build tasks if available.

HTML Report Viewer:
Open your generated report in a browser directly from the GUI.

Config Persistence:
Remembers your last project, report location, and step order.

Console Output:
Shows colored build output and highlights errors in real-time.

Requirements
Python 3.7+ (with Tkinter installed)

An existing Android project

(For full feature set) Gradle wrapper (gradlew) in your Android project directory

Installation
No installation required!
Just place android_health_checker_gui2.py in any folder.

Usage
Run the GUI:

sh
Copy code
python android_health_checker_gui2.py
Select your Android project directory.

Adjust steps as needed:

Use the arrows to reorder.

Add or remove steps from the dropdown.

Certain steps (like "Run Lint") appear only if supported.

Start Scan:

Click Start to run all steps in order.

Watch output and errors live in the console area.

View HTML Report:

If you ran the HTML Report step, click View Report to open it in your browser.

Create Lint Baseline:

If lint errors prevent your build, use the Create Lint Baseline button to generate a baseline file (Gradle projects only).

Configuration
Settings are stored in:
~/.android_health_checker_gui.json
This file remembers your project path, report filename, and custom step order.

Troubleshooting
If “Run Lint” or “Build APK” don’t appear, make sure your project contains a Gradle wrapper (gradlew or gradlew.bat).

For most steps, android_health_check.py is required in the same directory as this script.

Output is color-coded:

Green = Success

Red = Error/Failure

Blue = Info/Step

Customization
Add new steps:
Edit the ALL_STEPS list in the script.

Change default steps:
Also adjust ALL_STEPS and the config file if needed.

License
This project is provided as-is for personal or internal use.
No official support.
Feel free to modify!
