import googleapiclient.discovery
# Замените на ваш API ключ
from api_key_google import api_key 

def get_channel_video_count(api_key, channel_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    # Получаем информацию о канале
    request = youtube.channels().list(
        part="statistics",
        id=channel_id
    )
    response = request.execute()

    if not response['items']:
        print("Канал не найден.")
        return

    # Получаем количество видео из статистики канала
    video_count = response['items'][0]['statistics']['videoCount']
    print(f"Количество видео на канале: {video_count}")

if __name__ == "__main__":
    channel_id = input("Введите ID канала YouTube: ")
    get_channel_video_count(api_key, channel_id)