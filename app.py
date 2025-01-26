from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
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
    # Create a figure to hold multiple subplots (one for each month)
    months_diff = (filing_date.year - start_date.year) * 12 + (filing_date.month - start_date.month)
    num_months = months_diff + 1  # Include the start month and all months up to the filing month

    fig, axes = plt.subplots(1, num_months, figsize=(6 * num_months, 6))  # Adjust figure size based on the number of months
    if num_months == 1:
        axes = [axes]  # Ensure axes is always a list

    for i in range(num_months):
        current_date = start_date + timedelta(days=30 * i)  # Approximate month increment
        cal = calendar.monthcalendar(current_date.year, current_date.month)
        ax = axes[i]
        ax.set_title(f"{current_date.strftime('%B %Y')}")
        ax.axis('off')

        # Create a table for the calendar
        table = ax.table(
            cellText=cal,
            loc='center',
            cellLoc='center',
            colLabels=calendar.day_abbr,
        )

        # Highlight the start date (only in the first month)
        if i == 0:
            for week in cal:
                if start_date.day in week:
                    row = cal.index(week)
                    col = week.index(start_date.day)
                    table[(row + 1, col)].set_facecolor('#a6d8ff')  # Light blue for start date

        # Highlight the filing date (only in the last month)
        if i == num_months - 1:
            for week in cal:
                if filing_date.day in week:
                    row = cal.index(week)
                    col = week.index(filing_date.day)
                    table[(row + 1, col)].set_facecolor('#ffcccb')  # Light red for filing date

    # Save the calendar image to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
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

    # Add a timestamp to the image URL to prevent caching
    timestamp = int(datetime.timestamp(datetime.now()))
    return jsonify({
        'filing_date': filing_date.strftime('%Y-%m-%d'),
        'calendar_image': f"/static/{image_filename}?t={timestamp}"
    })

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/static/<filename>')
def serve_static(filename):
    # Serve static files with no-cache headers
    response = send_from_directory('static', filename)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response