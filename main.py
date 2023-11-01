import asyncio
import aiohttp
from bs4 import BeautifulSoup
import time
import xml.etree.ElementTree as ET
import os


start_time = time.time()
all_data = []

url = "https://zamki.biz"
headers = {
    'authority': 'zamki.biz',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    'referer': 'https://zamki.biz/catalog/zamki/',
    'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
}
cookies = {
    'BITRIX_SM_SALE_UID': '733c63c19d88fa1b0ad8c1ccb64ae9cd',
    'tmr_lvid': '957144c7e11bfb7d0d8609f9a23e5500',
    'tmr_lvidTS': '1694684415057',
    '_ym_uid': '1694684416959611920',
    '_ym_d': '1694684416',
    'BX_USER_ID': 'cc92e5640f4b26d2f8bf896bbd614bd6',
    'clbvid': '6502d500b991ec586c70e12e',
    'BITRIX_SM_MA_REGIONS_CONFIRM_CITY': 'Y',
    'PHPSESSID': 'FAgtTmSPIHMDqdTVIQ70jLdjB4MNekuJ',
    'BITRIX_SM_GUEST_ID': '2769243',
    'BITRIX_SM_LAST_ADV': '5_Y',
    'v1_data': '',
    'BITRIX_CONVERSION_CONTEXT_s1': '%7B%22ID%22%3A84%2C%22EXPIRE%22%3A1698346740%2C%22UNIQUE%22%3A%5B%22conversion_visit_day%22%5D%7D',
    '_ym_isad': '1',
    '_gid': 'GA1.2.583076535.1698315685',
    '_ym_visorc': 'w',
    'v1_referrer_callibri': '',
    'BITRIX_SM_LAST_VISIT': '26.10.2023%2015%3A24%3A16',
    '_ga_2643DRSVDF': 'GS1.1.1698315684.8.1.1698315863.0.0.0',
    '_ga': 'GA1.2.1555594788.1694684416',
    '_gat_gtag_UA_110484369_1': '1',
    'tmr_detect': '0%7C1698315867405',
}
pages = 30
delay = 0.1
proxies = "https://193.138.178.6:8282"
info_list = []
global_counter = 1


def new_file(path):
    root = ET.Element('products')
    tree = ET.ElementTree(root)
    with open(path, "wb") as file:
        tree.write(file)


async def get_product(session, product_url):
    try:
        async with session.get(url=product_url, headers=headers, cookies=cookies) as response:
            response_text = await response.text()
            product_soup = BeautifulSoup(response_text, "lxml")

            global global_counter

            try:
                title = product_soup.find("h1").text.strip()
            except Exception as e:
                print("Название товара не найдено")
                title = ""

            try:
                price = product_soup.find("div", class_="product-item-detail-info-container-inner-price").text.replace("РРЦ:", "").strip()
            except Exception as e:
                price = ""

            try:
                description = product_soup.find("div", class_="product-item-detail-description").text.strip()
            except Exception as e:
                description = ""

            try:
                gallery = []
                gallery_find = product_soup.find_all("div", class_="product-item-detail-slider-image")
                for gallery_element in gallery_find:
                    gallery_element = "https://zamki.biz" + gallery_element.find("img").get("src")
                    gallery.append(gallery_element)
            except Exception as e:
                gallery = []

            if len(gallery) > 0:
                img = gallery[0]
            else:
                img = ""

            if len(gallery) == 0 or len(gallery) == 1:
                gallery = []
            else:
                gallery = gallery[1:]

            try:
                characteristics = dict()
                characteristics_table = product_soup.find("div", class_="product-item-detail-properties asd").find_all("tr")

                for char in characteristics_table:
                    key = char.find_all("td")[0].text.strip()
                    value = char.find_all("td")[-1].text.strip()
                    characteristics[key] = value
            except Exception as e:
                characteristics = dict()

            info_dict = {
                    "title": title,
                    "price": price,
                    "description": description,
                    "gallery": gallery,
                    "img": img,
                    "characteristics": characteristics,
                }

            print(f"Product {global_counter}")
            print(product_url)
            print(info_dict)
            print()

            global_counter += 1
            return info_dict

    except Exception as e:
        print(f"Ошибка! Карточка товара не получена: {e}")
        info_dict = {
            "title": "",
            "price": "",
            "description": "",
            "gallery": [],
            "img": "",
            "characteristics": dict(),
        }
        return info_dict


async def get_page_data(session, page, path):
    page_url = f"https://zamki.biz/catalog/zamki/?count=80&PAGEN_1={page}"
    async with session.get(url=page_url, headers=headers, cookies=cookies) as response:
        response_text = await response.text()

        page_soup = BeautifulSoup(response_text, "lxml")
        cards_item = page_soup.find_all("div", class_="product-item")

        for item in cards_item:
            product_url = "https://zamki.biz" + item.find("div", class_="product-item-title").find("a").get("href")
            info_dict = await get_product(session, product_url)
            write_in_xml(info_dict, path)

        print("=============")
        print(f"Обработана страница {page}")
        print("=============")

        await asyncio.sleep(delay)


async def gather_data(path):
    async with aiohttp.ClientSession() as session:
        response = await session.get(url=url, headers=headers, cookies=cookies)
        soup = BeautifulSoup(await response.text(), "lxml")
        chapters = soup.find("div", class_="b-header-catalog-menu g-menu").find_all("a", class_="a-deep-1")

        for chapter in chapters:
            url_chapter = "https://zamki.biz" + chapter.get("href") + "?count=80"
            response = await session.get(url=url_chapter, headers=headers, cookies=cookies)
            soup_chapter = BeautifulSoup(await response.text(), "lxml")
            max_pages = soup_chapter.find_all("div", class_="b-page-navigation")

            if len(max_pages) > 0:
                max_pages = int(max_pages[0].find_all("a")[-2].get("href").split("PAGEN_1=")[-1])
                print(max_pages)
            else:
                max_pages = 1
                print(max_pages)

            tasks = []

            for page in range(1, max_pages + 1):
                task = asyncio.create_task(get_page_data(session, page, path))
                tasks.append(task)

            await asyncio.gather(*tasks)


def write_in_xml(info_dict, path):
    existing_tree = ET.parse(path, parser=ET.XMLParser(encoding="utf-8"))
    root = existing_tree.getroot()

    product = ET.SubElement(root, 'product')

    title = ET.SubElement(product, 'title')
    title.text = info_dict['title']

    price = ET.SubElement(product, 'price')
    price.text = info_dict['price']

    description = ET.SubElement(product, 'description')
    description.text = info_dict['description']

    gallery = ET.SubElement(product, "gallery")
    for picture in info_dict['gallery']:
        gallery_element = ET.SubElement(gallery, "gallery_element")
        gallery_element.text = picture

    img = ET.SubElement(product, 'img')
    img.text = info_dict['img']

    characteristics = ET.SubElement(product, "characteristics")
    for key, value in info_dict['characteristics'].items():
        char_element = ET.SubElement(characteristics, "char")
        char_element.set('name', key)
        char_element.text = value

    existing_tree.write(path, encoding="utf-8", xml_declaration=True)


def main():
    path = "data.xml"

    if not os.path.isfile(path):
        new_file(path)

    asyncio.run(gather_data(path))

    finish_time = time.time() - start_time
    print(f"Время работы скрипта: {finish_time}")


if __name__ == "__main__":
    main()

