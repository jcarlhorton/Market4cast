package com.market4cast;

import javafx.application.Application;
import javafx.application.Platform;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.stage.Stage;

import javax.imageio.ImageIO;
import java.awt.*;
import java.io.IOException;
import java.net.URL;

public class Market4castApp extends Application {

    private final SidecarManager sidecarManager = new SidecarManager();

    @Override
    public void start(Stage primaryStage) throws Exception {
        // Start the Python Sidecar
        sidecarManager.startSidecar();

        // Load UI
        FXMLLoader loader = new FXMLLoader(getClass().getResource("/fxml/Dashboard.fxml"));
        Parent root = loader.load();
        
        primaryStage.setTitle("Market4cast - Equity Predictor");
        primaryStage.setScene(new Scene(root, 1100, 750));
        
        // Handle window close
        primaryStage.setOnCloseRequest(event -> {
            Platform.setImplicitExit(false); // Keep app running in tray
            primaryStage.hide();
        });

        setupSystemTray(primaryStage);
        primaryStage.show();
    }

    private void setupSystemTray(Stage stage) {
        if (!SystemTray.isSupported()) {
            System.out.println("System tray not supported!");
            return;
        }

        try {
            SystemTray tray = SystemTray.getSystemTray();
            // Placeholder icon - in a real app, use a resource image
            java.awt.Image image = Toolkit.getDefaultToolkit().createImage(new URL("https://cdn-icons-png.flaticon.com/512/25/25694.png"));
            
            TrayIcon trayIcon = new TrayIcon(image, "Market4cast");
            trayIcon.setImageAutoSize(true);

            PopupMenu popup = new PopupMenu();
            MenuItem showItem = new MenuItem("Show Dashboard");
            showItem.addActionListener(e -> Platform.runLater(stage::show));
            
            MenuItem exitItem = new MenuItem("Exit");
            exitItem.addActionListener(e -> {
                sidecarManager.stopSidecar();
                Platform.exit();
                System.exit(0);
            });

            popup.add(showItem);
            popup.addSeparator();
            popup.add(exitItem);
            
            trayIcon.setPopupMenu(popup);
            tray.add(trayIcon);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public void stop() {
        sidecarManager.stopSidecar();
    }

    public static void main(String[] args) {
        launch(args);
    }
}
