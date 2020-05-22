import requests
from pathlib import Path
from requests_html import HTMLSession
import sys

session = HTMLSession()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'})
photos_api_url = "https://api.500px.com/v1/photos?feature=user&stream=photos&user_id={}&include_states=false&image_size[]=2048&page={}&rpp=100"
gallery_api_url = "https://api.500px.com/v1/users/{}/galleries/{}/items?rpp=50&image_size[]=2048&include_licensing=false&formats=jpeg,lytro&sort=position&sort_direction=asc&page={}&rpp=50"
photo_api_url = "https://api.500px.com/v1/photos?ids={}&image_size[]=2048&include_states=0&expanded_user_info=false&include_tags=false&include_geo=false&is_following=false&include_equipment_info=false&include_licensing=false&include_releases=false&liked_by=0&include_vendor_photos=false"
gallery_info = "https://api.500px.com/v1/users/{}/galleries/{}?include_user=true&include_cover=1&cover_size=2048"


def get_photo(photo_id):
    photo_page = photo_api_url.format(photo_id)
    photo_resp = requests.get(photo_page)
    photo_json = photo_resp.json()["photos"]
    photo = parse_photo_json(photo_json[photo_id])
    download_photo(photo)


def get_photos(user_id, gallery_id=None, gallery_name=None):
    if gallery_id:
        api_url = gallery_api_url
        photos_page = api_url.format(user_id, gallery_id, 1)
    else:
        api_url = photos_api_url
        photos_page = api_url.format(user_id, 1)
    photos_resp = requests.get(photos_page)
    photos_json = photos_resp.json()
    pages = photos_json["total_pages"]
    total = photos_json["total_items"]
    for i in range(1, pages + 1):
        if gallery_id:
            photos_page = api_url.format(user_id, gallery_id, i)
        else:
            photos_page = api_url.format(user_id, i)
        photos_resp = requests.get(photos_page)
        photos_json = photos_resp.json()
        for j in range(0, 50 - 1):
            photo_json = photos_json["photos"][j]
            photo = parse_photo_json(photo_json)
            print('Downloading {} ({}/{})'.format(photo.name, (i - 1) * 50 + j + 1, total))
            download_photo(photo, str(gallery_name))


def get_gallery(user_id, gallery_name):
    gallery_info_req = gallery_info.format(user_id, gallery_name)
    gallery_info_res = requests.get(gallery_info_req)
    gallery_id = gallery_info_res.json()["gallery"]["id"]
    get_photos(user_id, gallery_id, gallery_name)


def download_photo(photo, folder=None):
    if folder is None:
        folder = ""
    else:
        folder = "_Gallery/" + folder
    dir_name = "K:/ksy/500px-dl/Downloads/{}".format(folder)
    file_name = "/{}_{}.{}".format(photo.name, str(photo.id_), photo.format_)
    if Path(dir_name + file_name).exists():
        print("Skipping {} - Already exists".format(photo.name))
        return
    Path(dir_name).mkdir(parents=True, exist_ok=True)
    file = session.get(photo.url)
    open(dir_name + file_name, 'wb+').write(file.content)
    print("Downloaded: {}".format(photo.name))


def parse_photo_json(photo_json):
    author = photo_json["user"]["fullname"]
    photo_id = photo_json["id"]
    photo_url = photo_json["image_url"][0]
    photo_format = photo_json["image_format"]
    photo_name = photo_json["name"]
    return Photo(photo_id, photo_name, photo_url, photo_format, author)


def get_user_id(url):
    page = session.get(url)
    return page.html.search("App.CuratorId = \"{}\"")[0]


def let_it_rip(url):
    if "/galleries/" in url:
        user_id = get_user_id(url)
        get_gallery(user_id, Path(url).stem)
    elif "500px.com/photo/" in url:
        get_photo(url.split("/")[4])
    elif url.count("/") == 3:
        user_id = get_user_id(url)
        get_photos(user_id)
    else:
        print("Skipped {}".format(url))


class Photo:
    def __init__(self, id_, name, url, format_, author):
        self.id_ = id_
        self.name = name
        self.url = url
        self.format_ = format_
        self.author = author


for arg in sys.argv:
    let_it_rip(arg)
