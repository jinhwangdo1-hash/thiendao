package vn.alarm.pro;
import android.content.*;import org.json.*;
public class BootReceiver extends BroadcastReceiver {public void onReceive(Context c,Intent i){JSONArray a=Store.all(c);for(int j=0;j<a.length();j++)Store.schedule(c,a.optJSONObject(j),0);}}