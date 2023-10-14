import sched
import threading
import time

import requests
from flask import Flask, render_template
from geojson_scraper import RightmoveData
import json
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='app2.log', level=logging.DEBUG)

urls = [
    "https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=USERDEFINEDAREA%5E%7B%22polylines%22%3A%22q%7BrdIzkhNgpH%7CoEwrDojGmkFq~Vb%60BeqPlaAapJp%7DCslCnxCq%7CH%60Ve~EqxE%7BiKleJsrSjcN%7DqBlSr_e%40%7CsCruE%7CqHylDbq%40xiK~EpwPgsBztXkgFxnZijQixH%22%7D&minBedrooms=2&maxPrice=400000&propertyTypes=detached%2Csemi-detached%2Cterraced%2Cbungalow&maxDaysSinceAdded=14&mustHave=&dontShow=&furnishTypes=&keywords=",
    "https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=USERDEFINEDAREA%5E%7B%22polylines%22%3A%22kmreIpgrKspAqaAuzBvXajBhRcsAdPmgBa%5D%7BhAajAcn%40qnBhNc%60Ejo%40adClgBuaBhkBc%7B%40%60xBse%40bjBnT~hAvv%40rbAllBr%5DjhC%7CUv_CeIjsE%7BPbyAyp%40uI%22%7D&minBedrooms=2&maxPrice=400000&propertyTypes=detached%2Csemi-detached%2Cterraced%2Cbungalow&maxDaysSinceAdded=14&mustHave=&dontShow=&furnishTypes=&keywords="
]


# Cache variable to store the GeoJSON data

def scrape_data():
    results = []
    for url in urls:
        data = RightmoveData(url)
        results.extend(data.get_results["features"])

    geojson_obj = {
        "type": "FeatureCollection",
        "features": results
    }

    # Convert to JSON string
    geojson_str = json.dumps(geojson_obj)

    return geojson_str


def populate_cache():
    global cache
    cache = None
    cache = scrape_data()

@app.route('/')
def index():
    logging.debug("Rendering index page")
    
    # Generate the HTML content by rendering the template
    html_content = render_template('index.html', geojson=cache)
    
    # Save the HTML content to a file (e.g., output.html)
    with open('output.html', 'w') as file:
        file.write(html_content)

    return html_content


@app.route('/populate')
def populate():
    logging.debug("Populating cache")
    populate_cache()
    logging.debug("Cache has been populated")


def scheduled_job():
    try:
        # Make an HTTP GET request to your own endpoint to populate the cache
        response = requests.get('http://127.0.0.1:5000/')
        if response.status_code == 200:
            logging.debug("Healthcheck done")
    except Exception as e:
        logging.error(f"Error calling scheduled job: {str(e)}")


def scheduled_cache_populate():
    while True:
        # Populate the cache every 6 hours (6 * 60 * 60 seconds)
        time.sleep(6 * 60 * 60)
        logging.debug("Scheduled cache population started")
        populate_cache()
        logging.debug("Scheduled cache population done")


if __name__ == '__main__':
    # Populate the cache before starting the Flask server
    populate_cache()

    # Start the Flask server in a separate thread
    server_thread = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000})
    server_thread.start()

    # Start the scheduled job to populate the cache every 6 hours
    cache_populate_thread = threading.Thread(target=scheduled_cache_populate)
    cache_populate_thread.start()

    # Start the scheduled job for health check
    scheduler = sched.scheduler(time.time, time.sleep)
    while True:
        scheduler.enter(60, 1, scheduled_job, ())
        scheduler.run()

