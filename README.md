# CareCompass

**AI Shadow Coach for Healthcare Providers**

CareCompass turns every patient conversation into measurable quality improvement. It provides continuous, AI-powered feedback to healthcare providers after every patient interaction - improving HCAHPS scores, patient adherence, and clinical outcomes without adding to provider workload.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Plaud Device  │────▶│    iOS App      │────▶│  Backend API    │
│  (Recording)    │     │  (Sync + UI)    │     │  (FastAPI)      │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                        ┌────────────────────────────────┼────────────────────────────────┐
                        │                                │                                │
                        ▼                                ▼                                ▼
               ┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
               │  Plaud API      │             │ Interhuman AI   │             │ Crusoe Inference│
               │ (Transcription) │             │ (Engagement)    │             │ (Coaching)      │
               └─────────────────┘             └─────────────────┘             └─────────────────┘
```

## Components

### iOS App (`ios-plaud-sdk/`)
- Built on Plaud's template app with Embedded SDK
- Connects to Plaud devices via BLE/WiFi
- Syncs recordings and sends to backend for analysis
- Displays analysis results and coaching insights

### Backend API (`backend/`)
- FastAPI server orchestrating the analysis pipeline
- Integrates three APIs:
  - **Plaud Transcription API**: Speech-to-text with speaker diarization
  - **Interhuman AI API**: Engagement analysis and conversation quality
  - **Crusoe Inference API**: LLM-powered coaching generation

## Quick Start

### Prerequisites
- Mac with Xcode 16.0+ and XcodeGen (`brew install xcodegen`)
- Physical iPhone running iOS 14+
- Python 3.11+
- API credentials (see below)

### 1. Set Up Credentials

**Plaud** (from [portal.plaud.ai](https://portal.plaud.ai)):
- Client ID
- Client Secret  
- API Key

**Interhuman AI**:
- API Key with `interhumanai.upload.inter-2-audio` scope

**Crusoe** (from [console.crusoecloud.com](https://console.crusoecloud.com)):
- Inference API Key

### 2. Configure Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your credentials

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

### 3. Configure iOS App

```bash
cd ios-plaud-sdk/ios

# Create local config with your Plaud credentials
cat > PartnerConfig.local.xcconfig << EOF
USER_ACCESS_TOKEN = your_user_access_token
PLAUD_CLIENT_ID = your_client_id
PLAUD_API_KEY = your_api_key
EOF

# Generate Xcode project
xcodegen

# Open in Xcode
open PlaudTemplateApp.xcodeproj
```

### 4. Run

1. Start the backend: `uvicorn app.main:app --reload`
2. Build and run the iOS app on your physical iPhone
3. Pair your Plaud device
4. Record a conversation
5. Sync and analyze!

## API Endpoints

### Sessions
- `POST /sessions/` - Create a new session
- `POST /sessions/{id}/upload` - Upload audio for analysis
- `GET /sessions/{id}` - Get session with analysis results
- `GET /sessions/` - List sessions

### Dashboard
- `GET /dashboard/metrics/{provider_id}` - Provider metrics
- `GET /dashboard/metrics` - All provider metrics

## Analysis Pipeline

1. **Transcription** (Plaud): Audio → text with speaker IDs and timestamps
2. **Engagement Analysis** (Interhuman AI): 
   - Per-window engagement status (engaged/neutral/disengaged)
   - Social signals (confidence, hesitation, confusion, etc.)
   - Conversation Quality Index (clarity, authority, energy, rapport, learning)
3. **Coaching Generation** (Crusoe):
   - LLM analyzes transcript + engagement data
   - Generates 2-3 specific, actionable coaching insights

## Hackathon Prizes Targeted

- **Crusoe Overall (1st-3rd)**: All LLM inference on Crusoe
- **Plaud (1st/2nd)**: Deep SDK + API integration
- **UserTesting**: Product validation with healthcare professionals
- **DuploCloud "Most Sponsor Tools"**: 4+ meaningful integrations

## License

MIT
