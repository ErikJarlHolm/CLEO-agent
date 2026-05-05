# CLEO – Climate Expert Agent

**C**limate **L**earning and **E**xpert **O**utreach

An AI-powered scientific advisor on climate change.  CLEO answers questions
about the state-of-the-art knowledge on climate change, provides evidence-based
policy recommendations, and assists discussions on climate and sustainability.

CLEO is a **scientific advisor**, not a politician.  All answers are grounded
in peer-reviewed science (IPCC, NASA, NOAA, Nature, Science, …) and presented
in language accessible to politicians and the general public.

---

## Key Features

| Feature | Details |
|---------|---------|
| **Language-adaptive** | Replies in the user's language; default is **Norwegian** |
| **Web search** | Uses Tavily (preferred) or DuckDuckGo to fetch up-to-date sources |
| **Trusted-domain priority** | Prefers `ipcc.ch`, `nasa.gov`, `noaa.gov`, `nature.com`, `science.org`, `unep.org`, `iea.org`, … |
| **Structured output** | Every response follows a fixed format: Report Body → Date → Topic → Problem Statement → Executive Summary → Discussion → Sources |
| **Interactive mode** | Supports multi-turn conversations via the `--interactive` flag |

---

## Response Format

Every CLEO response is structured as follows (headings are translated to the
user's language automatically):

```
Report Body:       Full, detailed scientific answer with data and examples
Date:              YYYY-MM-DD
Topic:             1–3 word topic derived from the question
Problem Statement: Verbatim copy of the user's question
Executive Summary: ≤ 400 words – key findings and recommendations
Discussion:        ≤ 500 words – critical analysis and key uncertainties
Sources:           Numbered list of ≤ 20 references with URLs
```

---

## Requirements

- Python 3.10 or later
- An [OpenAI API key](https://platform.openai.com/api-keys) (**required**)
- A [Tavily API key](https://tavily.com) (*recommended* – free tier available;
  falls back to DuckDuckGo if absent)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/ErikJarlHolm/CLEO-agent.git
cd CLEO-agent

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (and optionally TAVILY_API_KEY)
```

---

## Usage

### Single question (command line)

```bash
# Norwegian (default)
python main.py "Hva er de viktigste tiltakene for å begrense global oppvarming til 1,5 °C?"

# English
python main.py "What does the IPCC AR6 say about limiting warming to 1.5 degrees?"

# Use a specific OpenAI model
python main.py --model gpt-4-turbo "Explain ocean acidification"

# Show agent reasoning steps
python main.py --verbose "What is the current CO2 concentration in the atmosphere?"
```

### Interactive session

```bash
python main.py --interactive
# or: python main.py -i
```

Type `avslutt`, `quit`, or `exit` to end the session.

### Library usage

```python
from cleo_agent.agent import run_agent

response = run_agent("Hva er status for Arktis-isen?")
print(response)
```

---

## Configuration

| Environment variable | Default | Description |
|---------------------|---------|-------------|
| `OPENAI_API_KEY` | — | **Required.** OpenAI API key |
| `TAVILY_API_KEY` | — | Recommended. Tavily search key (falls back to DuckDuckGo) |
| `CLEO_MODEL` | `gpt-4o` | OpenAI model to use |

---

## Project Structure

```
CLEO-agent/
├── cleo_agent/
│   ├── __init__.py   # Package metadata
│   ├── agent.py      # Agent creation and run_agent() helper
│   ├── prompts.py    # System prompt (persona, language rules, format)
│   └── tools.py      # Web-search tools (Tavily + DuckDuckGo fallback)
├── main.py           # CLI entry point
├── requirements.txt  # Python dependencies
├── .env.example      # Template for environment variables
└── README.md
```

---

## Trusted Sources

CLEO preferentially searches the following domains:

- [IPCC](https://www.ipcc.ch) – Intergovernmental Panel on Climate Change
- [NASA Climate](https://climate.nasa.gov)
- [NOAA](https://www.noaa.gov)
- [Nature](https://www.nature.com)
- [Science](https://www.science.org)
- [WMO](https://www.wmo.int)
- [UNEP](https://www.unep.org)
- [IEA](https://www.iea.org)
- [Carbon Brief](https://www.carbonbrief.org)
- [World Bank Climate](https://www.worldbank.org)
- [UN Climate](https://www.un.org/en/climatechange)

---

## License

MIT
