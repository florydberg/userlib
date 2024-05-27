# Author: Marcus Culemann
# Version: March 2024

import numpy as np
import numexpr as ne
from scipy.signal import correlate, find_peaks
from dataclasses import dataclass
from typing import Any

######################################################################################################
## This file deals with the generation of waveforms for the Spectrum card.                          ##
## The provided class takes care of data formats and specific settings that work with               ##
## the spectrum card.                                                                               ##
######################################################################################################

@dataclass
class SpectrumCardWaveformTool():
    """
    This class takes care of the generation of RF waveforms for the spectrum card.
    We only focus on the waveforms needed for the generation tweezer arrays.

    Class attributes:
        - freq_array_horizontal: Tuple including all the frequencies in Hz for the horizontal AOD. 
                                 Do not forget the comma even for single entries!
        - freq_array_vertical: Tuple including all the frequencies in Hz for the vertical AOD.
                               Do not forget the comma even for single entries!
        - amplitude_array_horizontal: Tuple including all the amplitudes for the above defined horizontal frequencies.
                                      The amplitudes all only responsible for the relative weighing of the different frequencies.
                                      They do not determine the output amplitude of the card. Do not forget the comma even for single entries!
        - amplitude_array_vertical: Tuple including all the amplitudes for the above defined vertical frequencies. 
                                    The amplitudes all only responsible for the relative weighing of the different frequencies.
                                    They do not determine the output amplitude of the card. Do not forget the comma even for single entries!
        - num_samples: Choose the number of points of the generated waveform. Pass 'auto' to let the program decide on it's own.
                       You can also choose a fixed value by passing an integer. num_samples correpsonds to memory size in the Spectrum Card.
                       TODO: Implement the auto function via SciPy correlate and findPeriodicity().
        - sample_rate: Sample rate of the Spectrum Card in MHz. For allowed settings see spectrum_card_interface.py. 1Mz = 1024**2 Hz!
    Usage: 
        - Specify the parameters for the tweezer array. You can either pass them on construction of the class 
          or modify them right after construction.
    """

    freq_array_horizontal: tuple = (1e6,)
    freq_array_vertical: tuple = (1e6,)
    amplitude_array_horizontal: tuple = (1,)
    amplitude_array_vertical: tuple = (1,)
    phase_array_horizontal: tuple = (0,)
    phase_array_vertical: tuple = (0,)
    num_samples: int = 1024**2 * 20
    sample_rate: int = 625

    def computeWaveform(self, freq_array, amp_array, phase_array, memory_size, sample_rate):
        """
        Compute the waveform composed of multiple frequencies using numexpr.
        This is much quicker than basic numpy!
        """
        # time_conversion=1000**2/1024**2
        # sample_rate *= 1048576 # 1024**2
        sample_rate*=1e6
        time = np.linspace(0, memory_size/sample_rate, memory_size, endpoint=False)
        freq_array = 2*np.pi*freq_array
        # Build the numexpr string
        expr = '0'
        for freq, amp, phase in zip(freq_array, amp_array, phase_array):
            expr += f'+{amp}*sin({freq}*time+{phase})'
        result = ne.evaluate(expr)
        result /= np.max(np.abs(result))
        result *= (2**15-1)
        return np.int16(result)

    def getWaveformHorizontal(self):
        """
        Retrieve the waveform for the horizontal AOD with the specified parameters.
        """
        return self.computeWaveform(self.freq_array_horizontal, self.amplitude_array_horizontal, self.phase_array_horizontal, self.num_samples, self.sample_rate)

    def getWaveformVertical(self):
        """
        Retrieve the waveform for the vertical AOD with the specified parameters.
        """
        return self.computeWaveform(self.freq_array_vertical, self.amplitude_array_vertical, self.phase_array_vertical, self.num_samples, self.sample_rate)

    def findPeriodicity_horizontal(self):
        """
        Approximate the periodicity of the signal. It is sufficient to evaluate the signal using larger timesteps. delta t <= 1/Nyquist_frequency.
        Returns the num_samples needed to approximate a periodic signal.
        """
        # Evaluate the signal on larger timesteps
        sample_rate = 1/(2*np.max(self.freq_array_horizontal))
        num_samples = 1e5/np.min(self.freq_array_horizontal) * sample_rate # 1e5 periods of the lowest frequency
        waveform = self.computeWaveform(self.freq_array_horizontal, self.amplitude_array_horizontal, self.phase_array_horizontal, num_samples, sample_rate)
        # Compute autocorrelation
        autocorrelation = correlate(waveform, waveform, mode='full', method='auto')
        len = autocorrelation.size
        autocorrelation = autocorrelation[len//2:]
        # Find highest peak.
        peaks = find_peaks(autocorrelation)[0]
        highest_peak_idx = np.argmax(autocorrelation[peaks])
        required_num_samples = peaks[highest_peak_idx]
        return required_num_samples
    
    def findPeriodicity_vertical(self):
        """
        Approximate the periodicity of the signal. It is sufficient to evaluate the signal using larger timesteps. delta t <= 1/Nyquist_frequency.
        Returns the num_samples needed to approximate a periodic signal.
        """
        # Evaluate the signal on larger timesteps
        sample_rate = 1/(2*np.max(self.freq_array_horizontal))
        num_samples = 1e5/np.min(self.freq_array_horizontal) * sample_rate # 1e5 periods of the lowest frequency
        waveform = self.computeWaveform(self.freq_array_horizontal, self.amplitude_array_horizontal, self.phase_array_horizontal, num_samples, sample_rate)
        waveform = np.float64(waveform)
        # Compute autocorrelation
        autocorrelation = correlate(waveform, waveform, mode='full', method='auto')
        len = autocorrelation.size
        autocorrelation = autocorrelation[len//2:]
        # Find highest peak.
        peaks = find_peaks(autocorrelation)[0]
        highest_peak_idx = np.argmax(autocorrelation[peaks])
        required_num_samples = peaks[highest_peak_idx]
        return required_num_samples

    def getWaveformHorizontal_periodic(self):
        """
        Returns waveform with the specified parameters. num_samples is automatically chosen to produce an approximately periodic signal. 
        """
        num_samples = self.findPeriodicity_horizontal()
        return self.computeWaveform(self.freq_array_horizontal, self.amplitude_array_horizontal, self.phase_array_horizontal, num_samples, self.sample_rate)

    def getWaveformVertrical_periodic(self):
        """
        Returns waveform with the specified parameters. num_samples is automatically chosen to produce an approximately periodic signal. 
        """
        num_samples = self.findPeriodicity_vertical()
        return self.computeWaveform(self.freq_array_vertical, self.amplitude_array_vertical, self.phase_array_vertical, num_samples, self.sample_rate)
    