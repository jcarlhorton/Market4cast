package com.market4cast;

import com.market4cast.db.DatabaseManager;
import javafx.application.Platform;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
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
        targetCol.setCellValueFactory(new PropertyValueFactory<>("target"));
        pctCol.setCellValueFactory(new PropertyValueFactory<>("targetPct"));
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

    private void startDataRefreshLoop() {
        refreshScheduler.scheduleAtFixedRate(() -> {
            List<DatabaseManager.PredictionRecord> records = dbManager.getActivePredictions();
            double confidence = dbManager.getSystemConfidence();
            
            Platform.runLater(() -> {
                predictionsTable.setItems(FXCollections.observableArrayList(records));
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
