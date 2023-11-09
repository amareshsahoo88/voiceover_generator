from dotenv import load_dotenv
import streamlit as st
from moviepy.editor import VideoFileClip
import cv2
import openai
from openai import OpenAI
load_dotenv()

import os
import requests
import tempfile
import base64

api_key = os.getenv('OPENAI_API_KEY')



def video_to_frames(video_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmpfile:
        tmpfile.write(video_file.read())
        video_filename = tmpfile.name

    video_duration = VideoFileClip(video_filename).duration

    video = cv2.VideoCapture(video_filename)
    base64Frames = []

    while video.isOpened():
        success, frame = video.read()
    if not success:
        break_, 
        buffer = cv2.imencode(".jpg", frame)
        base64Frames.append(base64.b64encode(buffer).decode("utf-8"))

    video.release()
    print(len(base64Frames), "frames read.")
    return base64Frames, video_filename, video_duration

def frames_to_story(base64Frames, prompt):
    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                prompt,
                *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::25]),
            ],
        },
    ]
    params = {
        "model": "gpt-4-vision-preview",
        "messages": PROMPT_MESSAGES,
        "max_tokens": 500,
    }

    result = client.chat.create(**params)
    print(result.choices[0].message.content)
    return result.choices[0].message.content


def text_to_audio(text):
    # Updated function to handle audio correctly.
    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": "tts-1",
            "input": text,
            "voice": "onyx",
        },
    )

    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}")

    audio_file_path = "output_audio.wav"
    with open(audio_file_path, "wb") as audio_file:
        audio_file.write(response.content)

    return audio_file_path

def merge_audio_video(video_filename, audio_filename, output_filename):
    print("Merging audio and video...")
    print("Video filename:", video_filename)
    print("Audio filename:", audio_filename)

    # Load the video file
    video_clip = VideoFileClip(video_filename)

    # Load the audio file
    audio_clip = AudioFileClip(audio_filename)

    # Set the audio of the video clip as the audio file
    final_clip = video_clip.set_audio(audio_clip)

    # Write the result to a file (without audio)
    final_clip.write_videofile(
        output_filename, codec='libx264', audio_codec='aac')

    # Close the clips
    video_clip.close()
    audio_clip.close()

    # Return the path to the new video file
    return output_filename

def main():
    st.set_page_config(page_title="Video voice over", page_icon=":bird:")

    st.header("Video voice over :bird:")
    uploaded_file = st.file_uploader("Choose a file")

    if uploaded_file is not None:
        st.video(uploaded_file)
        prompt = st.text_area(
            "Prompt", value="These are frames of a quick product demo walkthrough. Create a short voiceover script that outline the key actions to take, that can be used along this product demo.")

    if st.button('Generate', type="primary") and uploaded_file is not None:
        with st.spinner('Processing...'):
            base64Frames, video_filename, video_duration = video_to_frames(
                uploaded_file)

            est_word_count = video_duration * 2
            final_prompt = prompt + f"(This video is ONLY {video_duration} seconds long, so make sure the voice over MUST be able to be explained in less than {est_word_count} words)"

            # st.write(final_prompt)
            text = frames_to_story(base64Frames, final_prompt)
            st.write(text)

            # Generate audio from text
            audio_filename, audio_bytes_io = text_to_audio(text)

            # Merge audio and video
            output_video_filename = os.path.splitext(video_filename)[
                0] + '_output.mp4'
            final_video_filename = merge_audio_video(
                video_filename, audio_filename, output_video_filename)

            # Display the result
            st.video(final_video_filename)

            # Clean up the temporary files
            os.unlink(video_filename)
            os.unlink(audio_filename)
            os.unlink(final_video_filename)

if __name__ == '__main__':
    main()
