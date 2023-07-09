from flask import Flask, render_template
from geojson_scraper import RightmoveData
import json
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG)

# Example URLs
urls = [
    "https://www.rightmove.co.uk/property-for-sale/find.html?minBedrooms=2&propertyTypes=detached%2Csemi-detached%2Cterraced%2Cbungalow&keywords=&sortType=2&viewType=LIST&channel=BUY&index=0&maxPrice=350000&radius=0.0&maxDaysSinceAdded=1&locationIdentifier=USERDEFINEDAREA%5E%7B%22polylines%22%3A%22q%7BrdIzkhNgpH%7CoEwrDojGmkFq%7EVb%60BeqPlaAapJp%7DCslCnxCq%7CH%60Ve%7EEqxE%7BiKleJsrSjcN%7DqBlSr_e%40%7CsCruE%7CqHylDbq%40xiK%7EEpwPgsBztXkgFxnZijQixH%22%7D",
    "https://www.rightmove.co.uk/property-for-sale/find.html?minBedrooms=2&propertyTypes=detached%2Csemi-detached%2Cterraced%2Cbungalow&keywords=&sortType=2&viewType=LIST&channel=BUY&index=0&maxPrice=350000&radius=0.0&maxDaysSinceAdded=1&locationIdentifier=USERDEFINEDAREA%5E%7B%22polylines%22%3A%22kmreIpgrKspAqaAuzBvXajBhRcsAdPmgBa%5D%7BhAajAcn%40qnBhNc%60Ejo%40adClgBuaBhkBc%7B%40%60xBse%40bjBnT%7EhAvv%40rbAllBr%5DjhC%7CUv_CeIjsE%7BPbyAyp%40uI%22%7D"
]

# Cache variable to store the GeoJSON data
cache = None

def scrape_data():
    # Scrape data from each URL
    results = []
    for url in urls:
        data = RightmoveData(url)
        results.extend(data.get_results["features"])

    # Merge GeoJSON features into one GeoJSON object
    geojson_obj = {
        "type": "FeatureCollection",
        "features": results
    }

    # Convert to JSON string
    geojson_str = json.dumps(geojson_obj)

    logging.debug(f"Scraped GeoJSON: {geojson_str}")

    return geojson_str

def populate_cache():
    global cache
    if cache is None:
        # Get the GeoJSON data if it's not cached
        cache = scrape_data()

@app.route('/')
def index():
    logging.debug("Rendering index page")
    return render_template('index.html', geojson=cache)


if __name__ == '__main__':
    # Populate the cache before starting the Flask server
    populate_cache()

    # Run the Flask server
    app.run(host='0.0.0.0', port=5000)
