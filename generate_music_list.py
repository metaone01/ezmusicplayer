import os,json
music_path = os.path.realpath(r'G:\Songs\music')
lyric_path = os.path.realpath(r'G:\Songs\lyrics')
MUSIC_LIST = [
    (os.path.join(music_path, filename), os.path.join(lyric_path, filename))
    for filename in os.listdir(music_path)
]
with open('./settings/music_list.json','w',encoding='utf-8') as f:
    json.dump(MUSIC_LIST,f,indent=4,ensure_ascii=False)
