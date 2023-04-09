import csv
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

INPUT_FILE = "input.csv"
OUTPUT_FILE = "output.csv"
CURRENCY = "usd"
TABLE = "A"


def get_min_max_date() -> Tuple[str, str]:
    # Use 'with' statement to automatically close file after reading
    with open(INPUT_FILE, mode='r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        # Use a list comprehension to extract all non-empty dates from the CSV file
        dates = [row["Date"] for row in csv_reader if row["Date"]]
    # Use min() and max() built-in functions to get the minimum and maximum dates
    return min(dates), max(dates)


def get_nbp_rates(min_date: str, max_date: str) -> Dict[str, Dict[str, str]]:
    url = f'http://api.nbp.pl/api/exchangerates/rates/{TABLE}/{CURRENCY}/{min_date}/{max_date}/'
    response = requests.get(url)

    if response.status_code == 200:
        # Use a dictionary comprehension to extract effective dates, table numbers, and mid values from the JSON response
        return {rate['effectiveDate']: {'no': rate['no'], 'mid': rate['mid']} for rate in response.json()['rates']}
    else:
        raise Exception(f"Request to NBP API failed: {response.status_code}")


def subtract_days(date: str, number_of_days: int) -> str:
    # Use datetime.strptime() to convert a string date to a datetime object
    date = datetime.strptime(date, '%Y-%m-%d')
    # Use timedelta() to subtract a number of days from the datetime object
    date_before = date - timedelta(days=number_of_days)
    # Use strftime() to convert the datetime object back to a string date
    date_before_str = date_before.strftime('%Y-%m-%d')
    return date_before_str


def process_row(row: Dict[str, str], nbp_rates: Dict[str, Dict[str, str]]) -> Tuple[Optional[str], Optional[str], Optional[float], Optional[float], Optional[str]]:
    # Extract the date from the row
    date = row["Date"]
    # Check if the date is not empty
    if date:
        # Convert the date string to a datetime object and get the weekday
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        day_of_week = date_obj.weekday()
        # Subtract a number of days depending on the weekday
        if day_of_week == 0:
            date = subtract_days(date, 3)
        elif day_of_week == 6:
            date = subtract_days(date, 2)
        else:
            date = subtract_days(date, 1)
        # Check if the date is in the NBP rates dictionary
        if date in nbp_rates:
            nbp_rate = nbp_rates[date]
            no_parsed = nbp_rate["no"].split("/")
            usd_rate = nbp_rate["mid"]
            pln_amount = float(row["Amount"]) * usd_rate
            table_number = nbp_rate["no"]
            table_link = f'=HYPERLINK("https://nbp.pl/archiwum-kursow/tabela-nr-{no_parsed[0]}-a-nbp-{no_parsed[3]}-z-dnia-{date}/")'
            return date, table_number, usd_rate, pln_amount, table_link
        else:
            print(f"There is no NBP rate from date {date}")
            return None, None, None, None, None
    # If the date is empty, set all output fields to empty strings
    else:
        print(f"Date is empty in row")
        return None, None, None, None, None

    # Construct a new row with the additional output


def process_csv() -> None:
    # Get the minimum and maximum dates from the input file
    min_date, max_date = get_min_max_date()
    # Get the NBP rates for the period
    nbp_rates = get_nbp_rates(subtract_days(min_date, 3), max_date)

    # Use 'with' statement to automatically close files after reading/writing
    with open(INPUT_FILE, mode='r', encoding='utf-8-sig') as input_file, open(OUTPUT_FILE, mode='w', encoding='utf-8', newline='') as output_file:
        csv_reader = csv.DictReader(input_file)
        fieldnames = csv_reader.fieldnames + \
            ['Effective date','USD Rate', 'PLN Amount',
                'NBP Table No.', 'NBP Table Link']
        csv_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        csv_writer.writeheader()

        for row in csv_reader:
            # Process each row and add the additional output fields
            date, table_number, usd_rate, pln_amount, table_link = process_row(
                row, nbp_rates)
            csv_writer.writerow({**row,  'Effective date': date, 'PLN Amount': pln_amount,
                                 'NBP Table No.': table_number,
                                 'NBP Table Link': table_link,
                                 'USD Rate': usd_rate}
                                )


if __name__ == "__main__":
    process_csv()
