from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# List of public holidays (you can customize this list)
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
    days_to_add = int(data['days_to_add'])

    filing_date = calculate_filing_date(start_date, days_to_add)
    return jsonify({'filing_date': filing_date.strftime('%Y-%m-%d')})

if __name__ == '__main__':
    app.run(debug=True)