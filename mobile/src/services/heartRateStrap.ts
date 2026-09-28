/**
 * Bluetooth heart-rate straps through the standard Heart Rate Service (0x180D).
 *
 * Any strap that follows the Bluetooth SIG profile works (Polar, Garmin HRM,
 * Wahoo, Coospo, most gym straps). The measurement characteristic carries
 * beat-to-beat RR intervals, which is what HRV analysis needs; optical watch
 * bands usually omit them, in which case only heart rate is reported.
 */
import { PermissionsAndroid, Platform } from 'react-native';
import { BleManager, Device, Subscription } from 'react-native-ble-plx';
import { parseHeartRateMeasurement, type HeartRateReading } from './heartRateMeasurement';

export type { HeartRateReading } from './heartRateMeasurement';

const HEART_RATE_SERVICE = '0000180d-0000-1000-8000-00805f9b34fb';
const HEART_RATE_MEASUREMENT = '00002a37-0000-1000-8000-00805f9b34fb';

let manager: BleManager | null = null;
const getManager = () => (manager ??= new BleManager());

function decodeBase64(value: string): Uint8Array {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function ensurePermissions(): Promise<boolean> {
  if (Platform.OS !== 'android') return true;
  const needed = Platform.Version >= 31
    ? [PermissionsAndroid.PERMISSIONS.BLUETOOTH_SCAN, PermissionsAndroid.PERMISSIONS.BLUETOOTH_CONNECT]
    : [PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION];
  const result = await PermissionsAndroid.requestMultiple(needed);
  return needed.every((p) => result[p] === PermissionsAndroid.RESULTS.GRANTED);
}

/** Scans for the first strap advertising the Heart Rate Service. */
export async function findStrap(timeoutMs = 15000): Promise<Device> {
  if (!(await ensurePermissions())) throw new Error('Bluetooth permission was not granted.');
  const ble = getManager();
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      ble.stopDeviceScan();
      reject(new Error('No heart-rate strap found. Wet the strap contacts and wear it, then try again.'));
    }, timeoutMs);
    ble.startDeviceScan([HEART_RATE_SERVICE], null, (error, device) => {
      if (error) {
        clearTimeout(timer);
        ble.stopDeviceScan();
        reject(error);
      } else if (device) {
        clearTimeout(timer);
        ble.stopDeviceScan();
        resolve(device);
      }
    });
  });
}

/** Connects and streams readings until the returned stop function is called. */
export async function streamHeartRate(
  device: Device,
  onReading: (reading: HeartRateReading) => void,
): Promise<() => Promise<void>> {
  const connected = await device.connect();
  await connected.discoverAllServicesAndCharacteristics();
  const sub: Subscription = connected.monitorCharacteristicForService(
    HEART_RATE_SERVICE, HEART_RATE_MEASUREMENT,
    (error, characteristic) => {
      if (!error && characteristic?.value) onReading(parseHeartRateMeasurement(decodeBase64(characteristic.value)));
    },
  );
  return async () => {
    sub.remove();
    await connected.cancelConnection().catch(() => undefined);
  };
}
