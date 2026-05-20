package com.market4cast;

import com.market4cast.db.DatabaseManager;
import javafx.application.Platform;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.collections.transformation.SortedList;
import javafx.fxml.FXML;
import javafx.scene.control.*;
import javafx.scene.control.cell.PropertyValueFactory;
import javafx.scene.text.Text;

import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class DashboardController {

    @FXML private TableView<DatabaseManager.PredictionRecord> predictionsTable;
    @FXML private TableColumn<DatabaseManager.PredictionRecord, String> tickerCol;
    @FXML private TableColumn<DatabaseManager.PredictionRecord, String> dateCol;
    @FXML private TableColumn<DatabaseManager.PredictionRecord, Double> entryCol;
    @FXML private TableColumn<DatabaseManager.PredictionRecord, Double> targetCol;
    @FXML private TableColumn<DatabaseManager.PredictionRecord, Double> pctCol;
    @FXML private TableColumn<DatabaseManager.PredictionRecord, String> sectorCol;
    @FXML private TableColumn<DatabaseManager.PredictionRecord, String> catalystCol;

    @FXML private Text confidenceScoreText;
    @FXML private Label riskLabel;
    @FXML private TextArea evidenceArea;

    private final DatabaseManager dbManager = new DatabaseManager();
    private final ScheduledExecutorService refreshScheduler = Executors.newSingleThreadScheduledExecutor();

    @FXML
    public void initialize() {
        setupTableColumns();
        startDataRefreshLoop();
    }

    private void setupTableColumns() {
        tickerCol.setCellValueFactory(new PropertyValueFactory<>("ticker"));
        dateCol.setCellValueFactory(new PropertyValueFactory<>("date"));
        
        entryCol.setCellValueFactory(new PropertyValueFactory<>("entry"));
        entryCol.setCellFactory(tc -> new TableCell<>() {
            @Override
            protected void updateItem(Double price, boolean empty) {
                super.updateItem(price, empty);
                if (empty || price == null) {
                    setText(null);
                } else {
                    setText(String.format("$%.2f", price));
                }
            }
        });

        targetCol.setCellValueFactory(new PropertyValueFactory<>("target"));
        targetCol.setCellFactory(tc -> new TableCell<>() {
            @Override
            protected void updateItem(Double price, boolean empty) {
                super.updateItem(price, empty);
                if (empty || price == null) {
                    setText(null);
                } else {
                    setText(String.format("$%.2f", price));
                }
            }
        });

        pctCol.setCellValueFactory(new PropertyValueFactory<>("targetPct"));
        pctCol.setCellFactory(tc -> new TableCell<>() {
            @Override
            protected void updateItem(Double pct, boolean empty) {
                super.updateItem(pct, empty);
                if (empty || pct == null) {
                    setText(null);
                } else {
                    setText(String.format("%.2f%%", pct));
                }
            }
        });

        sectorCol.setCellValueFactory(new PropertyValueFactory<>("sector"));
        catalystCol.setCellValueFactory(new PropertyValueFactory<>("catalyst"));

        // Listen for selection changes to update evidence area
        predictionsTable.getSelectionModel().selectedItemProperty().addListener((obs, oldSelection, newSelection) -> {
            if (newSelection != null) {
                evidenceArea.setText("Ticker: " + newSelection.getTicker() + "\n\n" +
                                   "Analysis Evidence:\n" + newSelection.getCatalyst());
            }
        });
    }

    @FXML
    public void handleShowDocs() {
        Alert alert = new Alert(Alert.AlertType.INFORMATION);
        alert.setTitle("Market4cast - System Documentation");
        alert.setHeaderText("Market4cast Equity Predictor Overview");
        
        String docsText = "HOW THE SYSTEM WORKS:\n" +
                          "Market4cast identifies high-momentum growth anomalies using the Post-Earnings " +
                          "Announcement Drift (PEAD) quantitative strategy. It targets equities experiencing " +
                          "a >5% overnight price gap and a >200% volume spike immediately following an earnings release.\n\n" +
                          "DATA UPDATES & SCANNING FREQUENCY:\n" +
                          "The background Python sidecar engine executes a scan once every hour during market hours, " +
                          "writing newly detected anomalies directly to the local SQLite database.\n\n" +
                          "ACTIVE PREDICTIONS TABLE COLUMNS:\n" +
                          "• Ticker: The unique stock symbol representing the target equity.\n" +
                          "• Announced: The date the earnings event occurred and the gap/volume spike was captured.\n" +
                          "• Entry Price: Calculated entry price at the Open of the second trading day (Day 2 Open).\n" +
                          "• Target Price: The system-predicted price where momentum drift is expected to exhaust.\n" +
                          "• Target %: The predicted percentage growth target (typically +15.00% drift).\n" +
                          "• Sector: The stock's GICS market sector (used to cap aggregate industry risk exposure).\n" +
                          "• Catalyst Summary: High-level overview of the earnings beat and SEC filing commentary.\n\n" +
                          "PRICING & STOCK SPLITS:\n" +
                          "All historical prices are split-adjusted (e.g., NVDA's 10-for-1 split in June 2024). " +
                          "This is standard practice in quantitative trading to prevent artificial price drops on split dates, " +
                          "but means historical prices will appear lower than raw quotes in historical news articles.\n\n" +
                          "UNDERSTANDING OTHER UI SECTIONS:\n" +
                          "• System Confidence: The aggregate model reliability percentage, based on backtesting performance.\n" +
                          "• Risk Management: Alerts on sector concentration limit (max 20% / 3 picks per sector).\n" +
                          "• LLM Evidence Attribution: Displays raw, sourced quotes extracted from SEC filings to justify guidance scores.";
        
        alert.setContentText(docsText);
        alert.getDialogPane().setPrefSize(600, 620);
        alert.showAndWait();
    }

    @FXML
    public void handleShowAbout() {
        Alert alert = new Alert(Alert.AlertType.INFORMATION);
        alert.setTitle("About Market4cast");
        alert.setHeaderText("Market4cast Equity Predictor");
        alert.setContentText("Version 1.0.0\n" +
                             "A hybrid JavaFX Host & Python Sidecar system for executing quantitative earnings-drift strategies.\n\n" +
                             "Developed in 2026.");
        alert.showAndWait();
    }

    private void startDataRefreshLoop() {
        refreshScheduler.scheduleAtFixedRate(() -> {
            List<DatabaseManager.PredictionRecord> records = dbManager.getActivePredictions();
            double confidence = dbManager.getSystemConfidence();
            
            Platform.runLater(() -> {
                ObservableList<DatabaseManager.PredictionRecord> observableList = FXCollections.observableArrayList(records);
                SortedList<DatabaseManager.PredictionRecord> sortedList = new SortedList<>(observableList);
                sortedList.comparatorProperty().bind(predictionsTable.comparatorProperty());
                predictionsTable.setItems(sortedList);
                
                confidenceScoreText.setText((int)(confidence * 100) + "%");
                checkRiskFlags(records);
            });
        }, 0, 30, TimeUnit.SECONDS); // Refresh every 30 seconds
    }

    private void checkRiskFlags(List<DatabaseManager.PredictionRecord> records) {
        // Simple logic to flag high sector concentration
        long techCount = records.stream().filter(r -> "Technology".equalsIgnoreCase(r.getSector())).count();
        if (techCount > 3) {
            riskLabel.setText("WARNING: High Technology sector concentration detected (" + techCount + " picks).");
            riskLabel.setStyle("-fx-text-fill: #ef4444;");
        } else {
            riskLabel.setText("Sector exposure within safe limits.");
            riskLabel.setStyle("-fx-text-fill: #10b981;");
        }
    }

    public void stop() {
        refreshScheduler.shutdown();
    }
}
