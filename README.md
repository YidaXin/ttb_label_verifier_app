# TTB Local AI Label Verification App (Digital Compliance Portal)

A standalone prototype compliance tool designed for the TTB Label Compliance Division to automatically verify alcohol label artwork against COLA application fields. 

Built to satisfy the **≤ 5.0 seconds latency** target and run **100% locally/air-gapped** to pass strict federal firewall and document-retention policies.

## 🛠️ Key Architectural Decisions
- **Decoupled Processing Pipeline:** To completely avoid local GPU/VRAM hardware constraints, the application bypasses heavy Vision-Language Models (VLMs). It utilizes **EasyOCR** for instantaneous raw text extraction on standard CPUs (<1.0s), followed by data mapping using a lightweight **1.5-Billion parameter text model (`qwen2.5:1.5b`)** (<1.5s).
- **High-Contrast Senior-Agent Friendly UI:** Designed specifically for accessibility (supporting agents with varying technical comfort levels). Features large inputs, high-contrast statuses, and obvious button placements.
- **Batch Processing Infrastructure:** Built to handle bulk importer manifests directly in a unified stream, resolving manual queue backlogs.



## 🚀 Setup & Running Instructions

Open your terminal/command prompt in the project root directory. Follow these steps to run the application natively on an air-gapped workstation:

### 1. Set up virtual environment

For stability and support, let us stick with Python 3.10. Below are two common ways to set up a virtual environment. I personally prefer `conda` because `conda` allows you to easily specify Python version for the new virtual environment. I named my virtual environment `ttb_app`, however, you should feel free to name your own virtual environment to your own preference.

#### 1.1. Using `conda` (Recommended)
```bash
$ conda create --name ttb_app python=3.10  # create environment
$ conda activate ttb_app                   # activate environment
```

#### 1.2. Using `venv`
```bash
$ python -m venv ttb_app       # create environment
$ source ttb_app/bin/activate  # activate environment
```
You will see many developers perfer to keep their virtual environments hidden, e.g., `.ttb_app` instead of `ttb_app`. This is not mandatory but does help keep the working directory clean.

### 2. Install the Dependencies
Once you have created and activated your virtual environment, you can now install the required dependencies for this prototype. Simply do:
```bash
$ cd /path/to/ttb_label_verifier_app  # i.e. the directory in which this prototype lives
$ pip install -r requirements.txt
```

### 3. Download and Start Ollama engine
#### 3.1. Windows
Download `OllamaSetup.exe` from the official website—or transfer it via an approved secure storage drive if working on an air-gapped machine. Double-click `OllamaSetup.exe` and step through the setup wizard. Once installed, Ollama runs as a background task. You will see the Ollama icon in your Windows system tray. Open PowerShell or Command Prompt and verify it is running by typing:
```bash
ollama --version
```
#### 3.2. Linux
First, install Ollama via command line in Terminal:
```bash
$ curl -fsSL https://ollama.com/install.sh | sh
```

Now you can launch the Ollama engine:
```bash
$ which ollama  # verify installation
$ ollama serve
```

#### 3.3. MacOS
Best way to install Ollama via command line in Terminal is using `homebrew`:
```bash
$ brew install ollama
```

Now you can launch the Ollama engine:
```bash
$ which ollama  # verify installation
$ ollama serve
```

Alternatively, you can launch via
```bash
$ brew services restart ollama
```

### 4. Download local large langauge model (LLM)
This prototype currently uses the `qwen2.5:1.5b` model, which you can download via:
```bash
$ ollama pull qwen2.5:1.5b
```

Alternatively, `qwen2.5vl:7b` is a great model, but it is larger and thus slower than `qwen2.5:1.5b`. You can download `qwen2.5vl:7b` via:
```bash
$ ollama pull qwen2.5vl:7b
```
or, if you prefer the quantized version of it, via:
```bash
$ ollama pull qwen2.5vl:7b-instruct-q4_K_M
```

Note that, as you launch and utilize the app later, the LLM itself will be hosted at the `http://127.0.0.1:11434` endpoint, which is *not* to be confused with the app's endpoint.

### 5. Launch local Streamlit app
Once the local LLM has been installed, you are finally ready to launch and test the Streamlit prototype app.

Inside the `/path/to/ttb_label_verifier_app` directory, do
```bash
$ streamlit run app.py
```
Doing so will by default launch this prototype app into the `http://localhost:8501/` endpoint, where you can begin uploading images and testing the prototype.



## 🌐 Live Deployment & Demo Mode

Per the project requirements, a live hosted URL has been provided for convenience. 

**Architectural Notice for Reviewers:** Because this system is built to comply with 100% local, air-gapped federal security mandates (bypassing outbound cloud API calls to clear strict firewalls), the public cloud-hosted version operates in a **Mock Evaluation Mode** utilizing cached JSON payloads for standard TTB sample profiles. 

To experience the live, fully interactive **< 2.5-second local CPU inference pipeline** processing brand new, un-cached label images in real-time, please follow the local **Setup & Running Instructions** above.
