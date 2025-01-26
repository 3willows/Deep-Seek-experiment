from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # Set the backend to Agg
import matplotlib.pyplot as plt
import io
import calendar
import os

app = Flask(__name__)

# List of public holidays (customize this list)
public_holidays = [
    "2023-01-01",  # New Year's Day
    "2023-02-12",  # Chinese New Year
    "2023-04-07",  # Good Friday
    "2023-05-01",  # Labour Day
    "2023-07-01",  # HKSAR Establishment Day
    "2023-10-01",  # National Day
    "2023-12-25",  # Christmas Day
]

def is_weekend(date):
    return date.weekday() >= 5  # Saturday is 5, Sunday is 6

def is_public_holiday(date):
    return date.strftime("%Y-%m-%d") in public_holidays

def calculate_filing_date(start_date, days_to_add):
    current_date = start_date
    added_days = 0

    while added_days < days_to_add:
        current_date += timedelta(days=1)
        if not is_weekend(current_date) and not is_public_holiday(current_date):
            added_days += 1

    return current_date

def generate_calendar_image(start_date, filing_date):
    # Create a calendar for the month of the start date
    cal = calendar.monthcalendar(start_date.year, start_date.month)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title(f"Calendar for {start_date.strftime('%B %Y')}")
    ax.axis('off')

    # Create a table for the calendar
    table = ax.table(
        cellText=cal,
        loc='center',
        cellLoc='center',
        colLabels=calendar.day_abbr,
    )

    # Highlight the start date and filing date
    for i, week in enumerate(cal):
        for j, day in enumerate(week):
            if day == start_date.day:
                table[(i + 1, j)].set_facecolor('#a6d8ff')  # Light blue for start date
            if day == filing_date.day and start_date.month == filing_date.month:
                table[(i + 1, j)].set_facecolor('#ffcccb')  # Light red for filing date

    # Save the calendar image to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
    days_to_add = int(data['days_to_add'])

    filing_date = calculate_filing_date(start_date, days_to_add)

    # Generate the calendar image
    calendar_image = generate_calendar_image(start_date, filing_date)

    # Save the image to the static folder
    image_filename = f"calendar_{start_date.strftime('%Y%m%d')}.png"
    image_path = os.path.join(app.root_path, 'static', image_filename)
    with open(image_path, 'wb') as f:
        f.write(calendar_image.getvalue())

    return jsonify({
        'filing_date': filing_date.strftime('%Y-%m-%d'),
        'calendar_image': f"/static/{image_filename}"
    })

if __name__ == '__main__':
    app.run(debug=True)