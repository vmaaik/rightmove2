import datetime
import numpy as np
import pandas as pd
import requests
from lxml import html
import json
from geopy.geocoders import Nominatim
import smtplib
from email.mime.text import MIMEText
import logging
from geopy.distance import geodesic


class RightmoveData:
    def __init__(self, url: str, get_floorplans: bool = False):
        self._status_code, self._first_page = self._request(url)
        self._url = url
        self._validate_url()
        self._results = self._get_results(get_floorplans=get_floorplans)

    @staticmethod
    def _request(url: str):
        print(f"Making request to URL: {url}")
        r = requests.get(url)
        return r.status_code, r.content

    def _validate_url(self):
        """Basic validation that the URL at least starts in the right format and
        returns status code 200."""
        print(f"Validating URL: {self.url}")
        real_url = "{}://www.rightmove.co.uk/{}/find.html?"
        protocols = ["http", "https"]
        types = ["property-to-rent", "property-for-sale", "new-homes-for-sale"]
        urls = [real_url.format(p, t) for p in protocols for t in types]
        conditions = [self.url.startswith(u) for u in urls]
        conditions.append(self._status_code == 200)
        if not any(conditions):
            raise ValueError(f"Invalid rightmove search URL:\n\n\t{self.url}")

    @property
    def url(self):
        return self._url

    @property
    def get_results(self):
        return self._results

    @property
    def results_count_display(self):
        """Returns an integer of the total number of listings as displayed on
        the first page of results. Note that not all listings are available to
        scrape because rightmove limits the number of accessible pages."""
        tree = html.fromstring(self._first_page)
        xpath = """//span[@class="searchHeader-resultCount"]/text()"""
        return int(tree.xpath(xpath)[0].replace(",", ""))

    @property
    def page_count(self):
        """Returns the number of result pages returned by the search URL. There
        are 24 results per page. Note that the website limits results to a
        maximum of 42 accessible pages."""
        page_count = self.results_count_display // 24
        if self.results_count_display % 24 > 0:
            page_count += 1
        # Rightmove will return a maximum of 42 results pages, hence:
        if page_count > 42:
            page_count = 42
        return page_count

    def _get_page(self, request_content: str, get_floorplans: bool = False):
        """Method to scrape data from a single page of search results. Used
        iteratively by the `get_results` method to scrape data from every page
        returned by the search."""
        # Process the html:
        tree = html.fromstring(request_content)
        script_tag = tree.xpath('//script[contains(text(), "window.jsonModel")]/text()')

        if script_tag:
            json_model = script_tag[0].split('window.jsonModel = ')[-1].rstrip(';')

        data = json.loads(json_model)
        properties = data['properties']

        features = []

        geolocator = Nominatim(user_agent="my-app")
        # Extract the required information from each property
        for property_data in properties:
            display_addresses = property_data['displayAddress']
            property_sub_type = property_data['propertySubType']
            prices = property_data['price']['displayPrices'][0]['displayPrice']
            latitude = property_data['location']['latitude']
            longitude = property_data['location']['longitude']
            location = geolocator.reverse((latitude, longitude), exactly_one=True)
            address = location.raw['address']
            town = address.get('village') or address.get('town') or address.get('city') or ''
            agency = property_data['formattedBranchName']
            first_visible = property_data['firstVisibleDate']
            property_id = property_data['id']
            locations = f"http://www.google.com/maps/place/{latitude},{longitude}"
            bedrooms = property_data['bedrooms']
            bathrooms = property_data['bathrooms']
            property_urls = "https://www.rightmove.co.uk" + property_data['propertyUrl']
            added_reduced = property_data['addedOrReduced']

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "properties": {
                    'id': property_id,
                    'area': town,
                    'type': property_sub_type,
                    'beds': bedrooms,
                    'price': prices,
                    'status': added_reduced,
                    'first_published': first_visible,
                    'baths': bathrooms,
                    'address': display_addresses,
                    'location': locations,
                    'url': property_urls,
                    'lat': latitude,
                    'long': longitude
                }
            }
            features.append(feature)

        return features

    def _get_results(self, get_floorplans: bool = False):
        """Build a GeoJSON FeatureCollection with all results returned by the search."""
        results = self._get_page(self._first_page, get_floorplans=get_floorplans)

        # Iterate through all pages scraping results:
        for p in range(1, self.page_count + 1, 1):
            print(f"Scraping page {p} of {self.page_count}")
            # Create the URL of the specific results page:
            p_url = f"{str(self.url)}&index={p * 24}"

            # Make the request:
            status_code, content = self._request(p_url)

            # Requests to scrape lots of pages eventually get status 400, so:
            if status_code != 200:
                break
            # Create a temporary FeatureCollection of page results:
            temp_results = self._get_page(content, get_floorplans=get_floorplans)
            results.extend(temp_results)

        return {
            "type": "FeatureCollection",
            "features": results
        }

    @staticmethod
    def _clean_results(results: dict):
        # No cleaning needed in this case, so return the results as is
        return results
