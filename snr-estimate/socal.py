import sys
import numpy as np
import astropy.units as u

import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.rc('font', family='sans serif', size=16)

kpf_etc_dir = '/Users/ryanrubenzahl/Documents/CPS/KPF/code/KPF-etc/'
sys.path.insert(0,kpf_etc_dir)
from kpf_photon_noise_estimate import KPF_photon_noise_estimate


# Aperture size
D_socal = (3*u.imperial.inch).to(u.cm)
D_keck  = (10*u.m).to(u.cm)


# Integrating sphere specs
# https://www.thorlabs.com/thorproduct.cfm?partnumber=IS200
reflectivity = 0.99 # @ 350 to 1500 nm

sphere = 0 # which ThorLabs sphere to use
# HARPS-N has a 2 inch sphere, NEID is 1 inch
diameter_sphere = [(2*u.imperial.inch).to(u.cm),   (4*u.imperial.inch).to(u.cm)][sphere]
diameter_input  = [(0.5*u.imperial.inch).to(u.cm), (1*u.imperial.inch).to(u.cm)][sphere]
diameter_port   = [(0.5*u.imperial.inch).to(u.cm), (5*u.mm).to(u.cm)           ][sphere]
diameter_fiber  = (200*u.micron).to(u.cm) # (1*u.mm).to(u.cm)
numerical_aperture = 0.22 # Thorlabs fiber numerical aperture
nports = 1

# Integrating sphere properties
port_fraction = (nports*diameter_port**2 + diameter_input**2) / diameter_sphere**2
sphere_multiplier = reflectivity / (1 - reflectivity*(1-port_fraction))

print('IS port fraction:', port_fraction)
print('sphere multiplier: {:.2f}'.format(sphere_multiplier))

# Solar irradiance
S = 1400*u.W/u.m**2

# Sphere functions
# https://web.archive.org/web/20090815182409/http://www.sphereoptics.com/assets/sphere-optic-pdf/sphere-technical-guide.pdf

area_sphere = np.pi*(diameter_sphere/2)**2
area_port   = np.pi*(diameter_port/2)**2
area_fiber  = np.pi*(diameter_fiber/2)**2

# phi_in: input energy
def radiance_on_sphere_wall(phi_in):
    # W / m^2 / sr
    return phi_in / (np.pi*u.sr*area_sphere) * sphere_multiplier

def sphere_throughput_to_port(phi_in):
    #  FoV of illuminated source at port
    Omega = np.pi*u.sr # (simply pi steradians for projected solid angle of hemisphere)
    return radiance_on_sphere_wall(phi_in) * area_port * Omega

def sphere_throughput_to_fiber(phi_in, R=0, NA=numerical_aperture):
    # R = reflectivity of the fiber face
    # NA = numerical aperture of fiber
    Omega = np.pi*u.sr  * NA**2
    return radiance_on_sphere_wall(phi_in) * area_fiber * (1-R) * Omega

print('Throughput at the exit port: {:.3e}'.format(sphere_throughput_to_port(1)))
print('Throughput at the fiber: {:.3e}'.format(sphere_throughput_to_fiber(1)))

# Overfill-factor (area ratio) of fiber cross-section to final input cross-section
overfill_area = 10

# Compute what magnitude star the sun would look like to KPF
throughput = sphere_throughput_to_fiber(1)
#throughput = 2.5*10**(-5) 

# Add effects of fiber from roof->cal bench->FIU
length = 40 + 60 # meters
throughput *= (0.9+0.4)/2 # PDR page 63
#throughput *= 0.45 # H&K 380-410nm

dm = 2.5*np.log10(throughput * (D_socal/D_keck)**2 / overfill_area)
mag_sun = -26.832
mag = mag_sun - dm

if len(sys.argv) > 1:
    texp = float(sys.argv[1]) # seconds
else:
    texp = 20

# Scale to KPF etc working range
dv, orderinfo = KPF_photon_noise_estimate(5800.,mag+5,texp*100, fits_dir=kpf_etc_dir + '/grids/',save_file=False, quiet=True)

print('Throughput at the FIU: {:.3e}'.format(throughput))
print('In the configuration above, the Sun will appear to KPF like a {:.2f} magnitude star observed with Keck'.format(mag))

print('For a {} sec exposure...'.format(texp))
print('     Total velocity uncertainty: {:.2f} cm/s'.format(dv*100))

wave, snr, sigma_rv = orderinfo
print('     Median SNR/order: {:.2f}'.format(np.median(snr)))

if len(sys.argv) > 2:
    if sys.argv[2] == 'plot':
        fig, ax = plt.subplots(1,1,figsize=(10,5))

        ax.plot(wave, snr)
        ax.set(xlabel='Wavelength [nm]')
        ax.set_ylabel('Mean SNR [in order]', color='C0')

        ax2 = ax.twinx()
        ax2.plot(wave, sigma_rv, color='C1')
        ax2.set_ylabel(r'$\sigma_{RV}$ [m/s]', color='C1')

        plt.show()
