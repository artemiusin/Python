import googleapiclient.discovery
from pytube import YouTube
import os
import ffmpeg
from tqdm import tqdm
import time
import random
from pytube import exceptions  # Импортируем исключения pytube

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
        return []

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
        try:
            response = request.execute()
        except googleapiclient.errors.HttpError as e:
            print(f"Ошибка при получении списка видео: {e}")
            break

        for item in response['items']:
            video_title = item['snippet']['title']
            video_id = item['snippet']['resourceId']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            videos.append((video_title, video_url))

        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    return videos

def download_and_convert_to_mp3(video_url, output_path="output"):
    try:
        # Скачиваем видео
        yt = YouTube(video_url)
        video = yt.streams.filter(only_audio=True).first()
        if video:
            video_file = video.download(output_path)

            # Конвертируем видео в MP3 с помощью ffmpeg
            mp3_file = os.path.join(output_path, os.path.splitext(os.path.basename(video_file))[0] + ".mp3")
            try:
                ffmpeg.input(video_file).output(mp3_file).run(overwrite_output=True)
            except ffmpeg.Error as e:
                print(f"Ошибка при конвертации видео {video_url} в MP3: {e.stderr.decode()}")
                return None

            # Удаляем временный видео файл
            os.remove(video_file)

            return mp3_file
        else:
            print(f"Аудиопоток не найден для видео: {video_url}")
            return None
    except exceptions.RegexMatchError as e:
        print(f"Ошибка RegexMatchError при обработке видео {video_url}: {e}")
        return None
    except exceptions.VideoUnavailable as e:
        print(f"Видео недоступно {video_url}: {e}")
        return None
    except exceptions.AgeRestrictedError as e:
        print(f"Возрастное ограничение для видео {video_url}: {e}")
        return None
    except exceptions.LiveStreamError as e:
        print(f"Это прямая трансляция {video_url}: {e}")
        return None
    except Exception as e:
        print(f"Ошибка при обработке видео {video_url}: {e}")
        return None

def main():
    channel_id = input("Введите ID канала YouTube: ")
    output_path = input("Введите путь для сохранения MP3 файлов (по умолчанию 'output'): ") or "output"

    # Создаем директорию, если она не существует
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    videos = get_channel_videos(api_key, channel_id)

    if videos:
        print(f"\nВсего видео на канале: {len(videos)}")
        print("\nНачинаем скачивание и конвертацию...")

        # Используем tqdm для отображения прогресс-бара
        for title, url in tqdm(videos, desc="Обработка видео", unit="видео"):
            print(f"\nОбработка видео: {title}")
            # Добавляем случайную задержку перед каждой загрузкой
            time.sleep(random.randint(1, 5))  # Задержка от 1 до 5 секунд
            mp3_file = download_and_convert_to_mp3(url, output_path)
            if mp3_file:
                print(f"Успешно: {mp3_file}")
            else:
                print(f"Ошибка при обработке видео: {title}")

        print("\nВсе видео обработаны!")
    else:
        print("На канале нет видео.")

if __name__ == "__main__":
    main()
