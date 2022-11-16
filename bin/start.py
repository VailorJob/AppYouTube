import requests
from bs4 import BeautifulSoup as BS4
import time
import json

from pyfzf import FzfPrompt
import os
import database
from os.path import exists

def convert_to_binary_data(filename):
    # Converting data to binary format
    file = driver.get(filename)
    if file.status_code == 200:
        return file.content
    else:
        with open(filename, 'rb') as file:
            blob_data = file.read()
        return blob_data

def search(_sear=False, _filter=False):

    if _sear or _sear == "":
        sear = _sear
    elif _sear != "":
        sear = input("Enter what you want to find: ")
    
    print("I start searching " + sear)

    r = driver.get(f"{ALL_VAR['SEARCH_QUERY']}{sear}")

    soup = BS4(r.content, "lxml")

    sear_list = ["<-- Back"]
    videos =  soup.select(ALL_VAR["VIDEOS"])

    dict_sear = {}
    for i in range(len(videos)):
        # input(videos[i].prettify())
        video_text = videos[i].select(ALL_VAR["VIDEOS_TEXT_SELECT"])[0].text
        video_url = ALL_VAR["YOUTUBE"] + videos[i].select(ALL_VAR["VIDEOS_URL_SELECT"])[0].get('href')

        if not "channel" in video_url and _sear and _filter == "channel" or video_text in dict_sear and _filter == "channel":
            continue
        elif "channel" in video_url and _filter != "channel":
            video_text = "[Channel] " + video_text
        elif "playlist" in video_url:
            video_text = "[Playlist] " + video_text

        print(video_text)

        dict_sear[video_text] = video_url

    sear_list.extend(dict_sear)

    while(True):
        target_half=fzf.prompt(sear_list)
        print(target_half[0])
        vibor2 = target_half[0]

        if vibor2 == "<-- Back":
            return
        else:
            name = vibor2
            video_url = dict_sear[vibor2]
            print(video_url)
        
        if _filter == "channel":
            return video_url
        else:
            comand = "mpv --profile=youtube " + video_url
                    
            os.system(comand)

def update_video(_dict_video, _active_channel, _soup=False, _update=True):
    dict_video = _dict_video
    status_vid = ""

    if _soup:
        soup = _soup
    else:
        url = _active_channel[1].replace(ALL_VAR["YOUTUBE"], ALL_VAR["NOYOUTUBE"])
        r = driver.get(url)
        soup = BS4(r.content, "lxml")
    
    videos = soup.select(ALL_VAR["VIDEOS"])[::-1]
    video_name = set(title.select(ALL_VAR["VIDEOS_TEXT_SELECT"])[0].text for title in videos)

    # input(videos[0].prettify())

    if list(video_name & set(dict_video)):
        identic = True
    else:
        identic = False

    if _update:
        values = []
        for i in range(len(videos)):
            video_name = videos[i].select(ALL_VAR["VIDEOS_TEXT_SELECT"])[0].text
            video_link = ALL_VAR["YOUTUBE"] + videos[i].select(ALL_VAR["VIDEOS_URL_SELECT"])[0].get('href')
            
            if video_name in dict_video:
                continue

            if not _soup:
                print(f'\n{video_name}')
                print("++ Added ++")
            else:
                status_vid = "++ New videos added ++"

            values.append((_active_channel[0], video_name, video_link))

        if len(values) == 1:
            status_vid = "++ New videos added ++"
            db.insert(
                table="Videos", 
                column="(id_channel, name, url)", 
                values=values[0]
            )
        elif len(values) > 1:
            status_vid = "++ New videos added ++"
            db.insertmany(
                table="Videos", 
                column="(id_channel, name, url)", 
                values=values
            )
        else:
            print("-- No new videos! --")
            

    if _soup:
        return identic, status_vid 

def add_channel(_dict_channel=False, _h=False):
    if not _dict_channel:
        _dict_channel = db.get_dict('id, name, url', 'Channel')

    if _h:
        org_link = _h
    else:
        org_link = input("Enter channel name or address:\n")

        if not "https://www.youtube.com" in org_link:
            org_link = search(org_link, "channel")
            if not org_link:
                return "Cancel"

    h = org_link.replace(ALL_VAR["YOUTUBE"], ALL_VAR["NOYOUTUBE"])

    r = driver.get(h)
    soup = BS4(r.content, "lxml")

    element2 = soup.select(ALL_VAR["CHANNEL_NAME_SELECT"])[0]
    pre_canell = element2.text

    if pre_canell in _dict_channel:
        last_id = _dict_channel[pre_canell][0]
        print(pre_canell)
        status_up = ""
    else:
        last_id = db.insert(
            table="Channel", 
            column="(name, url)", 
            values=[pre_canell, org_link]
        )
        status_up = "Addition completed!"
        print(pre_canell)
        print("++ Added to database! ++")

    dict_video_channel = db.get_dict("id, name, url", "Videos", f"id_channel = {last_id}")
    identic, status_vid = update_video(dict_video_channel, [last_id, h], soup, False)

    h_list = [h]
    soup_list = [soup]

    if not dict_video_channel:
        status_up = ""

    while(not identic):
        print(f"Page additions: {len(soup_list)}")

        h = soup.select(ALL_VAR["CHANNEL_NEXT_PAGE"])
        if h:
            h = ALL_VAR["NOYOUTUBE"] + h[0].get("href")
            r = driver.get(h)
            soup = BS4(r.content, "lxml")
            dict_video_channel = db.get_dict("id, name, url", "Videos", f"id_channel = {last_id}")
            identic, status_vid = update_video(dict_video_channel, [last_id, h], soup, False)
            if not identic:
                h_list.append(h)
                soup_list.append(soup)
            else:
                break
        else:
            break
        time.sleep(1)

    while(soup_list):
        dict_video_channel = db.get_dict("id, name, url", "Videos", f"id_channel = {last_id}")
        identic, status_vid = update_video(dict_video_channel, [last_id, h_list.pop()], soup_list.pop())

    if status_vid:
        print(status_vid)
    print(status_up)

def del_channel():
    list_channel = start_list = ["<-- Back"]
    _dict_channel = db.get_dict('id, name, url', 'Channel')
    list_channel.extend(_dict_channel)

    while(True):
        target_chanel=fzf.prompt(list_channel)
        print(target_chanel[0])
        vibor = target_chanel[0]

        if vibor == "<-- Back":
            break
        else:
            delete_id = _dict_channel[target_chanel[0]][0]
            delete_videos = db.delete("Videos", f"id_channel = {delete_id}")
            delete_channel = db.delete("Channel", f"id = {delete_id}")

        list_channel.remove(target_chanel[0])

def my_video(where=1):
    my_dict_video = db.get_dict("id, name, url", "Videos", where)
    my_video = ["<-- Back"]
    my_video.extend(my_dict_video)

    while(True):
        target_video = fzf.prompt(my_video)[0]
        print(target_video)

        if target_video == "<-- Back":
            break

        link = my_dict_video[target_video][1]
        print(link)

        comand = "mpv --profile=youtube " + link
                
        os.system(comand)

def channel():
    start_ids = ["<-- Back", "++ Add channel ++", "-- Delete channel --"]

    while(True):
        dict_channel = db.get_dict('id, name, url', 'Channel')
        ids = start_ids + list(dict_channel)

        target_chanel=fzf.prompt(ids)
        print(target_chanel[0])
        vibor = target_chanel[0]

        if vibor == "<-- Back":
            break
        elif vibor == ids[1]:
            if add_channel() != "Cancel":
                input(pause_text)
        elif vibor == ids[2]:
            del_channel()
        else:
            active_channel = dict_channel[target_chanel[0]]

            dict_video = db.get_dict("id, name, url", "Videos", f"id_channel = {active_channel[0]}")

            if not dict_video:
                update_video(dict_video, active_channel)
                dict_video = db.get_dict("id, name, url", "Videos", f"id_channel = {active_channel[0]}")
            
            while(True):
                spisokNAME = ["<-- Back", "++ Update video ++"]
                spisokNAME.extend(dict_video)

                target1=fzf.prompt(spisokNAME)

                print(target1[0])

                you_vibor = target1[0]

                if you_vibor == "<-- Back":
                    break
                
                if you_vibor == "++ Update video ++":
                    update_video(dict_video, active_channel)
                    input(pause_text)
                    dict_video = db.get_dict("id, name, url", "Videos", f"id_channel = {active_channel[0]}")
                else:
                    active_video = dict_video[you_vibor]

                    link = active_video[1]
                    print(link)
                    comand2 = "mpv --profile=youtube " + link
                
                    status_code = os.system(comand2)

                    if status_code == 2:
                        print("The video is not available on YouTube so it will be removed from the database")
                        input(pause_text)

                        delete_video = db.delete("Videos", f"id = {active_video[0]}")
                        dict_video.pop(active_video[0])


def update_channel():
    db.query("""CREATE TABLE IF NOT EXISTS Channel (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        logo TEXT,
        url TEXT NOT NULL
    );""")

    db.query("""CREATE TABLE IF NOT EXISTS Videos (
        id INTEGER PRIMARY KEY,
        id_channel INTEGER NOT NULL,
        name TEXT NOT NULL,
        thumbnail_url TEXT,
        thumbnail BLOB,
        length TEXT,
        date_upload INT,
        url TEXT NOT NULL,
        FOREIGN KEY (id_channel) REFERENCES Channel(id)
    );""")

    file_sub = exists('../subscribe.txt')

    f = []
    dict_channel = db.get_dict('id, name, url', 'Channel')
    if file_sub:
        f = [i.strip('\n') for i in open('../subscribe.txt')]

    for _, id_url in dict_channel.items():
        if not id_url[1] in f:
            f.append(id_url[1])

    for k in f:
        add_channel(dict_channel, k)

    input(pause_text)

def func():
    first_menu = {
        "SEARCH+++": search,
        "Channels": channel,
        "My videos": my_video,
        "Update channel list": update_channel,
        "Exit": ""
    }

    ids = [i for i in first_menu.keys()]

    while(True):
        target_chanel=fzf.prompt(ids)
        vibor = target_chanel[0]
        print(vibor)

        if vibor == "Exit":
            break
        
        first_menu[vibor]()

def main():
    global ALL_VAR, pause_text, db, driver, fzf

    JSON_CONF = "youtube_conf.json"

    if exists(JSON_CONF):
        with open(JSON_CONF, encoding="utf-8") as f:
            ALL_VAR = json.load(f)

    else:
        ALL_VAR = {
            "NOYOUTUBE": [
                "https://yewtu.be", 
                "https://invidious.snopyta.org", 
                "https://invidious.kavin.rocks",
                "https://invidious-us.kavin.rocks",
                "https://vid.puffyan.us",
                "https://ytprivate.com",
                "https://invidious.exonip.de",
                "https://ytb.trom.tf",
                "https://ytprivate.com",
                ],
            "YOUTUBE": "https://www.youtube.com",
            "NOYOUTUBE_CHANNEL_LOGO": "/ggpht",
            "YOUTUBE_CHANNEL_LOGO": "https://yt3.ggpht.com",
            "YOUTUBE_VIDEO_THUMBNAIL": "https://i.ytimg.com",
            "SEARCH_QUERY": "/search?q=",
            "CHANNEL_NEXT_PAGE": "#contents > div:nth-child(10) > div:nth-child(3) > a",
            "CHANNEL_NAME_SELECT": ".channel-profile > span",
            "CHANNEL_DESCRIPTION": ".descriptionWrapper",
            "VIDEOS": ".pure-u-1.pure-u-md-1-4 > .h-box",
            "VIDEOS_URL_SELECT": "a",
            "VIDEOS_THUMBNAIL": "img.thumbnail",
            "VIDEOS_LENGTH": "p.length",
            "VIDEOS_TEXT_SELECT": "p[dir='auto']",
            "VIDEOS_DATE_UPLOAD": ".flex-left > p",
        }

        with open(JSON_CONF, "w", encoding="utf-8") as file:
            json.dump(ALL_VAR, file, indent=4, ensure_ascii=False)

    # It is necessary so that we are not perceived as a bot
    HEADERS = {
        "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/78.0.3904.99 Safari/537.36 Vivaldi/2.9.1705.41",
        "accept": "*/*"}

    driver = requests.Session()

    url = "https://www.youtube.com"

    for _ in ALL_VAR["NOYOUTUBE"]:
        if driver.get(_, headers=HEADERS, ).status_code == 200:
            ALL_VAR["NOYOUTUBE"] = _
            ALL_VAR["SEARCH_QUERY"] = _ + ALL_VAR["SEARCH_QUERY"]
            break

    fzf = FzfPrompt()

    pause_text = "\nPress any key to continue . . . "
    kom = exists("Channel.db")

    db = database.DB('Channel.db')

    if kom == True:
        print("Channel database found!")
        func()

    else:
        print("We generate the channel database, this may take some time...")
        update_channel()
        func()

if __name__ == "__main__":
    try:
        main()
        print("Shutdown")
    finally:
        if db.db:
            db.db.close()
            print("SQLite connection closed")

    # text = driver.get("https://dush.com.ua/image/catalog/easyphoto/36000_37000/36466/2505202102_7667.jpg")
    # with open("bn-1-90.jpg", "wb") as f:
    #     f.write(text.content)
                
