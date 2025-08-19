#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include <ESPping.h>
#include <vector>

// Configuración del servidor web
AsyncWebServer server(80);

// Variables globales
String connectedSSID = "";
IPAddress deviceIP;
IPAddress subnetMask(255, 255, 255, 240);
IPAddress networkAddr;
IPAddress broadcastAddr;
unsigned long lastScan = 0;
const unsigned long SCAN_INTERVAL = 10000; // 10 segundos

// Estructura para almacenar dispositivos detectados
struct NetworkDevice {
  IPAddress ip;
  String mac;
  bool active;
  unsigned long lastSeen;
};

std::vector<NetworkDevice> detectedDevices;

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("Inicializando ESP32-S3 WiFi Scanner con ESP-RESSID...");
  
  // Configurar modo WiFi
  WiFi.mode(WIFI_AP_STA);
  
  // Crear punto de acceso para configuración inicial
  WiFi.softAP("ESP32-WiFiConfig", "12345678");
  Serial.print("Punto de acceso creado: ");
  Serial.println(WiFi.softAPIP());
  
  // Configurar servidor web
  setupWebServer();
  
  Serial.println("Sistema listo. Accede a http://192.168.4.1");
  Serial.println("Interfaz Python debe conectarse a esta IP");
}

void loop() {
  // Actualizar escaneo de dispositivos cada 10 segundos
  if (millis() - lastScan > SCAN_INTERVAL) {
    if (WiFi.status() == WL_CONNECTED) {
      scanNetworkDevices();
    }
    lastScan = millis();
  }
  
  delay(10);
}

void setupWebServer() {
  // Configurar CORS para todas las rutas
  DefaultHeaders::Instance().addHeader("Access-Control-Allow-Origin", "*");
  
  // Endpoint para obtener redes WiFi disponibles
  server.on("/scan", HTTP_GET, [](AsyncWebServerRequest *request) {
    handleScanWiFi(request);
  });
  
  // Endpoint para conectar a una red WiFi
  server.on("/connect", HTTP_POST, [](AsyncWebServerRequest *request) {
    handleConnect(request);
  });
  
  // Endpoint para obtener estado de conexión
  server.on("/status", HTTP_GET, [](AsyncWebServerRequest *request) {
    handleStatus(request);
  });
  
  // Endpoint para obtener dispositivos detectados en la red
  server.on("/devices", HTTP_GET, [](AsyncWebServerRequest *request) {
    handleDevices(request);
  });
  
  // Endpoint para desconectar WiFi
  server.on("/disconnect", HTTP_POST, [](AsyncWebServerRequest *request) {
    handleDisconnect(request);
  });
  
  // Iniciar servidor
  server.begin();
  Serial.println("Servidor web iniciado en puerto 80");
}

void handleScanWiFi(AsyncWebServerRequest *request) {
  Serial.println("Escaneando redes WiFi...");
  
  int n = WiFi.scanNetworks();
  
  DynamicJsonDocument doc(4096);
  JsonArray networks = doc.createNestedArray("networks");
  
  for (int i = 0; i < n; i++) {
    JsonObject network = networks.createNestedObject();
    network["ssid"] = WiFi.SSID(i);
    network["rssi"] = WiFi.RSSI(i);
    network["encryption"] = (WiFi.encryptionType(i) == WIFI_AUTH_OPEN) ? "Open" : "Secured";
    network["channel"] = WiFi.channel(i);
    
    Serial.printf("Red encontrada: %s (%d dBm)\n", WiFi.SSID(i).c_str(), WiFi.RSSI(i));
  }
  
  String response;
  serializeJson(doc, response);
  request->send(200, "application/json", response);
}

void handleConnect(AsyncWebServerRequest *request) {
  if (!request->hasParam("ssid", true)) {
    request->send(400, "application/json", "{\"error\":\"Missing SSID parameter\"}");
    return;
  }
  
  String ssid = request->getParam("ssid", true)->value();
  String password = request->hasParam("password", true) ? request->getParam("password", true)->value() : "";
  
  Serial.println("Intentando conectar a: " + ssid);
  
  bool success = connectToWiFi(ssid, password);
  
  DynamicJsonDocument doc(512);
  doc["success"] = success;
  
  if (success) {
    doc["ip"] = WiFi.localIP().toString();
    doc["ssid"] = WiFi.SSID();
    calculateNetworkRange();
  }
  
  String response;
  serializeJson(doc, response);
  request->send(200, "application/json", response);
}

void handleStatus(AsyncWebServerRequest *request) {
  DynamicJsonDocument doc(512);
  doc["connected"] = (WiFi.status() == WL_CONNECTED);
  
  if (WiFi.status() == WL_CONNECTED) {
    doc["ssid"] = WiFi.SSID();
    doc["ip"] = WiFi.localIP().toString();
    doc["rssi"] = WiFi.RSSI();
    doc["gateway"] = WiFi.gatewayIP().toString();
    doc["dns"] = WiFi.dnsIP().toString();
  }
  
  String response;
  serializeJson(doc, response);
  request->send(200, "application/json", response);
}

void handleDevices(AsyncWebServerRequest *request) {
  DynamicJsonDocument doc(2048);
  JsonArray devices = doc.createNestedArray("devices");
  
  // Agregar información del propio dispositivo
  JsonObject selfDevice = devices.createNestedObject();
  selfDevice["ip"] = WiFi.localIP().toString();
  selfDevice["type"] = "Self (ESP32-S3)";
  selfDevice["active"] = true;
  selfDevice["mac"] = WiFi.macAddress();
  selfDevice["hostname"] = WiFi.getHostname();
  
  // Agregar dispositivos detectados
  for (const auto &device : detectedDevices) {
    if (device.active) {
      JsonObject deviceObj = devices.createNestedObject();
      deviceObj["ip"] = device.ip.toString();
      deviceObj["type"] = "Network Device";
      deviceObj["active"] = device.active;
      deviceObj["mac"] = device.mac.length() > 0 ? device.mac : "Unknown";
      deviceObj["lastSeen"] = device.lastSeen;
    }
  }
  
  // Agregar información de la red
  if (WiFi.status() == WL_CONNECTED) {
    doc["networkInfo"]["subnet"] = subnetMask.toString();
    doc["networkInfo"]["network"] = networkAddr.toString();
    doc["networkInfo"]["broadcast"] = broadcastAddr.toString();
    doc["networkInfo"]["gateway"] = WiFi.gatewayIP().toString();
    doc["networkInfo"]["dns"] = WiFi.dnsIP().toString();
  }
  
  doc["networkInfo"]["totalDevices"] = devices.size();
  doc["networkInfo"]["scanTime"] = millis();
  
  String response;
  serializeJson(doc, response);
  request->send(200, "application/json", response);
}

void handleDisconnect(AsyncWebServerRequest *request) {
  WiFi.disconnect();
  connectedSSID = "";
  detectedDevices.clear();
  
  Serial.println("Desconectado de WiFi");
  
  request->send(200, "application/json", "{\"success\":true}");
}

bool connectToWiFi(String ssid, String password) {
  Serial.println("Conectando a: " + ssid);
  
  WiFi.begin(ssid.c_str(), password.c_str());
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConectado exitosamente!");
    Serial.print("IP asignada: ");
    Serial.println(WiFi.localIP());
    Serial.print("Gateway: ");
    Serial.println(WiFi.gatewayIP());
    Serial.print("DNS: ");
    Serial.println(WiFi.dnsIP());
    
    connectedSSID = ssid;
    deviceIP = WiFi.localIP();
    calculateNetworkRange();
    
    return true;
  } else {
    Serial.println("\nFalló la conexión");
    return false;
  }
}

void calculateNetworkRange() {
  uint32_t ip = (uint32_t)deviceIP;
  uint32_t mask = (uint32_t)subnetMask;
  
  uint32_t network = ip & mask;
  uint32_t broadcast = network | (~mask);
  
  networkAddr = IPAddress(network);
  broadcastAddr = IPAddress(broadcast);
  
  Serial.println("Rango de red calculado:");
  Serial.print("Red: ");
  Serial.println(networkAddr);
  Serial.print("Broadcast: ");
  Serial.println(broadcastAddr);
  Serial.print("Dispositivos posibles: ");
  Serial.println((broadcast - network - 1));
}

void scanNetworkDevices() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }
  
  Serial.println("Escaneando dispositivos en la red...");
  
  uint32_t network = (uint32_t)networkAddr;
  uint32_t broadcast = (uint32_t)broadcastAddr;
  
  for (auto &device : detectedDevices) {
    device.active = false;
  }
  
  int devicesFound = 0;
  
  for (uint32_t ip = network + 1; ip < broadcast; ip++) {
    IPAddress targetIP(ip);
    
    if (targetIP == deviceIP) continue;
    
    if (Ping.ping(targetIP, 1)) {
      auto it = std::find_if(detectedDevices.begin(), detectedDevices.end(),
        [&targetIP](const NetworkDevice& device) {
          return device.ip == targetIP;
        });
      
      if (it != detectedDevices.end()) {
        it->active = true;
        it->lastSeen = millis();
      } else {
        NetworkDevice newDevice;
        newDevice.ip = targetIP;
        newDevice.mac = "Unknown";
        newDevice.active = true;
        newDevice.lastSeen = millis();
        detectedDevices.push_back(newDevice);
      }
      devicesFound++;
    }
    delay(100);
  }
  
  detectedDevices.erase(
    std::remove_if(detectedDevices.begin(), detectedDevices.end(),
      [](const NetworkDevice& device) {
        return !device.active && (millis() - device.lastSeen > 60000);
      }),
    detectedDevices.end()
  );
  
  Serial.printf("Escaneo completado. Dispositivos activos: %d\n", devicesFound);
}
