# Market4cast - PEAD Equity Predictor

Market4cast is a hybrid desktop application designed to detect and analyze Post-Earnings Announcement Drift (PEAD) anomalies. It consists of a JavaFX-based frontend dashboard and an unattended Python-based backend sidecar engine. They communicate through a shared SQLite database running in Write-Ahead Logging (WAL) mode.

---

## 1. Prerequisites

To build and run Market4cast, the following system components must be installed:

### Java Environment
- **Java Development Kit (JDK) 21**: Required to run the JavaFX 21 UI and support modern Java APIs.
- **Gradle 9.x**: Used to compile the Java host, manage its dependencies, and run the application.

### Python Environment
- **Python 3.8+**: Required to run the background prediction sidecar and backtesting scripts.
- **Python Packages**: The required libraries are defined in [requirements.txt](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/requirements.txt). Install them via pip:
  ```bash
  pip install -r requirements.txt
  ```
  The dependencies include:
  - `yfinance`: For fetching stock prices and historical data from Yahoo Finance.
  - `pandas` & `numpy`: For handling tabular price series and indicators.
  - `matplotlib` & `scipy`: For analysis and visualization support.
  - `xgboost`: For running the V2 machine learning model predictor.

---

## 2. Database Setup & Initialization

The project persistence is managed by a shared SQLite database: `market4cast.db` (located at the root folder).

### Write-Ahead Logging (WAL) Mode
To allow concurrent access—where the Python backend writes new predictions and the JavaFX UI reads data simultaneously—the database operates under Write-Ahead Logging.
When active, SQLite creates two temporary sidecar files in the root folder alongside the database:
- `market4cast.db-shm` (Shared memory file)
- `market4cast.db-wal` (Write-ahead log)

### Automatic Database Initialization
You do not need to create the database manually. The database is initialized automatically by [main.py](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/engine/main.py) during application startup:
1. The app connects to `market4cast.db`.
2. It checks if the `active_predictions` table exists.
3. If not found, it runs the schema script [db_schema.sql](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/engine/db_schema.sql) to create:
   - `active_predictions`: Current detected PEAD anomalies.
   - `historical_performance`: Historical prediction outcomes for training.
   - `system_metrics`: Global health and risk stats (seeded with defaults).
4. The database is populated with sample seed predictions (e.g., NVDA, TSLA, AMD).

### Resetting/Initializing from Scratch
If you encounter SQLite errors or want to wipe all data to start fresh:
1. Stop the application and sidecar completely.
2. Delete the three database files in the project root:
   - `market4cast.db`
   - `market4cast.db-wal`
   - `market4cast.db-shm`
3. Launch the application again. The database schema and default seeds will be automatically generated.

---

## 3. Starting the Application and Sidecar

The Java application controls the lifecycle of the Python sidecar. Spawning the background engine manually is not required for daily use.

### Step-by-Step Launch
1. Open a terminal in the root of the project.
2. Run the Gradle application task:
   ```powershell
   gradle run
   ```
3. Gradle will compile the Java classes and launch the JavaFX window.
4. During startup, the Java class [Market4castApp](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/main/java/com/market4cast/Market4castApp.java) invokes the [SidecarManager](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/main/java/com/market4cast/SidecarManager.java).
5. [SidecarManager](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/main/java/com/market4cast/SidecarManager.java) spawns `python src/engine/main.py` in the background and pipes its logs to the Java console.
6. A health monitoring scheduler checks the sidecar process every 5 seconds and automatically restarts it if it crashes.

---

## 4. Stopping the Application and Sidecar

The JavaFX UI uses a system-tray layout, meaning closing the main window merely hides the dashboard while the system continues running in the background.

### Full Shutdown Steps
To stop both the host interface and the background Python engine:
- **Via the System Tray (Recommended)**:
  1. Locate the Market4cast icon in your Windows system tray.
  2. Right-click the icon to open the context menu.
  3. Select **Exit**. This calls the cleanup hook to kill the sidecar subprocess and shut down the JVM.
- **Via Terminal**:
  - Press `Ctrl + C` in the terminal where `gradle run` is active. Gradle will propagate the shutdown signal, invoking the cleanup methods.
- **Sidecar Lifecycle Cleanup**:
  - When the Java application terminates, the cleanup hook in [SidecarManager](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/main/java/com/market4cast/SidecarManager.java) is called to destroy the sidecar subprocess and release the resources.

---

## 5. Running the Backtest

To run historical strategy simulation and calculate Heuristic V1 performance on control tickers:

1. Open a terminal in the root directory.
2. Run the backtest script:
   ```bash
   python src/engine/backtest.py
   ```
3. The script will fetch historical data using `yfinance` for the control group, scan for anomalies (>5% price gap and >200% volume spike), apply entry-pricing on Day 2 Open, and track outcomes over a 30-day window.
4. The output will show the overall heuristic accuracy and write the results to `backtest_results.csv` in the root folder.
5. **Configuring range/tickers**: You can edit [backtest.py](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/engine/backtest.py) to change the ticker watchlist or change the date parameters in `run_backtest`.

---

## 6. Loading Backtest Data into the Database

If you want to view the backtest results in the active predictions table in the desktop dashboard:

1. Execute the backtest first to generate `backtest_results.csv`.
2. Run the CSV import script:
   ```bash
   python src/engine/import_backtest_to_db.py
   ```
3. The script [import_backtest_to_db.py](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/engine/import_backtest_to_db.py) performs the following:
   - Connects to `market4cast.db`.
   - Clears any existing mock data in the `active_predictions` table.
   - Iterates over `backtest_results.csv`, calculates the entry, target (7% stop-loss floor, target prediction %), maps tickers to sectors, and writes them with `INSERT OR REPLACE`.
4. Open the Java dashboard; it will display the historical anomalies as active predictions, allowing you to interact with real historical anomaly data in the UI.

---

## 7. Administrative & Management Operations

### Logging & Diagnostics
- The Python sidecar outputs logs to the console and writes detailed diagnostic reports to `market4cast_sidecar.log` in the root folder.
- Inspect `market4cast_sidecar.log` to troubleshoot database lock issues, `yfinance` API rate limits, or file ingestion exceptions.

### Watchlist Customization
- **Daily Scans**: The sidecar scans a hardcoded watchlist in [IngestionEngine](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/engine/ingestion.py). Add or remove tickers in `get_recent_earnings_tickers` to change which stocks are monitored daily.

### LLM Qualitative Analysis
- The sidecar performs qualitative filing audits on SEC documents using the code in [FilingAnalyzer](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/engine/analysis.py).
- The LLM utility ([llm_utils.py](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/engine/llm_utils.py)) is configured with rate-limiting and supports a simulated mode when no live API keys are provided, allowing testing and offline operation.

### XGBoost Model Training
- The prediction engine uses a hybrid model ([ModelPredictor](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/engine/model_predictor.py)): it utilizes the XGBoost regressor if a trained model is present at `src/engine/models/market4cast_v2.json`, otherwise falling back to the Heuristic V1 formula.
- A retraining task in [ModelTrainer](file:///C:/Users/jcarl/Projects/GitHub/Market4cast/src/engine/model_trainer.py) runs automatically on Saturdays at 2:00 AM.
- It requires at least **500 historical closed predictions** in the `historical_performance` table to train. If the dataset is smaller, it defaults to the Heuristic V1 fallback.
