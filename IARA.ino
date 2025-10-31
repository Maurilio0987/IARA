#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// Wi-Fi
const char* ssid = "Dalvanir_TCM";
const char* senha = "510152030";

// Servidor Flask
//const char* servidor = "https://iara-k3zh.onrender.com";
const char* servidor = "http://192.168.3.41:5678";
const char* chave_horta = "f22c19ff-5c18-4d10-9754-5bf030e2c2cc";
const int HTTP_TIMEOUT = 5000; 

// Pinos
#define DHTPIN 35
#define DHTTYPE DHT11
#define SOIL_PIN 33
#define LED_WIFI 2
#define PINO_FLUXO 32
#define PINO_VALVULA 14
#define LED_VALVULA 26
#define RELE_IRRIGACAO 5

// Vazão do sensor (ml por pulso)
#define VAZAO 4.5

DHT dht(DHTPIN, DHTTYPE);

// Controle irrigação
volatile int pulsos = 0;
float litros_irrigados = 0.0;
float litros_meta = 0;
bool irrigando = false;
float litros_enviados = 0.0; // <<< CORREÇÃO: Variável movida para o escopo global

// Mutex para proteger a variável 'pulsos'
portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

// Temporizadores
unsigned long ultimo_envio_irrigado = 0;
unsigned long ultimo_envio_sensores = 0;
const unsigned long INTERVALO_SENSORES = 15000; // 15s

// Temporizadores para reconexão Wi-Fi
unsigned long ultimo_check_wifi = 0;
const unsigned long INTERVALO_WIFI_CHECK = 10000; // 10s

// NOVO: Temporizador para log de status
unsigned long ultimo_log_status = 0;
const unsigned long INTERVALO_LOG_STATUS = 5000; // Log de status a cada 5s

void IRAM_ATTR contarPulso() {
  portENTER_CRITICAL_ISR(&mux);
  pulsos++;
  portEXIT_CRITICAL_ISR(&mux);
}

void conectarWiFiInicial() {
  Serial.print("Conectando-se ao Wi-Fi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, senha);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    digitalWrite(LED_WIFI, HIGH);
    delay(250);
    digitalWrite(LED_WIFI, LOW);
    delay(250);
  }

  Serial.println("\nWi-Fi conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
  digitalWrite(LED_WIFI, HIGH);
}

float obterVolumeAIrrigar() {
  if (WiFi.status() != WL_CONNECTED) return 0.0f; 

  HTTPClient http;
  String url = String(servidor) + "/esp32/consumo/" + chave_horta;
  http.begin(url);
  http.setTimeout(HTTP_TIMEOUT); 

  int httpResponseCode = http.GET();
  if (httpResponseCode != 200) {
    // MODIFICADO: Log de erro mais detalhado
    Serial.printf("[HTTP] Erro ao obter irrigação pendente. Código: %d\n", httpResponseCode);
    http.end();
    return 0.0f;
  }

  String resposta = http.getString();
  http.end();

  StaticJsonDocument<256> doc;
  DeserializationError erro = deserializeJson(doc, resposta);
  if (erro) {
    Serial.print("[JSON] Erro ao parsear JSON: "); // MODIFICADO
    Serial.println(erro.c_str());
    return 0.0f;
  }

  float pendente = doc["pendente"] | 0.0f; 

  // Esta mensagem só aparece quando uma meta > 0 é recebida
  if (pendente > 0) {
    Serial.printf("[HTTP] Meta recebida do servidor: %.2f L\n", pendente); // MODIFICADO
  }

  if (pendente <= 0.0f) {
    return 0.0f; 
  }

  return pendente; 
}


void enviarDados(float temperatura, float umidade_ar, int umidade_solo) {
  if (WiFi.status() != WL_CONNECTED) return; 

  HTTPClient http;
  String url = String(servidor) + "/hortas/" + chave_horta + "/dados";
  http.begin(url);
  http.setTimeout(HTTP_TIMEOUT); 
  http.addHeader("Content-Type", "application/json");

  String json = "{";
  json += "\"temperatura\":" + String(temperatura, 1) + ",";
  json += "\"umidade_ar\":" + String(umidade_ar, 1) + ",";
  json += "\"umidade_solo\":" + String(umidade_solo);
  json += "}";

  int httpResponseCode = http.POST(json);
  
  if (httpResponseCode <= 0) {
    // MODIFICADO: Log de erro mais detalhado
    Serial.printf("[HTTP] Erro ao enviar dados dos sensores. Código: %d\n", httpResponseCode);
  } else {
    Serial.println("[HTTP] Dados dos sensores enviados com sucesso."); // NOVO
  }

  http.end();
}

void enviarVolumeIrrigado(float litros) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = String(servidor) + "/irrigado/" + chave_horta;
  http.begin(url);
  http.setTimeout(HTTP_TIMEOUT); 
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<128> doc;
  doc["irrigado"] = litros;
  String json;
  serializeJson(doc, json);

  int resp = http.POST(json);
  if (resp > 0) {
    // MODIFICADO: Log de sucesso mais detalhado
    Serial.printf("[HTTP] Volume irrigado parcial reportado: %.2f L\n", litros);
  } else {
    // MODIFICADO: Log de erro mais detalhado
    Serial.printf("[HTTP] Erro ao reportar volume irrigado. Código: %d\n", resp);
  }

  http.end();
}

void lerESalvarSensores() {
  float temperatura = dht.readTemperature();
  float umidade_ar = dht.readHumidity();
  //float temperatura = 33.3;
  //float umidade_ar = 70;
  
  int valor_bruto = analogRead(SOIL_PIN);
  int umidade_solo = map(valor_bruto, 0, 4095, 100, 0);

  if (!isnan(temperatura) && !isnan(umidade_ar)) {
    // NOVO: Log de leitura dos sensores
    Serial.printf("[SENSORES] Lendo -> Temp: %.1f°C | Umid Ar: %.1f%% | Solo: %d%%\n", temperatura, umidade_ar, umidade_solo);
    enviarDados(temperatura, umidade_ar, umidade_solo);
  } else {
    Serial.println("[SENSORES] Erro na leitura do DHT"); // MODIFICADO
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n\n--- INICIANDO SISTEMA DE IRRIGACAO ---"); // NOVO
  dht.begin();

  pinMode(PINO_FLUXO, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PINO_FLUXO), contarPulso, RISING);

  pinMode(PINO_VALVULA, OUTPUT);
  pinMode(LED_VALVULA, OUTPUT);
  digitalWrite(PINO_VALVULA, LOW);
  digitalWrite(LED_VALVULA, LOW);
  pinMode(SOIL_PIN, INPUT);
  pinMode(LED_WIFI, OUTPUT);
  pinMode(RELE_IRRIGACAO, OUTPUT);
  digitalWrite(LED_WIFI, LOW);

  WiFi.mode(WIFI_STA);
  conectarWiFiInicial(); 
}

void loop() {
  unsigned long agora = millis(); // NOVO: Definido no início do loop para reuso

  // --- Bloco de gerenciamento de Wi-Fi Não-Bloqueante ---
  if (WiFi.status() != WL_CONNECTED) {
    digitalWrite(LED_WIFI, LOW); 
    
    if (agora - ultimo_check_wifi >= INTERVALO_WIFI_CHECK) {
      ultimo_check_wifi = agora;
      Serial.println("[WIFI] Wi-Fi desconectado. Tentando reconectar..."); // MODIFICADO
    }
  } else {
    if (digitalRead(LED_WIFI) == LOW) {
       Serial.println("[WIFI] Wi-Fi Reconectado!"); // MODIFICADO
       Serial.print("[WIFI] IP: ");
       Serial.println(WiFi.localIP());
    }
    digitalWrite(LED_WIFI, HIGH);
    ultimo_check_wifi = agora; 
  }
  // --- Fim do Bloco de Wi-Fi ---

  // NOVO: Bloco de Log de Status Periódico
  if (agora - ultimo_log_status >= INTERVALO_LOG_STATUS) {
    ultimo_log_status = agora;
    if (irrigando) {
      // Se está irrigando, mostra o progresso
      Serial.printf("[STATUS] Irrigando: %.2f L / %.2f L\n", litros_irrigados, litros_meta);
    } else {
      // Se está ocioso, apenas informa
      Serial.println("[STATUS] Ocioso. Verificando tarefas...");
    }
  }
  // --- Fim do Bloco de Log de Status ---


  // <<< CORREÇÃO: A linha 'float litros_enviados = 0.0;' foi removida daqui

  if (!irrigando) {
    litros_meta = obterVolumeAIrrigar();
    
    if (litros_meta > 0) {
      portENTER_CRITICAL(&mux);
      pulsos = 0;
      portEXIT_CRITICAL(&mux);

      litros_irrigados = 0.0;
      litros_enviados = 0.0; // Resetado para 0 no INÍCIO da irrigação
      irrigando = true;
      digitalWrite(PINO_VALVULA, HIGH);
      digitalWrite(LED_VALVULA, HIGH);
      Serial.printf("[IRRIGACAO] Iniciando irrigação: %.2f L\n", litros_meta); // MODIFICADO
      
      // NOVO: Reseta o timer de log para mostrar o status "Irrigando" imediatamente
      ultimo_log_status = agora; 
      Serial.printf("[STATUS] Irrigando: 0.00 L / %.2f L\n", litros_meta);
    }
  } else {
    int pulsos_copia; 
    portENTER_CRITICAL(&mux);
    pulsos_copia = pulsos;
    portEXIT_CRITICAL(&mux);

    litros_irrigados = pulsos_copia * (VAZAO / 1000.0); // L

    // MODIFICADO: 'agora' já foi definido no topo do loop
    if (agora - ultimo_envio_irrigado > 5000) { // A cada 5s
      ultimo_envio_irrigado = agora;
      float delta = litros_irrigados - litros_enviados;
      if (delta >= 0.1) { 
        enviarVolumeIrrigado(delta); 
        litros_enviados += delta;
      }
    }

    if (litros_irrigados >= litros_meta) {
      irrigando = false;
      digitalWrite(PINO_VALVULA, LOW);
      digitalWrite(LED_VALVULA, LOW);
      Serial.println("[IRRIGACAO] Irrigação concluída"); // MODIFICADO

      float delta = litros_irrigados - litros_enviados;
      if (delta > 0.001) {
        Serial.println("[IRRIGACAO] Reportando volume final..."); // NOVO
        enviarVolumeIrrigado(delta);
      }
      
      litros_meta = 0; 
      
      // NOVO: Reseta o timer de log para mostrar o status "Ocioso" imediatamente
      ultimo_log_status = agora;
      Serial.println("[STATUS] Ocioso. Verificando tarefas...");
    }
  }

  // MODIFICADO: 'agora' já foi definido no topo do loop
  if (agora - ultimo_envio_sensores >= INTERVALO_SENSORES) {
    ultimo_envio_sensores = agora;
    lerESalvarSensores();
  }

  delay(100);
}