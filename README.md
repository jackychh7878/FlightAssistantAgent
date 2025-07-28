# Airline Assistant Demo App

A conversational AI assistant that helps users manage their airline reservations through natural language and voice interactions. This demo application supports multiple speech recognition and text-to-speech providers for a comprehensive voice-enabled experience.

## Features

✈️ **Flight Management**
- Find flight information using natural language queries
- Look up airline ticket policies
- Update and modify flight bookings
- Check flight schedules and availability

🎤 **Voice Interaction**
- Voice-to-text input for hands-free operation
- Text-to-speech responses for accessibility
- Support for multiple languages

🔧 **Multiple AI Providers**
- **Speech Recognition (ASR)**: Google, Azure, Fanolab
- **Text-to-Speech (TTS)**: Google, Azure, Fanolab
- Easy switching between providers in the application

## Quick Start

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd AKAAgenticAI
pip install -r requirements.txt
```

### 2. Configuration

Before running the app, ensure you have API keys configured for your preferred ASR/TTS providers:

- **Google Cloud**: Set up Google Cloud credentials for Speech-to-Text and Text-to-Speech APIs
- **Azure Cognitive Services**: Configure Azure Speech Services API key
- **Fanolab**: Set up Fanolab API credentials

⚠️ **Important**: Make sure you have:
- Valid API keys for your chosen providers
- Sufficient credits/quota for your selected services
- Proper authentication configured

### 3. Run the Application

Start the Streamlit app:

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Usage

### Demo Reset
🔄 **Note**: Each time the application starts, it automatically resets the SQLite database to ensure a clean demo environment for new users.

### Voice Mode Configuration

In the app interface, you can switch between different ASR and TTS providers:

1. **Google Cloud**: High-quality speech recognition and synthesis
2. **Azure Cognitive Services**: Microsoft's speech services
3. **Fanolab**: Specialized speech processing services

Make sure your selected provider has:
- ✅ Valid API credentials configured
- ✅ Sufficient account credits
- ✅ Proper network connectivity

### Sample Questions

Here are some example queries you can try (in Cantonese):

```
我最新的航班係幾時?
(When is my latest flight?)

如果我想轉去下星期, 最快既期有邊一日?
(If I want to change to next week, what's the earliest available date?)

幫我改期
(Help me change the date)

如果改機票要幾多錢?
(How much does it cost to change the flight ticket?)
```

## Technical Architecture

### Core Components

- **Frontend**: Streamlit web interface
- **Backend**: Python-based conversational AI
- **Database**: SQLite for flight data storage
- **AI Integration**: LangChain for natural language processing
- **Voice Processing**: Multiple ASR/TTS provider integrations

### Supported File Structure

```
AKAAgenticAI/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── src/
│   ├── azure_asr.py           # Azure Speech Recognition
│   ├── azure_tts.py           # Azure Text-to-Speech
│   ├── google_stt.py          # Google Speech-to-Text
│   ├── google_tts.py          # Google Text-to-Speech
│   ├── fanolab_asr_tts.py     # Fanolab ASR/TTS
│   ├── sqlite_tools.py        # Database utilities
│   └── vector_store_retriever.py # RAG implementation
└── research/                   # Development notebooks
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify your API keys are correctly configured
   - Check if you have sufficient credits/quota
   - Ensure proper authentication setup

2. **Audio Issues**
   - Check microphone permissions in your browser
   - Verify audio input/output devices are working
   - Test with different browsers if needed

3. **Database Issues**
   - The SQLite database resets on each startup (by design)
   - Check file permissions in the `src/sqlite_db/` directory

### Provider-Specific Setup

#### Google Cloud
1. Create a Google Cloud project
2. Enable Speech-to-Text and Text-to-Speech APIs
3. Create service account credentials
4. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

#### Azure Cognitive Services
1. Create Azure Cognitive Services resource
2. Get your subscription key and region
3. Configure environment variables for Azure Speech SDK

#### Fanolab
1. Register for Fanolab services
2. Obtain API credentials
3. Configure authentication in the application

## Development

For development and customization:

1. **Adding New Providers**: Extend the ASR/TTS modules in the `src/` directory
2. **Database Schema**: Modify `sqlite_setup.py` for data structure changes
3. **UI Customization**: Update `app.py` for interface modifications
4. **Voice Processing**: Enhance audio handling in respective provider modules

## License

[Add your license information here]

## Support

For questions or issues, please [add contact information or issue tracker link]. 