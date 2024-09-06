from openlocationcode import openlocationcode as olc
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError

def convert_to_plus_code(latitude, longitude):
    """
    Mengonversi koordinat menjadi Plus Code lengkap.
    """
    plus_code = olc.encode(latitude, longitude)
    return plus_code

def get_address_from_coordinates(latitude, longitude):
    """
    Mengambil alamat dari koordinat latitude dan longitude menggunakan Nominatim.
    """
    try:
        geolocator = Nominatim(user_agent="my_unique_application_name")
        location = geolocator.reverse((latitude, longitude), exactly_one=True)
        return location.address if location else "Alamat tidak ditemukan"
    except GeocoderServiceError as e:
        print(f"Error dalam geocoding: {e}")
        return "Tidak dapat mengakses layanan geocoding"

def generate_google_maps_url(plus_code):
    """
    Menghasilkan URL Google Maps untuk Plus Code dengan encoding khusus.
    """
    base_url = "https://www.google.com/maps/place/"
    # Replace space with %2B to match URL encoding for the Plus Code
    plus_code_encoded = plus_code.replace(" ", "%2B").replace("+", "%2B")
    return f"{base_url}{plus_code_encoded}/"

# Contoh penggunaan
latitude = -6.858613
longitude = 108.915838

# Mendapatkan Plus Code lengkap
plus_code = convert_to_plus_code(latitude, longitude)

# Mendapatkan alamat dari koordinat
address = get_address_from_coordinates(latitude, longitude)

# Menghasilkan URL Google Maps untuk Plus Code
maps_url = generate_google_maps_url(plus_code)

# Menggabungkan Plus Code dengan Alamat dan URL Google Maps
plus_code_with_address = f"Plus Code: {plus_code} {address}\nGoogle Maps URL: {maps_url}"

# Cetak hasil
print(f"Latitude: {latitude}, Longitude: {longitude}")
print(plus_code_with_address)
