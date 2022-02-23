import json
import random
from datetime import datetime
from typing import Optional
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import streamlit as st
import numpy as np

DESCRIPTION = """

👋 Welcome! This experiment should take around 2 hours of your time.

📢 Please only perform this experiment in case you have a somewhat clear idea on what harmony is.

⚠ We recommend using Firefox or Chrome on a device with a big screen.

ℹ️ This experiment is completely anonymous, and all the data collected will be used for research purposes. You can
stop participating in this experiment at any moment and there will be no data submitted as long as you don't see the
final message.

📢 Please read the following instructions carefully
and **don't reload the page** until you are finished, or you will lose your progress.

📃 You will be presented with four different playlists that contain the same music tracks, but in different order.
**You don't need to listen to each track for the full duration**, please listen to the tracks **just enough** to glimpse each track's key.

🎯 There are 9 playlists in total, your overall progress is indicated by the progress bar under these
instructions.

⏳ Please **don't think too much** about the answers or spend too much time on each track, answer intuitively by
adjusting the rating to that which feels right after familiarizing yourself with every track from a playlist.
Don't forget that there are no wrong answers.

⭐ For each playlist,
please assess **the harmonicity of each transition**.
Your task is to judge if every songs in a playlist would be mixed well with the song below regarding harmonicity.
In case you doubt, we recommend to play both songs simultaneously.

Overall:
### Mark the transitions that sound harmonically bad to you, then Submit:
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


def save_answer():
    st.session_state['progress'] += 1
    if st.session_state['progress'] == st.session_state['num_pages']:
        results = st.session_state['results']
        results = np.reshape(results, (-1, 4))
        df = pd.DataFrame(results)
        df.sort_index(inplace=True)
        for column, key in zip(df.columns, st.session_state['keys']):
            df = df.rename(columns={column:key})
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

    with open('listening_selection_data_10.json') as fp:
        data_all = json.load(fp)

    # infer shape of the results 3D-array from the data json
    num_pages = len(data_all)
    num_methods = len(data_all[0]['options'])
    num_transitions = len(list(data_all[0]['options'].values())[0]['permutation'])-1

    #instantiate global variables (not re-run every interaction)
    if 'num_pages' not in st.session_state:
        st.session_state['num_pages'] = num_pages
    if 'progress' not in st.session_state:
        st.session_state['progress'] = 0
    if 'results' not in st.session_state:
        st.session_state['results'] = np.ones((num_pages, num_transitions, num_methods))
    progress = st.session_state['progress']

    st.progress(progress / num_pages)

    if progress < num_pages:
        data = data_all[progress]
        keys = data['options'].keys()
        if keys not in st.session_state:
            st.session_state['keys'] = keys

        with st.form(key='form', clear_on_submit=True):
            #methods = data['options'].keys()
            columns = st.columns(num_methods)

            items={}
            for method in data['options']:
                items[method]=data['options'][method]['permutation']
            reference_track_id = data['playlist']['pid']

            #hide songs in an alias letter so we can't figure out the ground_truth
            abc = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
            randseed = (list(range(len(items[method]))))
            random.shuffle(randseed)
            song_keys=[abc[i] for i in randseed]


            #download the audio
            audio = []
            for uri in data['uris']:
                dwlink = sp.track(uri)['preview_url']
                download = requests.get(dwlink)
                audio.append(download.content)

            colordict = {}
            colorlist = ['#DC143C', '#FF82AB', '#DA70D6', '#FFE1FF', '#8470FF',
            '#CAE1FF', '#1C86EE', '#87CEFF', '#98F5FF', '#00F5FF', '#00FA9A',
            '#ADFF2F', '#FFFF00', '#CDCD00', '#FFA500', '#FFE4B5', '#CD6600',
            '#EE5C42', '#FF3030', '#8E388E', '#71C671', '#8E8E38', '#C5C1AA',
            '#C67171', '#FFB90F', '#FFFACD', '#EAEAEA', '#A9A9A9', '#EED5D2',
            '#EE5C42', '#CD661D', '#ED9121', '#FF9912', '#EECFA1', '#00CD00']

            bcolorlist = colorlist.copy()
            for i, (column, item) in enumerate(zip(columns,items)):
                with column:
                    st.markdown(f'### Playlist #{i+1}')
                    letterlist = [str(song_keys[x]) for x in items[item]]
                    translateion = {39: None}
                    letterlist = str(letterlist).translate(translateion)
                    letterlist = letterlist[1:]
                    letterlist = letterlist[0:-1]
                    letterlist = letterlist.replace(",", "➡")
                    letterlist = 'Song sequence: '+letterlist
                    st.markdown(letterlist)
                    for k,n in enumerate(items[item]):
                        st.audio(audio[n])
                        #avoid last track (no transition)
                        if k != len(items[item])-1 :
                            #assign a color to the transition
                            from_song = song_keys[items[item][k]]
                            to_song = song_keys[items[item][k+1]]
                            color = '└'+str(from_song)+'➡'+str(to_song)+'┐'
                            color2 = '└'+str(to_song)+'➡'+str(from_song)+'┐'
                            if color not in colordict:
                                if color2 not in colordict:
                                    colordict[color] = bcolorlist.pop()
                                    colordict[color2] = colordict[color]
                            #display the transition with the assigned color and the letter aliases
                            st.markdown('<span style="font-size:36px;background-color: '+colordict[color]+'">'+color+'</span>', unsafe_allow_html=True)
                            radio = st.radio(label = 'Harmonic compatibility between the track above with the track below is :', options = ['good','bad'], key=str(i)+str(k))
                            if radio == 'bad':
                                st.session_state['results'][progress, k, i] = 0
                            else:
                                st.session_state['results'][progress, k, i] = 1
                            #st.write('i '+str(i)+' k: '+str(k))
            submitted = st.form_submit_button("Submit")
            if submitted:
                save_answer()

    else:
        st.balloons()
        st.markdown(END_MESSAGE)


if __name__ == '__main__':
    main()
