import sys
import csv
import time
import pyrheliometer
from astropy.time import Time

try:
    pyr = pyrheliometer.EKOPyrheliometer()
    try:
        with open(sys.argv[1], 'a', buffering=1) as f:
            writer = csv.writer(f)#, delimiter=',', lineterminator='\n')
            print('Logging irradiance data...')
            while True:

                # Timestamp for data polling
                jd1 = Time.now().jd
                min_irrad, max_irrad, sensitivity, out_voltage, solar_irrad, temperature = pyr.poll()
                jd2 = Time.now().jd
                time_poll = (jd1+jd2)/2  

                # Write to file
                writer.writerow([time_poll, min_irrad, max_irrad, sensitivity, out_voltage, solar_irrad, temperature])
                time.sleep(1)
                f.flush()
                
    except KeyboardInterrupt:
        print('Closing connection.')
        pyr.close_connection()

except Exception as e:
    print(repr(e))