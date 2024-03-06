import shutil
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import os
import streamlit as st
from pytube import YouTube
from youtubesearchpython import VideosSearch
import moviepy.editor as mp
from pydub import AudioSegment
import random
import requests

# Function to empty a folder
def empty_folder(folder_path):
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        print(f"The folder {folder_path} does not exist.")

# Function to download videos and extract audio
def download_and_extract_audio(artist_names, num_songs):
    folder_path = "videos"
    audio_path = "audios"



# Create 'videos' directory if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    if not os.path.exists(audio_path):
        os.makedirs(audio_path)

    # Empty the folders before downloading new files
    empty_folder(folder_path)
    empty_folder(audio_path)

    for artist_name in artist_names:
        videosSearch = VideosSearch(artist_name, limit=num_songs)
        links = [video['link'] for video in videosSearch.result()['result']]

        


        for video_url in links:
            try:
                yt = YouTube(video_url)
                stream = yt.streams.get_highest_resolution()
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                stream.download(output_path=folder_path)
                st.write("Downloaded:", yt.title)
            except Exception as e:
                st.write(f"An error occurred while downloading {video_url}: {str(e)}")


        # Extract audio
        try:
            vids = os.listdir(folder_path)
        except FileNotFoundError:
            st.write(f"Directory not found: {folder_path}")
            continue  # Skip to the next artist if the directory is not found

        auds = [vid[:-4] for vid in vids]

        for i in range(len(vids)):
            try:
                clip = mp.VideoFileClip(f"{folder_path}/{vids[i]}")
                duration = clip.duration
                end = random.randint(40,60)
                clip = mp.VideoFileClip(f"{folder_path}/{vids[i]}").subclip(20, end)
                audio = clip.audio
                if not os.path.exists(audio_path):
                    os.makedirs(audio_path)
                audio.write_audiofile(f"{audio_path}/{auds[i]}.mp3", codec='libmp3lame')
            except Exception as e:
                st.write(f"An error occurred while extracting audio: {str(e)}")

    return yt.title

# Function to concatenate audio files
def concatenate_audio_files():
    combined = AudioSegment.empty()
    auds = os.listdir("audios")
    for aud in auds:
        audio_chunks = AudioSegment.from_file(f"audios/{aud}")
        combined += audio_chunks
    output_folder = "mashups"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    combined.export(f"{output_folder}/combined.mp3", format="mp3")


def send_email(email, audio_path):
    # Set up Mailgun API credentials
    MAILGUN_API_KEY = '97fb2ec732e860b24c2e067609b8d402-b7b36bc2-95c759dc'
    MAILGUN_DOMAIN = 'sandbox4c4f3417170a496bbdc086c35085e484.mailgun.org'

    # Get list of audio files in the folder
    audio_files = [f for f in os.listdir(audio_path) if os.path.isfile(os.path.join(audio_path, f)) and f.endswith('.mp3')]


    if not audio_files:
        raise ValueError('No audio files found in the specified folder.')

    # Create a new message with attachments
    response = requests.post(
        f'https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages',
        auth=('api', MAILGUN_API_KEY),
        files=[('attachment', (audio_file, open(os.path.join(audio_path, audio_file), 'rb').read())) for audio_file in audio_files],
        data={
            'from': "MeshupMania@sandbox4c4f3417170a496bbdc086c35085e484.mailgun.org",
            'to': [email],
            'subject': 'Mashup of Audios',
            'text': 'Attached is the mashup of audio files.'
        }
    )

    if response.status_code == 200:
        return True
    else:
        return False


# Streamlit UI
st.title("Mashup Creator")

artist_names_input = st.text_input("Enter the artist names separated by comma for creating mashup")
num_songs = st.text_input("Enter the number of songs for each artist")
email  = st.text_input("Enter your mail to recieve the mashup")
if st.button("Create Mashup"):
    if artist_names_input:
        artist_names = [name.strip() for name in artist_names_input.split(",")]
        st.write("Creating Mashup...")
        title = download_and_extract_audio(artist_names, int(num_songs))
        concatenate_audio_files()
        try:
            folder_path = folder_path = os.path.join(os.getcwd(), "mashups")
            send_email(email,folder_path)
            st.success('Email sent successfully!')
        except Exception as e:
            st.error(f'Failed to send email: {e}')
        st.success("Mashup Created Successfully!")
        audio_path = f"{folder_path}/combined.mp3"
        if audio_path:
            try:
                with open(audio_path, "rb") as f:
                    bytes_data = f.read()
                st.download_button(label=f"Download {title}.mp3", data=bytes_data, file_name=f"mahsup.mp3")
                st.success("Song Downloaded!")
            except Exception as e:
                st.error(f"Failed to download: {e}")
