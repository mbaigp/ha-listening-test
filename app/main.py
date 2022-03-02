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
import boto3

DESCRIPTION = """
👋 Welcome! This experiment should take around 20 minutes of your time.

📢 Only perform this experiment in case you have a somewhat clear idea on what harmony is.

"""

INSTRUCTIONS = """
📃 You will be presented with four different playlists that contain the same 10 music tracks, each with a corresponding letter from 'A' to 'J' assigned, but presented in a slightly different order.

**You don't need to listen to each track for the full duration**, please listen to the tracks **just enough** to glimpse each track's key.


⭐ For each pair of songs in every playlist,
please assess **the harmonic quality of the transitions**.

In case you doubt, we recommend to play both songs simultaneously.

Overall:

## Mark the transitions that sound inharmonic to you, THEN SUBMIT:
"""

END_MESSAGE = """
### Thanks for participating!
"""

LETTERS = ['A', 'B', 'C', 'D']

def save_respose(results):
    aws_path = st.secrets['AWS_PATH'].split('/')[2]
    s3 = boto3.client('s3')

    #we encode the name of the last playlist in the CSV path
    filename = str(datetime.now())+'_'+st.session_state['playlist']+'_'+st.session_state['username']+'.jsonl'

    data_string = ""
    for line in results:
        data_string += json.dumps(line, ensure_ascii=False)
        data_string += '\n'


    s3.put_object(Body=data_string,
                    Bucket=aws_path,
                    Key=filename)

def set_finish():
    #we read the value of each button and write in the results np.array:
    results = []
    for key in st.session_state['keys']:
        for k in range(st.session_state['num_transitions']):
            results.append(
            {"method": key, "transition_idx": k,
            "user": st.session_state['username'],
            "playlist": st.session_state['playlist'],
            "harmonicity": st.session_state[str(key)+str(k)].split(' ')[0]
            })
    #advance in the progress bar
    st.session_state['progress'] += 1
    save_respose(results)

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

    num_pages = 1
    num_methods = len(data_all[0]['options'])
    num_transitions = len(list(data_all[0]['options'].values())[0]['permutation'])-1

    #instantiate global variables (not re-run every interaction)
    if 'num_transitions' not in st.session_state:
        st.session_state['num_transitions'] = num_transitions
    if 'progress' not in st.session_state:
        st.session_state['progress'] = 0
    progress = st.session_state['progress']

    st.progress(progress / num_pages)

    if progress < num_pages:
        #here we randomly pick a playlist
        #pick = np.random.randint(0, len(data_all))
        #data = data_all[np.random.randint(0, len(data_all))]
        username = st.text_input('Please write a username and press Enter:', '', key='username')

        if username != '':
            all_names = ['<select>']
            for x in data_all:
                all_names.append(x['playlist']['name'])

            choice = st.selectbox('Now select a playlist:', all_names, key='playlist')
            if choice != '<select>':
                for data in data_all:
                    if data['playlist']['name'] == choice:
                        break
                #data = data_all[all_names.index(choice)]
                playlist_name = data['playlist']['name']

                st.markdown(INSTRUCTIONS)

                st.markdown('### Playlist: '+playlist_name)
                if 'playlist_name' not in st.session_state:
                    st.session_state['playlist_name'] = playlist_name
                keys = data['options'].keys()
                if keys not in st.session_state:
                    st.session_state['keys'] = keys

                with st.form(key='form', clear_on_submit=True):
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
                                    radio = st.radio(label = 'The track above and the track below have :', options = ['good harmonic compatibility','bad harmonic compatibility'], key=str(item)+str(k))


                    submitted = st.form_submit_button(on_click=set_finish)

    else:
        st.balloons()
        st.markdown(END_MESSAGE)


if __name__ == '__main__':
    main()
