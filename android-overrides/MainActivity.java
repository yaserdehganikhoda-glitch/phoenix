package ir.sewingstats.app;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(KarSystemPlugin.class); // باید قبل از super.onCreate باشد
        super.onCreate(savedInstanceState);
    }
}
