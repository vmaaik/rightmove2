import requests
from bs4 import BeautifulSoup
import json
from geopy.geocoders import Nominatim

class RightmoveData:
    def __init__(self, url: str, get_floorplans: bool = False):
        self._status_code, self._first_page = self._request(url)
        self._url = url
        self._validate_url()
        self._results = self._get_results(get_floorplans=get_floorplans)

    @staticmethod
    def _request(url: str):
        r = requests.get(url)
        return r.status_code, r.text

    def _validate_url(self):
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
        soup = BeautifulSoup(self._first_page, 'html.parser')
        result_count = soup.find('span', class_='searchHeader-resultCount')
        return int(result_count.text.replace(",", ""))

    @property
    def page_count(self):
        page_count = self.results_count_display // 24
        if self.results_count_display % 24 > 0:
            page_count += 1
        if page_count > 42:
            page_count = 42
        return page_count

    def _get_page(self, request_content: str, get_floorplans: bool = False):
        soup = BeautifulSoup(request_content, 'html.parser')
        script_tag = soup.find('script', text=lambda x: 'window.jsonModel' in str(x))
        if script_tag:
            json_model = script_tag.text.split('window.jsonModel = ')[-1].rstrip(';')

        data = json.loads(json_model)
        properties = data['properties']
        features = []

        geolocator = Nominatim(user_agent="my-app")
        for property_data in properties:
            display_addresses = property_data['displayAddress']
            property_sub_type = property_data['propertySubType']
            prices = property_data['price']['displayPrices'][0]['displayPrice']
            latitude = property_data['location']['latitude']
            longitude = property_data['location']['longitude']
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
        results = self._get_page(self._first_page, get_floorplans=get_floorplans)

        for p in range(1, self.page_count + 1, 1):
            p_url = f"{str(self.url)}&index={p * 24}"
            status_code, content = self._request(p_url)

            if status_code != 200:
                break
            temp_results = self._get_page(content, get_floorplans=get_floorplans)
            results.extend(temp_results)

        return {
            "type": "FeatureCollection",
            "features": results
        }

    @staticmethod
    def _clean_results(results: dict):
        return results

