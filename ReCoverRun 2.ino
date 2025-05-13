// This sketch manages the sensor read (FSR and potentiometer) and data sending through BLE
// It is the hardware side of the ReCoverRun rehabilitation game.

// This sketch advertises as ReCover and has a single service with 2 characteristics.
// The FSRUUID characteristic is used to send fsr data.
// The POTUUID characteristic is used to send potentiometer data.

// This sketch was written for the Hiletgo ESP32 dev board found here:
// https://www.amazon.com/HiLetgo-ESP-WROOM-32-Development-Microcontroller-Integrated/dp/B0718T232Z/ref=sr_1_3?keywords=hiletgo&qid=1570209988&sr=8-3

// ---------- includes ----------
// ADC calibration
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
// BLE communication
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>


// ---------- defines ----------
// ADC reads
#define NUM_SAMPLES 2 
// BLE service and characteristics
#define serviceUUID "A9E90000-194C-4523-A473-5FDF36AA4D20"
#define DATAUUID "A9E90001-194C-4523-A473-5FDF36AA4D20"


// ---------- variables ----------
// sensor acquisition
adc_channel_t adc_fsr = ADC_CHANNEL_4;
adc_channel_t adc_pot = ADC_CHANNEL_0;
adc_oneshot_unit_handle_t adc_handle;
adc_cali_handle_t cali_handle;
int send_delay = 50;
bool _windowAveraging = false; 
float fsr_window[NUM_SAMPLES] = {0};
float pot_window[NUM_SAMPLES] = {0};
// BLE
bool deviceConnected = false;
bool oldDeviceConnected = false;
BLEServer* pServer = 0;
BLECharacteristic* pCharacteristicCommandData = 0;
// BLECharacteristic* pCharacteristicData = 0;

// ---------- classes/functions ----------
uint32_t calibrate_ADC_Raw(int ADC_Raw) {

  // Function to obtain the calibrated voltage (in mV)
  // Inputs:
  //    ADC_Raw: int, adc raw read
  // Outputs:
  //    voltage_calibrated: int, calibrated voltage (in mV)

    int voltage_calibrated = 0;
    if (cali_handle) {
        adc_cali_raw_to_voltage(cali_handle, ADC_Raw, &voltage_calibrated);
    }
    return voltage_calibrated;
}



class BTServerCallbacks : public BLEServerCallbacks
{
  // BLE server-client custom callbacks
    void onConnect(BLEServer* pServer)
    {
    Serial.println("Connected...");
    deviceConnected = true;
    };

    void onDisconnect(BLEServer* pServer)
    {
    Serial.println("Disconnected...");
    deviceConnected = false;
    }
};


class BTCallbacks : public BLECharacteristicCallbacks
{
  // BLE characteristics custom callbacks
    void onRead(BLECharacteristic* pCharacteristic)
    {
    }
    /*
    void onWrite(BLECharacteristic* pCharacteristic)
    {
        uint8_t* data = pCharacteristic->getData();
        int len = pCharacteristic->getValue().isEmpty() ? 0 : pCharacteristic->getValue().length();

        if (len > 0)
        {
            // if the first byte is 0x01 / on / true
            if (data[0] == 0x01)
                digitalWrite(led, HIGH);
            else
                digitalWrite(led, LOW);
        }
    }*/
};

void BluetoothStartAdvertising()
{
    if (pServer != 0)
    {
        BLEAdvertising* pAdvertising = pServer->getAdvertising();
        pAdvertising->start();
    }
}

void BluetoothStopAdvertising()
{
    if (pServer != 0)
    {
        BLEAdvertising* pAdvertising = pServer->getAdvertising();
        pAdvertising->stop();
    }
}

void setup()
{
    Serial.begin(115200);

    //ADC
    // Initialize ADC One-shot mode
    adc_oneshot_unit_init_cfg_t init_config = {
        .unit_id = ADC_UNIT_1
    };
    adc_oneshot_new_unit(&init_config, &adc_handle);

    // Configure ADC channel (A0 corresponds to ADC1_CHANNEL_0 on ESP32)
    adc_oneshot_chan_cfg_t config = {
        .atten = ADC_ATTEN_DB_11,      // Fixed field order
        .bitwidth = ADC_BITWIDTH_DEFAULT
    };
    adc_oneshot_config_channel(adc_handle, adc_fsr, &config); // FSR ADC
    adc_oneshot_config_channel(adc_handle, adc_pot, &config); // POT ADC

    // Initialize ADC calibration
    adc_cali_scheme_ver_t scheme;
    if (adc_cali_check_scheme(&scheme) == ESP_OK) {
        adc_cali_curve_fitting_config_t cali_config = {
            .unit_id = ADC_UNIT_1,
            .atten = ADC_ATTEN_DB_11,
            .bitwidth = ADC_BITWIDTH_DEFAULT
        };
        ESP_ERROR_CHECK(adc_cali_create_scheme_curve_fitting(&cali_config, &cali_handle));
    }

    // BLE setup
    BLEDevice::init("ReCover");
    // BLEDevice::setCustomGattsHandler(my_gatts_event_handler);
    // BLEDevice::setCustomGattcHandler(my_gattc_event_handler);

    pServer = BLEDevice::createServer();
    BLEService* pService = pServer->createService(serviceUUID);
    pServer->setCallbacks(new BTServerCallbacks());

    // Data (FSR + POT) characteristic
    pCharacteristicCommandData = pService->createCharacteristic(
        DATAUUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);

    pCharacteristicCommandData->setCallbacks(new BTCallbacks());
    pCharacteristicCommandData->addDescriptor(new BLE2902());


    pService->start();
    BluetoothStartAdvertising();
}

void loop()
{
    int adc_raw = 0;
    uint32_t voltage_calibrated_fsr;
    uint32_t voltage_calibrated_pot;

    // FSR
    float fsr_mean = 0;
    uint16_t fsr_int;
    // POT
    float pot_mean = 0;
    uint16_t pot_int;
    // BLE send
    uint8_t data_send[4];


    if (pServer != 0)
    {
        // client disconnect, restart advertising
        if (!deviceConnected && oldDeviceConnected)
        {
            delay(500);                  // give the bluetooth stack the chance to get things ready
            pServer->startAdvertising(); // restart advertising
            Serial.println("start advertising");
            oldDeviceConnected = deviceConnected;
        }

        // client connect
        if (deviceConnected && !oldDeviceConnected)
        {
            oldDeviceConnected = deviceConnected;
        }
    }

    // Next element: Get new adc read and calibrate it
    adc_oneshot_read(adc_handle, adc_fsr, &adc_raw);
    voltage_calibrated_fsr = calibrate_ADC_Raw(adc_raw); // returns in mV directly
    adc_oneshot_read(adc_handle, adc_pot, &adc_raw);
    voltage_calibrated_pot = calibrate_ADC_Raw(adc_raw); // returns in mV directly


    // Window averaging
    if (_windowAveraging) {

      for (int i = NUM_SAMPLES - 2; i >= 0; i--){

        fsr_window[i+1] = fsr_window[i]; // shift elements in old array 1 position to the right
        fsr_mean += fsr_window[i]; // sum up first n-1 elements

        pot_window[i+1] = pot_window[i];
        pot_mean += pot_window[i];
      }

      fsr_window[0] = voltage_calibrated_fsr;
      fsr_mean += voltage_calibrated_fsr;

      pot_window[0] = voltage_calibrated_pot;
      pot_mean += voltage_calibrated_pot;

      // Finalize mean value
      fsr_mean = fsr_mean/NUM_SAMPLES;
      pot_mean = pot_mean/NUM_SAMPLES;

    } else {
      fsr_mean = (float) voltage_calibrated_fsr;
      pot_mean = (float) voltage_calibrated_pot;
    }
    

    fsr_int = (uint16_t) (fsr_mean*10); // keep 1 decimal point
    // convert to Little Endian format (LSB, MSB)
    data_send[0] = fsr_int;
    data_send[1] = fsr_int >> 8; 

    pot_int = (uint16_t) (pot_mean*10);
    // convert to Little Endian format (LSB, MSB)
    data_send[2] = pot_int;
    data_send[3] = pot_int >> 8; 

    if (deviceConnected){ // Send data to client

        // Set the value of the characteristic to the byte array
        pCharacteristicCommandData->setValue(data_send, 4);
    
        // Notify the client
        pCharacteristicCommandData->notify();

        // Serial.println(fsr_mean);
        // Serial.println(pot_mean);

    }
    
    delay(send_delay);
}