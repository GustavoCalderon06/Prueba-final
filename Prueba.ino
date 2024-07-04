#include <Wire.h>
#include <WiFi.h>
#include <WiFiClient.h>
#include <MPU9250_WE.h>

const char* ssid = "WIFI-DCI";         // Nombre de tu red WiFi
const char* password = "DComInf_2K24"; // Contraseña de tu red WiFi
const char* serverIP = "52.200.139.211"; // Dirección IP del servidor Flask
const int serverPort = 5000;            // Puerto del servidor Flask

WiFiClient client;
MPU9250_WE myMPU9250 = MPU9250_WE(0x68); // Usar la dirección 0x68 directamente

void setup() {
  Serial.begin(115200);
  delay(1000);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Conectando a WiFi...");
  }
  Serial.println("Conectado a WiFi");

  Wire.begin();
  if (!myMPU9250.init()) {
    Serial.println("MPU9250 no responde");
    while (1) delay(100);
  } else {
    Serial.println("MPU9250 está conectado");
  }
  
  // Calibración automática
  Serial.println("Posiciona el MPU9250 plano y no lo muevas - calibrando...");
  delay(1000);
  myMPU9250.autoOffsets();
  Serial.println("¡Listo!");

  // Configuraciones adicionales
  myMPU9250.setSampleRateDivider(5);
  myMPU9250.setAccRange(MPU9250_ACC_RANGE_2G);
  myMPU9250.enableAccDLPF(true);
  myMPU9250.setAccDLPF(MPU9250_DLPF_6);

  Serial.println("Inicialización completada");
}

void loop() {
  static unsigned long lastMillis = 0;
  const unsigned long interval = 1000 / 30; // Intervalo para capturar datos cada 33.33 ms (30 Hz)

  if (millis() - lastMillis >= interval) {
    lastMillis = millis();

    // Obtener valores de aceleración y g
    xyzFloat gValue = myMPU9250.getGValues();
    xyzFloat accRaw = myMPU9250.getAccRawValues();

    float gz = gValue.z;
    float az = accRaw.z / 16384.0; // Ajustar el valor de aceleración en g

    // Determinar el estado de la caldera
    bool calderaActiva = (gz > 1.0 || az > 1.0);

    if (client.connect(serverIP, serverPort)) {
      String postData = "{\"gz\": " + String(gz) + ", \"az\": " + String(az) + ", \"activo\": " + String(calderaActiva ? "true" : "false") + "}";
      client.println("POST /api/data HTTP/1.1");
      client.print("Host: ");
      client.println(serverIP);
      client.println("Content-Type: application/json");
      client.print("Content-Length: ");
      client.println(postData.length());
      client.println();
      client.println(postData);

      Serial.println("Datos enviados:");
      Serial.println(postData);
    } else {
      Serial.println("Error al conectar al servidor");
    }

    delay(100); // Espera breve para manejar estabilidad de la conexión
    client.stop();
  }
}

