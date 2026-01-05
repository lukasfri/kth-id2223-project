from enum import Enum
import os

from dotenv import load_dotenv
import gtfs_kit as gk
import pathlib as pl
import build.gen.gtfs_realtime_pb2 as gtfs_realtime_pb2
import requests
import py7zr
import zipfile

# SL	sl	✔️	✔️	✔️	
# UL	ul	✔️	✔️	✔️	
# Sörmlandstrafiken	sormland	✔️			
# Östgötatrafiken	otraf	✔️	✔️	✔️	✔️
# JLT	jlt	✔️	✔️	✔️	
# Kronoberg	krono	✔️	✔️	✔️	
# KLT	klt	✔️	✔️	✔️	
# Gotland	gotland	✔️	✔️	✔️	
# Blekingetrafiken	blekinge	✔️			
# Skånetrafiken	skane	✔️	✔️	✔️	✔️
# Hallandstrafiken	halland	✔️			
# Västtrafik	vt	✔️			
# Värmlandstrafik	varm	✔️	✔️	✔️	
# Örebro	orebro	✔️	✔️	✔️	
# Västmanland	vastmanland	✔️	✔️	✔️	
# Dalatrafik	dt	✔️	✔️	✔️	
# X-trafik	xt	✔️	✔️	✔️	
# Din Tur - Västernorrland	dintur	✔️	✔️	✔️	
# Jämtland	jamtland	✔️			
# Västerbotten	vasterbotten	✔️			
# Norrbotten	norrbotten	✔️			
# BT buss	btbuss	✔️			
# Destination Gotland	dg	✔️			
# Falcks Omnibus AB	falcks	✔️			
# Flixbus	flixbus	✔️			
# Härjedalingen	harje	✔️			
# Lennakatten	lenna	✔️			
# Luleå Lokaltrafik	lulea	✔️			
# Masexpressen	masen	✔️			
# Mälartåg ersättningstrafik	malartag	✔️			
# Norrtåg ersättningsstrafik (VR Sverige)	norrtag-vr-sverige	✔️			
# Ressel Rederi	ressel	✔️			
# Roslagens sjötrafik	roslagen	✔️			
# SJ	sj	✔️			
# SJ Norge	sjnorge	✔️			
# Sjöstadstrafiken (Stockholm Stad)	sjostadstrafiken	✔️			
# Skellefteåbuss	skelleftea	✔️			
# Snälltåget	snalltaget	✔️			
# Strömma Turism & Sjöfart AB	stromma	✔️			
# TiB ersättningstrafik (VR Sverige)	tib-vr-sverige	✔️			
# TJF Smalspåret	tjf	✔️			
# Trosabussen	trosa	✔️			
# Tågab	tagab	✔️			
# Uddevalla Skärgårdsbåtar AB	uddevalla	✔️			
# VR	vr	✔️			
# Vy Norge	vy-norge	✔️			
# Vy Tåg AB	vy-varmlandnorge	✔️			
# Vy Värmlandstrafik	vy-varmlandstrafik	✔️			
# Y-Buss	ybuss	✔️
class Operator(Enum):
    SL = "sl"
    UL = "ul"
    Sormland = "sormland"
    Otraf = "otraf"
    JLT = "jlt"
    Krono = "krono"
    KLT = "klt"
    Gotland = "gotland"
    Blekinge = "blekinge"
    Skane = "skane"
    Halland = "halland"
    VT = "vt"
    Varm = "varm"
    Orebro = "orebro"
    Vastmanland = "vastmanland"
    DT = "dt"
    XT = "xt"
    Dintur = "dintur"
    Jamtland = "jamtland"
    Vasterbotten = "vasterbotten"
    Norrbotten = "norrbotten"
    BTbuss = "btbuss"
    DG = "dg"
    Falcks = "falcks"
    Flixbus = "flixbus"
    Harje = "harje"
    Lenna = "lenna"
    Lulea = "lulea"
    Masen = "masen"
    Malartag = "malartag"
    NorrtagVRsverige = "norrtag-vr-sverige"
    Ressel = "ressel"
    Roslagen = "roslagen"
    SJ = "sj"
    SJNorge = "sjnorge"
    Sjostadstrafiken = "sjostadstrafiken"
    Skelleftea = "skelleftea"
    Snalltaget = "snalltaget"
    Stromma = "stromma"
    TibVRsverige = "tib-vr-sverige"
    TJF = "tjf"
    Trosa = "trosa"
    Tagab = "tagab"
    Uddevalla = "uddevalla"
    VR = "vr"
    VyNorge = "vy-norge"
    VyVarmlandnorge = "vy-varmlandnorge"
    VyVarmlandstrafik = "vy-varmlandstrafik"
    Ybuss = "ybuss"

class FeedID(Enum):
    ServiceAlerts = "ServiceAlerts"
    VehiclePositions = "VehiclePositions"
    TripUpdates = "TripUpdates"


def download_koda_file(operator: Operator, year: int, month: int, day: int, api_key: str):
    date = f"{year:04d}-{month:02d}-{day:02d}"
    file_name = f"./data/{operator.value}_{date}.zip"

    if os.path.exists(file_name):
        print(f"File {file_name} already exists. Skipping download.")
        return
    
    url = f"https://api.koda.trafiklab.se/KoDa/api/v2/gtfs-static/{operator.value}?date={date}&key={api_key}";

    print(f"Downloading {url}...")
    response = requests.get(url)
    print(response.status_code)
    with open(file_name, 'wb') as f:
        f.write(response.content)
    
    print(f"Extracting {file_name}...")
    # with py7zr.SevenZipFile(file_name, mode='r') as z:
    #     z.extractall('./data-tmp')
    with zipfile.ZipFile(file_name, 'r') as zip_ref:
        zip_ref.extractall('./data/data-tmp')

def download_gtfs_rt_file(operator: Operator, feedId: FeedID, year: int, month: int, day: int, hour: int, api_key: str):
    date = f"{year:04d}-{month:02d}-{day:02d}"

    url = f"https://api.koda.trafiklab.se/KoDa/api/v2/gtfs-rt/{operator.value}/{feedId.value}?date={date}&hour={hour:02d}&key={api_key}";

    print(f"Downloading {url}...")
    response = requests.get(url)
    print(response.status_code)
    file_name = f"./data/{operator.value}_{feedId.value}_{date}_{hour:02d}.7z"
    with open(file_name, 'wb') as f:
        f.write(response.content)
    
    with py7zr.SevenZipFile(file_name, mode='r') as z:
        z.extractall('./data/data-tmp-rt')

def load_feed_file(file_path: str):
    with open(file_path, 'rb') as f:
        data = f.read()
    
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(data)
    return feed

def debug_print_feed(feed: gtfs_realtime_pb2.FeedMessage):
    print(f"Parsed FeedMessage with {len(feed.entity)} entities")
    for entity in feed.entity:
        if entity.HasField('alert'):
            print(f"Alert ID: {entity.id}")
            for informed_entity in entity.alert.informed_entity:
                print(f"  Informed Entity: {informed_entity}")
            for header_text in entity.alert.header_text.translation:
                print(f"  Header Text ({header_text.language}): {header_text.text}")
            for description_text in entity.alert.description_text.translation:
                print(f"  Description Text ({description_text.language}): {description_text.text}")
            print()


def main():
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        raise ValueError("API_KEY not found in environment variables")

    # Use one of 'blekinge', 'dintur', 'dt', 'gotland', 'halland', 'klt', 'krono', 'orebro', 'otraf', 'sj', 'skane', 'sl', 'sormland', 'ul', 'varm', 'vastmanland', 'vt', 'xt'
    operator = Operator.SL
    year = 2024
    month = 6
    day = 15
    download_koda_file(operator, year, month, day, API_KEY)

    feedId = FeedID.VehiclePositions
    download_gtfs_rt_file(operator, feedId, year, month, day, 10, API_KEY)
    
    sl_path = pl.Path(f"./data/sl_2024-06-15.zip")

    a = gk.list_feed(sl_path)

    print(a)

    service_alert_file = "./data/data-tmp-rt/sl/ServiceAlerts/2024/06/15/10/sl-servicealerts-2024-06-15T10-00-03Z.pb"

    service_alert = load_feed_file(service_alert_file)
    debug_print_feed(service_alert)
    

if __name__ == "__main__":
    main()
