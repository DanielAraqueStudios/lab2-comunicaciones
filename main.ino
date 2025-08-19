#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <ESPping.h>
#include <vector>
#include <set>

// Configuración del servidor web
WebServer server(80);

// Variables globales
String connectedSSID = "";
IPAddress deviceIP;
IPAddress subnetMask(255, 255, 255, 240);
IPAddress networkAddr;
IPAddress broadcastAddr;
unsigned long lastScan = 0;
unsigned long SCAN_INTERVAL = 5000; // 5 segundos por defecto, configurable
unsigned long lastWiFiScan = 0;
const unsigned long WIFI_SCAN_INTERVAL = 30000; // Escanear WiFi cada 30 segundos

// Estructura para almacenar dispositivos detectados
struct NetworkDevice {
  IPAddress ip;
  String mac;
  String hostname;
  bool active;
  unsigned long lastSeen;
  unsigned long firstSeen;
  int responseTime;
};

// Estructura para almacenar redes WiFi únicas
struct WiFiNetwork {
  String ssid;
  int32_t rssi;
  String encryption;
  int32_t channel;
  String bssid;
};

std::vector<NetworkDevice> detectedDevices;
std::set<String> uniqueSSIDs; // Para evitar SSIDs duplicados

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("Inicializando ESP32-S3 WiFi Scanner Mejorado...");
  
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
  server.handleClient();
  
  // Actualizar escaneo de dispositivos según intervalo configurado
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
  server.enableCORS(true);
  
  // Endpoint para obtener redes WiFi disponibles (mejorado)
  server.on("/scan", HTTP_GET, handleScanWiFi);
  
  // Endpoint para conectar a una red WiFi
  server.on("/connect", HTTP_POST, handleConnect);
  
  // Endpoint para obtener estado de conexión
  server.on("/status", HTTP_GET, handleStatus);
  
  // Endpoint para obtener dispositivos detectados en la red
  server.on("/devices", HTTP_GET, handleDevices);
  
  // Endpoint para desconectar WiFi
  server.on("/disconnect", HTTP_POST, handleDisconnect);
  
  // Nuevo endpoint para configurar intervalo de escaneo
  server.on("/configure", HTTP_POST, handleConfigure);
  
  // Endpoint para obtener configuración actual
  server.on("/config", HTTP_GET, handleGetConfig);
  
  // Manejar preflight OPTIONS requests para CORS
  server.on("/scan", HTTP_OPTIONS, handleCORS);
  server.on("/connect", HTTP_OPTIONS, handleCORS);
  server.on("/status", HTTP_OPTIONS, handleCORS);
  server.on("/devices", HTTP_OPTIONS, handleCORS);
  server.on("/disconnect", HTTP_OPTIONS, handleCORS);
  server.on("/configure", HTTP_OPTIONS, handleCORS);
  server.on("/config", HTTP_OPTIONS, handleCORS);
  
  // Iniciar servidor
  server.begin();
  Serial.println("Servidor web iniciado en puerto 80");
}

void handleCORS() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
  server.send(200, "text/plain", "");
}

void handleScanWiFi() {
  Serial.println("Escaneando redes WiFi...");
  
  server.sendHeader("Access-Control-Allow-Origin", "*");
  
  // Limpiar lista de SSIDs únicos
  uniqueSSIDs.clear();
  
  int n = WiFi.scanNetworks(false, true); // async=false, show_hidden=true
  
  DynamicJsonDocument doc(6144);
  JsonArray networks = doc.createNestedArray("networks");
  
  // Usar vector para almacenar redes únicas por SSID
  std::vector<WiFiNetwork> uniqueNetworks;
  
  for (int i = 0; i < n; i++) {
    String ssid = WiFi.SSID(i);
    
    // Saltar redes sin SSID (ocultas vacías)
    if (ssid.length() == 0) continue;
    
    // Verificar si ya tenemos una red con este SSID
    bool found = false;
    for (int j = 0; j < uniqueNetworks.size(); j++) {
      if (uniqueNetworks[j].ssid == ssid) {
        // Si encontramos el mismo SSID, mantener el que tenga mejor señal
        if (WiFi.RSSI(i) > uniqueNetworks[j].rssi) {
          uniqueNetworks[j].rssi = WiFi.RSSI(i);
          uniqueNetworks[j].encryption = (WiFi.encryptionType(i) == WIFI_AUTH_OPEN) ? "Open" : "Secured";
          uniqueNetworks[j].channel = WiFi.channel(i);
          uniqueNetworks[j].bssid = WiFi.BSSIDstr(i);
        }
        found = true;
        break;
      }
    }
    
    // Si no se encontró, agregar como nueva red
    if (!found) {
      WiFiNetwork newNetwork;
      newNetwork.ssid = ssid;
      newNetwork.rssi = WiFi.RSSI(i);
      newNetwork.encryption = (WiFi.encryptionType(i) == WIFI_AUTH_OPEN) ? "Open" : "Secured";
      newNetwork.channel = WiFi.channel(i);
      newNetwork.bssid = WiFi.BSSIDstr(i);
      uniqueNetworks.push_back(newNetwork);
    }
  }
  
  // Ordenar por intensidad de señal (mayor a menor)
  std::sort(uniqueNetworks.begin(), uniqueNetworks.end(), 
    [](const auto& a, const auto& b) {
      return a.rssi > b.rssi;
    });
  
  // Agregar redes únicas al JSON
  for (const auto& network : uniqueNetworks) {
    JsonObject netObj = networks.createNestedObject();
    netObj["ssid"] = network.ssid;
    netObj["rssi"] = network.rssi;
    netObj["encryption"] = network.encryption;
    netObj["channel"] = network.channel;
    netObj["bssid"] = network.bssid;
    
    // Calcular calidad de señal
    String quality;
    if (network.rssi > -50) quality = "Excelente";
    else if (network.rssi > -60) quality = "Buena";
    else if (network.rssi > -70) quality = "Regular";
    else quality = "Débil";
    netObj["quality"] = quality;
    
    Serial.printf("Red única encontrada: %s (%d dBm, %s, Ch:%d)\n", 
                  network.ssid.c_str(), network.rssi, quality.c_str(), network.channel);
  }
  
  doc["totalNetworks"] = uniqueNetworks.size();
  doc["scanTime"] = millis();
  
  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
  
  Serial.printf("Escaneo completado. Redes únicas encontradas: %d\n", uniqueNetworks.size());
}

void handleConnect() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  
  if (!server.hasArg("ssid")) {
    server.send(400, "application/json", "{\"error\":\"Missing SSID parameter\"}");
    return;
  }
  
  String ssid = server.arg("ssid");
  String password = server.hasArg("password") ? server.arg("password") : "";
  
  Serial.println("Intentando conectar a: " + ssid);
  
  bool success = connectToWiFi(ssid, password);
  
  DynamicJsonDocument doc(512);
  doc["success"] = success;
  
  if (success) {
    doc["ip"] = WiFi.localIP().toString();
    doc["ssid"] = WiFi.SSID();
    doc["gateway"] = WiFi.gatewayIP().toString();
    doc["dns"] = WiFi.dnsIP().toString();
    doc["rssi"] = WiFi.RSSI();
    calculateNetworkRange();
  }
  
  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
}

void handleStatus() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  
  DynamicJsonDocument doc(512);
  doc["connected"] = (WiFi.status() == WL_CONNECTED);
  
  if (WiFi.status() == WL_CONNECTED) {
    doc["ssid"] = WiFi.SSID();
    doc["ip"] = WiFi.localIP().toString();
    doc["rssi"] = WiFi.RSSI();
    doc["gateway"] = WiFi.gatewayIP().toString();
    doc["dns"] = WiFi.dnsIP().toString();
    doc["bssid"] = WiFi.BSSIDstr();
    doc["channel"] = WiFi.channel();
    
    // Calcular tiempo de conexión
    doc["uptime"] = millis();
  }
  
  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
}

void handleDevices() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  
  DynamicJsonDocument doc(4096);
  JsonArray devices = doc.createNestedArray("devices");
  
  // Agregar información del propio dispositivo
  JsonObject selfDevice = devices.createNestedObject();
  selfDevice["ip"] = WiFi.localIP().toString();
  selfDevice["type"] = "ESP32-S3 Scanner";
  selfDevice["active"] = true;
  selfDevice["mac"] = WiFi.macAddress();
  selfDevice["hostname"] = WiFi.getHostname();
  selfDevice["responseTime"] = 0;
  selfDevice["uptime"] = millis();
  
  // Agregar dispositivos detectados (únicos por IP)
  std::set<String> seenIPs;
  for (const auto &device : detectedDevices) {
    String ipStr = device.ip.toString();
    
    // Solo agregar si no hemos visto esta IP y está activa
    if (device.active && seenIPs.find(ipStr) == seenIPs.end()) {
      seenIPs.insert(ipStr);
      
      JsonObject deviceObj = devices.createNestedObject();
      deviceObj["ip"] = ipStr;
      deviceObj["type"] = "Network Device";
      deviceObj["active"] = device.active;
      deviceObj["mac"] = device.mac.length() > 0 ? device.mac : "Unknown";
      deviceObj["hostname"] = device.hostname.length() > 0 ? device.hostname : "Unknown";
      deviceObj["lastSeen"] = device.lastSeen;
      deviceObj["firstSeen"] = device.firstSeen;
      deviceObj["responseTime"] = device.responseTime;
      
      // Calcular tiempo online
      unsigned long onlineTime = device.lastSeen - device.firstSeen;
      deviceObj["onlineTime"] = onlineTime;
    }
  }
  
  // Agregar información de la red
  if (WiFi.status() == WL_CONNECTED) {
    JsonObject networkInfo = doc.createNestedObject("networkInfo");
    networkInfo["subnet"] = subnetMask.toString();
    networkInfo["network"] = networkAddr.toString();
    networkInfo["broadcast"] = broadcastAddr.toString();
    networkInfo["gateway"] = WiFi.gatewayIP().toString();
    networkInfo["dns"] = WiFi.dnsIP().toString();
    networkInfo["ssid"] = WiFi.SSID();
    networkInfo["channel"] = WiFi.channel();
    networkInfo["rssi"] = WiFi.RSSI();
  }
  
  doc["totalDevices"] = devices.size();
  doc["scanInterval"] = SCAN_INTERVAL;
  doc["scanTime"] = millis();
  doc["activeDevices"] = seenIPs.size();
  
  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
}

void handleDisconnect() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  
  WiFi.disconnect();
  connectedSSID = "";
  detectedDevices.clear();
  
  Serial.println("Desconectado de WiFi");
  
  server.send(200, "application/json", "{\"success\":true}");
}

void handleConfigure() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  
  if (server.hasArg("scanInterval")) {
    unsigned long newInterval = server.arg("scanInterval").toInt();
    if (newInterval >= 1000 && newInterval <= 60000) { // Entre 1 y 60 segundos
      SCAN_INTERVAL = newInterval;
      Serial.printf("Intervalo de escaneo actualizado a: %lu ms\n", SCAN_INTERVAL);
    }
  }
  
  DynamicJsonDocument doc(256);
  doc["success"] = true;
  doc["scanInterval"] = SCAN_INTERVAL;
  
  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
}

void handleGetConfig() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  
  DynamicJsonDocument doc(512);
  doc["scanInterval"] = SCAN_INTERVAL;
  doc["wifiScanInterval"] = WIFI_SCAN_INTERVAL;
  doc["subnetMask"] = subnetMask.toString();
  doc["freeHeap"] = ESP.getFreeHeap();
  doc["uptime"] = millis();
  doc["version"] = "2.0.0";
  
  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
}

bool connectToWiFi(String ssid, String password) {
  Serial.println("Conectando a: " + ssid);
  
  WiFi.begin(ssid.c_str(), password.c_str());
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(1000);
    Serial.print(".");
    attempts++;
    
    // Permitir que el servidor web siga funcionando durante la conexión
    server.handleClient();
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n¡Conectado exitosamente!");
    Serial.printf("SSID: %s\n", WiFi.SSID().c_str());
    Serial.printf("IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("Gateway: %s\n", WiFi.gatewayIP().toString().c_str());
    Serial.printf("DNS: %s\n", WiFi.dnsIP().toString().c_str());
    Serial.printf("RSSI: %d dBm\n", WiFi.RSSI());
    Serial.printf("Canal: %d\n", WiFi.channel());
    Serial.printf("BSSID: %s\n", WiFi.BSSIDstr().c_str());
    
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
  // Calcular rango de red con máscara 255.255.255.240 (/28)
  uint32_t ip = (uint32_t)deviceIP;
  uint32_t mask = (uint32_t)subnetMask;
  
  uint32_t network = ip & mask;
  uint32_t broadcast = network | (~mask);
  
  networkAddr = IPAddress(network);
  broadcastAddr = IPAddress(broadcast);
  
  Serial.println("Rango de red calculado:");
  Serial.printf("Red: %s\n", networkAddr.toString().c_str());
  Serial.printf("Broadcast: %s\n", broadcastAddr.toString().c_str());
  Serial.printf("Dispositivos posibles: %d\n", (int)(broadcast - network - 1));
  Serial.printf("Intervalo de escaneo: %lu ms\n", SCAN_INTERVAL);
}

void scanNetworkDevices() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }
  
  Serial.printf("Escaneando dispositivos (intervalo: %lu ms)...\n", SCAN_INTERVAL);
  
  uint32_t network = (uint32_t)networkAddr;
  uint32_t broadcast = (uint32_t)broadcastAddr;
  
  // Marcar todos los dispositivos como no activos
  for (auto &device : detectedDevices) {
    device.active = false;
  }
  
  int devicesFound = 0;
  unsigned long scanStartTime = millis();
  
  // Escanear rango de IPs (excluyendo dirección de red y broadcast)
  for (uint32_t ip = network + 1; ip < broadcast; ip++) {
    IPAddress targetIP(ip);
    
    // Saltar nuestra propia IP
    if (targetIP == deviceIP) continue;
    
    // Permitir que el servidor web siga funcionando
    server.handleClient();
    
    // Hacer ping con timeout más corto para escaneo rápido
    unsigned long pingStart = millis();
    if (Ping.ping(targetIP, 1)) {
      unsigned long responseTime = millis() - pingStart;
      
      Serial.printf("Dispositivo encontrado: %s (%lu ms)\n", 
                    targetIP.toString().c_str(), responseTime);
      devicesFound++;
      
      // Buscar si ya existe en la lista
      bool found = false;
      for (auto &device : detectedDevices) {
        if (device.ip == targetIP) {
          device.active = true;
          device.lastSeen = millis();
          device.responseTime = responseTime;
          found = true;
          break;
        }
      }
      
      // Si no existe, agregarlo
      if (!found) {
        NetworkDevice newDevice;
        newDevice.ip = targetIP;
        newDevice.mac = getARPInfo(targetIP); // Mejorar con ARP real
        newDevice.hostname = "Unknown";
        newDevice.active = true;
        newDevice.lastSeen = millis();
        newDevice.firstSeen = millis();
        newDevice.responseTime = responseTime;
        detectedDevices.push_back(newDevice);
      }
    }
    
    // Pausa más corta para escaneo rápido
    delay(50);
  }
  
  // Remover dispositivos inactivos después de 2 minutos
  detectedDevices.erase(
    std::remove_if(detectedDevices.begin(), detectedDevices.end(),
      [](const NetworkDevice& device) {
        return !device.active && (millis() - device.lastSeen > 120000);
      }),
    detectedDevices.end()
  );
  
  unsigned long scanDuration = millis() - scanStartTime;
  Serial.printf("Escaneo completado en %lu ms. Dispositivos activos: %d\n", 
                scanDuration, devicesFound);
}

// Función auxiliar para obtener información ARP (simplificada)
String getARPInfo(IPAddress ip) {
  // En una implementación completa, consultarías la tabla ARP
  // Por ahora retornamos información básica
  return "Unknown";
}