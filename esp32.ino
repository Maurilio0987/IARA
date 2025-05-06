#include <WiFi.h>
#include <HTTPClient.h>

// ----- CONFIGURAÇÕES -----
const char* ssid = "ECOLOGIC";
const char* password = "JUAN1234";
const char* chave = "6027b14b-2879-11f0-92cc-a2aaabbee758";  // Substitua pela chave da horta
const char* servidor = "https://iara-k3zh.onrender.com/"; // sem a chave no final


const unsigned long intervalo = 15UL * 60UL * 1000UL; // 15 minutos em ms

// Pinos
const int PINO_VALVULA = 5; // Rele ligado à válvula solenoide
const int PINO_FLUXO = 4;   // YF-S201

// Sensor de fluxo
volatile int pulsos = 0;
float fatorCalibracao = 7.5; // Calibrar conforme necessário

unsigned long ultimoTempo = 0;

void IRAM_ATTR contarPulso() {
  pulsos++;
}

void conectarWiFi() {
  Serial.print("Conectando ao Wi-Fi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi conectado");
}

void liberarAgua(float volumeDesejadoL) {
  pulsos = 0;
  float litrosEntregues = 0;
  unsigned long tempoInicio = millis();

  attachInterrupt(digitalPinToInterrupt(PINO_FLUXO), contarPulso, RISING);
  digitalWrite(PINO_VALVULA, HIGH); // Liga a válvula
  Serial.println("Válvula ativada");

  while (litrosEntregues < volumeDesejadoL && millis() - tempoInicio < 60000) {
    delay(1000); // a cada segundo
    litrosEntregues = (pulsos / (fatorCalibracao * 60.0)); // L/min
    Serial.print("Volume atual: ");
    Serial.print(litrosEntregues, 3);
    Serial.println(" L");
  }

  detachInterrupt(digitalPinToInterrupt(PINO_FLUXO));
  digitalWrite(PINO_VALVULA, LOW); // Desliga a válvula
  Serial.println("Irrigação encerrada.");

  // Envia volume irrigado (em litros) com tentativas infinitas
  if (WiFi.status() == WL_CONNECTED) {
    bool enviado = false;

    while (!enviado) {
      HTTPClient http;
      String url = String(servidor) + "esp32/" + chave + "/irrigado";
      http.begin(url);
      http.addHeader("Content-Type", "application/json");

      String json = "{\"volume_irrigado\": " + String(litrosEntregues, 2) + "}";
      Serial.println(json);
      int httpResponseCode = http.POST(json);

      Serial.print("Tentativa de envio /irrigado: ");
      Serial.println(httpResponseCode);

      if (httpResponseCode > 0) {
        Serial.println("Volume irrigado enviado com sucesso!");
        Serial.println(http.getString());
        enviado = true;
      } else {
        Serial.println("Falha no envio. Tentando novamente em 5 segundos...");
        delay(5000); // espera 5 segundos antes de tentar novamente
      }

      http.end();
    }
    } else {
      Serial.println("WiFi desconectado. Não foi possível enviar volume irrigado.");
    }
}


void requisitarVolume() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(servidor) + "esp32/" + chave + "/volume";
    Serial.print("Requisitando: ");
    Serial.println(url);

    http.begin(url);
    int httpCode = http.GET();

    if (httpCode == 200) {
      String payload = http.getString();
      Serial.print("Resposta: ");
      Serial.println(payload);

      int volStart = payload.indexOf("\"volume\":") + 9;
      int volEnd = payload.indexOf(",", volStart);
      float volume = payload.substring(volStart, volEnd).toFloat();

      int irriStart = payload.indexOf("\"volume_irrigado\":") + 19;
      int irriEnd = payload.indexOf("}", irriStart);
      float volumeIrrigado = payload.substring(irriStart, irriEnd).toFloat();

      float volumeRestante = volume - volumeIrrigado;

      Serial.print("Volume restante a irrigar: ");
      Serial.print(volumeRestante, 3);
      Serial.println(" L");

      if (volumeRestante > 0) {
        liberarAgua(volumeRestante); // já está em litros
      } else {
        Serial.println("Nenhuma irrigação necessária.");
      }

    } else {
      Serial.print("Erro HTTP: ");
      Serial.println(httpCode);
      requisitarVolume();
    }

    http.end();
  } else {
    Serial.println("WiFi desconectado. Tentando reconectar...");
    conectarWiFi();
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PINO_VALVULA, OUTPUT);
  digitalWrite(PINO_VALVULA, LOW);
  pinMode(PINO_FLUXO, INPUT);

  conectarWiFi();
  ultimoTempo = millis() - intervalo; // Para executar logo ao iniciar
}

void loop() {
  unsigned long agora = millis();
  if (agora - ultimoTempo >= intervalo) {
    ultimoTempo = agora;
    requisitarVolume();
  }
}
