module com.market4cast {
    requires javafx.controls;
    requires javafx.fxml;
    requires java.sql;
    requires java.desktop;

    opens com.market4cast to javafx.fxml;
    opens com.market4cast.db to javafx.base;
    
    exports com.market4cast;
    exports com.market4cast.db;
}
