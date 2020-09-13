# Pulsar Analysis Package
```
Author      : Hrishikesh Shetgaokar(hrishikesh036@gmail.com)
Guide       : Prof. Avinash Deshpande
Co-Guide    : Dr. Kaushar Vaidya
Institute   : BITS Pilani, Pilani Campus & Raman Research Institue  
```

## Description:

This package was developed during my time at Raman Research Institute while working
with Prof Avinash Deshpande (*'desh'*). This is an attempt to systematically refactor
the highly inefficient and unreadable code which I had written during my naive days.

The objective of the 4 month thesis project was to study the radio emissions of a drifter
pulsar at different bands to better understand the magnetosphere. More information can be found 
in my Thesis Report ([Drifting_Subpulse_Thesis.pdf](Drifting_Subpulse_Thesis.pdf))

The idea here is to use OOPs to build a simple data processing tool for pulsar data.

## Table of Contents
1. [MBR to Dynamic Spectrum](#1-mbr-to-dynamic-spectrum)
2. [Dynamic Spectrum to Time Series](#2-dynamic-spectrum-to-time-series)


## 1. MBR to Dynamic Spectrum
The multi frequency data were recorded using RRI-GBT Multi-Band Receiver (MBR). The time varying voltage data from the MBR along with a header are saved in '.mbr' files.
These '.mbr' data files are to be placed in [MBRData](MBRData) directory for processing.

![mbrPacket](readmeImages/mbrPacket.png)
**

<p align="center">
  <img src="readmeImages/mbrPacket.png" title="Figure 1.1: MBR packet header"/>
</p>


Each mbr data file is made up of 2,027,520 mbr packets. The mbr packet is 1056 bytes long. 
The first 32 bytes in mbr packet is the header and stores information like Observation ID, Source Name, Local Oscillator 
(LO) frequency, GPS count, packet count, etc. and the structure of its header is shown in Fig 3.1. The 1024 bytes after the 
header contain raw voltage data sampled at 33 MHz. Of these 1024, 512 bytes are for X polarization and Y polarization each.

Each observation band is 16 MHz wide and the central frequency of this band can be calculated from LO frequency by using the formula RF = LO ± IF. Of these two values select the one which lies in the band. The LO, IF and resulting RF (central frequency) values obtained for 8 channels is given in Table 3.2

The recorded data also suffer from missing packets. These missing packets can be considered as bad data and are flagged (given a value -9999 in dynamic spectrum) so that they can be avoided while calculating time sequence. The missing packets were detected by keeping a count of number of packets read and comparing that to the packet number present in the header of current packet being read. The missing data can be seen as dark blue solid patches in dynamic spectra (Fig 3.4).


## 2. Dynamic Spectrum to Time Series 
