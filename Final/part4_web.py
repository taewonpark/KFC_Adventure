import streamlit as st
from mplcal import MplCalendar
from datetime import date
import ccloud_lib
from confluent_kafka import Producer, Consumer
from collections import defaultdict

import json

from playsound import playsound
from gtts import gTTS


st.set_option('deprecation.showPyplotGlobalUse', False)


COLOR_DICT = {
    'sadness': (157/255,236/255,250/255),
    'joy': (140/255,240/255,160/255),
    'love': (255/255,212/255,244/255), 
    'anger': (252/255,136/255,136/255),
    'fear': (230/255,204/255,255/255),
    'surprise': (255/255,246/255,163/255)
}
COLOR_IDX = {
    0: 'sadness',
    1: 'joy',
    2: 'love',
    3: 'anger',
    4: 'fear',
    5: 'surprise',
}


history = {
    '2022-12':{
        '03':{
            'content': 'Since I slept until noon, I failed to attend the machine learning course team meeting',
            'emotion': 'fear',
            'keyword': 'machine learning course',
        },
        
        '08': {
            'content': 'I finally submit my last report of the semester! It has been a busy semester, but I am proud of what I have accomplished so far',
            'emotion': 'joy',
            'keyword': '',
        },
        '08': {
            'content': 'Our team managed to complete the final project for the IDL class',
            'emotion': 'joy',
            'keyword': 'IDL class',
        },
        '13': {
            'content': 'I skated alone in the Central Park of New York City. I was lonely since there were many couples around.',
            'emotion': 'sadness',
            'keyword': 'Central Park',
        },
        '17': {
            'content': 'I went to the Metropolitan Museum for the first time, and I was quite amazed by the high quality of art and the enormous size of the museum',
            'emotion': 'surprise',
            'keyword': 'Metropolitan Museum',
        },
        '20': {
            'content': 'I had a fight with the Bolivian embassy over not giving me a visa',
            'emotion': 'anger',
            'keyword': 'Bolivian embassy',
        },
        '28': {
            'content': 'I almost vomited from mountain-sickness.',
            'emotion': 'sadness',
            'keyword': '',
        },
    },
    '2023-01': {
        '03': {
            'content': "I went to the top of the Cathedral of Learning at the University of Pittsburgh. Since it snowed recently, the white landscape of Pittsburgh was so beautiful.",
            'emotion': 'joy',
            'keyword': 'Cathedral of Learning',
        },
        '05': {
            'content': "I did not know that freshly baked cookies are so soft. I was startled when the neck of dog-shape cookie Minseon made was broken",
            'emotion': 'fear',
            'keyword': 'freshly baked cookies',
        },
        '12': {
            'content': 'I taught Juhyeon play F cord in guitar. Making hobbies is always interesting!',
            'emotion': 'joy',
            'keyword': '',
        },
        '21': {
            'content': 'My friend had a lovely baby. I visited her house and hugged him.',
            'emotion': 'love',
            'keyword': '',
        },
        '26': {
            'content': 'I visited the Carnegie Museum of Natural History and there were the fossils of two Tyrannosaurus Rexes. The sharp and huge teeth of them are so frightening.',
            'emotion': 'fear',
            'keyword': 'Tyrannosaurus Rexes',
        },
        
    },
    '2023-02': {
        '03': {
            'content': 'I am scared when I bumped into some deers in Schenley park at night.',
            'emotion': 'fear',
            'keyword': 'Schenley park',
        },
        '04': {
            'content': 'I ate Chinese soup near the University of Pittsburgh and it was too expensive.',
            'emotion': 'anger',
            'keyword': 'Chinese Soup',
        },
        '07': {
            'content': 'VJ looks disappointed',
            'emotion': 'sadness',
            'keyword': '',
        },
        '08': {
            'content': 'I got full score for the NLP final exam.',
            'emotion': 'joy',
            'keyword': 'NLP final exam',
        },
        '10': {
            'content': 'I was shocked by the color of the sky today. It resembles the burning fire.',
            'emotion': 'surprise',
            'keyword': 'Schenley park',
        },
        '14': {
            'content': "I love watching the design of the Fence in CMU changing day by day!",
            'emotion': 'joy',
            'keyword': 'Fence',
        },
        
    },
}

records = defaultdict(dict)
for key in history.keys():
    records[key] = history[key]

TODAY = date.today()
INITIAL_STATE = {"Message": "", "Records": records, "Year": TODAY.year, "Month": TODAY.month, "Finish": False, "Stop_flag": False, "play_record_text": "", "Title": "", "Content": "", "Keyword": ""}

# Setup Confluent
config_file = "confluent_kafka.config"  #TODO: path to 'confluent_kafka.config'
# Create Producer instance
conf = ccloud_lib.read_ccloud_config(config_file)
producer_topic = 'button_topic'
producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
# producer_conf['value.serializer'] = ccloud_lib.json_serializer
producer = Producer(producer_conf)
# Create topic if needed
ccloud_lib.create_topic(conf, producer_topic)


# Create Consumer instance
conf_ = ccloud_lib.read_ccloud_config(config_file)
consumer_topic = 'nlp_topic'
consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf_)
consumer_conf['group.id'] = 'web'
consumer_conf['auto.offset.reset'] = 'earliest'
consumer = Consumer(consumer_conf)
# Subscribe to topic
consumer.subscribe([consumer_topic])


## event data
def change_color(pixels, date, emotion):
    """
    date: int ex) 14, 28
    """
    week, w_day = pixels._monthday_to_index(date)
    pixels.axs[week][w_day].set_facecolor(COLOR_DICT[emotion])

 
def insert_keyword(pixels, date, keyword):
    """
    date: int ex) 14, 28 
    keyword: "happy"
    """
    week, w_day = pixels._monthday_to_index(date)
    pixels.axs[week][w_day].text(0.05, 0.08, s='#'+keyword)  # axis ㅡ ㅣ


def main():


    for key, val in INITIAL_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = val
            
    st.title("🗓️ Year in Pixels")

    button_columns = st.columns(4)
    with button_columns[0]:
        get_prev = st.button("🔙")
    with button_columns[1]:
        get_start = st.button("▶️")
    with button_columns[2]:
        get_stop = st.button("⏹")
    with button_columns[3]:
        get_next = st.button("🔜")

    # today = date.today() #2022-12-27
    pixels = MplCalendar(st.session_state['Year'], st.session_state['Month'])

    ## Tell streamlit to display the figure
    st_plot = st.pyplot(pixels.f)
    current_calendar_key = f"{st.session_state['Year']}-{st.session_state['Month']:02}"
    if current_calendar_key in st.session_state['Records']:
        current_records = st.session_state['Records'][current_calendar_key]
        for day in current_records.keys():
            # change color
            change_color(pixels, int(day), current_records[day]['emotion'])
            # insert keyword
            insert_keyword(pixels, int(day), current_records[day]['keyword'])
    
    st.write("* * *")
    st.header("🍪 History")
    date_click = []
    if current_calendar_key in st.session_state['Records']:
        records_candidate = list(st.session_state['Records'][current_calendar_key].keys())
        date_columns = st.columns(len(records_candidate))
        for i, j in enumerate(records_candidate):
            with date_columns[i]:
                date_click.append(st.button(str(int(j))))



    if st.session_state['Stop_flag']:
        st_plot.pyplot(pixels.f)
        try:
            while True:
                msg = consumer.poll(0.1)
                if msg is None:
                    continue
                elif msg.error():
                    print('error: {}'.format(msg.error()))
                else:
                    print('b')
                    nlp = msg.value()
                    nlp = json.loads(nlp)
                    emotion = COLOR_IDX[nlp['emotion']]
                    keyword = nlp['keywords']
                    stt_text = nlp['text']
                    break
        except:
            pass
        finally:
            consumer.close()

        st.session_state['Stop_flag'] = False
        st.session_state['Finish'] = False
        today_calendar_key = f"{TODAY.year}-{TODAY.month:02}"
        
        # store today recording
        st.session_state['Records'][today_calendar_key][f"{TODAY.day:02}"] = {
            'content': stt_text,
            'emotion': emotion,
            'keyword': keyword
        }

        if current_calendar_key == today_calendar_key:
            # change color
            change_color(pixels, TODAY.day, emotion)
            # insert keyword
            insert_keyword(pixels, TODAY.day, keyword)
            # reload page
            st.experimental_rerun()




    with st.spinner("Processing button..."):

        if get_start:
            st.session_state['play_record_text'] = ""
            producer.produce(producer_topic, value=bytes('start', 'utf-8'))
            producer.flush()

            st.session_state['Finish'] = True
                
        if get_stop:
            st.session_state['play_record_text'] = ""
            producer.produce(producer_topic, value=bytes('stop', 'utf-8'))
            producer.flush()

            if st.session_state['Finish']:
                st.session_state['Stop_flag'] = True
                st.experimental_rerun()

        if get_prev or get_next:
            st.session_state['play_record_text'] = ""
            if get_prev:
                if st.session_state['Month'] == 1:
                    st.session_state['Year'] -= 1
                    st.session_state['Month'] = 12
                else:
                    st.session_state['Month'] -= 1
            if get_next:
                if st.session_state['Month'] == 12:
                    st.session_state['Year'] += 1
                    st.session_state['Month'] = 1
                else:
                    st.session_state['Month'] += 1
            
            pixels = MplCalendar(st.session_state['Year'], st.session_state['Month'])
            change_calendar_key = f"{st.session_state['Year']}-{st.session_state['Month']:02}"
            if change_calendar_key in st.session_state['Records']:
                change_records = st.session_state['Records'][change_calendar_key]
                for day in change_records.keys():
                    # change color
                    change_color(pixels, int(day), change_records[day]['emotion'])
                    # insert keyword
                    insert_keyword(pixels, int(day), change_records[day]['keyword'])
            
            # reload page
            st.experimental_rerun()
        
        # Modify plot
        st_plot.pyplot(pixels.f)

    st.write("* * *")
    # st.header("Record")

    try:
        showing_date_idx = date_click.index(True)
        showing_date = records_candidate[showing_date_idx]
        record_showing_date = st.session_state['Records'][current_calendar_key][showing_date]

        st.session_state["Title"] = f"{current_calendar_key}-{showing_date} ({record_showing_date['emotion']})"
        st.session_state["Content"] = f"{record_showing_date['content']}"
        st.session_state["Keyword"] = f"# {record_showing_date['keyword']}"

        st.session_state["Message"] = f"""
            {current_calendar_key}-{showing_date} ({record_showing_date['emotion']}),\n
            \t{record_showing_date['content']}\n
            \t# {record_showing_date['keyword']}
        """
        st.session_state['play_record_text'] = record_showing_date['content']
        
    except:
        if st.session_state['play_record_text'] == '':
            st.session_state["Title"] = ""
            st.session_state["Content"] = ""
            st.session_state["Keyword"] = ""
            st.session_state["Message"] = ""

    st.markdown(f'##### {st.session_state["Title"]}')
    st.markdown(f'{st.session_state["Content"]}')
    st.markdown(f'**_{st.session_state["Keyword"]}_**')

    play_button_columns = st.columns(1)
    with play_button_columns[0]:
        get_play = st.button("Play the record")

    if get_play:
        text = st.session_state['play_record_text']

        mp3 = gTTS(text=text, lang='en', slow=False)
        mp3.save('example.mp3')

        playsound('example.mp3')
    
            
if __name__ == "__main__":
    main()
