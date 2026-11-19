package vn.alarm.pro;
import android.app.*;import android.content.*;import org.json.*;import java.util.*;
class Store {
 static JSONArray all(Context c){try{return new JSONArray(c.getSharedPreferences("data",0).getString("alarms","[]"));}catch(Exception e){return new JSONArray();}}
 static void save(Context c,JSONArray a){c.getSharedPreferences("data",0).edit().putString("alarms",a.toString()).apply();}
 static JSONObject get(Context c,int id){JSONArray a=all(c);for(int i=0;i<a.length();i++){JSONObject o=a.optJSONObject(i);if(o.optInt("id")==id)return o;}return null;}
 static PendingIntent pi(Context c,int id){return PendingIntent.getBroadcast(c,id,new Intent(c,AlarmReceiver.class).putExtra("id",id),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);}
 static void schedule(Context c,JSONObject o,long override){AlarmManager m=c.getSystemService(AlarmManager.class);int id=o.optInt("id");m.cancel(pi(c,id));if(!o.optBoolean("on")&&override==0)return;Calendar t=Calendar.getInstance();t.set(Calendar.HOUR_OF_DAY,o.optInt("h"));t.set(Calendar.MINUTE,o.optInt("m"));t.set(Calendar.SECOND,0);t.set(Calendar.MILLISECOND,0);if(t.getTimeInMillis()<=System.currentTimeMillis())t.add(Calendar.DATE,1);int days=o.optInt("days",127);if(days!=0)while((days&(1<<(t.get(Calendar.DAY_OF_WEEK)-1)))==0)t.add(Calendar.DATE,1);long when=override>0?override:t.getTimeInMillis();if(android.os.Build.VERSION.SDK_INT>=31&&!m.canScheduleExactAlarms())return;m.setAlarmClock(new AlarmManager.AlarmClockInfo(when,PendingIntent.getActivity(c,id,new Intent(c,MainActivity.class),PendingIntent.FLAG_IMMUTABLE)),pi(c,id));}
 static void update(Context c,JSONObject o){JSONArray a=all(c);boolean found=false;for(int i=0;i<a.length();i++)if(a.optJSONObject(i).optInt("id")==o.optInt("id")){try{a.put(i,o);}catch(Exception e){}found=true;}if(!found)a.put(o);save(c,a);}
 static void put(JSONObject o,String k,Object v){try{o.put(k,v);}catch(Exception e){}}
}