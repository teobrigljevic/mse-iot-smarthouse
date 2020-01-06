package com.example.smarthouseiotmobile;

import androidx.appcompat.app.AppCompatActivity;

import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.text.InputFilter;
import android.text.Spanned;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.TextView;

import com.estimote.coresdk.common.requirements.SystemRequirementsChecker;
import com.estimote.coresdk.observation.region.beacon.BeaconRegion;
import com.estimote.coresdk.recognition.packets.Beacon;
import com.estimote.coresdk.service.BeaconManager;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Dictionary;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.google.firebase.firestore.FirebaseFirestore;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.annotation.WorkerThread;
import android.util.Log;

import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.OnFailureListener;
import com.google.android.gms.tasks.OnSuccessListener;
import com.google.android.gms.tasks.Task;
import com.google.android.gms.tasks.Tasks;
import com.google.firebase.Timestamp;
import com.google.firebase.firestore.CollectionReference;
import com.google.firebase.firestore.DocumentChange;
import com.google.firebase.firestore.DocumentChange.Type;
import com.google.firebase.firestore.DocumentReference;
import com.google.firebase.firestore.DocumentSnapshot;
import com.google.firebase.firestore.EventListener;
import com.google.firebase.firestore.FieldPath;
import com.google.firebase.firestore.FieldValue;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.FirebaseFirestoreException;
import com.google.firebase.firestore.FirebaseFirestoreSettings;
import com.google.firebase.firestore.ListenerRegistration;
import com.google.firebase.firestore.MetadataChanges;
import com.google.firebase.firestore.Query;
import com.google.firebase.firestore.Query.Direction;
import com.google.firebase.firestore.QueryDocumentSnapshot;
import com.google.firebase.firestore.QuerySnapshot;
import com.google.firebase.firestore.ServerTimestamp;
import com.google.firebase.firestore.SetOptions;
import com.google.firebase.firestore.Source;
import com.google.firebase.firestore.Transaction;
import com.google.firebase.firestore.WriteBatch;
import com.jjoe64.graphview.GraphView;
import com.jjoe64.graphview.helper.DateAsXAxisLabelFormatter;
import com.jjoe64.graphview.series.DataPoint;
import com.jjoe64.graphview.series.LineGraphSeries;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;
import java.util.concurrent.Executor;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;


public class MainActivity extends AppCompatActivity {

    TextView positionText;
    TextView roomSensors;
    ImageView farBeaconView;
    ImageView nearBeaconView;
    TextView nearBeaconInfo;
    TextView farBeaconInfo;
    EditText percentage;
    Button   incrButton;
    Button   decrButton;
    Button   lightButton;
    Button   storeButton;
    Button   radiatorButton;
    Boolean  beaconDetected;
    Beacon  nearestBeacon;
    LineGraphSeries < DataPoint > xSeries = null;
    LineGraphSeries < DataPoint > ySeries = null;
    int index = 0;

    private FirebaseFirestore db;

    // In the "OnCreate" function below:
    // - TextView, EditText and Button elements are linked to their graphical parts (Done for you ;) )
    // - "OnClick" functions for Increment and Decrement Buttons are implemented (Done for you ;) )
    //
    // TODO List:
    // - Use the Estimote SDK to detect the closest Beacon and figure out the current Room
    //     --> See Estimote documentation:  https://github.com/Estimote/Android-SDK
    // - Set the PositionText with the Room name
    // - Implement the "OnClick" functions for LightButton, StoreButton and RadiatorButton

    private BeaconManager beaconManager;
    private BeaconRegion region;
    private Beacon beacon;

    private static final Map<String, List<String>> PLACES_BY_BEACONS;

    // TODO: replace "<major>:<minor>" strings to match your own beacons.
    static{
        Map<String, List<String>> placesByBeacons = new HashMap<>();
        placesByBeacons.put("12423:15713", new ArrayList<String>() {{
            add("Room 15713\n(Major ID 12423)");
        }});
        placesByBeacons.put("12423:28809", new ArrayList<String>() {{
            add("Room 28809\n(Major ID 12423)");
        }});
        PLACES_BY_BEACONS = Collections.unmodifiableMap(placesByBeacons);
    }

    private List<String> placesNearBeacon(Beacon beacon) {
        String beaconKey = String.format("%s:%s", beacon.getMajor(), beacon.getMinor());
        if (PLACES_BY_BEACONS.containsKey(beaconKey)) {
            return PLACES_BY_BEACONS.get(beaconKey);
        }
        return Collections.emptyList();
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        positionText   =  findViewById(R.id.PositionText);
        nearBeaconView = (ImageView)findViewById(R.id.nearBeaconView);
        nearBeaconInfo   =  findViewById(R.id.nearBeaconInfo);
        farBeaconView = (ImageView)findViewById(R.id.farBeaconView);
        farBeaconInfo   =  findViewById(R.id.farBeaconInfo);
        percentage     =  findViewById(R.id.Percentage);
        incrButton     =  findViewById(R.id.IncrButton);
        decrButton     =  findViewById(R.id.DecrButton);
        lightButton    =  findViewById(R.id.LightButton);
        storeButton    =  findViewById(R.id.StoreButton);
        radiatorButton =  findViewById(R.id.RadiatorButton);
        roomSensors =  findViewById(R.id.roomSensors);
        beaconDetected =false;
        xSeries = new LineGraphSeries<>();
        ySeries = new LineGraphSeries<>();

        db = FirebaseFirestore.getInstance();

        roomSensors.setText("Presence: False \nTemperature: 22C \nLuminance: 200Lux \nHumidity: 40%");
        nearBeaconInfo.setText("");
        farBeaconInfo.setText("");
        nearBeaconView.setVisibility(View.INVISIBLE);
        farBeaconView.setVisibility(View.INVISIBLE);

        getRoomInfo("01");


        beaconManager = new BeaconManager(this);
        region = new BeaconRegion("ranged region",
                UUID.fromString("B9407F30-F5F8-466E-AFF9-25556B57FE6D"), null, null);
        beaconManager.setRangingListener(new BeaconManager.BeaconRangingListener() {
            @Override
            public void onBeaconsDiscovered(BeaconRegion region, List<Beacon> list) {
                if (!list.isEmpty()) {
                    Beacon nearestBeacon = list.get(0);

                    //if (nearestBeacon.getMinor()!=nearestBeacon_new.getMinor()) {
                    //    nearestBeacon = nearestBeacon_new;
                        double distance = -1;

                        List<String> places = placesNearBeacon(nearestBeacon);
                        positionText.setText("Room: " + nearestBeacon.getMinor() + "\n(Mayor ID: " + nearestBeacon.getMajor() + ")");
                        distance = list.get(0).getMeasuredPower() - list.get(0).getRssi();
                        distance = distance / (10 * 3);
                        distance = Math.pow(10, distance);
                        //distance= Math.pow(10, (list.get(0).getMeasuredPower()-list.get(0).getRssi())/(10*2));
                        nearBeaconInfo.setText("Beacon: " + list.get(0).getMinor() +
                                "\nPower: " + String.valueOf(list.get(0).getRssi() +
                                "\nDistance: " + String.format("%.2f", distance)) + "m");

                        if (nearestBeacon.getMinor() == 28809)
                            nearBeaconView.setImageResource(R.mipmap.beacon_rose);
                        if (nearestBeacon.getMinor() == 15713)
                            nearBeaconView.setImageResource(R.mipmap.beacon_blue);
                        nearBeaconView.setVisibility(View.VISIBLE);

                        if (list.size() == 2) {
                            Beacon farBeacon = list.get(1);
                            farBeaconView.setVisibility(View.VISIBLE);
                            distance = farBeacon.getMeasuredPower() - farBeacon.getRssi();
                            distance = distance / (10 * 3);
                            distance = Math.pow(10, distance);
                            farBeaconInfo.setText("Beacon: " + farBeacon.getMinor() +
                                    "\nPower: " + String.valueOf(farBeacon.getRssi() +
                                    "\nDistance: " + String.format("%.2f", distance)) + "m");
                            if (farBeacon.getMinor() == 28809)
                                farBeaconView.setImageResource(R.mipmap.beacon_rose);
                            if (farBeacon.getMinor() == 15713)
                                farBeaconView.setImageResource(R.mipmap.beacon_blue);


                        } else {
                            farBeaconView.setVisibility(View.INVISIBLE);
                            farBeaconInfo.setText("");
                        }

                        Log.d("NearBeacon", String.format(places.toString()));
                        //getRoomInfo("01");
                    //}
                    //else{
                    //    updateRoomInfo("01");


                    //}
                }
                else{
                    farBeaconView.setVisibility(View.INVISIBLE);
                    nearBeaconView.setVisibility(View.INVISIBLE);
                    nearBeaconInfo.setText("");
                    farBeaconInfo.setText("");
                    roomSensors.setText("");
                }
            }
        });



        // Only accept input values between 0 and 100
        percentage.setFilters(new InputFilter[]{new InputFilterMinMax("0", "100")});

        incrButton.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                int number = Integer.parseInt(percentage.getText().toString());
                if (number<100) {
                    number++;
                    Log.d("IoTLab-Inc", String.format("%d",number));
                    percentage.setText(String.format("%d",number));
                }
            }
        });

        decrButton.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                int number = Integer.parseInt(percentage.getText().toString());
                if (number>0) {
                    number--;
                    Log.d("IoTLab-Dec", String.format("%d",number));
                    percentage.setText(String.format("%d",number));
                }
            }
        });


        lightButton.setOnClickListener(new View.OnClickListener() {

            public void onClick(View v) {
                // TODO Send HTTP Request to command light
                Log.d("IoTLab", percentage.getText().toString());
            }
        });



        storeButton.setOnClickListener(new View.OnClickListener() {

            public void onClick(View v) {

                // TODO Send HTTP Request to command store
                Log.d("IoTLab", percentage.getText().toString());
            }
        });



        radiatorButton.setOnClickListener(new View.OnClickListener() {

            public void onClick(View v) {

                // TODO Send HTTP Request to command radiator
                Log.d("IoTLab", percentage.getText().toString());
            }
        });


    }

    public void getRoomInfo(String roomid){
        String collectionPath= "ROOM" + roomid + "_EXAMPLE";

        db.collection(collectionPath)
                .get()
                .addOnCompleteListener(new OnCompleteListener<QuerySnapshot>() {
                    @Override
                    public void onComplete(@NonNull Task<QuerySnapshot> task) {
                        if (task.isSuccessful()) {
                            String temperature=null;
                            String luminosity=null;
                            String presence=null;
                            String humidity=null;
                            Map<String, Object>  data = new HashMap<>();
                            JSONObject json = null;
                            int x = task.getResult().size();



                            for (QueryDocumentSnapshot document : task.getResult()) {
                                Log.d("TAG", document.getId() + " => " + document.getData());

                                data = document.getData();
                                json = new JSONObject(data);
                                JSONObject temp = verifyJSON(json);



                                try {
                                    if(temp != null) {
                                        temperature = temp.getString("zTemperature");
                                        luminosity = temp.getString("zLuminosity");
                                        presence = temp.getString("zPresence");
                                        humidity = temp.getString("zHumidity");
                                        xSeries.appendData(new DataPoint(index, Double.parseDouble(temperature)),false,100);
                                        ySeries.appendData(new DataPoint(index, Double.parseDouble(luminosity)),false,100);
                                        index+=1;
                                    }
                                } catch (JSONException e) {
                                    e.printStackTrace();
                                }


                            }
                            final GraphView graph = (GraphView) findViewById(R.id.graph);
                            graph.setVisibility(View.VISIBLE);
                            /*DataPoint[] dataPointsX = new DataPoint[20];
                            DataPoint[] dataPointsY = new DataPoint[20];
                            for (int index = 0; index < 20; index++) {
                                dataPointsX[index] = new DataPoint(index, index);
                                dataPointsY[index] = new DataPoint(index, index+1);

                            }*/


                            xSeries.setColor(Color.BLUE);
                            ySeries.setColor(Color.RED);
                            graph.addSeries(xSeries);
                            graph.addSeries(ySeries);
                            //graph.getGridLabelRenderer().setLabelFormatter(new DateAsXAxisLabelFormatter(this));
                            graph.getGridLabelRenderer().setNumHorizontalLabels(3);
                            graph.getGridLabelRenderer().setNumVerticalLabels(3);

                            /*graph.getViewport().setMinX(0);
                            graph.getViewport().setMaxX(20);
                            graph.getViewport().setMinY(0);
                            graph.getViewport().setMaxY(20);*/
                            graph.getViewport().setXAxisBoundsManual(true);

                            graph.getGridLabelRenderer().setHumanRounding(false);

                            roomSensors.setText("Presence: " + presence + " \nTemperature: " + temperature + " C \nLuminance: " + luminosity + " Lux \nHumidity:  " + humidity + " % ");

                        } else {
                            Log.w("TAG", "Error getting documents.", task.getException());
                        }
                    }
                });



    }

    public void updateRoomInfo(String roomid){
        String collectionPath= "ROOM" + roomid + "_EXAMPLE";
        String documentPath= "0zLATESTVALUES";

        DocumentReference docRef = db.collection(collectionPath).document(documentPath);
        docRef.get().addOnCompleteListener(new OnCompleteListener<DocumentSnapshot>() {
            @Override
            public void onComplete(@NonNull Task<DocumentSnapshot> task) {
                if (task.isSuccessful()) {
                    DocumentSnapshot document = task.getResult();
                    if (document.exists()) {

                        Map<String, Object>  data = new HashMap<>();
                        data = document.getData();
                        Log.d("TAG", "DocumentSnapshot data: " + data);

                        String temperature=null;
                        String luminosity=null;
                        String presence=null;
                        String humidity=null;

                        JSONObject json = null;
                        json = new JSONObject(data);
                        JSONObject temp = verifyJSON(json);

                        try {
                            if(temp != null) {
                                temperature = temp.getString("zTemperature");
                                luminosity = temp.getString("zLuminosity");
                                presence = temp.getString("zPresence");
                                humidity = temp.getString("zHumidity");
                                xSeries.appendData(new DataPoint(index, Double.parseDouble(temperature)),false,100);
                                ySeries.appendData(new DataPoint(index, Double.parseDouble(luminosity)),false,100);
                                index+=1;
                            }
                        } catch (JSONException e) {
                            e.printStackTrace();
                        }
                        final GraphView graph = (GraphView) findViewById(R.id.graph);
                        graph.setVisibility(View.VISIBLE);
                            /*DataPoint[] dataPointsX = new DataPoint[20];
                            DataPoint[] dataPointsY = new DataPoint[20];
                            for (int index = 0; index < 20; index++) {
                                dataPointsX[index] = new DataPoint(index, index);
                                dataPointsY[index] = new DataPoint(index, index+1);

                            }*/



                        graph.addSeries(xSeries);
                        graph.addSeries(ySeries);
                        //graph.getGridLabelRenderer().setLabelFormatter(new DateAsXAxisLabelFormatter(this));
                        graph.getGridLabelRenderer().setNumHorizontalLabels(3);
                        graph.getGridLabelRenderer().setNumVerticalLabels(3);

                            /*graph.getViewport().setMinX(0);
                            graph.getViewport().setMaxX(20);
                            graph.getViewport().setMinY(0);
                            graph.getViewport().setMaxY(20);*/
                        graph.getViewport().setXAxisBoundsManual(true);

                        graph.getGridLabelRenderer().setHumanRounding(false);

                        roomSensors.setText("Presence: " + presence + " \nTemperature: " + temperature + " C \nLuminance: " + luminosity + " Lux \nHumidity:  " + humidity + " % ");






                    } else {
                        Log.d("TAG", "No such document");
                    }
                } else {
                    Log.d("TAG", "get failed with ", task.getException());
                }
            }
        });


    }


    public JSONObject verifyJSON(JSONObject json){
        JSONObject temp;
        try {
            temp = json.getJSONObject("zSensor01");
        } catch (JSONException e) {
            temp = null;
            e.printStackTrace();

        }
        return temp;
    }


    // You will be using "OnResume" and "OnPause" functions to resume and pause Beacons ranging (scanning)
    // See estimote documentation:  https://developer.estimote.com/android/tutorial/part-3-ranging-beacons/
    @Override
    protected void onResume() {
        super.onResume();

        SystemRequirementsChecker.checkWithDefaultDialogs(this);

        beaconManager.connect(new BeaconManager.ServiceReadyCallback() {
            @Override
            public void onServiceReady() {
                beaconManager.startRanging(region);
            }
        });

    }


    @Override
    protected void onPause() {
        beaconManager.stopRanging(region);

        super.onPause();

    }

}










// This class is used to filter input, you won't be using it.

class InputFilterMinMax implements InputFilter {
    private int min, max;

    public InputFilterMinMax(int min, int max) {
        this.min = min;
        this.max = max;
    }

    public InputFilterMinMax(String min, String max) {
        this.min = Integer.parseInt(min);
        this.max = Integer.parseInt(max);
    }

    @Override
    public CharSequence filter(CharSequence source, int start, int end, Spanned dest, int dstart, int dend) {
        try {
            int input = Integer.parseInt(dest.toString() + source.toString());
            if (isInRange(min, max, input))
                return null;
        } catch (NumberFormatException nfe) { }
        return "";
    }

    private boolean isInRange(int a, int b, int c) {
        return b > a ? c >= a && c <= b : c >= b && c <= a;
    }
}

 /*  // Create a new user with a first and last name
         Map<String, Object>  data = new HashMap<>();
        data.put("first", "Ada");
        data.put("last", "Lovelace");
        data.put("born", 1815);

        // Add a new document with a generated ID
        db.collection("ROOM01_EXAMPLE")
                .add(data)
                .addOnSuccessListener(new OnSuccessListener<DocumentReference>() {
                    @Override
                    public void onSuccess(DocumentReference documentReference) {
                        Log.d("TAG", "DocumentSnapshot added with ID: " + documentReference.getId());
                    }
                })
                .addOnFailureListener(new OnFailureListener() {
                    @Override
                    public void onFailure(@NonNull Exception e) {
                        Log.w("TAG", "Error adding document", e);
                    }
                });*/
      /* DocumentReference docRef = db.collection("mytest").document("test");
        docRef.get().addOnCompleteListener(new OnCompleteListener<DocumentSnapshot>() {
            @Override
            public void onComplete(@NonNull Task<DocumentSnapshot> task) {
                if (task.isSuccessful()) {
                    DocumentSnapshot document = task.getResult();
                    if (document.exists()) {
                        Log.d("mytag", "DocumentSnapshot data: " + document.getData());
                    } else {
                        Log.d("mytag", "No such document");
                    }
                } else {
                    Log.d("mytag", "get failed with ", task.getException());
                }
            }
        });*/











