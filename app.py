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

def calculate_filing_deadline(hearing_date, hours_before):
    current_date = hearing_date
    hours_remaining = int(hours_before)

    while hours_remaining > 0:
        current_date -= timedelta(hours=1)
        if not is_weekend(current_date) and not is_public_holiday(current_date):
            hours_remaining -= 1

    return current_date

def generate_calendar_image(hearing_date, filing_deadline):
    # Create a figure to hold multiple subplots (one for each month)
    months_diff = (hearing_date.year - filing_deadline.year) * 12 + (hearing_date.month - filing_deadline.month)
    num_months = months_diff + 1  # Include the filing month and all months up to the hearing month

    # Adjust figsize to reduce the height of the Ax
    fig, axes = plt.subplots(1, num_months, figsize=(6 * num_months, 4))  # Reduced height to 4
    if num_months == 1:
        axes = [axes]  # Ensure axes is always a list

    for i in range(num_months):
        current_date = filing_deadline + timedelta(days=30 * i)  # Approximate month increment
        cal = calendar.monthcalendar(current_date.year, current_date.month)
        ax = axes[i]
        ax.axis('off')

        # Create a table for the calendar
        table = ax.table(
            cellText=cal,
            loc='center',
            cellLoc='center',
            colLabels=calendar.day_abbr,
            colColours=['#F2F3F4'] * 7,  # Light gray background for column headers
            cellColours=[['white'] * 7 for _ in range(len(cal))],  # White background for cells
        )

        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 1.5)  # Adjust cell size

        # Highlight the filing deadline (only in the first month)
        if i == 0:
            for week in cal:
                if filing_deadline.day in week:
                    row = cal.index(week)
                    col = week.index(filing_deadline.day)
                    table[(row + 1, col)].set_facecolor('#A9DFBF')  # Light green for filing deadline
                    table[(row + 1, col)].set_text_props(weight='bold', color='black')

        # Highlight the hearing date (only in the last month)
        if i == num_months - 1:
            for week in cal:
                if hearing_date.day in week:
                    row = cal.index(week)
                    col = week.index(hearing_date.day)
                    table[(row + 1, col)].set_facecolor('#F5B7B1')  # Light red for hearing date
                    table[(row + 1, col)].set_text_props(weight='bold', color='black')

    # Adjust layout to reduce spacing
    plt.tight_layout()

    # Save the calendar image to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    hearing_date = datetime.strptime(data['hearing_date'], '%Y-%m-%d')
    hours_before = int(data['hours_before'])

    filing_deadline = calculate_filing_deadline(hearing_date, hours_before)

    # Generate the calendar image
    calendar_image = generate_calendar_image(hearing_date, filing_deadline)

    # Save the image to the static folder
    image_filename = f"calendar_{hearing_date.strftime('%Y%m%d')}.png"
    image_path = os.path.join(app.root_path, 'static', image_filename)
    with open(image_path, 'wb') as f:
        f.write(calendar_image.getvalue())

    # Add a timestamp to the image URL to prevent caching
    timestamp = int(datetime.timestamp(datetime.now()))
    return jsonify({
        'filing_deadline': filing_deadline.strftime('%Y-%m-%d %H:%M:%S'),
        'calendar_image': f"/static/{image_filename}?t={timestamp}"
    })

if __name__ == '__main__':
    app.run(debug=True)