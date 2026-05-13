package com.market4cast.db;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class DatabaseManager {
    private static final String DB_URL = "jdbc:sqlite:market4cast.db";

    public Connection getConnection() throws SQLException {
        return DriverManager.getConnection(DB_URL);
    }

    public List<PredictionRecord> getActivePredictions() {
        List<PredictionRecord> list = new ArrayList<>();
        String query = "SELECT * FROM active_predictions WHERE status = 'ACTIVE'";
        
        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(query)) {
            
            while (rs.next()) {
                list.add(new PredictionRecord(
                    rs.getString("ticker"),
                    rs.getString("announcement_date"),
                    rs.getDouble("entry_price"),
                    rs.getDouble("predicted_target_price"),
                    rs.getDouble("predicted_target_pct"),
                    rs.getString("catalyst_summary"),
                    rs.getString("sector")
                ));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return list;
    }

    public double getSystemConfidence() {
        String query = "SELECT metric_value FROM system_metrics WHERE metric_name = 'system_confidence_score'";
        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(query)) {
            if (rs.next()) {
                return rs.getDouble("metric_value");
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return 0.0;
    }

    // Data model for table rows
    public static class PredictionRecord {
        public String ticker;
        public String date;
        public double entry;
        public double target;
        public double targetPct;
        public String catalyst;
        public String sector;

        public PredictionRecord(String ticker, String date, double entry, double target, double targetPct, String catalyst, String sector) {
            this.ticker = ticker;
            this.date = date;
            this.entry = entry;
            this.target = target;
            this.targetPct = targetPct;
            this.catalyst = catalyst;
            this.sector = sector;
        }

        // Getters for JavaFX TableView
        public String getTicker() { return ticker; }
        public String getDate() { return date; }
        public double getEntry() { return entry; }
        public double getTarget() { return target; }
        public double getTargetPct() { return targetPct; }
        public String getCatalyst() { return catalyst; }
        public String getSector() { return sector; }
    }
}
