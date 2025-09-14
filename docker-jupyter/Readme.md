# Understanding the Setup

Benefits of This Setup:

- No authentication - direct access to both Jupyter and VSCode
- Multiple access methods - browser and desktop VSCode
- Full Python data science stack - pandas, scikit-learn, numpy, etc.
- Persistent data - files saved in ./notebooks and ./data
- Development flexibility - use whichever interface suits your task

NOTE: Tested on Windows only

## Prerequisites

- Docker Desktop installed and running
- VSCode installed (for Methods 3 & 4)

## Access Methods

After starting, you'll have **four ways** to code:

| Method                          | Interface | URL/Setup                | Best For                   |
| ------------------------------- | --------- | ------------------------ | -------------------------- |
| **1. Jupyter Lab**              | Browser   | http://localhost:8888    | Data science, notebooks    |
| **2. Browser VSCode**           | Browser   | http://localhost:8080    | Quick code editing         |
| **3. Desktop VSCode + Jupyter** | Desktop   | Connect to remote kernel | Notebook development       |
| **4. Dev Containers**           | Desktop   | Reopen in container      | Full development isolation |

### Architecture Flow:

- **Method 1:** `Browser → Jupyter Lab → Container`
- **Method 2:** `Browser → code-server → Container`
- **Method 3:** `Desktop VSCode → Jupyter Server → Container`
- **Method 4:** `Desktop VSCode → VSCode Server → Container`

### Which Method Should I Use?

- **For Data Science & Notebooks:** Method 1 (Jupyter Lab)
- **For Quick Code Editing:** Method 2 (Browser VSCode)
- **For Notebook Development with Desktop VSCode:** Method 3 (Jupyter Extension)
- **For Full Development with Complete Isolation:** Method 4 (Dev Containers)

## Host VSCode Integration Methods

NOTE: Method 1 & 2 are straight forward and are easily accessible through http://localhost:8888 and http://localhost:8080 respectively.

### Method 3: VS Code + Jupyter Extension

- Ensure docker compose is up
- Using Jupyter Lab (http://localhost:8888) create a notebook in `work` folder (say `test.ipynb` ). That notebook will sync with local folder `notebooks` on the host machine.
- Open VS Code on host machine and open current project folder (which will have `data` and `notebooks` folders created automatically by docker compose)
- Install `Jupyter extension` in host VSCode
- Open the `notebooks\test.ipynb` file
- Click `Select Kernel` from top right of VSCode IDE
- Select `Existing Jupyter Server`
- Enter: `http://localhost:8888`
- Insecure: `yes`
- Display Name: `localhost` (any name to identify the server is fine)
- Select a Kernel: `Python 3 (ipykernel) opt\conda\bin\python`
- Write `print("Hello")` and press Ctrl+Enter (to execute)

### Method 4: using "Dev Containers" extension

Dev Containers essentially give you local VSCode UI with remote execution environment. It's like having VSCode "project" itself into the container while keeping the familiar interface on your host machine.
The magic is that it feels completely native, but all the actual development work (Python execution, package access, terminal commands) happens inside your Docker container with all your data science tools!

- Open project folder in VS Code IDE
- Ctrl+Shift+P -> `Dev Containers: Reopen in Container`
- This will restart VS Code IDE in `work` folder of Jupyter Docker container environment
- Ctrl+Shift+P -> `Create: New Jupyter Notebook`
- Save it: `/home/jovyan/work/demo.ipynb`
- Click `Select Kernel` from top right of VS IDE
- Select the Kernel: `base (Python 3.11.6) /opt/conda/bin/python`
- Write `print("Hello")` and press Ctrl+Enter (to execute)

NOTE: additional VS extensions can be added in `devcontainer.json`

## Quick understanding about all above methods

### When You Run `docker-compose up -d`:

What Starts:

- Docker container ✅ (datascience container boots up)
- Jupyter Lab ✅ (Available at localhost:8888)
- code-server installation ✅ (Downloads and installs)
- code-server service ✅ (Available at localhost:8080)
- Container file system ✅ (Mounts ./notebooks and ./data)

What's NOT Running Yet:

- VSCode Server ❌ (Not installed until Dev Container connects)
- VSCode Desktop connection ❌ (No connection established)
- Any Dev Container extensions ❌ (Not installed yet)

Container Status:

- Python environment ✅ (Ready with all data science packages)
- Port forwarding ✅ (8888 and 8080 accessible from host)
- Background processes ✅ (code-server running in background)

### When You Connect via Method 1: Jupyter Lab

What Happens:

- Browser opens localhost:8888 ✅ (Direct HTTP connection)
- Jupyter server serves interface ✅ (Already running from compose)
- No authentication required ✅ (Token disabled)
- Notebook environment loads ✅ (Ready for data science)

What You Get:

- Interactive notebooks ✅ (Best for data science)
- Rich output rendering ✅ (Plots, tables, HTML)
- Container's Python kernel ✅ (All packages available)
- Cell-based execution ✅ (Interactive development)
- Data visualization ✅ (Matplotlib, Plotly work perfectly)
- Markdown support ✅ (Documentation in notebooks)

What's Optimized For:

- Data exploration ✅ (Interactive analysis)
- Prototyping ✅ (Quick experiments)
- Sharing results ✅ (Notebook format)
- Teaching/demos ✅ (Clear narrative flow)

### When You Connect via Method 2: Browser VSCode (code-server)

What Happens:

- Browser opens localhost:8080 ✅ (Direct HTTP connection)
- code-server serves web interface ✅ (VSCode UI in browser)
- No additional installation ✅ (Already running from compose)
- Direct container access ✅ (No client-server split)

What You Get:

- VSCode interface in browser ✅ (Familiar UI)
- Container's Python interpreter ✅ (Direct access)
- Integrated terminal ✅ (Bash inside container)
- Basic extensions ✅ (Limited to what code-server supports)
- File editing capabilities ✅ (Full file system access)

What You Don't Get:

- Desktop integration ❌ (No native OS features)
- Full extension ecosystem ❌ (Limited browser compatibility)
- Advanced debugging ❌ (Reduced debugging features)
- Native performance ❌ (Browser rendering overhead)

### When You Connect via Method 3: VS Code Desktop + Jupyter Extension

What Happens During Connection:

- VSCode Desktop opens ✅ (Runs on your host machine)
- Jupyter extension activates ✅ (Host-based extension)
- Extension connects to remote server ✅ (http://localhost:8888)
- Kernel selection shows container options ✅ (Container's Python)
- Remote kernel connection established ✅ (VSCode ↔ Jupyter Server)
- Notebook interface loads ✅ (Desktop UI with remote execution)

What You Get:

- Desktop VSCode UI ✅ (Native host application)
- Container's Python kernel ✅ (Code runs in container)
- Jupyter notebook experience ✅ (Cell-based execution)
- Host-based extensions ✅ (Your installed extensions work)
- IntelliSense from container ✅ (Via Jupyter connection)
- Rich output rendering ✅ (Plots, tables display in VSCode)

What Stays on Host:

- VSCode application ✅ (Desktop process)
- File operations ✅ (Files saved locally via mounts)
- Extension ecosystem ✅ (Host extensions active)
- Git integration ✅ (Host git tools)
- UI responsiveness ✅ (No remote protocol overhead)

What Runs in Container:

- Python code execution ✅ (All compute in container)
- Package imports ✅ (Container's libraries)
- Jupyter kernel ✅ (Container's Jupyter server)
- Data processing ✅ (Container's resources)

### When You Connect via Method 4: Dev Containers (using Desktop VSCode)

What Happens During Connection:

- VSCode detects devcontainer.json ✅ (Reads configuration)
- VSCode Server downloads ✅ (Into container at ~/.vscode-server/)
- Extensions install ✅ (Python, Jupyter, etc. install in container)
- Connection established ✅ (Desktop ↔ Container communication)
- Workspace opens ✅ (Shows /home/jovyan/work)

What You Get:

- Full desktop VSCode experience ✅ (Native UI)
- Container's Python interpreter ✅ (IntelliSense works)
- Integrated terminal ✅ (Bash inside container)
- Debugging capabilities ✅ (Python debugger in container)
- Git integration ✅ (Works with mounted files)
- Extension ecosystem ✅ (All specified extensions active)

Resource Usage:

- VSCode Server process ✅ (Additional memory usage in container)
- Extension host processes ✅ (Language servers running)
- Real-time sync overhead ✅ (File operations over network)

### Comparison: Method 3 vs Method 4

Method 3 (Jupyter Remote Kernel):
Desktop VSCode → Jupyter Server → Container's Python

- UI runs on host
- Extensions run on host
- Only code execution in container
- Hybrid host/container approach

Method 4 (Dev Containers):
Desktop VSCode → VSCode Server → Container's Python

- EVERYTHING runs in container
- Extensions install in container
- Full environment isolation
- Complete remote development

### Method Comparison

| Method                | Interface | Extensions | Best For                |
| --------------------- | --------- | ---------- | ----------------------- |
| 1 - Jupyter Lab       | Browser   | N/A        | Data science, notebooks |
| 2 - Browser VSCode    | Browser   | Limited    | Quick editing           |
| 3 - Desktop + Jupyter | Desktop   | Host       | Notebook development    |
| 4 - Dev Containers    | Desktop   | Container  | Full development        |
