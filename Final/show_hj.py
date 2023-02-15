import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import calendar
import july
from july.utils import date_range
from mplcal import MplCalendar
from datetime import date
import ccloud_lib
from confluent_kafka import SerializingProducer, Producer
from collections import defaultdict

import copy

from st_click_detector import click_detector


st.set_option('deprecation.showPyplotGlobalUse', False)

COLOR_DICT = {
    'sadness': (157/255,236/255,250/255),
    'joy': (140/255,240/255,160/255),
    'love': (255/255,212/255,244/255), 
    'angry': (252/255,136/255,136/255),
    'fear': (230/255,204/255,255/255),
    'surprise': (255/255,246/255,163/255)
}



history = {
    '2023-01': {
        '05': {
            'content': 'milestone2',
            'emotion': 'joy',
            'keyword': 'joy',
        },
        '20': {
            'content': 'it was nice weather today',
            'emotion': 'joy',
            'keyword': 'joy',
        },
    },
    '2023-02': {
        '03': {
            'content': 'I felt blue',
            'emotion': 'sadness',
            'keyword': 'blue',
        },
        '04': {
            'content': 'it was nice weather today',
            'emotion': 'joy',
            'keyword': 'nice weather',
        },
        '06': {
            'content': 'I got C for my IDL class',
            'emotion': 'angry',
            'keyword': 'C',
        },
        '07': {
            'content': 'VJ looks disappointed',
            'emotion': 'fear',
            'keyword': 'VJ',
        },
        '08': {
            'content': 'I got full score for the NLP final exam.',
            'emotion': 'surprise',
            'keyword': 'final exam',
        },
        '14': {
            'content': "It is Valentine's day today!",
            'emotion': 'love',
            'keyword': 'Valentine',
        },
    },
}


records = defaultdict(dict)
for key in history.keys():
    records[key] = history[key]

TODAY = date.today()
INITIAL_STATE = {"Message": "", "Records": records, "Year": TODAY.year, "Month": TODAY.month}

# Setup Confluent
config_file = "C:/Users/hojeong/Desktop/CMU/Studio/python.config"
# Create Producer instance
conf = ccloud_lib.read_ccloud_config(config_file)
producer_topic = 'button_topic'
producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
# producer_conf['value.serializer'] = ccloud_lib.json_serializer
producer = Producer(producer_conf)
# Create topic if needed
ccloud_lib.create_topic(conf, producer_topic)

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
            
    # st.image('total_logo.png', width=500)
    # st.title("NEED Project")
    # st.header('Team KFC')

    st.title("🗓️ Year in Pixels")

    button_columns = st.columns(4)
    with button_columns[0]:
        get_prev = st.button("Previous")
    with button_columns[1]:
        get_start = st.button("Start")
    with button_columns[2]:
        get_stop = st.button("Stop")
    with button_columns[3]:
        get_next = st.button("Next")

    # today = date.today() #2022-12-27
    pixels = MplCalendar(st.session_state['Year'], st.session_state['Month']) # 2017, 2
    pixels._render()

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


    # last_date = calendar.monthrange(st.session_state['Year'], st.session_state['Month'])[1]
    # date_columns = st.columns(last_date)
    # date_click = []
    # for i in range(last_date):
    #     with date_columns[i]:
    #         date_click.append(st.button(str(i+1)))
    
    st.write("* * *")
    st.header("🗓️ History")
    date_click = []
    if current_calendar_key in st.session_state['Records']:
        records_candidate = list(st.session_state['Records'][current_calendar_key].keys())
        date_columns = st.columns(len(records_candidate))
        for i, j in enumerate(records_candidate):
            with date_columns[i]:
                date_click.append(st.button(str(int(j))))
    
    # date_columns = [st.columns(10) for _ in range(3)]
    # date_columns.append(st.columns(1))
    # date_click = []
    # for i in range(31):
    #     with date_columns[i//10][i%10]:
    #         if current_calendar_key in st.session_state['Records'] and f"{i+1:02}" in st.session_state['Records'][current_calendar_key].keys():
    #             date_click.append(st.button(str(i+1)))
    #         else:
    #             date_click.append(st.button())

    with st.spinner("Processing button..."):
        if get_start:
            # producer.produce(producer_topic, value=bytes('start', 'utf-8'))
            # producer.flush()
            # st.session_state["Message"] = ""
            pass
                
        if get_stop:
            # producer.produce(producer_topic, value=bytes('stop', 'utf-8'))
            # producer.flush()
            # st.session_state["Message"] = "Stop"
            
            #TODO: conusmer로 emotion 받아와야함, records dictionary에 정보 저장해야 함
            stt_text = "it was terrible"  # TODO
            emotion = "angry"  # TODO
            keyword = "bad day"  # TODO
            
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

        if get_prev or get_next:
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
        st.session_state["Message"] = f"""
            Recording Date: {current_calendar_key}-{showing_date},\n
            \tContent: {record_showing_date['content']}\n
            \tEmotion: {record_showing_date['emotion']}\n
            \tKeyword: {record_showing_date['keyword']}
        """
    except:
        st.session_state["Message"] = ""

    # click 시에만 message에 값 넣어주기
    st.text_area(label="Record", value=st.session_state["Message"], disabled=False, height=500)
    
            
if __name__ == "__main__":
    main()
