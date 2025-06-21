import datetime
import json
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
import re

from unidecode import unidecode


@dataclass
class Episode:
    title: str
    audio_url: str
    date: str

    def __str__(self):
        return f"{self.title} - {self.audio_url}"

def scrap_episodes_url(url: str) -> list[str]:
    params = {'p': 1}
    all_items = []

    while True:
        print(f"Scraping page {params['p']}...")
        resp = requests.get(url, params=params)
        if params['p'] > 1 and not resp.url.endswith(str(params['p'])):
            print(f"No more content found at page {params['p']}.")
            break
        parsed_html = BeautifulSoup(resp.text, 'html.parser')

        for item in parsed_html.find_all('script', type='application/ld+json'):
            for graph in json.loads(item.text)["@graph"]:
                if graph["@type"] == "ItemList":
                    for element in graph["itemListElement"]:
                        all_items.append(element["url"])
        params['p'] += 1
    return all_items


def scrap_episodes_content(episode_urls: list[str]) -> list[Episode]:
    all_medias = []
    for episode_url in episode_urls:
        print(f"Scraping episode {episode_url}...")
        resp = requests.get(episode_url)
        parsed_html = BeautifulSoup(resp.text, 'html.parser')

        for item in parsed_html.find_all('script', type='application/ld+json'):
            for graph in json.loads(item.text)["@graph"]:
                if graph["@type"] == "RadioEpisode":
                    try:
                        date_format = '%Y-%m-%d'
                        datetime_str = str(datetime.datetime.fromisoformat(graph["dateCreated"]).strftime(date_format))
                        all_medias.append( Episode(title=graph["name"], audio_url=graph["mainEntity"]["contentUrl"], date=datetime_str) )
                    except Exception as e:
                        print(f"Error parsing episode {episode_url}: {e}")


    return all_medias

def download_episodes(episodes: list[Episode]):
    for episode in episodes:
        print(f"Downloading: {episode.title}")
        response = requests.get(episode.audio_url)
        filename = f"{episode.date}_{re.sub(r'[^a-zA-Z0-9]', '', unidecode(episode.title))}." + episode.audio_url.split(".")[-1]
        with open(filename, 'wb') as file:
            file.write(response.content)
        print(f"Saved: {filename}")

if __name__ == "__main__":
    url = 'https://www.radiofrance.fr/francemusique/podcasts/cine-tempo'
    download_episodes(scrap_episodes_content(scrap_episodes_url(url)))
