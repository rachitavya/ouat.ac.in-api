import requests
from bs4 import BeautifulSoup
import json
import requests
import tempfile
import os
import shutil
import logging
import aiohttp

async def download_pdf(url, temp_dir):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix=".pdf")
                    with open(temp_file.name, 'wb') as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                    return temp_file.name
                else:
                    logging.error(f"Failed to download PDF from {url}: {response.status}")
                    return None
    except Exception as e:
        logging.error(f"Error downloading PDF: {e}")
        return None

def scraper():
    url = 'https://ouat.ac.in/quick-links/agro-advisory-services/'
    rename_districts = {
        'angul': 'anugul',
        'balasore': 'baleshwar',
        'boudh': 'baudh',
        'deogarh': 'debagarh',
        'keonjhar': 'kendujhar',
        'mayurbhanjha': 'mayurbhanj',
        'nabarangpur': 'nabarangapur',
        'sonepur': 'subarnapur'
    }    
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        data = []
        districts = soup.find_all('div', class_='hide1')
        for district in districts:
            district_name = district.get('id')[:-1]
            if district_name in rename_districts.keys():
                district_name=rename_districts[district_name]
            data_dict = {'district_name': district_name}
            table = district.find('table').find('tbody')
            if len(table.select('tr')) > 0:
                rows = table.select('tr')[0]
            else:
                continue
            columns = rows.find_all('td')
            date = columns[1].text.strip()
            data_dict['date'] = date
            english_link = columns[2].find('a')['href']
            odia_link = columns[3].find('a')['href']
            link_dict = {'english': english_link, 'odia': odia_link}
            data_dict['link'] = link_dict
            data.append(data_dict)
        print(data)

        return data

    except Exception as e:
        logging.error(f"Error scraping website: {e}")
        return []
    

def move_json_to_history(source_dir, dest_dir):
    def process_directory(source, destination):
        os.makedirs(destination, exist_ok=True)
        for filename in os.listdir(source):
            if filename.endswith(".json"):
                source_path = os.path.join(source, filename)
                with open(source_path, 'r') as json_file:
                    data = json.load(json_file)
                    date = data.get('date')
                    if not date:
                        print(f"Skipping {filename}: 'date' not found in JSON")
                        continue

                    final_dest_dir = destination
                    if "ERROR" in data.keys():
                        final_dest_dir = os.path.join(destination, "error")
                        os.makedirs(final_dest_dir, exist_ok=True)

                    district_name = filename.split('.')[0]
                    history_filename = f"{date}_{district_name}.json"
                    dest_path = os.path.join(final_dest_dir, history_filename)

                    shutil.move(source_path, dest_path)
                    print(f"Moved {filename} to {dest_path}")

    process_directory(source_dir, dest_dir)
    hindi_source_dir = os.path.join(source_dir, "hindi")
    hindi_dest_dir = os.path.join(dest_dir, "hindi")
    if os.path.exists(hindi_source_dir):
        process_directory(hindi_source_dir, hindi_dest_dir)            