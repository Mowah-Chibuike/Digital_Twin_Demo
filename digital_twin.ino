#include <Wire.h>
#include <MPU6050_light.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#define network "Timothy's A16"
#define password "nmg9h28vmhjth6m"

MPU6050 mpu(Wire);

// MQTT settings
const char* mqtt_server = "broker.hivemq.com";
const char* angle_topic = "my_angles";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long publishTimer = 0;

float x, y, z;

void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");

    String clientId = "ESP8266-";
    clientId += String(ESP.getChipId(), HEX);

    if (client.connect(clientId.c_str())) {
      Serial.println(" Connected!");
    } else {
      Serial.print(" Failed, rc=");
      Serial.print(client.state());
      Serial.println(" Retrying in 5 seconds...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  // Initialize MPU6050
  Wire.begin();
  byte status = mpu.begin();

  if (status != 0) {
    Serial.print("MPU6050 initialization failed. Status: ");
    Serial.println(status);
    while (1);
  }

  Serial.println("Calculating offsets. Keep the sensor still...");
  delay(1000);
  mpu.calcOffsets();
  Serial.println("Done!");

  // Connect to Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.begin(network, password);

  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Wi-Fi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Configure MQTT server
  client.setServer(mqtt_server, 1883);

  // Connect to MQTT
  reconnect();
}

void loop() {

  if (!client.connected()) {
    reconnect();
  }

  client.loop();

  // Update MPU6050
  mpu.update();

  // Read angles
  x = mpu.getAngleX();
  y = mpu.getAngleY();
  z = mpu.getAngleZ();

  // Publish every 200 ms
  if (millis() - publishTimer >= 1) {
    publishTimer = millis();
   JsonDocument doc;
    doc["x"] = x;
    doc["y"] = y;
    doc["z"] = z;

    char jsonBuffer[128];
    serializeJson(doc, jsonBuffer);

    client.publish(angle_topic, jsonBuffer);

    Serial.print("Published: ");
    Serial.println(jsonBuffer);
  }
}