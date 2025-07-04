from copy import deepcopy
from datetime import datetime, date
import json
import os
from pathlib import Path
import re
import time

from bs4 import BeautifulSoup
import numpy as np
from PIL import Image
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class Godok:
    SINGULAR_VALUES = 20
    COMPRESSED_DIMENSIONS = 32

    def __init__(self):
        if not os.path.isdir('dat'): os.mkdir('dat')

        # Load figure (index primary key) metadata
        try:
            with open('dat/metadata.json', 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}

        # Load homma information
        try:
            with open('dat/homma_metadata.json', 'r', encoding='utf-8') as f:
                __load = json.load(f)
                self.homma_to_photo: dict[str, list[str]] = __load['photo']
                self.banned_hommas: list[str] = __load['banned']
                self.bubble_directory: str = __load['bubble_dir']
        except FileNotFoundError:
            self.homma_to_photo: dict[str, list[str]] = {'(알 수 없음)': []}
            self.banned_hommas: list[str] = []
            self.bubble_directory: str = ''

        # Load tag information
        try:
            with open('dat/tags.json', 'r', encoding='utf-8') as f:
                self.tag_counter: dict[str, int] = json.load(f)
        except FileNotFoundError:
            self.tag_counter: dict[str, int] = {}

        # Rule out non-existent images
        for __path in self.data.copy().keys():
            if os.path.isfile(__path): continue
            self.remove_entry(__path)

        self.export()

    def export(self):
        with open('dat/metadata.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=True, indent=4)
        with open('dat/homma_metadata.json', 'w', encoding='utf-8') as f:
            json.dump({'photo': self.homma_to_photo, 'banned': self.banned_hommas,
                       'bubble_dir': self.bubble_directory}, f, ensure_ascii=True, indent=4)
        with open('dat/tags.json', 'w', encoding='utf-8') as f:
            json.dump(self.tag_counter, f, ensure_ascii=True, indent=4)

    @staticmethod
    def test_internet_connectivity(host="8.8.8.8", port=53, timeout=3):
        """
        Checks internet connectivity by attempting to connect to a known DNS server.
        Default is Google DNS (8.8.8.8) on port 53.
        :param host: DNS server hostname.
        :param port: DNS server port.
        :param timeout: Timeout in seconds.
        :return: True if connected.
        """
        import socket
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except TimeoutError:
            return False

    @staticmethod
    def scrape_tweet(progress_callback, url: str, save_dir: str) -> tuple[list[str], list[dict], str]:
        def load_cookies(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Set up Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run in background
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        progress_callback(20)

        driver.get("https://x.com/")
        time.sleep(3)
        # Step 3: Inject cookies
        cookies = load_cookies("dat/x_cookies.json")

        for cookie in cookies:
            cookie.pop("sameSite", None)  # optional fix for compatibility
            try: driver.add_cookie(cookie)
            except Exception as e: print(f"[-] Cookie error: {e} -- {cookie.get('name')}")

        progress_callback(54)

        driver.get(url)
        time.sleep(3)  # Let JS load
        progress_callback(84)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        # Extract Post Text and Hashtags
        tweet_text = "(알 수 없음)"

        # Identify post time
        time_tag = soup.find('time')
        progress_callback(85)
        dt_tuple = (2022, 2, 22)

        if time_tag and time_tag.has_attr('datetime'):
            timestamp = time_tag['datetime']
            dt_utc = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.000Z")
            dt_local = dt_utc.astimezone()
            dt_tuple = (dt_local.year, dt_local.month, dt_local.day)

        # Try common meta properties for description
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            if tag.get('property') == 'og:title':
                tweet_text = tag.get('content', '').strip()
                break
        progress_callback(86)

        # Extract hashtags using regex
        hashtags: list[str] = re.findall(r'#\w+', tweet_text)

        # Extract images
        images = []
        for img_tag in soup.find_all('img'):
            src = img_tag.get('src')
            if src and 'media' in src and src not in images:
                images.append(src)
        progress_callback(88)

        load_imgdirs = []
        for idx, img_url in enumerate(images):
            try:
                # Force full-resolution version
                high_res_url = re.sub(r'&name=\w+$', '&name=orig', img_url)
                img_data = requests.get(high_res_url).content
                img_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx + 1}.png"
                img_path = os.path.join(save_dir, img_name)
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                load_imgdirs.append(img_path)
            except Exception as e:
                raise ConnectionError(f"Failed to download image {img_url}: {e}")
            finally:
                progress_callback(88 + (idx + 1) * (12 / len(images)))

        __met = {'source': url,
                 'members': any(['릴리' in hashtag for hashtag in hashtags]) * 32
                            + any(['해원' in hashtag for hashtag in hashtags]) * 16
                            + any(['설윤' in hashtag for hashtag in hashtags]) * 8
                            + any(['배이' in hashtag for hashtag in hashtags]) * 4
                            + any(['지우' in hashtag for hashtag in hashtags]) * 2
                            + any(['규진' in hashtag for hashtag in hashtags]),
                 'homma': url.split('/')[3],
                 'date': dt_tuple,
                 'tags': [''] * 6,
                 'dir': save_dir}

        return load_imgdirs, [__met for _ in load_imgdirs], tweet_text[tweet_text.find(':') + 1: tweet_text.find('#')]

    @staticmethod
    def pixsvd_from_pillow(pillow_img: Image) -> tuple[list, list]:
        # Compute compressed image (to 32 x 32)
        __resized = pillow_img.resize((32, 32))
        __dat = np.array(__resized.convert('RGB').getdata()).reshape(Godok.COMPRESSED_DIMENSIONS ** 2, 3) @ np.array(
            [65536, 256, 1])
        __gray = np.array(__resized.convert('L').getdata()).reshape(32, 32)

        # Calculate singular values
        _, __sg, _ = np.linalg.svd(__gray, full_matrices=False)

        return __dat.tolist(), __sg[:Godok.SINGULAR_VALUES].tolist()

    def add_entry(self, path, metadata) -> bool:
        new_entry = False

        if path not in self.data.keys():
            new_entry = True
            __newpix, __newsvd = Godok.pixsvd_from_pillow(Image.open(path))

            # Update DB
            self.data[path] = {'pix': __newpix, 'svd': __newsvd}

        if metadata['homma'] not in self.homma_to_photo.keys():
            self.homma_to_photo[metadata['homma']] = []

        if new_entry: self.homma_to_photo[metadata['homma']].append(path)
        else:
            for __oldtag in self.data[path]['meta']['tags']:
                if len(__oldtag) == 0: continue
                self.tag_counter[__oldtag] -= 1
                if self.tag_counter[__oldtag] == 0:
                    del self.tag_counter[__oldtag]

        for __tag in metadata['tags']:
            if len(__tag) == 0: continue
            self.tag_counter[__tag] = self.tag_counter.get(__tag, 0) + 1

        self.data[path]['meta'] = metadata
        return new_entry

    def remove_entry(self, path) -> bool:
        if os.path.isfile(path):
            os.removedirs(path)

        if path not in self.data.keys():
            return False

        __homma = self.data[path]['meta']['homma']
        self.homma_to_photo[__homma].remove(path)
        if __homma != '(알 수 없음)' and len(self.homma_to_photo[__homma]) == 0:
            del self.homma_to_photo[__homma]

        for __tag in self.data[path]['meta']['tags']:
            if len(__tag) == 0: continue
            self.tag_counter[__tag] -= 1
            if self.tag_counter[__tag] == 0:
                del self.tag_counter[__tag]

        if path in self.data:
            del self.data[path]
            return True
        return False

    def stats(self) -> tuple[int, int, int]:
        tot, permit, hommas = len(self.bubble_paths), 0, 0
        for __homma, __photos in self.homma_to_photo.items():
            tot += len(__photos)
            if __homma not in self.banned_hommas:
                permit += len(__photos)
            hommas += 1

        return tot, permit, hommas - 1

    @property
    def hommas(self) -> list[str]:
        return list(self.homma_to_photo.keys())

    @property
    def safe_hommas(self) -> list[str]:
        return list(set(self.hommas).difference(set(self.banned_hommas)))

    @property
    def tags(self) -> list[str]:
        l = list(self.tag_counter.keys())
        return l

    @property
    def bubble_paths(self) -> list[str]:
        if len(self.bubble_directory) == 0: return []
        __ret = []
        for extension in ['.jpg', '.jpeg', '.png']:
            __ret.extend(map(str, Path(self.bubble_directory).glob(f'*{extension}*')))
        return __ret

    def search(self, condition: dict) -> tuple[list[str], list[dict]]:
        search_scope = []

        # Bubble tab
        if condition['misc']['bubbleInclude']:
            search_scope += self.bubble_paths

        # Misc tab & Homma tab
        for __homma, __photos in self.homma_to_photo.items():
            if condition['homma']['logic'] == 'exclude' and __homma in condition['homma']['tests']: continue
            if condition['homma']['logic'] == 'strict' and __homma not in condition['homma']['tests']: continue

            if __homma not in self.banned_hommas:
                search_scope += __photos
            elif condition['misc']['banHommaInclude']:
                search_scope += __photos
            elif condition['homma']['logic'] == 'superset' and __homma in condition['homma']['tests']:
                search_scope += __photos

        # Filters
        for __path in deepcopy(search_scope):
            if __path not in self.data.keys(): search_scope.remove(__path)
            __meta, __pix, __svd = self.data[__path]['meta'], self.data[__path]['pix'], self.data[__path]['svd']

            # Member tab
            if condition['members']['logic'] == 'superset':
                if condition['members']['bitval'] & __meta['members'] != condition['members']['bitval']:
                    search_scope.remove(__path)
                    continue
            elif condition['members']['logic'] == 'strict':
                if condition['members']['bitval'] != __meta['members']:
                    search_scope.remove(__path)
                    continue
            elif condition['members']['logic'] == 'atleast':
                if not (condition['members']['bitval'] & __meta['members']):
                    search_scope.remove(__path)
                    continue

            # Tag tab
            if condition['tags']['logic'] == 'superset':
                if not set(__meta['tags']).issuperset(set(condition['tags']['tests'])):
                    search_scope.remove(__path)
                    continue
            elif condition['tags']['logic'] == 'strict':
                if set(__meta['tags']).symmetric_difference(set(condition['tags']['tests'])) != {''}:
                    search_scope.remove(__path)
                    continue
            elif condition['tags']['logic'] == 'atleast':
                if set(__meta['tags']).isdisjoint(set(condition['tags']['tests'])):
                    search_scope.remove(__path)
                    continue

            # Date tab
            if condition['date']['startlogic']:
                if date(*condition['date']['start']) > date(*__meta['date']):
                    search_scope.remove(__path)
                    continue
            if condition['date']['endlogic']:
                if date(*condition['date']['end']) < date(*__meta['date']):
                    search_scope.remove(__path)
                    continue

        __respath, __resmeta = [], []
        for __path in search_scope:
            __respath.append(__path)
            __resmeta.append(self.data[__path]['meta'])

        return __respath, __resmeta

    def norm_rank(self, progress_callback, query_pix: list, query_svd: list, scope: list[str]) -> list[str]:
        if len(scope) == 0: return []

        __scopepix_temp, __scopesvd_temp = [], []
        for i, __path in enumerate(scope):
            if __path in self.data.keys():
                __pix = self.data[__path]['pix']
                __svd = self.data[__path]['svd']
            else:
                __pix, __svd = Godok.pixsvd_from_pillow(Image.open(__path))
            __scopepix_temp.append(__pix)
            __scopesvd_temp.append(__svd)
            progress_callback((i + 1) * 100 // len(scope))

        __scopepix = np.array(__scopepix_temp)
        __scopesvd = np.array(__scopesvd_temp)

        pixel_dists_red = np.linalg.norm((__scopepix >> 16) - query_pix, axis=1)
        pixel_dists_green = np.linalg.norm(((__scopepix >> 8) % 256) - query_pix, axis=1)
        pixel_dists_blue = np.linalg.norm((__scopepix % 256) - query_pix, axis=1)
        svd_dists = np.linalg.norm(__scopesvd - query_svd, axis=1)

        return [scope[i] for i in np.argsort(pixel_dists_red + pixel_dists_green + pixel_dists_blue + svd_dists)]

    def get_metalist(self, paths: list[str]) -> list[dict]:
        return [self.data[path]['meta'] if path in self.data.keys() else self.default_meta(path) for path in paths]

    def ban_homma(self, homma: str):
        if homma not in self.banned_hommas:
            self.banned_hommas.append(homma)

    def unban_homma(self, homma: str):
        self.banned_hommas.remove(homma)

    @staticmethod
    def default_meta(path: str) -> dict:
        return {'source': '',
                'members': 0,
                'homma': '(알 수 없음)',
                'date': (datetime.today().year, datetime.today().month, datetime.today().day),
                'tags': [''] * 6,
                'dir': os.path.split(path)[0]}
