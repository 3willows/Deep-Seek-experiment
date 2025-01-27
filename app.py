from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import calendar
import os
import time

app = Flask(__name__)

# Preload public holidays into a set for faster lookup
PUBLIC_HOLIDAYS = set([
    "2025-01-01",  # The first day of January
    "2025-01-29",  # Lunar New Year's Day
    "2025-01-30",  # The second day of Lunar New Year
    "2025-01-31",  # The third day of Lunar New Year
    "2025-04-04",  # Ching Ming Festival
    "2025-04-18",  # Good Friday
    "2025-04-19",  # The day following Good Friday
    "2025-04-21",  # Easter Monday
    "2025-05-01",  # Labour Day
    "2025-05-05",  # The Birthday of the Buddha
    "2025-05-31",  # Tuen Ng Festival
    "2025-07-01",  # Hong Kong Special Administrative Region Establishment Day
    "2025-10-01",  # National Day
    "2025-10-07",  # The day following the Chinese Mid-Autumn Festival
    "2025-10-29",  # Chung Yeung Festival
    "2025-12-25",  # Christmas Day
    "2025-12-26",  # The first weekday after Christmas Day
])


def is_weekend(date):
    return date.weekday() >= 5

def is_public_holiday(date):
    return date.strftime("%Y-%m-%d") in PUBLIC_HOLIDAYS

def calculate_filing_deadline(hearing_date, hours_before):
    while is_weekend(hearing_date) or is_public_holiday(hearing_date):
        hearing_date -= timedelta(days=1)

    current_date = hearing_date
    hours_remaining = int(hours_before)

    while hours_remaining > 0:
        current_date -= timedelta(hours=1)
        if not is_weekend(current_date) and not is_public_holiday(current_date):
            hours_remaining -= 1

    return current_date

def cleanup_old_files():
    """
    Remove files older than an hour from the 'static' folder, 
    skipping 'styles.css'. Asynchronous cleanup is recommended for production.
    """
    static_folder = os.path.join(app.root_path, 'static')
    now = time.time()
    excluded_files = {'styles.css'}

    try:
        for filename in os.listdir(static_folder):
            if filename in excluded_files:
                continue

            file_path = os.path.join(static_folder, filename)
            if os.path.isfile(file_path) and now - os.path.getmtime(file_path) > 3600:
                os.remove(file_path)

    except Exception as e:
        # Log the exception for debugging
        print(f"Error during cleanup: {e}")

def generate_calendar_image(hearing_date, filing_deadline):
    # Optimized calendar generation
    months_diff = (hearing_date.year - filing_deadline.year) * 12 + (hearing_date.month - filing_deadline.month)
    num_months = months_diff + 1

    fig, axes = plt.subplots(1, num_months, figsize=(6 * num_months, 3))  # Smaller height
    if num_months == 1:
        axes = [axes]

    for i, ax in enumerate(axes):
        current_date = filing_deadline + timedelta(days=30 * i)
        cal = calendar.monthcalendar(current_date.year, current_date.month)
        ax.axis('off')

        table = ax.table(
            cellText=cal,
            loc='center',
            cellLoc='center',
            colLabels=calendar.day_abbr,
            colColours=['#F2F3F4'] * 7,
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.3)

        if i == 0:
            for week in cal:
                if filing_deadline.day in week:
                    row = cal.index(week)
                    col = week.index(filing_deadline.day)
                    table[(row + 1, col)].set_facecolor('#A9DFBF')

        if i == num_months - 1:
            for week in cal:
                if hearing_date.day in week:
                    row = cal.index(week)
                    col = week.index(hearing_date.day)
                    table[(row + 1, col)].set_facecolor('#F5B7B1')

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=80)  # Lower DPI
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
    calendar_image = generate_calendar_image(hearing_date, filing_deadline)

    image_filename = f"calendar_{hearing_date.strftime('%Y%m%d')}.png"
    image_path = os.path.join(app.root_path, 'static', image_filename)
    with open(image_path, 'wb') as f:
        f.write(calendar_image.getvalue())

    return jsonify({
        'filing_deadline': filing_deadline.strftime('%Y-%m-%d %H:%M:%S'),
        'calendar_image': f"/static/{image_filename}?t={int(time.time())}"
    })

@app.after_request
def after_request(response):
    cleanup_old_files()
    return response

# For running locally
# if __name__ == '__main__':
#     app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
