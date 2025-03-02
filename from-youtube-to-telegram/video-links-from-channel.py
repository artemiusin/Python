import googleapiclient.discovery
# Замените на ваш API ключ
from api_key_google import api_key    

def get_channel_videos(api_key, channel_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    # Получаем ID плейлиста с загруженными видео канала
    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    response = request.execute()

    if not response['items']:
        print("Канал не найден.")
        return

    uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    # Получаем все видео из плейлиста
    videos = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            video_title = item['snippet']['title']
            video_id = item['snippet']['resourceId']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            videos.append((video_title, video_url))

        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    return videos

def main():
    channel_id = input("Введите ID канала YouTube: ")

    videos = get_channel_videos(api_key, channel_id)

    if videos:
        print(f"\nВсего видео на канале: {len(videos)}")
        print("\nСписок видео на канале:")
        for index, (title, url) in enumerate(videos, start=1):
            print(f"{index}. {title}: {url}")
    else:
        print("На канале нет видео.")

if __name__ == "__main__":
    main()