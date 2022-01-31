import json
import random
from datetime import datetime
from typing import Optional
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import pandas as pd
import streamlit as st

SIMILARITY = {
    'Not harmonic': 0,
    'Somewhat harmonic': 1,
    'Quite harmonic': 2,
    'Very harmonic': 3
}

DESCRIPTION = """
👋 Welcome! This experiment should take around 40 minutes of your time.

📢 Please only perform this experiment in case you have a somewhat clear idea on what harmony is.

⚠ We recommend using Firefox or Chrome on a device with a big screen.

ℹ️ This experiment is completely anonymous, and all the data collected will be used for research purposes. You can
stop participating in this experiment at any moment and there will be no data submitted as long as you don't see the
final message.

📢 Please read the following instructions carefully
and **don't reload the page** until you are finished, or you will lose your progress.

📃 You will be presented with four different playlists that contain the same music tracks.
**You don't need to listen to each track for the full duration**, please listen to the tracks **just enough** to glimpse each track's key.

🎯 There are 4 playlists in total, your overall progress is indicated by the progress bar under these
instructions.

⏳ Please **don't think too much** about the answers or spend too much time on each track, answer intuitively by
adjusting the rating to that which feels right after familiarizing yourself with every track from a playlist.
Don't forget that there are no wrong answers.

⭐ For each playlist,
please rate **the harmonicity of the transitions** on the 4-point scale from _"not harmonic"_ to _"very harmonic"_.
Your task is to judge how well songs in a playlist would be mixed with the previous song. In case you doubt if a transition is harmonic,
we recommend to play both songs simultaneously. Overall:

### Which of these playlists has smoother transitions in terms of musical harmony?
"""

END_MESSAGE = """
### Thanks for participating!


"""

LETTERS = ['A', 'B', 'C', 'D']

def save_respose(df: pd.DataFrame) -> None:
    print(df)
    aws_path = st.secrets['AWS_PATH']
    aws_path += f'{datetime.now()}.csv'
    df.to_csv(aws_path, storage_options={'anon': False})


def save_answer(keys: list[str], track_id: int, total: int) -> None:
    st.session_state['progress'] += 1

    results = {k: SIMILARITY[st.session_state[k]] for k in keys}
    if st.session_state['skip']:
        results['uncertainty'] = 'UNCERTAIN'
    else:
        results['uncertainty'] = 'CERTAIN'

    st.session_state['results'][track_id] = results

    if st.session_state['progress'] == total:
        df = pd.DataFrame(st.session_state['results'])
        df.sort_index(inplace=True)
        save_respose(df)


def main():
    #login into spotify API
    cid = st.secrets['SPOTIPY_CLIENT_ID']
    secret = st.secrets['SPOTIPY_CLIENT_SECRET']
    client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    sp = sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

    st.set_page_config(layout='wide')
    st.markdown('# Playlist harmonicity experiment')
    st.markdown(DESCRIPTION)

    with open('listening_selection_data_5.json') as fp:
        data_all = json.load(fp)

    if 'progress' not in st.session_state:
        st.session_state['progress'] = 0
        st.session_state['results'] = {}
    progress = st.session_state['progress']

    total = len(data_all)
    st.progress(progress / total)
    if progress < total:
        data = data_all[progress]

        with st.form(key='form', clear_on_submit=True):

            keys = data['options'].keys()
            columns = st.columns(len(data['options']))
            items={}
            for method in data['options']:
                items[method]=data['options'][method]['permutation']
            reference_track_id = data['playlist']['pid']
            #download the audio
            audio = []
            for uri in data['uris']:
                download = requests.get(sp.track(uri)['preview_url'])
                audio.append(download.content)

            for i, (column, item) in enumerate(zip(columns,items)):
                with column:
                    st.markdown(f'### Playlist #{i+1}')
                    for n in items[item]:
                        st.audio(audio[n])
                    st.select_slider('How harmonic?', options=SIMILARITY.keys(), key=item)

            st.checkbox('I have very low confidence in judging transitions in this playlist', key='skip',
                        help='Only tick this checkbox if you have ***zero*** idea on how to rate the harmonicity of transitions, '
                             'your results will be flagged as dubious')
            st.form_submit_button(on_click=save_answer, args=[keys, reference_track_id, total])
    else:
        st.balloons()
        st.markdown(END_MESSAGE)


if __name__ == '__main__':
    main()
