//#include <SoftwareSerial.h>
#include <TinyGPS.h>
#include <SPI.h>
#include <RH_RF95.h>

static void flushSerial();
static String substring(char set[], int start, int len);
static void smartdelay(unsigned long ms);
static void addline(String &base, char* addition);

/* Modo de simulación.
Existen 3 modos de simulación del sensor de gas natural, dependiendo del valor
asignado a SENSOR_MODE
  0: Funcionamiento normal, el sensor recibe y transmite datos por el puerto serie.
  1: Sensor simulado, nos comunicamos mediante el puerto serie con un sensor simulado
    y también enviamos información del estado mediante ese mismo puerto serie.
  2: No sensor, los datos del sensor se generan de manera interna al arduino sin ninguna
    conexión externa.
*/
#define SENSOR_MODE 0
#define WAIT_FOR_FIX 0
#define SENSOR_SERIAL Serial
#define GPS_SERIAL Serial1


#define TX_TIME 12000

/*
Cada dispositivo puede tener una ID de 0 a 254 según el protocolo LoRa. No es
imprescindible que la ID sea única a no ser que se quiera implementar comunicación
sólo con este dispositivo y ninguno más. y no hay código en este proyecto que
haga uso de esta información. Sólo se define para facilitar futuras modificaciones.
*/
#define DEVICE_ID 1

//Para la representación en el propio dispositivo, definimos los leds y los niveles
//a los que se encienden.
#define GREEN_LED 13
#define GREEN_ALERT 100

#define YELLOW_LED 12
#define YELLOW_ALERT 1000

#define RED_LED 11
#define RED_ALERT 25000

#if SENSOR_MODE == 2
//Test class, this makes up values instead of getting them from the serial port.
class GasMeter
{

  int index = 0;
  unsigned long values[7] = {0, 100, 1000, 10000, 25000,45000,50000};
public:
  void initialize(){
  }
  bool get_reading(unsigned long &resultado){
    resultado = values[index];
    index++;
    if (index >= 7) index = 0;
    return true;
  }
};

#else
class GasMeter
{
  public:
    void initialize(){
      SENSOR_SERIAL.begin(38400,SERIAL_8N2);
      /*
      * Se establece la configuración del puerto serie
      * adaptándose a la por defecto del micro integrado.
      * (38400 baudios. 8 bits. Sin paridad. 2 bits parada)
      */
      SENSOR_SERIAL.print("[C]");
      smartdelay(10);
      SENSOR_SERIAL.print("[I]");
      smartdelay(120);
      SENSOR_SERIAL.print("[B]");
      smartdelay(50);
      SENSOR_SERIAL.print("[H]");
      smartdelay(500);
      /*
      * Inicialización del sensor según el manual del fabricante:
      * - Ordena al sensor entrar en modo Configuración
      * - Espera un tiempo de precaución antes de enviar la
      *
      siguiente orden (10ms)
      * - Solicita la información de los parámetros del sensor.
      * - Enviar dicha información tarda alrededor de 80ms por
      *
      lo que el tiempo de precaución debe ser mayor en este
      *
      caso.
      * - Ordena al sensor entrar en "modo ingeniería"
      * - Ordena al sensor entrar en "modo bajo demanda"
      */
    }
    bool get_reading(unsigned long &resultado){
      /*
        Para recopilar los datos del sensor, primero se limpia el buffer de
        entrada del puerto serie y se recopilan los primeros 28 bytes del mensaje.

        Si el mensaje comienza por "[AK]", significa que estamos recibiendo un dato
        así que se convierte el valor de una cifra de 8 cifras hexadecimales al
        final del mensaje en un número.
      */
      flushSerial();
      char inData[29];
      int i=0;
      char buff[10];

      SENSOR_SERIAL.print("[Q]");
      smartdelay(40);
      while ((SENSOR_SERIAL.available() > 0) && (i < 28)){
        inData[i] = SENSOR_SERIAL.read();
        i++;
        inData[i] = '\0';
      }

      if (substring(inData,0,4) == "5b41"){
        String hex = substring(inData, 20, 8);
        hex.toCharArray(buff,9);
        resultado = strtol(buff, NULL, 16);
        return true;
      } else {
        return false;
      }
    }

};
#endif
class DataPoint
{
public:
  unsigned long gas_high, gas_avg, date, time = 0;
  long  lat, lon = 0;
  unsigned int avg_count = 0;

  /*
  Con este método comparamos los valores de un nuevo punto de medida con los
  el valor ya almacenado. Si el valor es más alto, se sobreescriben los valores,
  y también se calcula la media de los valores hasta ahora recogidos.
  Al final quedará el primer valor más alto en caso de que se detectaran varios iguales.
  */
  bool add_measurement(DataPoint newData){
    bool was_higher = false;
    if (gas_high < newData.gas_high){
      gas_high = newData.gas_high;
      lat = newData.lat;
      lon = newData.lon;
      date = newData.date;
      time = newData.time;
      was_higher = true;
    }
    avg_count++;
    gas_avg = ((avg_count-1)*gas_avg +newData.gas_high)/(avg_count);
    return was_higher;
  }

  void clear(){
    avg_count = 0;
    gas_high=0;
    gas_avg=0;
  }
};
GasMeter sensor;
TinyGPS gps;

unsigned long session_id, age, last_transmission = 0;
DataPoint new_data, out_data;
RH_RF95 rf95;
uint8_t payload[28] = {0};
void setup() {
  unsigned long date,time;
  sensor.initialize();
  GPS_SERIAL.begin(9600);
  while(!rf95.init()){
    smartdelay(1000);
  }
  rf95.setFrequency(868.1);
  rf95.setModemConfig(RH_RF95::Bw125Cr45Sf128);
  rf95.setHeaderTo(255);
  rf95.setHeaderFrom(DEVICE_ID);
  rf95.setSignalBandwidth(250000);
  rf95.setSpreadingFactor(9);

  #if WAIT_FOR_FIX
  //Esperamos hasta tener una fecha y hora válidas.
  do{
    smartdelay(1000);
    gps.get_datetime(&date,&time,&age);
  } while(age == TinyGPS::GPS_INVALID_AGE);

  /*
  La fecha viene dada como un entero en formato ddmmyy
  La hora viene dada en formato hhmmsscc
  Un unsigned long puede almacenar un valor de hasta 4294967296
  Si eliminamos la información del año y las centésimas, y concatenamos las cifras
  obtenemos un número en formato ddmmhhmmss con un valor máximo de 3112235959
  que será único a la sesión excepto en el caso de que 2 sesiones ocurran en la misma
  fecha, hora, minuto y segundo en el mismo año o años diferentes.
  Dada la baja probabilidad de que esto ocurra junto a la facilidad de comprobar
  en recepción si la sesión a modificar es de este año, utilizamos este sistema
  para identificar cada sesión.
  */
  session_id = (date/100)*1000000 + time/100;

  #else

  randomSeed(analogRead(0));
  session_id = random();
  #endif

  pinMode( GREEN_LED , OUTPUT);
  pinMode( YELLOW_LED , OUTPUT);
  pinMode( RED_LED , OUTPUT);

  last_transmission = millis();
}

void loop() {
  if(sensor.get_reading(new_data.gas_high))
    {
      gps.get_position(&new_data.lat, &new_data.lon, &age);
      gps.get_datetime(&new_data.date, &new_data.time, &age);
      #if SENSOR_MODE == 1
      SENSOR_SERIAL.print("[R]");
      SENSOR_SERIAL.println(session_id, HEX);
      SENSOR_SERIAL.println(new_data.gas_high, HEX);
      SENSOR_SERIAL.println(new_data.lat, HEX);
      SENSOR_SERIAL.println(new_data.lon, HEX);
      SENSOR_SERIAL.println(new_data.date, HEX);
      SENSOR_SERIAL.println(new_data.time, HEX);
      #endif
      out_data.add_measurement(new_data);
      digitalWrite(GREEN_LED, (new_data.gas_high > GREEN_ALERT) ? HIGH : LOW);
      digitalWrite(YELLOW_LED, (new_data.gas_high > YELLOW_ALERT) ? HIGH : LOW);
      digitalWrite(RED_LED, (new_data.gas_high > RED_ALERT) ? HIGH : LOW);
  }

  if ((millis() - last_transmission) > TX_TIME){
    if(out_data.avg_count > 0){
      memcpy(&payload[0], &session_id, 4);
      memcpy(&payload[4], &out_data.gas_high, 4);
      memcpy(&payload[8], &out_data.gas_avg, 4);
      memcpy(&payload[12], &out_data.lat, 4);
      memcpy(&payload[16], &out_data.lon, 4);
      memcpy(&payload[20], &out_data.date, 4);
      memcpy(&payload[24], &out_data.time, 4);
      rf95.send(payload,28);
    }
    out_data.clear();
    last_transmission = millis();
  }

  smartdelay(1000);
}

static void flushSerial(){
  //Limpia los bytes que quedan en el buffer RX
  while(SENSOR_SERIAL.available() !=0){
    SENSOR_SERIAL.read();
  }
}
static String substring(char set[], int start, int len){
  //Devuelve una sección de un array de Char como String
  String s;
  int i;
  for (i=start; i<start+len; i++) {
    s += set[i];
  }
  return s;
}
static void smartdelay(unsigned long ms)
{
  unsigned long start = millis();
  do
  {
    while (GPS_SERIAL.available())
    {
      gps.encode(GPS_SERIAL.read());
    }
  } while (millis() - start < ms);
}
