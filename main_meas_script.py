import sys, os, time
import datetime

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as ss

import adi

def measure_psd_wideband(sdr_obj, center_freq_lst, psd_nfft):
    freq_arr = []
    psd_arr = []
    
    for c_freq_idx, center_freq in enumerate(center_freq_lst):

        sdr_obj.rx_lo = int(center_freq)
        sdr_obj.rx_destroy_buffer() # clears the RX buffer, make the new settings take effect
        rx_sig = sdr_obj.rx()

        rx_sig_freq_arr, rx_sig_psd_arr = ss.welch(rx_sig, fs=sdr.sample_rate, window='hann', noverlap=psd_nfft // 2, 
                                                    nfft=psd_nfft, nperseg=psd_nfft, return_onesided=False)

        sorted_rx_sig_freq_arr = np.concatenate((rx_sig_freq_arr[-(psd_nfft // 2):], rx_sig_freq_arr[0:psd_nfft // 2])) + center_freq
        sorted_rx_sig_psd_arr = np.concatenate((rx_sig_psd_arr[-(psd_nfft // 2):], rx_sig_psd_arr[0:psd_nfft // 2]))

        # trim the frequency range
        if c_freq_idx == len(center_freq_lst) - 1:
            sel_idx = np.where(sorted_rx_sig_freq_arr <= freq_stop + freq_bin_res // 2)
            sorted_rx_sig_freq_arr = sorted_rx_sig_freq_arr[sel_idx]
            sorted_rx_sig_psd_arr = sorted_rx_sig_psd_arr[sel_idx]

        freq_arr.append(sorted_rx_sig_freq_arr)
        psd_arr.append(sorted_rx_sig_psd_arr)
    
    return freq_arr, psd_arr

if __name__ == "__main__":
    # Wideband sweep
    sample_rate = int(61.44e6) # single-channel: min: 520.83e3, max: 61.44e6 [SPS], dual-channel: min: 520.83e3, max: 30.72e6 [SPS]

    freq_start = 300e6
    freq_stop = 3000e6
    psd_nfft = 2**12 # should be a power of two for fast computation
    n_snapshots = 2**10 # also a power of 2 to keep the buffer size 

    freq_bin_res = sample_rate / psd_nfft
    print("Frequency bin resolution: %1.1f [KHz]" % (freq_bin_res / 1e3))
    buffer_size = psd_nfft * n_snapshots # min: 2, max: 2**24 = 16 777 216 # number of samples returned per call to rx()/tx()

    center_freq_lst = np.arange(freq_start + sample_rate // 2, freq_stop + sample_rate // 2, sample_rate)

    # Pluto SDR setup
    rx_gain = 50 # fc: 70 … 1300 [MHz] min: -1, max: 73, fc: 130 ... 4000 [MHz] min: -3, max: 71,  fc: 4000 … 6000 [MHz] min: -10 max: 62 [dB], For all freq: min: -1 max: 62 [dB]

    sdr = adi.Pluto("ip:192.168.2.1")
    sdr.sample_rate = int(61.44e6) # single-channel: min: 520.83e3, max: 61.44e6 [SPS], dual-channel: min: 520.83e3, max: 30.72e6 [SPS]
    sdr.rx_rf_bandwidth = int(61.44e6) 
    sdr.rx_buffer_size = buffer_size # min: 2, max: 2**24 = 16 777 216 # number of samples returned per call to rx()/tx()

    sdr.gain_control_mode_chan0 = 'manual'
    sdr.rx_hardwaregain_chan0 = rx_gain # fc: 70 … 1300 [MHz] min: -1, max: 73, fc: 130 ... 4000 [MHz] min: -3, max: 71,  fc: 4000 … 6000 [MHz] min: -10 max: 62 [dB], For all freq: min: -1 max: 62 [dB]

    start_time = time.time()
    freq_arr, psd_arr = measure_psd_wideband(sdr, center_freq_lst, psd_nfft)
    sweep_time = time.time() - start_time
    print("Single sweep time: %1.2f [s]" % (sweep_time))

    # saving the data as binary file is over 2.5 times more memory efficient
    # single sweep takes about 1 min
    n_sweeps = int(60 * 24 *5.5) # save data for about 5 days
    print("Total measurment time: %1.2f [h]" % (sweep_time * n_sweeps / 3600))

    save_freq_arr_once = True

    datetime_arr = []
    for sweep_idx in range(n_sweeps):
        
        start_datetime = datetime.datetime.now()
        freq_arr, psd_arr = measure_psd_wideband(sdr, center_freq_lst, psd_nfft)
        stop_datetime = datetime.datetime.now()
        
        datetime_diff = stop_datetime - start_datetime
        mid_measurment_datetime = start_datetime  + datetime_diff / 2
        datetime_arr.append(mid_measurment_datetime)
        
        np.save("data/datetime_arr.npy", datetime_arr)
        
        if save_freq_arr_once:
            np.save("data/freq_arr.npy", np.concatenate(freq_arr))
            save_freq_arr_once = False
            
        np.save("data/psd_arr_%d.npy" %(sweep_idx), np.concatenate(psd_arr))
