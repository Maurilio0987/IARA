#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// Wi-Fi
const char* ssid = "IARA";
const char* senha = "IARACYMA";

// Servidor Flask
const char* servidor = "https://iara-k3zh.onrender.com";
const char* chave_horta = "f22c19ff-5c18-4d10-9754-5bf030e2c2cc";

// Pinos
#define DHTPIN 4
#define DHTTYPE DHT11
#define SOIL_PIN 34
#define LED_WIFI 2
#define PINO_FLUXO 27
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

// Temporizadores
unsigned long ultimo_envio_irrigado = 0;
unsigned long ultimo_envio_sensores = 0;
const unsigned long INTERVALO_SENSORES = 15000; // 15s

void IRAM_ATTR contarPulso() {
  pulsos++;
}

void conectarWiFi() {
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
  if (WiFi.status() != WL_CONNECTED) return 0.0f;  // Retorna 0 se não estiver conectado

  HTTPClient http;
  String url = String(servidor) + "/esp32/consumo/" + chave_horta;
  http.begin(url);

  int httpResponseCode = http.GET();
  if (httpResponseCode != 200) {
    Serial.println("Erro ao obter irrigação pendente");
    http.end();
    return 0.0f;  // Retorna 0 se houver erro na requisição
  }

  String resposta = http.getString();
  http.end();

  StaticJsonDocument<256> doc;
  DeserializationError erro = deserializeJson(doc, resposta);
  if (erro) {
    Serial.print("Erro ao parsear JSON: ");
    Serial.println(erro.c_str());
    return 0.0f;  // Retorna 0 se houver erro ao parsear o JSON
  }

  // Obtém o valor do campo "pendente" diretamente da resposta
  float pendente = doc["pendente"] | 0.0f;  // Valor de irrigação pendente como float

  // Exibe o valor retornado para depuração
  Serial.print("Pendentes para irrigação: ");
  Serial.println(pendente);

  // Ajuste de verificação para garantir que não seja zero (também pode incluir valores menores que 0.01)
  if (pendente <= 0.0f) {
    Serial.println("Pendentes inválidos, retornando 0.0");
    return 0.0f;  // Garantir que o valor seja 0 se pendente for 0 ou negativo
  }

  // Retorna o valor a irrigar sem alterações
  return pendente;  // Retorna o valor diretamente
}


void enviarDados(float temperatura, float umidade_ar, int umidade_solo) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = String(servidor) + "/hortas/" + chave_horta + "/dados";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  String json = "{";
  json += "\"temperatura\":" + String(temperatura, 1) + ",";
  json += "\"umidade_ar\":" + String(umidade_ar, 1) + ",";
  json += "\"umidade_solo\":" + String(umidade_solo);
  json += "}";

  int httpResponseCode = http.POST(json);
  //Serial.print("POST status: ");
  //Serial.println(httpResponseCode);

  if (httpResponseCode > 0) {
    String response = http.getString();
    //Serial.println("Resposta: " + response);
  } else {
    Serial.println("Erro ao enviar dados");
  }

  http.end();
}

void enviarVolumeIrrigado(float litros) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = String(servidor) + "/irrigado/" + chave_horta;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<128> doc;
  doc["irrigado"] = litros;
  String json;
  serializeJson(doc, json);

  int resp = http.POST(json);
  if (resp > 0) {
    Serial.println("Volume irrigado enviado");
  } else {
    Serial.println("Erro ao enviar volume irrigado");
  }

  http.end();
}

void lerESalvarSensores() {
  float temperatura = dht.readTemperature();
  float umidade_ar = dht.readHumidity();
  int valor_bruto = analogRead(SOIL_PIN);
  int umidade_solo = map(valor_bruto, 0, 4095, 0, 100);

  if (!isnan(temperatura) && !isnan(umidade_ar)) {
    //Serial.printf("Temp: %.1f°C | Umidade Ar: %.1f%% | Solo: %d%%\n", temperatura, umidade_ar, umidade_solo);
    enviarDados(temperatura, umidade_ar, umidade_solo);
  } else {
    Serial.println("Erro na leitura do DHT");
  }
}

void setup() {
  Serial.begin(115200);
  dht.begin();

  pinMode(PINO_FLUXO, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PINO_FLUXO), contarPulso, RISING);

  pinMode(PINO_VALVULA, OUTPUT);
  pinMode(LED_VALVULA, OUTPUT);
  digitalWrite(PINO_VALVULA, LOW);
  digitalWrite(LED_VALVULA, LOW);

  pinMode(LED_WIFI, OUTPUT);
  pinMode(RELE_IRRIGACAO, OUTPUT);
  digitalWrite(LED_WIFI, LOW);

  WiFi.mode(WIFI_STA);
  conectarWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    digitalWrite(LED_WIFI, LOW);
    conectarWiFi();
  }

  float litros_enviados = 0.0;  // Total já enviado

  // Verifica se não está irrigando
  if (!irrigando) {
    litros_meta = obterVolumeAIrrigar();
    Serial.println(litros_meta);
    // Se houver volume para irrigar
    if (litros_meta > 0) {
      pulsos = 0;
      litros_irrigados = 0.0;
      litros_enviados = 0.0;  // Reset
      irrigando = true;
      digitalWrite(PINO_VALVULA, HIGH);
      digitalWrite(LED_VALVULA, HIGH);
      Serial.printf("Iniciando irrigação: %.2f L\n", litros_meta); // Usando %.2f para mostrar 2 casas decimais
    }
  } else {
    litros_irrigados = pulsos * (VAZAO / 1000.0); // L

    unsigned long agora = millis();
    if (agora - ultimo_envio_irrigado > 5000) { // A cada 5s
      ultimo_envio_irrigado = agora;

      // Calcula o delta de litros irrigados (evita o envio de dados repetidos)
      float delta = litros_irrigados - litros_enviados;
      if (delta >= 0.01) {  // Evita ruído menor que 10ml
        enviarVolumeIrrigado(delta);
        litros_enviados += delta;
      }
    }

    // Se a irrigação atingir a meta
    if (litros_irrigados >= litros_meta) {
      irrigando = false;
      digitalWrite(PINO_VALVULA, LOW);
      digitalWrite(LED_VALVULA, LOW);
      Serial.println("Irrigação concluída");

      // Envio final (se ficou algo não enviado por arredondamento)
      float delta = litros_irrigados - litros_enviados;
      if (delta > 0.001) {
        enviarVolumeIrrigado(delta);
      }

      // Reseta a irrigação para permitir novo ciclo
      // Isso garante que o sistema esteja pronto para irrigar novamente quando houver necessidade
      litros_meta = 0;  // Reset após conclusão da irrigação
    }
  }

  // A cada intervalo, lê e envia dados dos sensores
  if (millis() - ultimo_envio_sensores >= INTERVALO_SENSORES) {
    ultimo_envio_sensores = millis();
    lerESalvarSensores();
  }

  delay(100);
}
