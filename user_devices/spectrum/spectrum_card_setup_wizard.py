# Author: Marcus Culemann
# Version: March 2024

import numpy as np
from spectrum_card_interface import SpectrumCardInterface
from spectrum_card_waveform_generation_tool import SpectrumCardWaveformTool

######################################################################################################
## This file automatically sets up the Spectrum Card according to the chosen settings.              ##
######################################################################################################

#####################
# Waveform settings #
#####################

freq_array_horizontal = np.array([200e6])
freq_array_vertical = np.array([60e6, 61e6])

amplitude_array_horizontal = np.ones_like(freq_array_horizontal)
amplitude_array_vertical = np.ones_like(freq_array_vertical)

rng = np.random.default_rng(seed=13438354524)
phase_array_horizontal = rng.uniform(size=freq_array_horizontal.size)*2*np.pi
phase_array_vertical = rng.uniform(size=freq_array_vertical.size)*2*np.pi

#################
# Card Settings #
#################
spectrum_card = SpectrumCardInterface()
spectrum_card.ch1_enabled = True
spectrum_card.ch2_enabled = True
spectrum_card.amplitude_ch1 = 2500
spectrum_card.amplitude_ch2 = 158
spectrum_card.num_loops = 1000
spectrum_card.memory_size = 1024**2 * 20
spectrum_card.sampleRate = 625

########################################
# Generate the waveform and setup card #
########################################

waveform_generator = SpectrumCardWaveformTool(freq_array_horizontal=freq_array_horizontal,
                                     freq_array_vertical=freq_array_vertical,
                                     amplitude_array_horizontal=amplitude_array_horizontal,
                                     amplitude_array_vertical=amplitude_array_vertical,
                                     phase_array_horizontal=phase_array_horizontal,
                                     phase_array_vertical=phase_array_vertical,
                                     num_samples=spectrum_card.memory_size,
                                     sample_rate=spectrum_card.sampleRate
                                     )

spectrum_card.replay_data_ch1 = waveform_generator.getWaveformHorizontal()
spectrum_card.replay_data_ch2 = waveform_generator.getWaveformVertical()

spectrum_card.setupCard()
spectrum_card.startReplay()

spectrum_card.closeCard()