package com.market4cast;

import java.io.IOException;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class SidecarManager {
    private Process sidecarProcess;
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();

    public void startSidecar() {
        System.out.println("Starting Python Sidecar...");
        try {
            // Assumes 'python' is in the PATH and src/engine/main.py exists
            ProcessBuilder pb = new ProcessBuilder("python", "src/engine/main.py");
            pb.inheritIO(); // Pipe output to Java console for debugging
            sidecarProcess = pb.start();
            
            // Monitor process health
            scheduler.scheduleAtFixedRate(() -> {
                if (sidecarProcess != null && !sidecarProcess.isAlive()) {
                    System.err.println("Sidecar process died. Restarting...");
                    startSidecar();
                }
            }, 5, 5, TimeUnit.SECONDS);
            
        } catch (IOException e) {
            System.err.println("Failed to start sidecar: " + e.getMessage());
        }
    }

    public void stopSidecar() {
        System.out.println("Stopping Python Sidecar...");
        if (sidecarProcess != null) {
            sidecarProcess.destroy();
        }
        scheduler.shutdown();
    }
}
