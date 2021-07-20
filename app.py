import asyncio
import logging
import logging.handlers
import queue
import threading
import urllib.request
from pathlib import Path
from typing import List, NamedTuple

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore

import av
import cv2
import json
import random
import time
import matplotlib.pyplot as plt
from streamlit_echarts import JsCode
from streamlit_echarts import st_echarts
import numpy as np
import pandas as pd
import pydub
import datetime
import streamlit as st
import altair as alt
from aiortc.contrib.media import MediaPlayer

from streamlit_webrtc import (
    AudioProcessorBase,
    ClientSettings,
    VideoProcessorBase,
    WebRtcMode,
    webrtc_streamer,
)

HERE = Path(__file__).parent

logger = logging.getLogger(__name__)
st.set_page_config(page_title="Smart Kitchen", page_icon='./images/company_logo.png',layout="wide")


# This code is based on https://github.com/streamlit/demo-self-driving/blob/230245391f2dda0cb464008195a470751c01770b/streamlit_app.py#L48  # noqa: E501
def download_file(url, download_to: Path, expected_size=None):
    # Don't download the file twice.
    # (If possible, verify the download using the file length.)
    if download_to.exists():
        if expected_size:
            if download_to.stat().st_size == expected_size:
                return
        else:
            st.info(f"{url} is already downloaded.")
            if not st.button("Download again?"):
                return

    download_to.parent.mkdir(parents=True, exist_ok=True)

    # These are handles to two visual elements to animate.
    weights_warning, progress_bar = None, None
    try:
        weights_warning = st.warning("Downloading %s..." % url)
        progress_bar = st.progress(0)
        with open(download_to, "wb") as output_file:
            with urllib.request.urlopen(url) as response:
                length = int(response.info()["Content-Length"])
                counter = 0.0
                MEGABYTES = 2.0 ** 20.0
                while True:
                    data = response.read(8192)
                    if not data:
                        break
                    counter += len(data)
                    output_file.write(data)

                    # We perform animation by overwriting the elements.
                    weights_warning.warning(
                        "Downloading %s... (%6.2f/%6.2f MB)"
                        % (url, counter / MEGABYTES, length / MEGABYTES)
                    )
                    progress_bar.progress(min(counter / length, 1.0))
    # Finally, we remove these visual elements by calling .empty().
    finally:
        if weights_warning is not None:
            weights_warning.empty()
        if progress_bar is not None:
            progress_bar.empty()


WEBRTC_CLIENT_SETTINGS = ClientSettings(
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={
        "video": True,
        "audio": True,
    },
)


def main():

    st.markdown(""" <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style> """, unsafe_allow_html=True)

    import os
    import base64

    @st.cache(allow_output_mutation=True)
    def get_base64_of_bin_file(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()

    @st.cache(allow_output_mutation=True)
    def get_img_with_href(local_img_path, target_url):
        img_format = os.path.splitext(local_img_path)[-1].replace('.', '')
        bin_str = get_base64_of_bin_file(local_img_path)
        html_code = f'''
            <a href="{target_url}">
                <img src="data:image/{img_format};base64,{bin_str}" width="50" />
            </a>'''
        return html_code

    #col3, col4 = st.sidebar.beta_columns((1,4))
    logo_link = get_img_with_href('./images/company_logo.png', 'https://www.wavelet-ai.com')
    #col3.markdown(logo_link, unsafe_allow_html=True)
    #col4.header("Wavelet Smart Kitchen ")

    st.sidebar.markdown(logo_link, unsafe_allow_html=True)
    st.sidebar.title("Wavelet Smart Kitchen ")

    st.sidebar.markdown("")
    col1, col2 = st.sidebar.beta_columns((1,3))
    col1.image("https://image.flaticon.com/icons/png/512/149/149071.png",width = 60)
    col2.markdown('#### Andrew Lee \n #### andrew@wavelet-ai.com' )
    st.sidebar.markdown("")

    st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous">', unsafe_allow_html=True)

    # dashboard_page = "Dashboard"
    # statistics_page = "Statistics"
    # algorithm_page = "Algorithm"
    # knowledge_base_page = "Knowledge Base"
    # staff_page = "staff"
    # #
    # app_mode = st.sidebar.selectbox(
    #     "",
    #     [
    #         dashboard_page,
    #         statistics_page,
    #         algorithm_page,
    #         knowledge_base_page,
    #         staff_page,
    #     ],
    # )

    # app_mode = 'dashboard_page'

    # first_time_loading = True

    st.markdown(""" <style> div.stButton > button:first-child {width:90%; align:center; border-radius:5px 5px 5px 5px; } </style>""", unsafe_allow_html=True)

    import SessionState
    session_state = SessionState.get(app_mode='')

    button_dashboard = st.sidebar.button('Dashboard')
    button_statistics = st.sidebar.button('Statistics')
    button_algorithm = st.sidebar.button('WaveKitchen')
    button_knowledge = st.sidebar.button('Knowledge Base')
    button_staff = st.sidebar.button('Staff Management')

    if button_dashboard:
        session_state.app_mode = 'Dashboard'
    if button_statistics:
        session_state.app_mode = 'Statistics'
    if button_algorithm:
        session_state.app_mode = 'Algorithm'
    if button_knowledge:
        session_state.app_mode = 'Knowledge Base'
    if button_staff:
        session_state.app_mode = 'Staff Management'

    app_mode = session_state.app_mode

    if app_mode == '':
        app_dashboard()
    elif app_mode == 'Dashboard':
        app_dashboard()
    elif app_mode == 'Statistics':
        app_statistics()
    elif app_mode == 'Algorithm':
        app_algorithm()
    elif app_mode == 'Knowledge Base':
        app_knowledge_base()
    elif app_mode == 'Staff Management':
        app_staff()




    # if st.sidebar.button('Dashboard')):
    #     first_time_loading = False
    #     app_dashboard()
    #
    # if st.sidebar.button('Statistics'):
    #     first_time_loading = False
    #     app_statistics()
    #
    # if st.sidebar.button('Algorithm'):
    #     first_time_loading = False
    #     app_algorithm()
    #
    # if st.sidebar.button('Knowledge Base'):
    #     first_time_loading = False
    #     app_knowledge_base()
    #
    # if st.sidebar.button('Staff Management'):
    #     first_time_loading = False
    #     app_staff()

    # if (first_time_loading):
    #     app_dashboard()

    # if app_mode == dashboard_page:
    #     app_dashboard()
    # elif app_mode == statistics_page:
    #     app_statistics()
    # elif app_mode == algorithm_page:
    #     app_algorithm()
    # elif app_mode == knowledge_base_page:
    #     app_knowledge_base()
    # elif app_mode == staff_page:
    #     app_staff()

    # logger.debug("=== Alive threads ===")
    # for thread in threading.enumerate():
    #     if thread.is_alive():
    #         logger.debug(f"  {thread.name} ({thread.ident})")

def app_loopback():
    """ Simple video loopback """
    webrtc_streamer(
        key="loopback",
        mode=WebRtcMode.SENDRECV,
        client_settings=WEBRTC_CLIENT_SETTINGS,
        video_processor_factory=None,  # NoOp
    )

def app_dashboard():

    st.header('Dashboard')

    row1_1, row1_2, row1_3, row1_4 = st.beta_columns((2,2,2,2))
    row1_1.markdown(f'''<div class="card text-white bg-success mb-3">
      <div class="card-body">
        <h6 class="card-title" style="color:white">Mask wearing rate</h6>
        <p class="card-text">90%</p>
      </div>
    </div>''', unsafe_allow_html=True)

    row1_2.markdown(f'''<div class="card text-white bg-success mb-3">
      <div class="card-body">
        <h6 class="card-title" style="color:white">Uniform wearing rate</h6>
        <p class="card-text">90%</p>
      </div>
    </div>''', unsafe_allow_html=True)

    row1_3.markdown(f'''<div class="card text-white bg-danger mb-3">
      <div class="card-body">
        <h6 class="card-title" style="color:white">Rodent risk</h6>
        <p class="card-text">High</p>
      </div>
    </div>''', unsafe_allow_html=True)

    row1_4.markdown(f'''<div class="card text-white bg-success mb-3">
      <div class="card-body">
        <h6 class="card-title" style="color:white">Risk of gas leakage</h6>
        <p class="card-text">Low</p>
      </div>
    </div>''', unsafe_allow_html=True)


    row2_1, row2_2 = st.beta_columns((6,2))

    with row2_1:
        st.write("**Kitchen Status Radar**")
        kitchen_status_radar()
    with row2_2:
        st.write("**Message**")
        st.markdown(f'''<div class="card text-white bg-info mb-3">
          <div class="card-body">
            <h6 class="card-title" style="color:white">06/05 16:30</h6>
            <h6 class="card-title" style="color:white">staff ID: 052</h6>
            <p class="card-text">Did not wear mask</p>
          </div>
        </div>''', unsafe_allow_html=True)

        st.markdown(f'''<div class="card text-white bg-info mb-3">
          <div class="card-body">
            <h6 class="card-title" style="color:white">06/10 07:23</h6>
            <h6 class="card-title" style="color:white">staff ID: 530</h6>
            <p class="card-text">Did not wear chef hat</p>
          </div>
        </div>''', unsafe_allow_html=True)

        st.markdown(f'''<div class="card text-white bg-warning mb-3">
          <div class="card-body">
            <h6 class="card-title" style="color:white">06/12 11:15</h6>
            <p class="card-text">High risk of gas leakage</p>
          </div>
        </div>''', unsafe_allow_html=True)



    row3_1, row3_2 = st.beta_columns((4,4))

    with row3_1:
        st.write("**Staff Performance Scoring**")
        staff_scoring_bar_chart()

    with row3_2:
        st.write("**Canteen Capacity**")
        capacity_gauge()


def kitchen_status_radar():
    option = {
        #"title": {"text": "基础雷达图"},
        "radar": {
            "indicator": [
                {"name": "Manpower arrangement", "max": 6500},
                {"name": "Operation Efficiency", "max": 16000},
                {"name": "Food quality", "max": 30000},
                {"name": "Cleaness", "max": 38000},
                {"name": "Client Satisfaction", "max": 52000},
                {"name": "Safety awareness", "max": 25000},
            ]
        },
        "series": [
            {
                "name": "Budget vs spending",
                "type": "radar",
                "data": [
                    {
                        "value": [4200, 3000, 20000, 35000, 50000, 18000],
                        "name": "Last week",
                    },
                    {
                        "value": [5000, 14000, 28000, 26000, 42000, 21000],
                        "name": "This week",
                    },
                ],
            }
        ],
        "legend": {"data": ["Last week", "This week"]},
    }
    st_echarts(option, height="400px")


def capacity_gauge():
    option = {
        "series": [
            {
                "type": "gauge",
                "startAngle": 90,
                "endAngle": -270,
                "pointer": {"show": False},
                "progress": {
                    "show": True,
                    "overlap": False,
                    "roundCap": True,
                    "clip": False,
                    "itemStyle": {"borderWidth": 0, "borderColor": "#464646"},
                },
                "axisLine": {"lineStyle": {"width": 40}},
                "splitLine": {"show": False, "distance": 0, "length": 10},
                "axisTick": {"show": False},
                "axisLabel": {"show": False, "distance": 50},
                "data": [
                    {
                        "value": random.randint(1, 99),
                        "name": "Hall 1",
                        "title": {"offsetCenter": ["0%", "-35%"]},
                        "detail": {"offsetCenter": ["0%", "-20%"]},
                    },
                    {
                        "value": random.randint(1, 99),
                        "name": "Hall 2",
                        "title": {"offsetCenter": ["0%", "0%"]},
                        "detail": {"offsetCenter": ["0%", "15%"]},
                    },
                    {
                        "value": random.randint(1, 99),
                        "name": "Hall 3",
                        "title": {"offsetCenter": ["0%", "30%"]},
                        "detail": {"offsetCenter": ["0%", "45%"]},
                    },
                ],
                "title": {"fontSize": 14},
                "detail": {
                    "width": 50,
                    "height": 14,
                    "fontSize": 14,
                    "color": "auto",
                    "borderColor": "auto",
                    "borderRadius": 20,
                    "borderWidth": 1,
                    "formatter": "{value}%",
                },
            }
        ]
    }

    st_echarts(option, height="400px", key="echarts")


def staff_scoring_bar_chart():
    options = {
        "xAxis": {
            "type": "category",
            "data": ["Andy","Chris","Dan","Frank","Tim","Zoltan","Roland"],
        },
        "yAxis": {"type": "value"},
        "series": [
            {
                "data": [
                    120,
                    {"value": 200, "itemStyle": {"color": "#a90000"}},
                    150,
                    80,
                    70,
                    110,
                    130,
                ],
                "type": "bar",
            }
        ],
    }
    st_echarts(
        options=options, height="400px",
    )


def staff_scoring_line_chart():
    with open("./data_input/life-expectancy-table.json") as f:
        raw_data = json.load(f)
    Staffs = [
        "Andy",
        "Chris",
        "Dan",
        "Frank",
        "Tim",
        "Zoltan",
        "Roland",
        "Zoe",
    ]

    datasetWithFilters = [
        {
            "id": f"dataset_{Staff}",
            "fromDatasetId": "dataset_raw",
            "transform": {
                "type": "filter",
                "config": {
                    "and": [
                        {"dimension": "Year", "gte": 1950},
                        {"dimension": "Staff", "=": Staff},
                    ]
                },
            },
        }
        for Staff in Staffs
    ]

    seriesList = [
        {
            "type": "line",
            "datasetId": f"dataset_{Staff}",
            "showSymbol": False,
            "name": Staff,
            "endLabel": {
                "show": True,
                "formatter": JsCode(
                    "function (params) { return params.value[3]}"
                ).js_code,
            },
            "labelLayout": {"moveOverlap": "shiftY"},
            "emphasis": {"focus": "series"},
            "encode": {
                "x": "Year",
                "y": "Income",
                "label": ["Staff", "Income"],
                "itemName": "Year",
                "tooltip": ["Income"],
            },
        }
        for Staff in Staffs
    ]

    option = {
        "animationDuration": 10000,
        "dataset": [{"id": "dataset_raw", "source": raw_data}] + datasetWithFilters,
        "tooltip": {"order": "valueDesc", "trigger": "axis"},
        "xAxis": {"type": "category", "nameLocation": "middle"},
        "yAxis": {"name":"score"},
        "grid": {"right": 40},
        "series": seriesList,
    }
    st_echarts(options=option, height="500px")


def crowd_monitoring_heat_map():
    hours = [
        "12a",
        "1a",
        "2a",
        "3a",
        "4a",
        "5a",
        "6a",
        "7a",
        "8a",
        "9a",
        "10a",
        "11a",
        "12p",
        "1p",
        "2p",
        "3p",
        "4p",
        "5p",
        "6p",
        "7p",
        "8p",
        "9p",
        "10p",
        "11p",
    ]
    days = [
        "Saturday",
        "Friday",
        "Thursday",
        "Wednesday",
        "Tuesday",
        "Monday",
        "Sunday",
    ]

    data = [
        [0, 0, 5],
        [0, 1, 1],
        [0, 2, 0],
        [0, 3, 0],
        [0, 4, 0],
        [0, 5, 0],
        [0, 6, 0],
        [0, 7, 0],
        [0, 8, 0],
        [0, 9, 0],
        [0, 10, 0],
        [0, 11, 2],
        [0, 12, 4],
        [0, 13, 1],
        [0, 14, 1],
        [0, 15, 3],
        [0, 16, 4],
        [0, 17, 6],
        [0, 18, 4],
        [0, 19, 4],
        [0, 20, 3],
        [0, 21, 3],
        [0, 22, 2],
        [0, 23, 5],
        [1, 0, 7],
        [1, 1, 0],
        [1, 2, 0],
        [1, 3, 0],
        [1, 4, 0],
        [1, 5, 0],
        [1, 6, 0],
        [1, 7, 0],
        [1, 8, 0],
        [1, 9, 0],
        [1, 10, 5],
        [1, 11, 2],
        [1, 12, 2],
        [1, 13, 6],
        [1, 14, 9],
        [1, 15, 11],
        [1, 16, 6],
        [1, 17, 7],
        [1, 18, 8],
        [1, 19, 12],
        [1, 20, 5],
        [1, 21, 5],
        [1, 22, 7],
        [1, 23, 2],
        [2, 0, 1],
        [2, 1, 1],
        [2, 2, 0],
        [2, 3, 0],
        [2, 4, 0],
        [2, 5, 0],
        [2, 6, 0],
        [2, 7, 0],
        [2, 8, 0],
        [2, 9, 0],
        [2, 10, 3],
        [2, 11, 2],
        [2, 12, 1],
        [2, 13, 9],
        [2, 14, 8],
        [2, 15, 10],
        [2, 16, 6],
        [2, 17, 5],
        [2, 18, 5],
        [2, 19, 5],
        [2, 20, 7],
        [2, 21, 4],
        [2, 22, 2],
        [2, 23, 4],
        [3, 0, 7],
        [3, 1, 3],
        [3, 2, 0],
        [3, 3, 0],
        [3, 4, 0],
        [3, 5, 0],
        [3, 6, 0],
        [3, 7, 0],
        [3, 8, 1],
        [3, 9, 0],
        [3, 10, 5],
        [3, 11, 4],
        [3, 12, 7],
        [3, 13, 14],
        [3, 14, 13],
        [3, 15, 12],
        [3, 16, 9],
        [3, 17, 5],
        [3, 18, 5],
        [3, 19, 10],
        [3, 20, 6],
        [3, 21, 4],
        [3, 22, 4],
        [3, 23, 1],
        [4, 0, 1],
        [4, 1, 3],
        [4, 2, 0],
        [4, 3, 0],
        [4, 4, 0],
        [4, 5, 1],
        [4, 6, 0],
        [4, 7, 0],
        [4, 8, 0],
        [4, 9, 2],
        [4, 10, 4],
        [4, 11, 4],
        [4, 12, 2],
        [4, 13, 4],
        [4, 14, 4],
        [4, 15, 14],
        [4, 16, 12],
        [4, 17, 1],
        [4, 18, 8],
        [4, 19, 5],
        [4, 20, 3],
        [4, 21, 7],
        [4, 22, 3],
        [4, 23, 0],
        [5, 0, 2],
        [5, 1, 1],
        [5, 2, 0],
        [5, 3, 3],
        [5, 4, 0],
        [5, 5, 0],
        [5, 6, 0],
        [5, 7, 0],
        [5, 8, 2],
        [5, 9, 0],
        [5, 10, 4],
        [5, 11, 1],
        [5, 12, 5],
        [5, 13, 10],
        [5, 14, 5],
        [5, 15, 7],
        [5, 16, 11],
        [5, 17, 6],
        [5, 18, 0],
        [5, 19, 5],
        [5, 20, 3],
        [5, 21, 4],
        [5, 22, 2],
        [5, 23, 0],
        [6, 0, 1],
        [6, 1, 0],
        [6, 2, 0],
        [6, 3, 0],
        [6, 4, 0],
        [6, 5, 0],
        [6, 6, 0],
        [6, 7, 0],
        [6, 8, 0],
        [6, 9, 0],
        [6, 10, 1],
        [6, 11, 0],
        [6, 12, 2],
        [6, 13, 1],
        [6, 14, 3],
        [6, 15, 4],
        [6, 16, 0],
        [6, 17, 0],
        [6, 18, 0],
        [6, 19, 0],
        [6, 20, 1],
        [6, 21, 2],
        [6, 22, 2],
        [6, 23, 6],
    ]
    data = [[d[1], d[0], d[2] if d[2] != 0 else "-"] for d in data]

    option = {
        "tooltip": {"position": "top"},
        "grid": {"height": "50%", "top": "10%"},
        "xAxis": {"type": "category", "data": hours, "splitArea": {"show": True}},
        "yAxis": {"type": "category", "data": days, "splitArea": {"show": True}},
        "visualMap": {
            "min": 0,
            "max": 10,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": "15%",
        },
        "series": [
            {
                "name": "Punch Card",
                "type": "heatmap",
                "data": data,
                "label": {"show": True},
                "emphasis": {
                    "itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0, 0, 0, 0.5)"}
                },
            }
        ],
    }
    st_echarts(option, height="500px")


def cost_ranking_pie_chart():
    option = {
        "legend": {"top": "bottom"},
        "toolbox": {
            "show": True,
            "feature": {
                "mark": {"show": True},
                #"dataView": {"show": True, "readOnly": False},
                #"restore": {"show": True},
                #"saveAsImage": {"show": True},
            },
        },
        "series": [
            {
                "type": "pie",
                "radius": [25, 100],
                "center": ["50%", "50%"],
                "roseType": "area",
                "itemStyle": {"borderRadius": 8},
                "data": [
                    {"value": 40, "name": "Human Resource"},
                    {"value": 38, "name": "Rental"},
                    {"value": 32, "name": "Cooking Ingredients"},
                    {"value": 30, "name": "Infrastructure"},
                    {"value": 28, "name": "Maintenance"},
                    {"value": 26, "name": "Others"},
                    #{"value": 22, "name": "cost 7"},
                    #{"value": 18, "name": "cost 8"},
                ],
            }
        ],
    }

    st_echarts(options=option, height="300px")


def object_detected_bar_chart():
    options = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {
            "data": ["Bottle", "Uniform", "Apron", "Mask", "Face"]
        },
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {
            "type": "category",
            "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        },
        "series": [
            {
                "name": "Bottle",
                "type": "bar",
                "stack": "total",
                "label": {"show": True},
                "emphasis": {"focus": "series"},
                "data": [320, 302, 301, 334, 390, 330, 320],
            },
            {
                "name": "Uniform",
                "type": "bar",
                "stack": "total",
                "label": {"show": True},
                "emphasis": {"focus": "series"},
                "data": [120, 132, 101, 134, 90, 230, 210],
            },
            {
                "name": "Apron",
                "type": "bar",
                "stack": "total",
                "label": {"show": True},
                "emphasis": {"focus": "series"},
                "data": [220, 182, 191, 234, 290, 330, 310],
            },
            {
                "name": "Mask",
                "type": "bar",
                "stack": "total",
                "label": {"show": True},
                "emphasis": {"focus": "series"},
                "data": [150, 212, 201, 154, 190, 330, 410],
            },
            {
                "name": "Face",
                "type": "bar",
                "stack": "total",
                "label": {"show": True},
                "emphasis": {"focus": "series"},
                "data": [820, 832, 901, 934, 1290, 1330, 1320],
            },
        ],
    }
    st_echarts(options=options, height="300px")

def app_statistics():
    st.header('Statistics')

    row1, row2 = st.beta_columns((2,2))

    with row1:
        st.write("**Cost Ranking**")
        cost_ranking_pie_chart()
    with row2:
        st.write("**Detected Objects**")
        object_detected_bar_chart()

    st.write("")
    st.write("**Hourly Staff Stay-in Monitoring**")
    crowd_monitoring_heat_map()


def app_video_filters():
    """ Video transforms with OpenCV """

    class OpenCVVideoProcessor(VideoProcessorBase):
        type: Literal["noop", "cartoon", "edges", "rotate"]

        def __init__(self) -> None:
            self.type = "noop"

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")

            if self.type == "noop":
                pass
            elif self.type == "cartoon":
                # prepare color
                img_color = cv2.pyrDown(cv2.pyrDown(img))
                for _ in range(6):
                    img_color = cv2.bilateralFilter(img_color, 9, 9, 7)
                img_color = cv2.pyrUp(cv2.pyrUp(img_color))

                # prepare edges
                img_edges = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                img_edges = cv2.adaptiveThreshold(
                    cv2.medianBlur(img_edges, 7),
                    255,
                    cv2.ADAPTIVE_THRESH_MEAN_C,
                    cv2.THRESH_BINARY,
                    9,
                    2,
                )
                img_edges = cv2.cvtColor(img_edges, cv2.COLOR_GRAY2RGB)

                # combine color and edges
                img = cv2.bitwise_and(img_color, img_edges)
            elif self.type == "edges":
                # perform edge detection
                img = cv2.cvtColor(cv2.Canny(img, 100, 200), cv2.COLOR_GRAY2BGR)
            elif self.type == "rotate":
                # rotate image
                rows, cols, _ = img.shape
                M = cv2.getRotationMatrix2D((cols / 2, rows / 2), frame.time * 45, 1)
                img = cv2.warpAffine(img, M, (cols, rows))

            return av.VideoFrame.from_ndarray(img, format="bgr24")

    webrtc_ctx = webrtc_streamer(
        key="opencv-filter",
        mode=WebRtcMode.SENDRECV,
        client_settings=WEBRTC_CLIENT_SETTINGS,
        video_processor_factory=OpenCVVideoProcessor,
        async_processing=True,
    )

    if webrtc_ctx.video_processor:
        webrtc_ctx.video_processor.type = st.radio(
            "Select transform type", ("noop", "cartoon", "edges", "rotate")
        )

    st.markdown(
        "This demo is based on "
        "https://github.com/aiortc/aiortc/blob/2362e6d1f0c730a0f8c387bbea76546775ad2fe8/examples/server/server.py#L34. "  # noqa: E501
        "Many thanks to the project."
    )


def app_audio_filter():
    DEFAULT_GAIN = 1.0

    class AudioProcessor(AudioProcessorBase):
        gain = DEFAULT_GAIN

        def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
            raw_samples = frame.to_ndarray()
            sound = pydub.AudioSegment(
                data=raw_samples.tobytes(),
                sample_width=frame.format.bytes,
                frame_rate=frame.sample_rate,
                channels=len(frame.layout.channels),
            )

            sound = sound.apply_gain(self.gain)

            # Ref: https://github.com/jiaaro/pydub/blob/master/API.markdown#audiosegmentget_array_of_samples  # noqa
            channel_sounds = sound.split_to_mono()
            channel_samples = [s.get_array_of_samples() for s in channel_sounds]
            new_samples: np.ndarray = np.array(channel_samples).T
            new_samples = new_samples.reshape(raw_samples.shape)

            new_frame = av.AudioFrame.from_ndarray(
                new_samples, layout=frame.layout.name
            )
            new_frame.sample_rate = frame.sample_rate
            return new_frame

    webrtc_ctx = webrtc_streamer(
        key="audio-filter",
        mode=WebRtcMode.SENDRECV,
        client_settings=WEBRTC_CLIENT_SETTINGS,
        audio_processor_factory=AudioProcessor,
        async_processing=True,
    )

    if webrtc_ctx.audio_processor:
        webrtc_ctx.audio_processor.gain = st.slider(
            "Gain", -10.0, +20.0, DEFAULT_GAIN, 0.05
        )


def app_delayed_echo():
    DEFAULT_DELAY = 1.0

    class VideoProcessor(VideoProcessorBase):
        delay = DEFAULT_DELAY

        async def recv_queued(self, frames: List[av.VideoFrame]) -> List[av.VideoFrame]:
            logger.debug("Delay:", self.delay)
            await asyncio.sleep(self.delay)
            return frames

    class AudioProcessor(AudioProcessorBase):
        delay = DEFAULT_DELAY

        async def recv_queued(self, frames: List[av.AudioFrame]) -> List[av.AudioFrame]:
            await asyncio.sleep(self.delay)
            return frames

    webrtc_ctx = webrtc_streamer(
        key="delay",
        mode=WebRtcMode.SENDRECV,
        client_settings=WEBRTC_CLIENT_SETTINGS,
        video_processor_factory=VideoProcessor,
        audio_processor_factory=AudioProcessor,
        async_processing=True,
    )

    if webrtc_ctx.video_processor and webrtc_ctx.audio_processor:
        delay = st.slider("Delay", 0.0, 5.0, DEFAULT_DELAY, 0.05)
        webrtc_ctx.video_processor.delay = delay
        webrtc_ctx.audio_processor.delay = delay


def app_algorithm():
    st.header('WaveKitchen')

    # """Object detection demo with MobileNet SSD.
    # This model and code are based on
    # https://github.com/robmarkcole/object-detection-app
    # """
    #MODEL_URL = "https://github.com/robmarkcole/object-detection-app/raw/master/model/MobileNetSSD_deploy.caffemodel"  # noqa: E501
    MODEL_LOCAL_PATH = HERE / "./models/MobileNetSSD_deploy.caffemodel"
    #PROTOTXT_URL = "https://github.com/robmarkcole/object-detection-app/raw/master/model/MobileNetSSD_deploy.prototxt.txt"  # noqa: E501
    PROTOTXT_LOCAL_PATH = HERE / "./models/MobileNetSSD_deploy.prototxt.txt"

    CLASSES = [
        "background",
        "person",
        "bicycles",
        "car",
        "motorcycle",
        "airplane",
        "bus",
        "train",
        "truck",
        "boat",
        "traffic light",
        "fire hydrant",
        "stop sign",
        "parking meter",
        "bench",
        "bird",
        "cat",
        "dog",
        "horse",
        "sheep",
        "cow",
        "elephant",
        "bear",
        "zebra",
        "giraffe",
        "backpack",
        "umbrella",
        "handbag",
        "tie",
        "suitcase",
        "frisbee",
        "skis",
        "snowboard",
        "sports ball",
        "kite",
        "baseball bat",
        "baseball glove",
        "skateboard",
        "surfboard",
        "tennis racket",
        "bottle",
        "wine glass",
        "cup",
        "fork",
        "knife",
        "spoon",
        "bowl",
        "banana",
        "apple",
        "sandwich",
        "orange",
        "broccoli",
        "carrot",
        "hot dog",
        "pizza",
        "donut",
        "cake",
        "chair",
        "couch",
        "potted plant",
        "bed",
        "dining table",
        "toilet",
        "tv",
        "laptop",
        "mouse",
        "remote",
        "keyboard",
        "cell phone",
        "microwave",
        "oven",
        "toaster",
        "sink",
        "refrigerator",
        "book",
        "clock",
        "vase",
        "scissors",
        "teddy bear",
        "hair drier",
        "toothbrush"
    ]
    COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

    #download_file(MODEL_URL, MODEL_LOCAL_PATH, expected_size=23147564)
    #download_file(PROTOTXT_URL, PROTOTXT_LOCAL_PATH, expected_size=29353)

    DEFAULT_CONFIDENCE_THRESHOLD = 0.1 # default 0.5

    class Detection(NamedTuple):
        name: str
        prob: float

    class MobileNetSSDVideoProcessor(VideoProcessorBase):
        confidence_threshold: float
        result_queue: "queue.Queue[List[Detection]]"

        def __init__(self) -> None:
            self._net = cv2.dnn.readNetFromCaffe(
                str(PROTOTXT_LOCAL_PATH), str(MODEL_LOCAL_PATH)
            )
            self.confidence_threshold = DEFAULT_CONFIDENCE_THRESHOLD
            self.result_queue = queue.Queue()

        def _annotate_image(self, image, detections):
            # loop over the detections
            (h, w) = image.shape[:2]
            result: List[Detection] = []
            for i in np.arange(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]

                if confidence > self.confidence_threshold:
                    # extract the index of the class label from the `detections`,
                    # then compute the (x, y)-coordinates of the bounding box for
                    # the object
                    idx = int(detections[0, 0, i, 1])
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")

                    name = CLASSES[idx]
                    result.append(Detection(name=name, prob=float(confidence)))

                    # display the prediction
                    label = f"{name}: {round(confidence * 100, 2)}%"
                    cv2.rectangle(image, (startX, startY), (endX, endY), COLORS[idx], 2)
                    y = startY - 15 if startY - 15 > 15 else startY + 15
                    cv2.putText(
                        image,
                        label,
                        (startX, y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        COLORS[idx],
                        2,
                    )
            return image, result

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            image = frame.to_ndarray(format="bgr24")
            blob = cv2.dnn.blobFromImage(
                cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5
            )
            self._net.setInput(blob)
            detections = self._net.forward()
            annotated_image, result = self._annotate_image(image, detections)

            # NOTE: This `recv` method is called in another thread,
            # so it must be thread-safe.
            self.result_queue.put(result)

            return av.VideoFrame.from_ndarray(annotated_image, format="bgr24")

    webrtc_ctx = webrtc_streamer(
        key="object-detection",
        mode=WebRtcMode.SENDRECV,
        client_settings=WEBRTC_CLIENT_SETTINGS,
        video_processor_factory=MobileNetSSDVideoProcessor,
        async_processing=True,
    )

    confidence_threshold = st.slider(
        "Confidence threshold", 0.0, 1.0, DEFAULT_CONFIDENCE_THRESHOLD, 0.05
    )
    if webrtc_ctx.video_processor:
        webrtc_ctx.video_processor.confidence_threshold = confidence_threshold

    if st.checkbox("Show the detected labels", value=True):
        if webrtc_ctx.state.playing:
            labels_placeholder = st.empty()
            # NOTE: The video transformation with object detection and
            # this loop displaying the result labels are running
            # in different threads asynchronously.
            # Then the rendered video frames and the labels displayed here
            # are not strictly synchronized.
            while True:
                if webrtc_ctx.video_processor:
                    try:
                        result = webrtc_ctx.video_processor.result_queue.get(
                            timeout=1.0
                        )
                    except queue.Empty:
                        result = None
                    labels_placeholder.table(result)
                else:
                    break

    # st.markdown(
    #     "This demo uses a model and code from "
    #     "https://github.com/robmarkcole/object-detection-app. "
    #     "Many thanks to the project."
    # )

    left_column, right_column = st.beta_columns((3,2))
    # You can use a column just like st.sidebar:
    data = {'Name':['SDC-001', 'SDC-002', 'SDC-003','SDC-004'],
        'Position':['Kichen Center', 'Kichen Corner Left', 'Kichen Corner Right','Kichen Corner Up'],
        'Status':['Running', 'Running', 'Running',"Closed"]}

    with left_column:
        st.write("**Device List**")
        import pandas as pd
        df = pd.DataFrame(data)
        st.table(df)

    # Or even better, call Streamlit functions inside a "with" block:
    with right_column:
        st.write("**Settings**")
        # to make the radio buttons align horizontally
        st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
        display = st.radio(
            'Display',
            ("Single View", "Multiple View"))
        warning_message = st.radio(
            'Warning Message',
            ("On", "Off"))
        warning_sound = st.radio(
            'Warning Sound',
            ("On", "Off"))

def app_knowledge_base():
    st.header('Knowledge Base')

    st.write('**Frequently Asked Questions (FAQs)**')

    with st.beta_expander('System and Applicaitons'):
        st.write('**1. How to download the historical detected recordings?**')
        st.markdown('Access Algorithm Page -> Export Recordings Button -> Download to Local Folder')
        st.markdown('**2. How to send the alerts to SMS and Email?**')
        st.markdown('Please subsribe the add-on services packages in the admin panel.')
        st.markdown('**3. Where to find the related AI product offerings?**')
        st.markdown('Please access the link: [https://www.wavelet-ai.com](https://www.wavelet-ai.com)')

    with st.beta_expander('Kitchen Cleaness Standards'):
        st.markdown('**1. Cleaness Requirements:**')
        from PIL import Image
        image = Image.open("./images/cleaness.png")
        st.image(image)

    with st.beta_expander('Kitchen Safety Guidelines'):
        st.markdown('**1. Six Kitchen Safety Guidelines:**')
        st.markdown('(1) Always wear shoes.')
        st.markdown('(2) Wear safe clothing.')
        st.markdown('(3) Don’t forget to wash your hands.')
        st.markdown('(4) Use different chopping boards for raw meat, fruits, and vegetables.')
        st.markdown('(5) Handle hot dishes with care')
        st.markdown('(6) Have a fire extinguisher and know how to use it.')


    with st.beta_expander('Emergency Handbook'):
        st.markdown('**1. Emergency Handbook**')
        st.markdown('(1) Smother the flames of a grease fire with a dish towel or a pot lid, then remove the pan from the heat source.')
        st.markdown('(2) Turn off the oven immediately in the event of an oven fire. Keep the oven door closed — the lack of oxygen will suffocate the fire.')
        st.markdown('(3) Treat bruises from a fall by applying a cold pack or a bag of ice wrapped in a towel. Never apply ice cubes directly to your skin.')
        st.markdown('(4) Apply warm water or the cut surface of a cold, raw potato to soothe pain from a burn and prevent burn blisters from forming.')
        st.markdown('(5) For minor burns, apply a little honey. Research shows that this will help the wounds heal faster.')
        st.markdown('(6) Cover open burn injuries with a sterile, non-stick bandage and cool with an icepack. For severe burns, go to the ER right away.')


def app_staff():
    st.header("Staff Management")

    d = st.date_input(
        "Select a date:",
        datetime.date(2021, 6, 18))

    st.write('**Staff Performance Scoring**')
    staff_scoring_line_chart()


def app_streaming():
    """ Media streamings """
    MEDIAFILES = {
        "big_buck_bunny_720p_2mb.mp4 (local)": {
            "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_2mb.mp4",  # noqa: E501
            "local_file_path": HERE / "data/big_buck_bunny_720p_2mb.mp4",
            "type": "video",
        },
        "big_buck_bunny_720p_10mb.mp4 (local)": {
            "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_10mb.mp4",  # noqa: E501
            "local_file_path": HERE / "data/big_buck_bunny_720p_10mb.mp4",
            "type": "video",
        },
        "file_example_MP3_700KB.mp3 (local)": {
            "url": "https://file-examples-com.github.io/uploads/2017/11/file_example_MP3_700KB.mp3",  # noqa: E501
            "local_file_path": HERE / "data/file_example_MP3_700KB.mp3",
            "type": "audio",
        },
        "file_example_MP3_5MG.mp3 (local)": {
            "url": "https://file-examples-com.github.io/uploads/2017/11/file_example_MP3_5MG.mp3",  # noqa: E501
            "local_file_path": HERE / "data/file_example_MP3_5MG.mp3",
            "type": "audio",
        },
        "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov": {
            "url": "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov",
            "type": "video",
        },
    }
    media_file_label = st.radio(
        "Select a media source to stream", tuple(MEDIAFILES.keys())
    )
    media_file_info = MEDIAFILES[media_file_label]
    if "local_file_path" in media_file_info:
        download_file(media_file_info["url"], media_file_info["local_file_path"])

    def create_player():
        if "local_file_path" in media_file_info:
            return MediaPlayer(str(media_file_info["local_file_path"]))
        else:
            return MediaPlayer(media_file_info["url"])

        # NOTE: To stream the video from webcam, use the code below.
        # return MediaPlayer(
        #     "1:none",
        #     format="avfoundation",
        #     options={"framerate": "30", "video_size": "1280x720"},
        # )

    class OpenCVVideoProcessor(VideoProcessorBase):
        type: Literal["noop", "cartoon", "edges", "rotate"]

        def __init__(self) -> None:
            self.type = "noop"

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")

            if self.type == "noop":
                pass
            elif self.type == "cartoon":
                # prepare color
                img_color = cv2.pyrDown(cv2.pyrDown(img))
                for _ in range(6):
                    img_color = cv2.bilateralFilter(img_color, 9, 9, 7)
                img_color = cv2.pyrUp(cv2.pyrUp(img_color))

                # prepare edges
                img_edges = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                img_edges = cv2.adaptiveThreshold(
                    cv2.medianBlur(img_edges, 7),
                    255,
                    cv2.ADAPTIVE_THRESH_MEAN_C,
                    cv2.THRESH_BINARY,
                    9,
                    2,
                )
                img_edges = cv2.cvtColor(img_edges, cv2.COLOR_GRAY2RGB)

                # combine color and edges
                img = cv2.bitwise_and(img_color, img_edges)
            elif self.type == "edges":
                # perform edge detection
                img = cv2.cvtColor(cv2.Canny(img, 100, 200), cv2.COLOR_GRAY2BGR)
            elif self.type == "rotate":
                # rotate image
                rows, cols, _ = img.shape
                M = cv2.getRotationMatrix2D((cols / 2, rows / 2), frame.time * 45, 1)
                img = cv2.warpAffine(img, M, (cols, rows))

            return av.VideoFrame.from_ndarray(img, format="bgr24")

    WEBRTC_CLIENT_SETTINGS.update(
        {
            "media_stream_constraints": {
                "video": media_file_info["type"] == "video",
                "audio": media_file_info["type"] == "audio",
            }
        }
    )

    webrtc_ctx = webrtc_streamer(
        key=f"media-streaming-{media_file_label}",
        mode=WebRtcMode.RECVONLY,
        client_settings=WEBRTC_CLIENT_SETTINGS,
        player_factory=create_player,
        video_processor_factory=OpenCVVideoProcessor,
    )

    if webrtc_ctx.video_processor:
        webrtc_ctx.video_processor.type = st.radio(
            "Select transform type", ("noop", "cartoon", "edges", "rotate")
        )

    st.markdown(
        "The video filter in this demo is based on "
        "https://github.com/aiortc/aiortc/blob/2362e6d1f0c730a0f8c387bbea76546775ad2fe8/examples/server/server.py#L34. "  # noqa: E501
        "Many thanks to the project."
    )


def app_sendonly_video():
    """A sample to use WebRTC in sendonly mode to transfer frames
    from the browser to the server and to render frames via `st.image`."""
    webrtc_ctx = webrtc_streamer(
        key="video-sendonly",
        mode=WebRtcMode.SENDONLY,
        client_settings=WEBRTC_CLIENT_SETTINGS,
    )

    image_place = st.empty()

    while True:
        if webrtc_ctx.video_receiver:
            try:
                video_frame = webrtc_ctx.video_receiver.get_frame(timeout=1)
            except queue.Empty:
                logger.warning("Queue is empty. Abort.")
                break

            img_rgb = video_frame.to_ndarray(format="rgb24")
            image_place.image(img_rgb)
        else:
            logger.warning("AudioReciver is not set. Abort.")
            break


def app_sendonly_audio():
    """A sample to use WebRTC in sendonly mode to transfer audio frames
    from the browser to the server and visualize them with matplotlib
    and `st.pyplot`."""
    webrtc_ctx = webrtc_streamer(
        key="sendonly-audio",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=256,
        client_settings=WEBRTC_CLIENT_SETTINGS,
    )

    fig_place = st.empty()

    fig, [ax_time, ax_freq] = plt.subplots(
        2, 1, gridspec_kw={"top": 1.5, "bottom": 0.2}
    )

    sound_window_len = 5000  # 5s
    sound_window_buffer = None
    while True:
        if webrtc_ctx.audio_receiver:
            try:
                audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
            except queue.Empty:
                logger.warning("Queue is empty. Abort.")
                break

            sound_chunk = pydub.AudioSegment.empty()
            for audio_frame in audio_frames:
                sound = pydub.AudioSegment(
                    data=audio_frame.to_ndarray().tobytes(),
                    sample_width=audio_frame.format.bytes,
                    frame_rate=audio_frame.sample_rate,
                    channels=len(audio_frame.layout.channels),
                )
                sound_chunk += sound

            if len(sound_chunk) > 0:
                if sound_window_buffer is None:
                    sound_window_buffer = pydub.AudioSegment.silent(
                        duration=sound_window_len
                    )

                sound_window_buffer += sound_chunk
                if len(sound_window_buffer) > sound_window_len:
                    sound_window_buffer = sound_window_buffer[-sound_window_len:]

            if sound_window_buffer:
                # Ref: https://own-search-and-study.xyz/2017/10/27/python%E3%82%92%E4%BD%BF%E3%81%A3%E3%81%A6%E9%9F%B3%E5%A3%B0%E3%83%87%E3%83%BC%E3%82%BF%E3%81%8B%E3%82%89%E3%82%B9%E3%83%9A%E3%82%AF%E3%83%88%E3%83%AD%E3%82%B0%E3%83%A9%E3%83%A0%E3%82%92%E4%BD%9C/  # noqa
                sound_window_buffer = sound_window_buffer.set_channels(
                    1
                )  # Stereo to mono
                sample = np.array(sound_window_buffer.get_array_of_samples())

                ax_time.cla()
                times = (np.arange(-len(sample), 0)) / sound_window_buffer.frame_rate
                ax_time.plot(times, sample)
                ax_time.set_xlabel("Time")
                ax_time.set_ylabel("Magnitude")

                spec = np.fft.fft(sample)
                freq = np.fft.fftfreq(sample.shape[0], 1.0 / sound_chunk.frame_rate)
                freq = freq[: int(freq.shape[0] / 2)]
                spec = spec[: int(spec.shape[0] / 2)]
                spec[0] = spec[0] / 2

                ax_freq.cla()
                ax_freq.plot(freq, np.abs(spec))
                ax_freq.set_xlabel("Frequency")
                ax_freq.set_yscale("log")
                ax_freq.set_ylabel("Magnitude")

                fig_place.pyplot(fig)
        else:
            logger.warning("AudioReciver is not set. Abort.")
            break


def app_media_constraints():
    """ A sample to configure MediaStreamConstraints object """
    frame_rate = 5
    WEBRTC_CLIENT_SETTINGS.update(
        ClientSettings(
            media_stream_constraints={
                "video": {"frameRate": {"ideal": frame_rate}},
            },
        )
    )
    webrtc_streamer(
        key="media-constraints",
        mode=WebRtcMode.SENDRECV,
        client_settings=WEBRTC_CLIENT_SETTINGS,
    )
    st.write(f"The frame rate is set as {frame_rate}")


if __name__ == "__main__":
    import os

    DEBUG = os.environ.get("DEBUG", "false").lower() not in ["false", "no", "0"]

    logging.basicConfig(
        format="[%(asctime)s] %(levelname)7s from %(name)s in %(pathname)s:%(lineno)d: "
        "%(message)s",
        force=True,
    )

    logger.setLevel(level=logging.DEBUG if DEBUG else logging.INFO)

    st_webrtc_logger = logging.getLogger("streamlit_webrtc")
    st_webrtc_logger.setLevel(logging.DEBUG)

    fsevents_logger = logging.getLogger("fsevents")
    fsevents_logger.setLevel(logging.WARNING)

    main()
