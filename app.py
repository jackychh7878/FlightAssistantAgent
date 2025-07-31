import os
import uuid
import time
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import MemorySaver
import base64

from src.sqlite_tools import search_flights
from src.sqlite_setup import download_db
from src.vector_store_retriever import download_rag_doc
from streamlit_mic_recorder import mic_recorder
from src.google_stt import google_stt_transcribe
from src.google_tts import google_tts_response
from src.graph_node import builder
from src.azure_asr import azure_stt_transcribe, azure_stt_transcribe_from_mic
from src.azure_tts import azure_tts_response
from src.fanolab_asr_tts import fanolab_stt_transcribe, fanolab_tts_response

from google.cloud import speech, texttospeech
from datetime import date, datetime, timedelta
from typing import Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
import markdown

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(page_title="航班助手", page_icon="🤖")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "agent" not in st.session_state:
    st.session_state.agent = None
if "config" not in st.session_state:
    st.session_state.config = None
if "client_info" not in st.session_state:
    st.session_state.client_info = None
if "flight_info" not in st.session_state:
    st.session_state.flight_info = None
if "google_stt_client" not in st.session_state:
    st.session_state.google_stt_client = None
if "google_tts_client" not in st.session_state:
    st.session_state.google_tts_client = None
if "voice_mode" not in st.session_state:
    st.session_state.voice_mode = False
if "voice_mode_auto_play" not in st.session_state:
    st.session_state.voice_mode_auto_play = False
if "voice_mode_auto_play_already" not in st.session_state:
    st.session_state.voice_mode_auto_play_already = True
if "last_message_stream_already" not in st.session_state:
    st.session_state.last_message_stream_already = True
if "event" not in st.session_state:
    st.session_state.event = None
if "is_human_in_loop" not in st.session_state:
    st.session_state.is_human_in_loop = False


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str

# Initialize agent and return it
def initialize_agent():
    memory = MemorySaver()
    graph = builder.compile(
        checkpointer=memory,
        # NEW: The graph will always halt before executing the "tools" node.
        # The user can approve or reject (or even alter the request) before
        # the assistant continues
        interrupt_before=["sensitive_tools"],
    )

    return graph

# Cache agent initialization
@st.cache_resource
def get_agent():
    # Download the RAG and SQLite database if haven't
    download_rag_doc()
    download_db()

    # Initialize the agent
    if st.session_state.agent is None:
        st.session_state.agent = initialize_agent()
    if st.session_state.google_stt_client is None:
        st.session_state.google_stt_client = speech.SpeechClient(client_options={"api_key": os.getenv("GOOGLE_API_KEY")})
    if st.session_state.google_tts_client is None:
        st.session_state.google_tts_client = texttospeech.TextToSpeechClient(client_options={"api_key": os.getenv("GOOGLE_API_KEY")})
    return st.session_state.agent, st.session_state.thread_id, st.session_state.google_stt_client, st.session_state.google_tts_client

def reload_chat():
    for message in st.session_state.messages[:-1]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    if st.session_state.messages is not None and len(st.session_state.messages) > 0:
        last_message = st.session_state.messages[-1]
        with st.chat_message(last_message["role"]):
            last_message_content = last_message["content"]
            if not st.session_state.last_message_stream_already:
                st.write_stream(stream_data(last_message_content))
                st.session_state.last_message_stream_already = True
            else:
                st.write(last_message_content)
            if st.session_state.voice_mode and last_message_content:
                # Azure TTS
                st.audio(azure_tts_response(text=last_message_content), format="audio/mpeg", autoplay=st.session_state.voice_mode_auto_play and (st.session_state.voice_mode_auto_play_already == False))
                # Google TTS
                # st.audio(google_tts_response(st.session_state.google_tts_client, last_message_content), format="audio/mpeg", autoplay=st.session_state.voice_mode_auto_play and (st.session_state.voice_mode_auto_play_already == False))
                # Fano TTS
                # st.audio(fanolab_tts_response(text=last_message_content), format="audio/mpeg",autoplay=st.session_state.voice_mode_auto_play and (st.session_state.voice_mode_auto_play_already == False))
                st.session_state.voice_mode_auto_play_already = True

def stream_data(response_data):
    for word in response_data.split(" "):
        yield word + " "
        time.sleep(0.02)

def reset_chat():
    # Clear messages
    st.session_state.messages = []
    # Generate new thread ID
    st.session_state.thread_id = str(uuid.uuid4())
    # Clear cache
    st.cache_resource.clear()
    # Reset agent
    get_agent()
    # Rerun the app to refresh the UI
    st.rerun()

graph, thread_id, google_stt_client, google_tts_client = get_agent()

# Set up the configuration
config = {
    "configurable": {
        "passenger_id": os.getenv('MY_ID'),
        "passenger_name": os.getenv('MY_NAME'),
        "passenger_email": os.getenv('MY_EMAIL'),
        "thread_id": st.session_state.thread_id,
    }
}
st.session_state.config = config

# Streamlit UI
st.title("航班助手 🤖")
st.write("搜尋航班、公司政策和其他資訊")

# Voice mode
st.session_state.voice_mode = st.toggle("Voice Mode", value=st.session_state.voice_mode)
if st.session_state.voice_mode:
    st.session_state.voice_mode_auto_play = st.toggle("Auto Play", value=st.session_state.voice_mode_auto_play)


#Reload chat history
reload_chat()

# Handle the human in the loop confirmation
@st.dialog("確認更改?")
def confirm_change(graph, config):
    event = st.session_state.event
    tool_name = event["messages"][-1].tool_calls[0]["name"]

    message = "是否確認進行更改?"
    if tool_name == 'update_ticket_to_new_flight':
        message = "是否確認進行更改機票?"
    if tool_name == 'cancel_ticket':
        message = "是否確認取消機票?"
    if tool_name in ['create_calendar_event', 'update_calendar_event']:
        message = "是否確認進行更改日程?"
    if tool_name in ['create_gmail_draft', 'send_gmail_message', 'search_gmail', 'get_gmail_message', 'get_gmail_thread']:
        message = "是否確認進行發送電郵?"
    st.write(message)

    if st.button("確認"):
        # Just continue
        result = graph.invoke(
            None,
            config,
        )
        last_message = result["messages"][-1]

        if last_message:
            full_response = last_message.content
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": "確認要求"})
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        st.session_state.is_human_in_loop = False
        st.session_state.event = None
        st.rerun()
    if st.button("拒絕"):
        # Satisfy the tool invocation by
        # providing instructions on the requested changes / change of mind
        result = graph.invoke(
            {
                "messages": [
                    ToolMessage(
                        tool_call_id=event["messages"][-1].tool_calls[0]["id"],
                        content=f"API call denied by user. Continue assisting, accounting for the user's input.",
                    )
                ]
            },
            config,
        )
        last_message = result["messages"][-1]
        if last_message:
            full_response = last_message.content
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": "拒絕要求"})
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.is_human_in_loop = False
        st.session_state.event = None
        st.rerun()

if st.session_state.is_human_in_loop:
    confirm_change(graph=graph, config=config)
    if st.button("確認要求"):
        confirm_change(graph=graph, config=config)

chat_input = st.chat_input("Hi, how can I help you today?")
# Chat input handling

def handle_chat_input(prompt_text):
    if prompt_text:
        with st.chat_message("user"):
            st.write(prompt_text)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.write("🤔 Thinking...")

        try:
            # Get response from langgraph agent
            inputs = {"messages": [("user", prompt_text)]}
            events = graph.stream(inputs, config, stream_mode="values")

            last_message = None
            for event in events:
                message = event["messages"][-1]
                last_message = event["messages"][-1]

                # tool_name = message.name
                if isinstance(message, tuple):
                    response_text = str(message)
                else:
                    response_text = message.pretty_print() if message.pretty_print() else ""

            # Human in the loop
            snapshot = graph.get_state(config)
            # print("Snapshot:", snapshot[-1])
            # print("Event:", event)
            if snapshot.next:
                st.session_state.is_human_in_loop = True
                st.session_state.event = event
            # Store response in chat history
            if last_message:
                full_response = last_message.content
                # message_placeholder.empty()

                # st.write_stream(stream_data(full_response))
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt_text})
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.last_message_stream_already = False
                st.session_state.voice_mode_auto_play_already = False

        except Exception as e:
            # message_placeholder.write(f"Sorry, I encountered an error: {str(e)}")
            st.error(f"Error: {str(e)}")



# Voice mode module
if st.session_state.voice_mode:

    # Google TTS
    # audio = mic_recorder(
    #     start_prompt="⏺️ Start (Google TTS)", stop_prompt="⏹️ End",
    #     just_once=True,
    #     use_container_width=False,
    #     format="wav",
    #     callback=None,
    #     args=(),
    #     kwargs={},
    #     key='recorder'
    # )
    # if audio:
    #     try:
    #         speech_to_text = google_stt_transcribe(st.session_state.google_stt_client, audio['bytes'])
    #         if speech_to_text:
    #             handle_chat_input(speech_to_text)
    #             st.rerun()
    #     except Exception as e:
    #         st.error(f"Error transcribing audio: {str(e)}")

    # Azure ASR
    mic_button = st.button("🎤 Click To Speak", key="use_mic_directly")
    if mic_button:
        with st.spinner("Listening... Please speak now and pause when finished"):
            try:
                speech_to_text = azure_stt_transcribe_from_mic()
                if speech_to_text and speech_to_text.startswith("Recognition failed") == False:
                    handle_chat_input(speech_to_text)
                    st.rerun()
            except Exception as e:
                st.error(f"Error with microphone transcription: {str(e)}")
    # Fano Lab
    # audio_fanolab = mic_recorder(
    #     start_prompt="⏺️ Start (Fano Lab TTS)", stop_prompt="⏹️ End",
    #     just_once=True,
    #     use_container_width=False,
    #     format="wav",
    #     callback=None,
    #     args=(),
    #     kwargs={},
    #     key='recorder'
    # )
    # if audio_fanolab:
    #     try:
    #         speech_to_text = fanolab_stt_transcribe(audio_bytes=audio_fanolab['bytes'])
    #         if speech_to_text:
    #             handle_chat_input(speech_to_text)
    #             st.rerun()
    #     except Exception as e:
    #         st.error(f"Error transcribing audio: {str(e)}")



if chat_input:
    handle_chat_input(chat_input)
    st.rerun()

# Sidebar information
def about_tab():
    st.write("Click RESET to rest the database and chat session")
    if st.button("RESET"):
        reset_chat()

    st.title("About")
    st.write("""
    我可以為你提供以下幫助：
    - 搜尋航班、公司政策和其他資訊以協助用戶查詢
    - 更改已預約機票
    """)

    st.subheader("Example Queries")
    example_queries = [
        "Hi there, what time is my flight?",
        "Am i allowed to update my flight to something sooner? I want to leave later today.",
        "Update my flight to sometime next week then",
        "The next available option is great",
    ]

    for query in example_queries:
        st.write(f"- {query}")
        # if st.button(query):
        #     handle_chat_input(query)
        #     st.rerun()

import sqlite3
import pandas as pd

SAVE_DIR = "./src/sqlite_db"
DB_NAME = "travel2.sqlite"
DOC_PATH = os.path.join(SAVE_DIR, DB_NAME)

def run_query(query):
    """Run a SQL query on the SQLite database and return the results as a DataFrame."""
    try:
        with sqlite3.connect(DOC_PATH) as conn:
            df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def fetch_airports():
    """Fetch airport data from the database."""
    conn = sqlite3.connect(DOC_PATH)
    query = "SELECT airport_code, airport_name, city FROM airports_data WHERE 1 = 1"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def search_flights(
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
        start_time: Optional[date | datetime] = None,
        end_time: Optional[date | datetime] = None,
        limit: int = 20,
):
    """Search for flights based on departure airport, arrival airport, and departure time range."""
    conn = sqlite3.connect(DOC_PATH)

    query = "SELECT * FROM flights WHERE 1 = 1"
    params = []

    if departure_airport:
        query += " AND departure_airport = ?"
        params.append(departure_airport)

    if arrival_airport:
        query += " AND arrival_airport = ?"
        params.append(arrival_airport)

    if start_time:
        query += " AND scheduled_departure >= ?"
        params.append(start_time)

    if end_time:
        query += " AND scheduled_departure <= ?"
        params.append(end_time)

    query += " LIMIT ?"
    params.append(limit)

    try:
        df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"An error occurred: {e}")
        df = pd.DataFrame()  # Return an empty DataFrame in case of error
    finally:
        conn.close()

    return df

def reload_pd():
    if st.session_state.client_info is not None:
        st.write("Passenger Info:")
        # st.dataframe(st.session_state.client_info)
        if not st.session_state.client_info.empty:
            # Transpose the DataFrame and reset the index
            transposed_df = st.session_state.client_info.transpose().reset_index()
            # Display the transposed DataFrame
            transposed_df.columns = ['Item', 'Value']
            st.dataframe(transposed_df, hide_index=True)

        else:
            st.write("No passenger information available.")
    if st.session_state.flight_info is not None:
        st.write("Flight Info:")
        st.dataframe(st.session_state.flight_info)

def sqlite_query_tab():
    st.title("Database Search")

    # Fetch airport data
    airports_df = fetch_airports()
    # airport_options = airports_df.apply(lambda row: f"{row['airport_code']} - {row['city']} ({row['airport_name']})",
    #                                     axis=1).tolist()
    airport_options = airports_df.apply(lambda row: f"{row['airport_code']}",
                                        axis=1).tolist()
    query = """
    SELECT 
        t.ticket_no, t.book_ref,
        f.flight_id, f.flight_no, f.departure_airport, f.arrival_airport, f.scheduled_departure, f.scheduled_arrival,
        bp.seat_no, tf.fare_conditions
    FROM 
        tickets t
        LEFT JOIN ticket_flights tf ON t.ticket_no = tf.ticket_no
        LEFT JOIN flights f ON tf.flight_id = f.flight_id
        LEFT JOIN boarding_passes bp ON bp.ticket_no = t.ticket_no AND bp.flight_id = f.flight_id
    WHERE 
        t.passenger_id = '8149 604011'
    """

    # Input fields
    departure_airport = st.selectbox("Departure Airport", [""] + airport_options)
    start_date = st.date_input("Start Date", datetime.now().date())
    arrival_airport = st.selectbox("Arrival Airport", [""] + airport_options)
    end_date = st.date_input("End Date", datetime.now().date() + timedelta(days=2))
    limit = st.slider("Number of results", min_value=1, max_value=50, value=10)

    if st.button("Flight Search"):
        client_info = run_query(query)
        if client_info is not None:
            st.session_state.client_info = client_info

        #Flight info
        departure_code = departure_airport.split(" - ")[0] if departure_airport else None
        arrival_code = arrival_airport.split(" - ")[0] if arrival_airport else None

        # Convert dates to datetime
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        flight_info = search_flights(
            departure_airport=departure_code,
            arrival_airport=arrival_code,
            start_time=start_datetime,
            end_time=end_datetime,
            limit=limit
        )
        if flight_info is not None:
            st.session_state.flight_info = flight_info

        st.rerun()

    #Display pd
    reload_pd()


def policy_tab():
    st.title("Swiss Airlines Policy")

    # Read the content of the markdown file
    with open("./src/rag_doc/swiss_faq.md", "r", encoding="utf-8") as file:
        md_content = file.read()

    # Convert markdown to HTML
    html_content = markdown.markdown(md_content)

    # Display the HTML content
    st.markdown(html_content, unsafe_allow_html=True)

with st.sidebar:
    tab1, tab2, tab3 = st.tabs(["About", "SQLite Query", "Policy"])

    with tab1:
        about_tab()

    with tab2:
        sqlite_query_tab()

    with tab3:
        policy_tab()
