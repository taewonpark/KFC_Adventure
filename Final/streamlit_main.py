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
st.set_option('deprecation.showPyplotGlobalUse', False)

INITIAL_STATE = {"Message": ""}

# Setup Confluent
config_file = "/Users/gubo/Downloads/python.config"
# Create Producer instance
conf = ccloud_lib.read_ccloud_config(config_file)
producer_topic = 'button_topic'
producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
# producer_conf['value.serializer'] = ccloud_lib.json_serializer
producer = Producer(producer_conf)
# Create topic if needed
ccloud_lib.create_topic(conf, producer_topic)


## event data
def change_color(pixels, a, date):
    """
    date: int ex) 14, 28
    """
    week, w_day = pixels._monthday_to_index(date)
    pixels.axs[week][w_day].set_facecolor('red')

 
def insert_text(pixels, a, date, text):
    """
    date: int ex) 14, 28 
    text: "happy"
    """
    week, w_day = pixels._monthday_to_index(date)
    pixels.axs[week][w_day].text(0.05, 0.08, s='#'+text)  # axis ㅡ ㅣ

def main():

    for key, val in INITIAL_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = val
            
    st.image('total_logo.png', width=500)
    st.title("NEED Project")
    st.header('Team KFC')

    today = date.today() #2022-12-27
    pixels = MplCalendar(today.year, today.month) # 2017, 2
    

    st.title("🗓️ Year in Pixels")
    ## Tell streamlit to display the figure
    a = st.pyplot(pixels.f)


    button_columns = st.columns(2)
    with button_columns[0]:
        get_start = st.button("Start")
    with button_columns[1]:
        get_stop = st.button("Stop")

    with st.spinner("Processing button..."):
        if get_start:
            producer.produce(producer_topic, value=bytes('start', 'utf-8'))
            producer.flush()
            st.session_state["Message"] = "Start"
                
        if get_stop:
            producer.produce(producer_topic, value=bytes('stop', 'utf-8'))
            producer.flush()
            st.session_state["Message"] = "Stop"
            
            #TODO: conusmer로 emotion 받아와야함
            
            # change color
            change_color(pixels, a, today.day)
            
            # TODO: perform keyword_extraction, write text
            insert_text(pixels, a, today.day, 'exciting')
            
            # Modify plot
            a.pyplot()
            
    st.write("* * *")
    st.header("Result")

    st.text_area(label="Message", value=st.session_state["Message"], disabled=True)
    
            
if __name__ == "__main__":
    main()
