import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import calendar
from july.utils import date_range
from mplcal import MplCalendar
from datetime import date

st.set_option('deprecation.showPyplotGlobalUse', False)


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
        
        if get_stop:      
            # TODO: conusmer로 emotion 받아와야함
            # change color
            change_color(pixels, a, today.day)
            
            # TODO: perform keyword_extraction, write text
            
            insert_text(pixels, a, today.day, 'exciting')
            
            # Modify plot
            a.pyplot()
            
if __name__ == "__main__":
    main()