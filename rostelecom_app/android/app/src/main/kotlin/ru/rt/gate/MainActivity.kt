package ru.rt.gate

import android.view.WindowManager.LayoutParams  
import android.os.Bundle                        
import io.flutter.embedding.android.FlutterActivity

class MainActivity: FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(LayoutParams.FLAG_SECURE)
    }
}
